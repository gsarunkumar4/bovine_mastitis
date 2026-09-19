"""MastiSense — Retraining Pipeline (§15).

Orchestrates automated retraining using accumulated readings + confirmed
veterinary outcomes from the feedback table.

Workflow:
  1. Pulls historical readings from SQLite database + baseline training data.
  2. Queries confirmed outcomes from ``feedback`` table (only confirmed
     veterinary diagnoses are used as training labels).
  3. Executes the identical shared feature pipeline (``features.py``).
  4. Trains candidate 7-day and 14-day models with cow-level splitting.
  5. Calibrates probabilities on validation predictions.
  6. Evaluates on holdout test cows.
  7. Performs promotion safety checks against the deployed model (``models/current``).
  8. If safe, promotes candidate to ``models/current``. Otherwise preserves current
     model and records the candidate with failure reasons.

Run:  python retrain.py
"""

import json, sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np

from config import (
    ROOT, MODELS_DIR, TRAINING_SEED, TARGET_RECALL,
    TARGET_RECALL_7D, TARGET_RECALL_14D,
    USE_REAL_FARM_FEATURES, FIXED_GOOD_VALUES, DATA_TYPE,
    FEATURE_PIPELINE_VERSION,
)
from app.services.database import connect
from app.services.features import (
    engineer, add_scc_staleness_to_training, SIGNALS,
)
from app.services.versioning import (
    next_version, save_model_version, load_current_model,
    promote, check_promotion_safety, record_promotion_status,
)
from train_model import (
    cow_split, exclude_incomplete_windows, train_horizon,
)


def load_retraining_data():
    """Build the dataset for retraining by combining base dataset with
    any confirmed outcomes from the feedback table."""
    base_path = ROOT / "data/cleaned.csv"
    if not base_path.exists():
        raise FileNotFoundError(f"Base training dataset not found at {base_path}")

    df = pd.read_csv(base_path)
    print(f"[retrain] Loaded base dataset with {len(df):,} records across {df.cow_id.nunique()} cows.")

    # Check for confirmed outcomes in the feedback table
    c = connect()
    feedback_rows = c.execute(
        "SELECT cow_id, event_date, confirmed_mastitis, notes FROM feedback "
        "WHERE confirmed_mastitis IS NOT NULL"
    ).fetchall()
    c.close()

    if feedback_rows:
        print(f"[retrain] Found {len(feedback_rows)} confirmed feedback outcomes in database.")
        for row in feedback_rows:
            cid, edate, confirmed, _ = row
            # If confirmed positive event, update label window for this cow
            if confirmed == 1 and edate:
                ev_date = pd.to_datetime(edate).normalize()
                mask = (df["cow_id"] == cid)
                if mask.any():
                    ts = pd.to_datetime(df.loc[mask, "timestamp"]).dt.normalize()
                    # 7-day forward window: 1 <= (ev_date - ts).days <= 7
                    diff_days = (ev_date - ts).dt.days
                    df.loc[mask & (diff_days >= 1) & (diff_days <= 7), "target_7d"] = 1
                    df.loc[mask & (diff_days >= 1) & (diff_days <= 14), "target_14d"] = 1
    else:
        print("[retrain] No confirmed veterinary feedback in database; retraining on base dataset.")

    return df


def retrain():
    print("=" * 65)
    print(f"MastiSense Automated Retraining Pipeline")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 65)

    df_raw = load_retraining_data()

    if not USE_REAL_FARM_FEATURES:
        for col, value in FIXED_GOOD_VALUES.items():
            df_raw[col] = value

    df_raw = add_scc_staleness_to_training(df_raw)
    df = engineer(df_raw)
    print(f"[retrain] Engineered features: {len(df):,} rows x {len(df.columns)} columns")

    train_all, val_all, test_all = cow_split(df)

    # 7-day candidate
    train_7 = exclude_incomplete_windows(train_all, 7, "target_7d")
    val_7 = exclude_incomplete_windows(val_all, 7, "target_7d")
    test_7 = exclude_incomplete_windows(test_all, 7, "target_7d")
    features_7, res_7, m_7d, cal_7d = train_horizon(df, "target_7d", 7, (train_7, val_7, test_7), TARGET_RECALL_7D)

    # 14-day candidate
    train_14 = exclude_incomplete_windows(train_all, 14, "target_14d")
    val_14 = exclude_incomplete_windows(val_all, 14, "target_14d")
    test_14 = exclude_incomplete_windows(test_all, 14, "target_14d")
    features_14, res_14, m_14d, cal_14d = train_horizon(df, "target_14d", 14, (train_14, val_14, test_14), TARGET_RECALL_14D)

    candidate_version = next_version(MODELS_DIR)
    print(f"\n[retrain] Candidate version created: {candidate_version}")

    candidate_metrics = {
        "7d": res_7,
        "14d": res_14,
        "signals_used": SIGNALS,
        "farm_information_used": USE_REAL_FARM_FEATURES,
    }

    cal_info = {
        "7d": {"method": "sigmoid", "brier_score": res_7["calibration_brier_score"]},
        "14d": {"method": "sigmoid", "brier_score": res_14["calibration_brier_score"]},
    }

    metadata = {
        "retrained_at": datetime.now(timezone.utc).isoformat(),
        "candidate_version": candidate_version,
        "feature_pipeline_version": FEATURE_PIPELINE_VERSION,
        "data_type": DATA_TYPE,
    }

    save_model_version(
        candidate_version,
        model_7d=m_7d,
        model_14d=m_14d,
        feature_cols=features_7,
        metrics=candidate_metrics,
        calibrator_7d=cal_7d,
        calibrator_14d=cal_14d,
        calibration_info=cal_info,
        training_metadata=metadata,
        models_dir=MODELS_DIR,
    )

    # ── Promotion Gating ──
    safe, reasons, gate_type, crit = check_promotion_safety(candidate_metrics, MODELS_DIR)
    if safe:
        promote(candidate_version, MODELS_DIR)
        record_promotion_status(
            candidate_version, status="promoted", reasons=[],
            gate_type=gate_type, criteria=crit, models_dir=MODELS_DIR
        )
        print(f"[retrain] [PROMOTED] Candidate {candidate_version} passed all gates ({gate_type}) -> promoted to current/")
        return {"status": "promoted", "version": candidate_version, "metrics": candidate_metrics}
    else:
        record_promotion_status(
            candidate_version, status="rejected", reasons=reasons,
            gate_type=gate_type, criteria=crit, models_dir=MODELS_DIR
        )
        print(f"[retrain] [BLOCKED] Candidate {candidate_version} blocked from promotion ({gate_type}):")
        for r in reasons:
            print(f"   - {r}")
        print(f"[retrain] Active production model remains unchanged (or unset).")
        return {"status": "rejected", "version": candidate_version, "reasons": reasons}


if __name__ == "__main__":
    retrain()
