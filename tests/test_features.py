"""Tests for feature engineering, calendar-day reindexing, and staleness (§5, §6)."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.services.features import (
    engineer, add_dim, add_scc_staleness,
    prepare_signals, derive_heat_index,
)


def test_calendar_day_reindexing_handles_gaps():
    """Verify that a 1-day missed reading does not break rolling window continuity."""
    # Days 0, 1, 3 (day 2 was dropped out due to sensor/WiFi drop)
    dates = [datetime(2026, 1, 1), datetime(2026, 1, 2), datetime(2026, 1, 4)]
    df = pd.DataFrame({
        "cow_id": "cow_dropout",
        "timestamp": [d.isoformat() for d in dates],
        "milk_yield_l": [14.0, 14.2, 13.0],
        "milk_conductivity": [4.5, 4.6, 5.2],
        "milk_temp_c": [38.5, 38.6, 38.8],
        "scc_value": [150000.0, np.nan, 220000.0],
    })
    feat = engineer(df)
    # 3 observed days should be returned
    assert len(feat) == 3
    # Missed days in 3-day window at day 4 should be 1
    last_row = feat.iloc[-1]
    assert last_row["missed_days_3d"] >= 1.0


def test_forward_fill_limit_exceeded():
    """Verify that gaps > 2 days are NOT silently filled with stale values."""
    # 5-day gap between day 1 and day 7
    dates = [datetime(2026, 1, 1), datetime(2026, 1, 7)]
    df = pd.DataFrame({
        "cow_id": "cow_long_gap",
        "timestamp": [d.isoformat() for d in dates],
        "milk_yield_l": [15.0, 12.0],
        "milk_conductivity": [4.2, 5.5],
        "milk_temp_c": [38.4, 39.1],
        "scc_value": [180000.0, np.nan],
    })
    feat = engineer(df)
    assert len(feat) == 2
    # The 7-day missed count at day 7 should reflect the long outage
    assert feat.iloc[-1]["missed_days_7d"] >= 5.0


def test_days_in_milk_calculation():
    """Verify DIM is computed correctly from calving_date without future leakage."""
    df = pd.DataFrame({
        "cow_id": "cow_dim",
        "timestamp": ["2026-02-15T00:00:00"],
        "calving_date": ["2026-01-01"],
    })
    out = add_dim(df)
    assert "days_in_milk" in out.columns
    # Jan 1 to Feb 15 = 45 days
    assert out.iloc[0]["days_in_milk"] == 45


def test_scc_staleness_flag():
    """Verify scc_stale and days_since_scc correctly flag tests older than threshold."""
    dates = [
        datetime(2026, 1, 1),   # fresh test
        datetime(2026, 1, 3),   # 2 days old
        datetime(2026, 1, 10),  # 9 days old -> stale (>7d)
    ]
    df = pd.DataFrame({
        "cow_id": "cow_scc",
        "timestamp": [d.isoformat() for d in dates],
        "scc_value": [170000.0, np.nan, np.nan],
    })
    out = add_scc_staleness(df)
    assert "days_since_scc" in out.columns
    assert "scc_stale" in out.columns
    assert out.iloc[0]["days_since_scc"] == 0
    assert out.iloc[0]["scc_stale"] == 0
    assert out.iloc[1]["days_since_scc"] == 2
    assert out.iloc[1]["scc_stale"] == 0
    assert out.iloc[2]["days_since_scc"] == 9
    assert out.iloc[2]["scc_stale"] == 1


def test_heat_index_derivation_from_dht22():
    """Verify that farm_temperature_c and farm_humidity derive heat index properly."""
    df = pd.DataFrame({
        "cow_id": "cow_env",
        "timestamp": ["2026-01-01T00:00:00"],
        "farm_temperature_c": [30.0],
        "farm_humidity": [70.0],
        "environment_heat_index": [np.nan],
    })
    out = derive_heat_index(df)
    # 30.0 + 0.36*70.0 - 10.0 = 45.2
    assert round(out.iloc[0]["environment_heat_index"], 1) == 45.2
