"""MastiSense model training pipeline.

Trains two independent XGBoost classifiers (7-day, 14-day) with:
  - Cow-level stratified train/validation/test split (§7)
  - Incomplete-window label exclusion per horizon (§3)
  - Early stopping on validation AUCPR (§9)
  - Logistic Regression baseline for uplift comparison (§9)
  - Probability calibration on validation predictions (§8)
  - Brier score & reliability curve (§8)
  - AUC > 0.99 audit (§9)
  - Versioned artifact output (§15)
  - Full training configuration saved (§9)

Run:  python train_model.py
"""

import hashlib, json, platform, sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from xgboost import XGBClassifier

from app.services.calibration import (
    apply_calibration,
    compute_brier_score,
    compute_reliability_curve,
    fit_calibrator,
)
from app.services.features import (
    FIXED_GOOD_VALUES,
    SIGNALS,
    add_scc_staleness_to_training,
    engineer,
)
from app.services.versioning import (
    check_promotion_safety,
    list_versions,
    load_current_model,
    next_version,
    promote,
    record_promotion_status,
    save_model_version,
)
from config import (
    DATA_TYPE,
    FEATURE_PIPELINE_VERSION,
    MODELS_DIR,
    TARGET_RECALL,
    TARGET_RECALL_7D,
    TARGET_RECALL_14D,
    TARGET_RECALLS,
    TRAINING_SEED,
    USE_REAL_FARM_FEATURES,
)

# ── Columns excluded from features (§7) ───────────────────────────────
# Identifiers, labels, anything only knowable because an event happened.
NON_FEATURE_COLS = [
    "cow_id", "timestamp", "target_7d", "target_14d", "event_onset_day",
    "subclinical", "breed", "calving_date", "herd_id",
    # SCC staleness intermediaries (the features days_since_scc, scc_stale
    # ARE kept — these are the raw columns used to derive them).
]


# ── Splitting (§7) ────────────────────────────────────────────────────

def cow_split(df):
    """Cow-level stratified 70/15/15 split.  No animal in >1 split."""
    labels = df.groupby("cow_id")["target_7d"].max().reset_index()
    pos = labels.loc[labels.target_7d == 1, "cow_id"].to_numpy()
    neg = labels.loc[labels.target_7d == 0, "cow_id"].to_numpy()
    rng = np.random.default_rng(TRAINING_SEED)
    rng.shuffle(pos)
    rng.shuffle(neg)

    def split(a):
        n = len(a)
        return a[: int(0.70 * n)], a[int(0.70 * n) : int(0.85 * n)], a[int(0.85 * n) :]

    pt, pv, pe = split(pos)
    nt, nv, ne = split(neg)
    return (
        df[df.cow_id.isin(set(np.r_[pt, nt]))],
        df[df.cow_id.isin(set(np.r_[pv, nv]))],
        df[df.cow_id.isin(set(np.r_[pe, ne]))],
    )


def report_split(name, split_df, target_col):
    """Print and return per-split statistics (§7)."""
    n = len(split_df)
    n_cows = split_df.cow_id.nunique()
    pos = int(split_df[target_col].sum())
    neg = n - pos
    rate = pos / max(1, n)
    info = {
        "name": name,
        "n_cows": n_cows,
        "n_rows": n,
        "positive": pos,
        "negative": neg,
        "positive_rate": round(rate, 4),
    }
    print(f"  {name}: {n_cows} cows, {n:,} rows, {pos} pos / {neg} neg ({rate:.2%})")
    return info


# ── Incomplete-window exclusion (§3) ──────────────────────────────────

def exclude_incomplete_windows(df, horizon, target_col):
    """Remove rows where the label window extends beyond the cow's timeline.

    For each cow, if we have data through day D_max, then rows where
    D_max - current_day < horizon cannot have a reliable label — we don't
    know whether a mastitis event would have occurred in the unobserved
    future window.  The generator assigns these as 0, but they should be
    excluded from training rather than defaulting to negative (§3).

    This is applied per-horizon independently (Q1 decision):
    - 7d model: excludes rows where future window < 7 days
    - 14d model: excludes rows where future window < 14 days
    """
    df = df.copy()
    df["_ts_norm"] = pd.to_datetime(df["timestamp"]).dt.normalize()
    keep_mask = pd.Series(True, index=df.index)

    for cow_id, g in df.groupby("cow_id"):
        max_day = g["_ts_norm"].max()
        # Rows where the full horizon isn't observable
        incomplete = (max_day - g["_ts_norm"]).dt.days < horizon
        keep_mask.loc[g.index[incomplete]] = False

    n_excluded = int((~keep_mask).sum())
    df_clean = df.loc[keep_mask].drop(columns=["_ts_norm"])
    print(f"  Incomplete-window exclusion ({target_col}, horizon={horizon}d): "
          f"removed {n_excluded} rows ({n_excluded/len(df):.1%})")
    return df_clean


# ── Threshold tuning (§8) ─────────────────────────────────────────────

def choose_threshold(y, p, target_recall=TARGET_RECALL):
    """Grid-search threshold on validation data targeting recall ≥ target_recall.

    Among thresholds meeting the target recall floor (rec >= target_recall),
    prioritizes precision first, then specificity, then recall.
    If no threshold reaches target_recall, falls back to the threshold maximizing
    F1 (balanced precision and recall) rather than maximizing recall at all costs.
    """
    best = None
    best_fallback = None
    best_f1 = -1.0
    for t in np.linspace(0.01, 0.99, 197):
        pred = (p >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
        rec = tp / max(1, tp + fn)
        spec = tn / max(1, tn + fp)
        prec = tp / max(1, tp + fp)
        item = (t, rec, spec, prec)

        if rec >= target_recall:
            # Prioritize precision, then specificity, then recall among qualifying thresholds
            if best is None or (prec, spec, rec) > (best[3], best[2], best[1]):
                best = item

        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        if f1 > best_f1:
            best_f1 = f1
            best_fallback = item

    return best if best is not None else (best_fallback if best_fallback is not None else (0.5, 0, 0, 0))


# ── Evaluation (§9) ───────────────────────────────────────────────────

def evaluate(y, p, t, calibrated_p=None):
    """Full metric set for a single horizon."""
    pred = (p >= t).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    result = {
        "auc": float(roc_auc_score(y, p)),
        "average_precision": float(average_precision_score(y, p)),
        "threshold": float(t),
        "sensitivity_recall": float(recall_score(y, pred, zero_division=0)),
        "specificity": float(tn / max(1, tn + fp)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }
    # Brier score on calibrated probabilities (or raw if no calibration).
    brier_probs = calibrated_p if calibrated_p is not None else p
    result["brier_score"] = float(brier_score_loss(y, brier_probs))
    return result


# ── AUC > 0.99 audit (§9) ─────────────────────────────────────────────

def audit_high_auc(auc, df, train_cows, val_cows, test_cows, features, target_col):
    """If AUC exceeds 0.99, run automated checks and return audit findings."""
    findings = []
    if auc <= 0.99:
        return {"triggered": False, "auc": auc}

    findings.append(f"AUC={auc:.4f} exceeds 0.99 — auditing for leakage.")

    # Check 1: duplicate cow_ids across splits
    overlap_tv = set(train_cows) & set(val_cows)
    overlap_te = set(train_cows) & set(test_cows)
    overlap_ve = set(val_cows) & set(test_cows)
    if overlap_tv or overlap_te or overlap_ve:
        findings.append(f"LEAKAGE: cow overlap train∩val={len(overlap_tv)}, "
                       f"train∩test={len(overlap_te)}, val∩test={len(overlap_ve)}")
    else:
        findings.append("No cow overlap across splits — OK.")

    # Check 2: duplicated rows
    n_dup = df.duplicated(subset=["cow_id", "timestamp"]).sum()
    findings.append(f"Duplicated (cow_id, timestamp) rows: {n_dup}")

    # Check 3: feature importance concentration
    findings.append(
        "Note: High AUC on synthetic data may reflect that the generator's "
        "deterioration curves are more deterministic than real-world data. "
        "This AUC should NOT be cited as real-world performance."
    )

    return {"triggered": True, "auc": auc, "findings": findings}


# ── Train one horizon ─────────────────────────────────────────────────

def train_horizon(df_full, target_col, horizon_days, split_data, target_recall=None):
    """Train XGBoost + baseline LR for one forecast horizon."""
    train, val, test = split_data
    features = [c for c in train.columns if c not in NON_FEATURE_COLS]
    if target_recall is None:
        target_recall = TARGET_RECALLS.get(f"{horizon_days}d", TARGET_RECALL)

    print(f"\n{'='*60}")
    print(f"Training {horizon_days}-day model  (target: {target_col}, target_recall: {target_recall:.2f})")
    print(f"{'='*60}")

    # Per-split statistics
    split_info = []
    for name, sdf in [("train", train), ("val", val), ("test", test)]:
        split_info.append(report_split(name, sdf, target_col))

    Xtr, ytr = train[features], train[target_col]
    Xv, yv = val[features], val[target_col]
    Xte, yte = test[features], test[target_col]

    # ── Logistic Regression baseline ──
    baseline = LogisticRegression(
        max_iter=1000, class_weight="balanced", solver="liblinear"
    ).fit(Xtr, ytr)
    base_p = baseline.predict_proba(Xte)[:, 1]

    # ── XGBoost ──
    pos = max(1, int(ytr.sum()))
    neg = max(1, int((ytr == 0).sum()))
    model = XGBClassifier(
        n_estimators=400,
        max_depth=4,
        learning_rate=0.04,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=3,
        reg_lambda=1.5,
        objective="binary:logistic",
        eval_metric="aucpr",
        scale_pos_weight=neg / pos,
        random_state=TRAINING_SEED,
        n_jobs=4,
        tree_method="hist",
        early_stopping_rounds=30,
    )
    model.fit(Xtr, ytr, eval_set=[(Xv, yv)], verbose=False)
    n_est_used = int(getattr(model, "best_iteration", model.n_estimators) or model.n_estimators) + 1

    # ── Threshold tuning on validation ──
    raw_val_probs = model.predict_proba(Xv)[:, 1]
    threshold, vr, vs, vp = choose_threshold(yv, raw_val_probs, target_recall)
    print(f"  Threshold: {threshold:.3f}  (target={target_recall:.2f}, val recall={vr:.3f}, spec={vs:.3f}, prec={vp:.3f})")

    # ── Calibration on validation predictions (§8) ──
    calibrator = fit_calibrator(yv.to_numpy(), raw_val_probs, method="sigmoid")
    cal_val_probs = apply_calibration(raw_val_probs, calibrator)
    print(f"  Calibration: sigmoid (Platt), fitted on {len(yv)} validation predictions")
    print(f"  Brier (val, calibrated): {compute_brier_score(yv.to_numpy(), cal_val_probs):.4f}")

    # ── Test evaluation ──
    raw_test_probs = model.predict_proba(Xte)[:, 1]
    calibrated_test_probs = apply_calibration(raw_test_probs, calibrator)
    result = evaluate(yte, raw_test_probs, threshold, calibrated_test_probs)

    # Reliability curve on calibrated test probs
    reliability = compute_reliability_curve(yte.to_numpy(), calibrated_test_probs)

    result.update({
        "baseline_logistic_auc": float(roc_auc_score(yte, base_p)),
        "baseline_logistic_brier": float(brier_score_loss(yte, base_p)),
        "forecast_horizon_days": horizon_days,
        "target_recall_setting": float(target_recall),
        "window_type": "calendar-day aware rolling 3D/7D (handles missed readings)",
        "validation_recall": float(vr),
        "validation_specificity": float(vs),
        "validation_precision": float(vp),
        "split": "cow-level stratified",
        "split_details": split_info,
        "data_type": DATA_TYPE,
        "n_estimators_used": n_est_used,
        "signals_used": SIGNALS,
        "farm_information_used": USE_REAL_FARM_FEATURES,
        "prototype_fixed_baselines": None if USE_REAL_FARM_FEATURES else FIXED_GOOD_VALUES,
        "calibration_method": "sigmoid",
        "calibration_brier_score": float(brier_score_loss(yte, calibrated_test_probs)),
        "reliability_curve": reliability,
    })

    # ── AUC > 0.99 audit ──
    train_cows = train.cow_id.unique()
    val_cows = val.cow_id.unique()
    test_cows = test.cow_id.unique()
    audit = audit_high_auc(result["auc"], df_full, train_cows, val_cows, test_cows, features, target_col)
    result["auc_audit"] = audit
    if audit["triggered"]:
        print(f"\n  ⚠️  AUC > 0.99 AUDIT for {target_col}:")
        for f in audit["findings"]:
            print(f"     {f}")

    return features, result, model, calibrator


# ══════════════════════════════════════════════════════════════════════
# Main training script
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"MastiSense Training Pipeline")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Data type: {DATA_TYPE}")
    print(f"Real farm features: {USE_REAL_FARM_FEATURES}")
    print()

    # ── Load data ──
    base_df = pd.read_csv("data/cleaned.csv")
    data_hash = hashlib.sha256(Path("data/cleaned.csv").read_bytes()).hexdigest()[:16]
    print(f"Loaded {len(base_df):,} rows from data/cleaned.csv (hash: {data_hash})")

    if not USE_REAL_FARM_FEATURES:
        for col, value in FIXED_GOOD_VALUES.items():
            base_df[col] = value

    # Add SCC staleness features on raw data (before ffill in engineer)
    base_df = add_scc_staleness_to_training(base_df)

    # ── Engineer features ──
    df = engineer(base_df)
    print(f"Engineered features: {len(df):,} rows, {len(df.columns)} columns")

    # ── Split by cow ──
    print("\nCow-level split:")
    train_all, val_all, test_all = cow_split(df)

    # ── Train 7-day model ──
    # Independent incomplete-window exclusion for 7d (Q1: independent per horizon)
    train_7 = exclude_incomplete_windows(train_all, 7, "target_7d")
    val_7 = exclude_incomplete_windows(val_all, 7, "target_7d")
    test_7 = exclude_incomplete_windows(test_all, 7, "target_7d")

    features_7, result7, model_7d, cal_7d = train_horizon(
        df, "target_7d", 7, (train_7, val_7, test_7), TARGET_RECALL_7D
    )

    # ── Train 14-day model ──
    # Independent incomplete-window exclusion for 14d
    train_14 = exclude_incomplete_windows(train_all, 14, "target_14d")
    val_14 = exclude_incomplete_windows(val_all, 14, "target_14d")
    test_14 = exclude_incomplete_windows(test_all, 14, "target_14d")

    features_14, result14, model_14d, cal_14d = train_horizon(
        df, "target_14d", 14, (train_14, val_14, test_14), TARGET_RECALL_14D
    )

    # ── Verify feature parity ──
    assert set(features_7) == set(features_14), (
        f"Feature mismatch between 7d and 14d models: "
        f"7d-only={set(features_7)-set(features_14)}, "
        f"14d-only={set(features_14)-set(features_7)}"
    )

    # ── Save versioned artifacts ──
    version = next_version(MODELS_DIR)
    print(f"\nSaving model version: {version}")

    metrics = {
        "7d": result7,
        "14d": result14,
        "signals_used": SIGNALS,
        "farm_information_used": USE_REAL_FARM_FEATURES,
        "prototype_fixed_baselines": None if USE_REAL_FARM_FEATURES else FIXED_GOOD_VALUES,
    }

    calibration_info = {
        "7d": {
            "method": "sigmoid",
            "brier_score": result7["calibration_brier_score"],
            "reliability_curve": result7["reliability_curve"],
            "data_type": DATA_TYPE,
            "note": "Calibration fitted on synthetic validation data — "
                    "does not represent clinical probability accuracy.",
        },
        "14d": {
            "method": "sigmoid",
            "brier_score": result14["calibration_brier_score"],
            "reliability_curve": result14["reliability_curve"],
            "data_type": DATA_TYPE,
            "note": "Calibration fitted on synthetic validation data — "
                    "does not represent clinical probability accuracy.",
        },
    }

    training_config = {
        "xgboost": {
            "n_estimators": 400, "max_depth": 4, "learning_rate": 0.04,
            "subsample": 0.85, "colsample_bytree": 0.85, "min_child_weight": 3,
            "reg_lambda": 1.5, "early_stopping_rounds": 30,
        },
        "target_recall": TARGET_RECALL,
        "target_recall_7d": TARGET_RECALL_7D,
        "target_recall_14d": TARGET_RECALL_14D,
        "split_seed": TRAINING_SEED,
        "use_real_farm_features": USE_REAL_FARM_FEATURES,
        "incomplete_window_exclusion": "independent_per_horizon",
    }

    training_metadata = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "data_file": "data/cleaned.csv",
        "data_hash": data_hash,
        "data_type": DATA_TYPE,
        "feature_pipeline_version": FEATURE_PIPELINE_VERSION,
        "python_version": platform.python_version(),
        "xgboost_version": __import__("xgboost").__version__,
        "sklearn_version": __import__("sklearn").__version__,
        "n_estimators_used_7d": result7["n_estimators_used"],
        "n_estimators_used_14d": result14["n_estimators_used"],
        "version": version,
    }

    save_model_version(
        version,
        model_7d=model_7d,
        model_14d=model_14d,
        feature_cols=features_7,
        metrics=metrics,
        calibrator_7d=cal_7d,
        calibrator_14d=cal_14d,
        calibration_info=calibration_info,
        training_config=training_config,
        training_metadata=training_metadata,
        models_dir=MODELS_DIR,
    )

    # ── Promotion decision ──
    safe, reasons, gate_type, crit = check_promotion_safety(metrics, MODELS_DIR)
    if safe:
        promote(version, MODELS_DIR)
        record_promotion_status(
            version, status="promoted", reasons=[],
            gate_type=gate_type, criteria=crit, models_dir=MODELS_DIR
        )
        print(f"[PROMOTION APPROVED] Candidate {version} passed all gates ({gate_type}) -> promoted to current/")
    else:
        record_promotion_status(
            version, status="rejected", reasons=reasons,
            gate_type=gate_type, criteria=crit, models_dir=MODELS_DIR
        )
        print(f"\n{'='*60}")
        print(f"[PROMOTION BLOCKED] Candidate {version} failed promotion gate ({gate_type}):")
        for r in reasons:
            print(f"  - {r}")
        print(f"Candidate {version} remains archived for audit in models/{version}/.")
        print(f"models/current/ remains unset — no unvalidated model will be served.")
        print(f"{'='*60}\n")

    # ── Summary ──
    print(f"\n{'='*60}")
    print("TRAINING SUMMARY")
    print(f"{'='*60}")
    print(json.dumps(metrics, indent=2, default=str))
