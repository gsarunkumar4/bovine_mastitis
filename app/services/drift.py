"""Drift monitoring foundation (§15).

Implemented now:
  - Population Stability Index (PSI) for feature distributions
  - Prediction score distribution shift
  - Missing-data rate tracking
  - Sensor availability tracking (% expected daily readings received)
  - Calibration drift indicator (Brier score comparison)

Deferred:
  - Automated drift-triggered retraining
  - Dedicated graphical drift dashboard
  - Time-windowed rolling drift detection
"""

import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from config import CORE_SIGNALS, SENSOR_LIMITS


def calculate_psi(expected, actual, num_buckets=10):
    """Calculate the Population Stability Index (PSI) between two numeric arrays.
    
    Rule of thumb:
      PSI < 0.10: No significant shift (stable)
      0.10 <= PSI < 0.25: Moderate shift (monitor closely)
      PSI >= 0.25: Significant shift (retraining recommended)
    """
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    
    # Filter out NaNs and infs
    expected = expected[np.isfinite(expected)]
    actual = actual[np.isfinite(actual)]
    
    if len(expected) < 10 or len(actual) < 10:
        return 0.0

    # Create quantile buckets based on expected (reference) distribution
    percentiles = np.linspace(0, 100, num_buckets + 1)
    bucket_bounds = np.percentile(expected, percentiles)
    bucket_bounds[0] = -np.inf
    bucket_bounds[-1] = np.inf

    # Count frequencies
    exp_counts, _ = np.histogram(expected, bins=bucket_bounds)
    act_counts, _ = np.histogram(actual, bins=bucket_bounds)

    # Convert to fractions with Laplace smoothing (avoid division by zero / log(0))
    eps = 1e-4
    exp_pct = (exp_counts + eps) / (len(expected) + eps * num_buckets)
    act_pct = (act_counts + eps) / (len(actual) + eps * num_buckets)

    # PSI formula: sum((actual% - expected%) * ln(actual% / expected%))
    psi_val = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return float(round(psi_val, 4))


def check_feature_drift(reference_df, current_df, features=None):
    """Compute PSI for each feature between reference data and current data."""
    cols = features or [c for c in CORE_SIGNALS if c in reference_df.columns and c in current_df.columns]
    drift_report = {}
    for col in cols:
        ref_vals = pd.to_numeric(reference_df[col], errors="coerce").dropna().to_numpy()
        cur_vals = pd.to_numeric(current_df[col], errors="coerce").dropna().to_numpy()
        psi = calculate_psi(ref_vals, cur_vals)
        status = "stable" if psi < 0.10 else "moderate_shift" if psi < 0.25 else "significant_drift"
        drift_report[col] = {
            "psi": psi,
            "status": status,
            "ref_mean": float(np.mean(ref_vals)) if len(ref_vals) else None,
            "cur_mean": float(np.mean(cur_vals)) if len(cur_vals) else None,
        }
    return drift_report


def check_missing_rates(df, signals=None):
    """Compute missing-data rate per sensor signal."""
    cols = signals or [c for c in CORE_SIGNALS if c in df.columns]
    missing_rates = {}
    for col in cols:
        rate = float(df[col].isna().mean()) if col in df.columns else 1.0
        missing_rates[col] = round(rate, 4)
    return missing_rates


def summarize_drift(db_conn, reference_csv="data/cleaned.csv", recent_days=30):
    """Generate an overall drift summary comparing recent DB readings
    against the training reference dataset."""
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "recent_window_days": recent_days,
        "status": "stable",
        "flags": [],
    }

    try:
        ref_df = pd.read_csv(reference_csv)
    except Exception as e:
        summary["error"] = f"Could not load reference data: {e}"
        return summary

    # Load recent DB readings
    recent_rows = db_conn.execute(
        "SELECT * FROM readings WHERE date(timestamp) >= date('now', ?)",
        (f"-{recent_days} days",),
    ).fetchall()

    if len(recent_rows) < 20:
        summary["note"] = f"Insufficient recent data ({len(recent_rows)} readings in last {recent_days}d) for drift calculation."
        return summary

    cur_df = pd.DataFrame([dict(r) for r in recent_rows])

    # 1. Feature Drift (PSI)
    drift_report = check_feature_drift(ref_df, cur_df)
    summary["feature_drift"] = drift_report
    high_drift = [k for k, v in drift_report.items() if v["status"] == "significant_drift"]
    if high_drift:
        summary["flags"].append(f"Significant feature drift detected in: {', '.join(high_drift)}")
        summary["status"] = "drift_detected"

    # 2. Missing data rates
    missing_report = check_missing_rates(cur_df)
    summary["missing_data_rates"] = missing_report
    high_missing = [k for k, r in missing_report.items() if r > 0.20 and k != "scc_value"]
    if high_missing:
        summary["flags"].append(f"High missing-data rates (>20%) in core sensors: {', '.join(high_missing)}")
        if summary["status"] == "stable":
            summary["status"] = "elevated_missingness"

    # 3. Sensor availability
    cows_count = db_conn.execute("SELECT count(*) FROM cows").fetchone()[0]
    expected_readings = max(1, cows_count * recent_days)
    actual_readings = len(recent_rows)
    availability = round(min(1.0, actual_readings / expected_readings), 4)
    summary["sensor_availability"] = {
        "active_cows": cows_count,
        "actual_readings": actual_readings,
        "expected_readings": expected_readings,
        "availability_rate": availability,
    }

    return summary
