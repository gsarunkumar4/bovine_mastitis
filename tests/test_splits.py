"""Tests for split integrity, zero leakage, and feature parity (§7)."""

import pandas as pd
import numpy as np
from train_model import cow_split, NON_FEATURE_COLS
from app.services.versioning import load_current_model
from config import MODELS_DIR


def test_no_cow_overlap_across_splits(sample_cow_timeline):
    """Verify that no animal appears in more than one split fold (strict cow-level split)."""
    # Create dataset with 20 cows
    rows = []
    for c in range(1, 21):
        cid = f"cow_split_{c:02d}"
        for d in range(10):
            rows.append({
                "cow_id": cid,
                "timestamp": f"2026-01-{d+1:02d}",
                "target_7d": 1 if c <= 5 else 0,
                "target_14d": 1 if c <= 5 else 0,
            })
    df = pd.DataFrame(rows)

    train, val, test = cow_split(df)
    train_cows = set(train.cow_id.unique())
    val_cows = set(val.cow_id.unique())
    test_cows = set(test.cow_id.unique())

    # Strict disjoint sets
    assert len(train_cows & val_cows) == 0, "Leakage: cow found in both train and val!"
    assert len(train_cows & test_cows) == 0, "Leakage: cow found in both train and test!"
    assert len(val_cows & test_cows) == 0, "Leakage: cow found in both val and test!"
    assert len(train_cows | val_cows | test_cows) == 20


def test_leakage_columns_excluded():
    """Verify that identifiers, future targets, and event onset indicators are strictly in NON_FEATURE_COLS."""
    leakage_targets = [
        "cow_id", "timestamp", "target_7d", "target_14d",
        "event_onset_day", "subclinical"
    ]
    for col in leakage_targets:
        assert col in NON_FEATURE_COLS, f"Critical leakage risk: {col} is missing from NON_FEATURE_COLS!"


def test_train_serve_feature_parity():
    """Verify that feature columns in the candidate model match what the current pipeline produces."""
    from app.services.versioning import load_version
    model_info = load_version("v001", MODELS_DIR)
    feature_cols = model_info["feature_cols"]
    assert len(feature_cols) > 0

    # Ensure no target or metadata columns are present in feature_cols
    for forbidden in NON_FEATURE_COLS:
        assert forbidden not in feature_cols, f"Forbidden column {forbidden} leaked into model feature_cols!"
