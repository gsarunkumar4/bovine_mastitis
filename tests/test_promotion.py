"""Tests for model promotion gating and quality bars (§15)."""

import pytest
import json
from app.services.versioning import (
    check_first_promotion_safety,
    check_replacement_promotion_safety,
    check_promotion_safety,
    has_current_model,
    record_promotion_status,
)


def test_first_promotion_fails_low_test_recall():
    """Verify that a candidate with test recall < 80% is blocked from first promotion."""
    metrics = {
        "7d": {
            "sensitivity_recall": 0.625,  # < 0.80 -> FAILS
            "auc": 0.955,
            "baseline_logistic_auc": 0.890,
            "brier_score": 0.008,
        },
        "14d": {
            "sensitivity_recall": 0.655,  # < 0.80 -> FAILS
            "auc": 0.773,
            "baseline_logistic_auc": 0.826,
            "brier_score": 0.021,
        },
    }
    safe, reasons, crit = check_first_promotion_safety(metrics, min_recall=0.80)
    assert safe is False
    assert any("7d test recall 0.625 < required 0.800" in r for r in reasons)
    assert any("14d test recall 0.655 < required 0.800" in r for r in reasons)


def test_first_promotion_fails_baseline_deficit():
    """Verify that a candidate where XGBoost underperforms Logistic Regression by > 0.02 is blocked."""
    metrics = {
        "7d": {
            "sensitivity_recall": 0.82,
            "auc": 0.90,
            "baseline_logistic_auc": 0.88,
            "brier_score": 0.01,
        },
        "14d": {
            "sensitivity_recall": 0.81,
            "auc": 0.7726,
            "baseline_logistic_auc": 0.8265,  # deficit = 0.0539 > 0.02 -> FAILS
            "brier_score": 0.02,
        },
    }
    safe, reasons, crit = check_first_promotion_safety(metrics, max_auc_deficit=0.02)
    assert safe is False
    assert any("14d XGBoost ROC-AUC (0.7726) is worse than Logistic Regression" in r for r in reasons)


def test_first_promotion_passes_when_all_criteria_met():
    """Verify approval when all absolute first-promotion criteria are satisfied."""
    metrics = {
        "7d": {
            "sensitivity_recall": 0.82,
            "auc": 0.95,
            "baseline_logistic_auc": 0.89,
            "brier_score": 0.01,
        },
        "14d": {
            "sensitivity_recall": 0.81,
            "auc": 0.84,
            "baseline_logistic_auc": 0.83,
            "brier_score": 0.02,
        },
    }
    safe, reasons, crit = check_first_promotion_safety(metrics)
    assert safe is True
    assert len(reasons) == 0


def test_replacement_promotion_blocks_recall_regression():
    """Verify replacement gating blocks candidates that drop active model recall by > 0.03."""
    current = {
        "7d": {"sensitivity_recall": 0.85, "average_precision": 0.70, "auc": 0.92},
        "14d": {"sensitivity_recall": 0.82, "average_precision": 0.60, "auc": 0.85},
    }
    candidate = {
        "7d": {"sensitivity_recall": 0.80, "average_precision": 0.71, "auc": 0.93},  # drop = 0.05 > 0.03 -> FAILS
        "14d": {"sensitivity_recall": 0.82, "average_precision": 0.60, "auc": 0.85},
    }
    safe, reasons, crit = check_replacement_promotion_safety(candidate, current, max_recall_drop=0.03)
    assert safe is False
    assert any("7d recall regressed from 0.850 to 0.800" in r for r in reasons)


def test_replacement_promotion_blocks_auprc_regression():
    """Verify replacement gating blocks candidates that drop active model AUPRC by > 0.03."""
    current = {
        "7d": {"sensitivity_recall": 0.85, "average_precision": 0.70, "auc": 0.92},
        "14d": {"sensitivity_recall": 0.82, "average_precision": 0.60, "auc": 0.85},
    }
    candidate = {
        "7d": {"sensitivity_recall": 0.85, "average_precision": 0.65, "auc": 0.92},  # drop = 0.05 > 0.03 -> FAILS
        "14d": {"sensitivity_recall": 0.82, "average_precision": 0.60, "auc": 0.85},
    }
    safe, reasons, crit = check_replacement_promotion_safety(candidate, current, max_auprc_drop=0.03)
    assert safe is False
    assert any("7d AUPRC regressed from 0.700 to 0.650" in r for r in reasons)


def test_promotion_status_record_written(tmp_path):
    """Verify that promotion status records are persisted in candidate directory."""
    rec = record_promotion_status(
        "v001",
        status="rejected",
        reasons=["7d test recall 0.625 < required 0.800"],
        gate_type="first_promotion",
        criteria={"min_test_recall": 0.80},
        models_dir=tmp_path,
    )
    status_file = tmp_path / "v001" / "promotion_status.json"
    assert status_file.exists()
    data = json.loads(status_file.read_text())
    assert data["status"] == "rejected"
    assert len(data["reasons"]) == 1
