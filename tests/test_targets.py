"""Tests for target construction and incomplete-window label exclusion (§3)."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from train_model import exclude_incomplete_windows


def test_target_window_definition(sample_cow_timeline):
    """Verify target_7d and target_14d strictly adhere to (t, t+N] definition."""
    df = sample_cow_timeline
    cow1 = df[df.cow_id == "cow_test_01"].sort_values("timestamp").reset_index(drop=True)
    onset_idx = 20

    for idx, row in cow1.iterrows():
        lead_time = onset_idx - idx
        # target_7d = 1 if 1 <= lead_time <= 7
        if 1 <= lead_time <= 7:
            assert row["target_7d"] == 1, f"Expected target_7d=1 at day {idx} (lead {lead_time})"
        else:
            assert row["target_7d"] == 0, f"Expected target_7d=0 at day {idx} (lead {lead_time})"

        # target_14d = 1 if 1 <= lead_time <= 14
        if 1 <= lead_time <= 14:
            assert row["target_14d"] == 1, f"Expected target_14d=1 at day {idx} (lead {lead_time})"
        else:
            assert row["target_14d"] == 0, f"Expected target_14d=0 at day {idx} (lead {lead_time})"


def test_exclude_incomplete_windows_7d(sample_cow_timeline):
    """Verify that rows within the trailing 7 days of each cow's timeline
    are excluded from training data rather than defaulting to negative."""
    df = sample_cow_timeline
    # 3 cows x 30 days = 90 rows
    assert len(df) == 90

    # Horizon 7: the last 7 days of each 30-day timeline (days 24-29: 6 days + day 30: 7 days)
    filtered = exclude_incomplete_windows(df, horizon=7, target_col="target_7d")
    
    # Check that each cow now has exactly 30 - 7 = 23 rows
    for cid, g in filtered.groupby("cow_id"):
        assert len(g) == 23, f"Cow {cid} should have 23 rows after excluding 7-day trailing window, got {len(g)}"
    assert len(filtered) == 69


def test_exclude_incomplete_windows_14d(sample_cow_timeline):
    """Verify independent exclusion for 14-day horizon (excludes trailing 14 days)."""
    df = sample_cow_timeline
    filtered = exclude_incomplete_windows(df, horizon=14, target_col="target_14d")
    for cid, g in filtered.groupby("cow_id"):
        assert len(g) == 16, f"Cow {cid} should have 16 rows after excluding 14-day trailing window, got {len(g)}"
    assert len(filtered) == 48


def test_no_negative_default_at_boundary():
    """Verify that boundary rows are completely dropped and not retained with false 0 labels."""
    dates = pd.date_range("2026-01-01", periods=10, freq="D")
    df = pd.DataFrame({
        "cow_id": "cow_single",
        "timestamp": dates.astype(str),
        "target_7d": 0,
    })
    filtered = exclude_incomplete_windows(df, horizon=7, target_col="target_7d")
    # For 10 days, days 0, 1, 2 have >= 7 days ahead (days 3..9).
    # Day 3 has (9 - 3) = 6 days ahead < 7 -> excluded.
    # So exactly 3 rows remain (days 0, 1, 2).
    assert len(filtered) == 3
    assert filtered.iloc[-1]["timestamp"].startswith("2026-01-03")
