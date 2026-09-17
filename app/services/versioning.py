"""Model version management: loading, saving, promotion gating, registry.

Directory layout
-----------------
models/
  v001/                        ← candidate model version (immutable)
    model_7d.joblib
    model_14d.joblib
    calibrator_7d.joblib       ← Platt/isotonic calibrator
    calibrator_14d.joblib
    feature_cols.joblib
    metrics.json
    calibration_info.json      ← calibration method + Brier + reliability data
    config.json                ← full training hyperparameters
    training_metadata.json     ← timestamps, data hash, split counts, …
    promotion_status.json      ← gate decision: "promoted" or "rejected" with reasons
  v002/
    …
  current/                     ← copy of promoted active production model
                               (only present when a candidate satisfies promotion gates)

CRITICAL SEPARATION:
  "A trained candidate model exists" is NOT the same as "a validated production/current
  model is approved for serving."
  Models are stored as versioned candidates even if they do not satisfy promotion gates.
  A model only becomes models/current/ when it passes the explicit promotion policy.
"""

import json, shutil
from pathlib import Path
from datetime import datetime, timezone

import joblib


def _models_dir():
    from config import MODELS_DIR
    return MODELS_DIR


# ── version helpers ────────────────────────────────────────────────────

def next_version(models_dir=None):
    """Return the next available version string, e.g. ``'v002'``."""
    d = models_dir or _models_dir()
    d.mkdir(parents=True, exist_ok=True)
    existing = sorted(
        p.name for p in d.iterdir()
        if p.is_dir() and p.name.startswith("v") and p.name[1:].isdigit()
    )
    if not existing:
        return "v001"
    return f"v{int(existing[-1][1:]) + 1:03d}"


def list_versions(models_dir=None):
    """Return a list of dicts summarizing all versioned candidates."""
    d = models_dir or _models_dir()
    if not d.exists():
        return []
    versions = []
    for p in sorted(d.iterdir()):
        if p.is_dir() and p.name.startswith("v") and p.name[1:].isdigit():
            summary = {"version": p.name}
            mp = p / "metrics.json"
            if mp.exists():
                try:
                    m = json.loads(mp.read_text())
                    summary["7d_auc"] = m.get("7d", {}).get("auc")
                    summary["7d_recall"] = m.get("7d", {}).get("sensitivity_recall")
                    summary["14d_auc"] = m.get("14d", {}).get("auc")
                    summary["14d_recall"] = m.get("14d", {}).get("sensitivity_recall")
                except Exception:
                    pass
            sp = p / "promotion_status.json"
            if sp.exists():
                try:
                    s = json.loads(sp.read_text())
                    summary["promotion_status"] = s.get("status", "unknown")
                    summary["promotion_reasons"] = s.get("reasons", [])
                except Exception:
                    pass
            else:
                summary["promotion_status"] = "unassessed"
            versions.append(summary)
    return versions


# ── save ───────────────────────────────────────────────────────────────

def save_model_version(
    version, *, model_7d, model_14d, feature_cols, metrics,
    calibrator_7d=None, calibrator_14d=None, calibration_info=None,
    training_config=None, training_metadata=None, models_dir=None,
):
    """Persist every artifact for *version* into ``models/<version>/``.
    
    Does NOT write to models/ root or models/current/. Promotion is a separate,
    explicit operation gated by check_promotion_safety.
    """
    d = (models_dir or _models_dir()) / version
    d.mkdir(parents=True, exist_ok=True)

    joblib.dump(model_7d,  d / "model_7d.joblib")
    joblib.dump(model_14d, d / "model_14d.joblib")
    joblib.dump(feature_cols, d / "feature_cols.joblib")

    if calibrator_7d is not None:
        joblib.dump(calibrator_7d,  d / "calibrator_7d.joblib")
    if calibrator_14d is not None:
        joblib.dump(calibrator_14d, d / "calibrator_14d.joblib")

    (d / "metrics.json").write_text(json.dumps(metrics, indent=2))
    if calibration_info:
        (d / "calibration_info.json").write_text(json.dumps(calibration_info, indent=2))
    if training_config:
        (d / "config.json").write_text(json.dumps(training_config, indent=2))

    meta = training_metadata or {}
    meta.setdefault("saved_at", datetime.now(timezone.utc).isoformat())
    (d / "training_metadata.json").write_text(json.dumps(meta, indent=2))

    return d


def record_promotion_status(version, status, reasons=None, gate_type="first_promotion",
                            criteria=None, models_dir=None):
    """Write an explicit audit record of the promotion decision into models/<version>/."""
    d = (models_dir or _models_dir()) / version
    d.mkdir(parents=True, exist_ok=True)
    record = {
        "version": version,
        "status": status,  # "promoted" or "rejected"
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "gate_type": gate_type,
        "reasons": reasons or [],
        "criteria": criteria or {},
    }
    (d / "promotion_status.json").write_text(json.dumps(record, indent=2))
    return record


# ── load ───────────────────────────────────────────────────────────────

def has_current_model(models_dir=None):
    """Return True IF AND ONLY IF a validated, approved model exists in current/."""
    d = models_dir or _models_dir()
    cur = d / "current"
    if not (cur / "model_7d.joblib").exists():
        return False
    # Verify promotion status record confirms it was approved
    status_file = cur / "promotion_status.json"
    if status_file.exists():
        try:
            st = json.loads(status_file.read_text())
            return st.get("status") == "promoted"
        except Exception:
            return False
    # If no status file exists in current/, treat as unverified
    return False


def load_current_model(models_dir=None):
    """Load the validated production model from ``models/current/``.
    
    Raises FileNotFoundError if no approved production model is active.
    Never falls back silently to unvetted flat artifacts.
    """
    d = models_dir or _models_dir()
    if not has_current_model(d):
        raise FileNotFoundError(
            f"No validated production model approved in {d / 'current'}. "
            f"Candidate models may exist under {d} for audit."
        )
    return _load_version_dir(d / "current")


def load_version(version, models_dir=None):
    """Load a specific candidate version for inspection/audit."""
    d = (models_dir or _models_dir()) / version
    if not d.exists():
        raise FileNotFoundError(f"Version {version} not found in {d}")
    return _load_version_dir(d)


def _load_version_dir(vdir):
    models = {
        "7d": joblib.load(vdir / "model_7d.joblib"),
        "14d": joblib.load(vdir / "model_14d.joblib"),
    }
    feature_cols = joblib.load(vdir / "feature_cols.joblib")
    metrics = json.loads((vdir / "metrics.json").read_text())

    calibrators = {}
    for h in ("7d", "14d"):
        cp = vdir / f"calibrator_{h}.joblib"
        calibrators[h] = joblib.load(cp) if cp.exists() else None

    ci_path = vdir / "calibration_info.json"
    calibration_info = json.loads(ci_path.read_text()) if ci_path.exists() else None

    mp = vdir / "training_metadata.json"
    metadata = json.loads(mp.read_text()) if mp.exists() else {}

    sp = vdir / "promotion_status.json"
    promotion_status = json.loads(sp.read_text()) if sp.exists() else None

    return {
        "models": models,
        "feature_cols": feature_cols,
        "metrics": metrics,
        "calibrators": calibrators,
        "calibration_info": calibration_info,
        "metadata": metadata,
        "promotion_status": promotion_status,
        "version": vdir.name,
    }


# ── promotion policy & gating ──────────────────────────────────────────

def check_first_promotion_safety(candidate_metrics, min_recall=None,
                                 max_auc_deficit=0.02, max_brier=0.05):
    """Absolute quality bar for the FIRST model deployment (when current/ is unset).
    
    Criteria:
      a) Test recall >= min_recall for both 7-day and 14-day models.
         Defaults to config.MIN_PROMOTION_RECALL (7d >= 0.70, 14d >= 0.50).
      b) Test ROC-AUC must not be worse than Logistic Regression baseline by more
         than max_auc_deficit (0.02) for both horizons.
      c) Calibrated Brier score <= max_brier (0.05).
      d) No leakage detected in AUC audit.
      
    Returns (safe: bool, reasons: list[str])
    """
    reasons = []
    if min_recall is None:
        try:
            from config import MIN_PROMOTION_RECALL
            min_recall_dict = MIN_PROMOTION_RECALL
        except ImportError:
            min_recall_dict = {"7d": 0.70, "14d": 0.50}
    elif isinstance(min_recall, dict):
        min_recall_dict = min_recall
    else:
        # Scalar provided (e.g. min_recall=0.80) -> apply to both horizons
        min_recall_dict = {"7d": float(min_recall), "14d": float(min_recall)}

    criteria = {
        "min_test_recall": min_recall_dict,
        "max_auc_deficit_vs_baseline": max_auc_deficit,
        "max_calibrated_brier_score": max_brier,
    }

    for h in ("7d", "14d"):
        cm = candidate_metrics.get(h, {})
        req_recall = min_recall_dict.get(h, 0.70 if h == "7d" else 0.50)
        
        # Check a: Test recall >= required
        rec = cm.get("sensitivity_recall", 0.0)
        if rec < req_recall:
            reasons.append(
                f"{h} test recall {rec:.3f} < required {req_recall:.3f}"
            )
            
        # Check b: Comparison vs. Logistic Regression baseline
        xgb_auc = cm.get("auc", 0.0)
        base_auc = cm.get("baseline_logistic_auc", 0.0)
        if base_auc > 0.0:
            deficit = base_auc - xgb_auc
            if deficit > max_auc_deficit:
                reasons.append(
                    f"{h} XGBoost ROC-AUC ({xgb_auc:.4f}) is worse than Logistic Regression "
                    f"baseline ({base_auc:.4f}) by {deficit:.4f} (max allowed deficit: {max_auc_deficit:.4f})"
                )
                
        # Check c: Calibration quality
        brier = cm.get("brier_score", cm.get("calibration_brier_score", 1.0))
        if brier > max_brier:
            reasons.append(
                f"{h} calibrated Brier score {brier:.4f} exceeds acceptable limit {max_brier:.4f}"
            )
            
        # Check d: Leakage audit
        audit = cm.get("auc_audit", {})
        if audit.get("triggered", False):
            leak_findings = [f for f in audit.get("findings", []) if "LEAKAGE" in f]
            if leak_findings:
                reasons.append(f"{h} data leakage detected: {'; '.join(leak_findings)}")

    safe = (len(reasons) == 0)
    return safe, reasons, criteria


def check_replacement_promotion_safety(candidate_metrics, current_metrics,
                                      max_recall_drop=0.03, max_auprc_drop=0.03,
                                      max_auc_drop=0.03):
    """Comparative quality bar when an active production model ALREADY exists.
    
    Ensures the candidate does not regress the active model:
      a) Recall must not drop by > max_recall_drop (0.03) on either horizon.
      b) AUPRC must not drop by > max_auprc_drop (0.03) on either horizon.
      c) ROC-AUC must not drop by > max_auc_drop (0.03) on either horizon.
    """
    reasons = []
    criteria = {
        "max_recall_drop": max_recall_drop,
        "max_auprc_drop": max_auprc_drop,
        "max_auc_drop": max_auc_drop,
    }

    for h in ("7d", "14d"):
        cm = candidate_metrics.get(h, {})
        om = current_metrics.get(h, {})

        new_rec = cm.get("sensitivity_recall", 0.0)
        old_rec = om.get("sensitivity_recall", 0.0)
        if old_rec > 0 and (old_rec - new_rec) > max_recall_drop:
            reasons.append(
                f"{h} recall regressed from {old_rec:.3f} to {new_rec:.3f} "
                f"(drop {old_rec - new_rec:.3f} > max allowed {max_recall_drop:.3f})"
            )

        new_ap = cm.get("average_precision", 0.0)
        old_ap = om.get("average_precision", 0.0)
        if old_ap > 0 and (old_ap - new_ap) > max_auprc_drop:
            reasons.append(
                f"{h} AUPRC regressed from {old_ap:.3f} to {new_ap:.3f} "
                f"(drop {old_ap - new_ap:.3f} > max allowed {max_auprc_drop:.3f})"
            )

        new_auc = cm.get("auc", 0.0)
        old_auc = om.get("auc", 0.0)
        if old_auc > 0 and (old_auc - new_auc) > max_auc_drop:
            reasons.append(
                f"{h} ROC-AUC regressed from {old_auc:.3f} to {new_auc:.3f} "
                f"(drop {old_auc - new_auc:.3f} > max allowed {max_auc_drop:.3f})"
            )

    safe = (len(reasons) == 0)
    return safe, reasons, criteria


def check_promotion_safety(candidate_metrics, models_dir=None):
    """Unified promotion check: routes to first-promotion or replacement-promotion."""
    d = models_dir or _models_dir()
    if has_current_model(d):
        current = load_current_model(d)
        safe, reasons, crit = check_replacement_promotion_safety(
            candidate_metrics, current.get("metrics", {})
        )
        gate_type = "replacement_promotion"
    else:
        safe, reasons, crit = check_first_promotion_safety(candidate_metrics)
        gate_type = "first_promotion"
    return safe, reasons, gate_type, crit


def promote(version, models_dir=None):
    """Promote an approved version to ``models/current/``.
    
    Must only be called if promotion safety checks pass.
    """
    d = models_dir or _models_dir()
    src = d / version
    dst = d / "current"
    if not src.exists():
        raise FileNotFoundError(f"Version {version} not found in {d}")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    # Ensure current contains a promotion record confirming approval
    status_file = dst / "promotion_status.json"
    rec = {
        "version": version,
        "status": "promoted",
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "reasons": [],
    }
    status_file.write_text(json.dumps(rec, indent=2))
    print(f"[versioning] Promoted {version} -> current/")
    return dst
