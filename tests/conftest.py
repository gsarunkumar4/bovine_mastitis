"""Shared test fixtures for MastiSense test suite."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from app.services.database import connect, init_db


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Ensure tests run against an isolated temporary SQLite database."""
    test_db = tmp_path / "test_mastitis.db"
    monkeypatch.setattr("config.DATABASE_PATH", test_db)
    monkeypatch.setattr("app.services.database.DB_PATH", test_db)
    init_db()
    yield test_db


@pytest.fixture
def sample_cow_timeline():
    """Generates a small 30-day longitudinal timeline for 3 cows."""
    rows = []
    cows = [
        ("cow_test_01", 1, 0, "2025-11-01"),
        ("cow_test_02", 2, 1, "2025-10-15"),
        ("cow_test_03", 3, 0, "2025-12-01"),
    ]
    start_date = datetime(2026, 1, 1)
    
    for cid, parity, prior_mast, calving in cows:
        for d in range(30):
            dt = start_date + timedelta(days=d)
            # Mastitis event on day 20 for cow 01
            has_event = (cid == "cow_test_01")
            onset = 20
            # Target labels
            t7 = 1 if (has_event and 1 <= onset - d <= 7) else 0
            t14 = 1 if (has_event and 1 <= onset - d <= 14) else 0
            
            # Periodic SCC: every 4th day
            scc = 160000.0 if d % 4 == 0 else np.nan
            if has_event and d >= onset - 5:
                scc = 500000.0 if d % 4 == 0 else np.nan

            rows.append({
                "cow_id": cid,
                "timestamp": dt.isoformat(),
                "milk_yield_l": 15.0 - (2.0 if has_event and d >= 15 else 0.0),
                "milk_conductivity": 4.5 + (1.2 if has_event and d >= 15 else 0.0),
                "milk_temp_c": 38.5 + (0.5 if has_event and d >= 15 else 0.0),
                "scc_value": scc,
                "activity_score": 0.9,
                "rumination_min": 520.0,
                "environment_heat_index": 70.0,
                "hygiene_score": 0.9,
                "feed_score": 0.9,
                "milking_hygiene_score": 0.95,
                "target_7d": t7,
                "target_14d": t14,
                "event_onset_day": onset if has_event else -1,
                "subclinical": 0,
                "breed": "HF",
                "age_years": 4,
                "parity": parity,
                "vaccination_status": 1,
                "prior_mastitis_flag": prior_mast,
                "calving_date": calving,
                "herd_id": "test_herd",
            })

    return pd.DataFrame(rows)
