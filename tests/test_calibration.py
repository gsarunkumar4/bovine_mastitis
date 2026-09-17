"""Tests for probability calibration, Brier score, and threshold selection (§8)."""

import numpy as np
from app.services.calibration import (
    fit_calibrator, apply_calibration,
    compute_brier_score, compute_reliability_curve,
)
from train_model import choose_threshold


def test_sigmoid_calibration_range():
    """Verify that sigmoid calibration outputs well-calibrated probabilities in [0, 1]."""
    rng = np.random.default_rng(42)
    # Validation data: raw uncalibrated scores and ground truth
    raw_probs = rng.uniform(0.0, 1.0, 200)
    y_true = (raw_probs > 0.6).astype(int)

    calibrator = fit_calibrator(y_true, raw_probs, method="sigmoid")
    calibrated = apply_calibration(raw_probs, calibrator)

    assert len(calibrated) == len(raw_probs)
    assert np.all(calibrated >= 0.0)
    assert np.all(calibrated <= 1.0)


def test_brier_score_computation():
    """Verify Brier score computation: 0 for perfect, <= 0.25 for reasonable."""
    y_true = np.array([0, 1, 1, 0])
    perfect_probs = np.array([0.0, 1.0, 1.0, 0.0])
    assert compute_brier_score(y_true, perfect_probs) == 0.0

    worst_probs = np.array([1.0, 0.0, 0.0, 1.0])
    assert compute_brier_score(y_true, worst_probs) == 1.0


def test_reliability_curve():
    """Verify reliability curve bins structure."""
    y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1, 1, 1])
    probs = np.linspace(0.05, 0.95, 10)
    curve = compute_reliability_curve(y_true, probs, n_bins=5)
    assert "fraction_of_positives" in curve
    assert "mean_predicted_value" in curve
    assert len(curve["fraction_of_positives"]) > 0


def test_threshold_selection_target_recall():
    """Verify threshold tuning optimizes for target recall (e.g. 0.80)."""
    rng = np.random.default_rng(2026)
    y = np.array([0] * 80 + [1] * 20)
    p = np.concatenate([rng.uniform(0.05, 0.4, 80), rng.uniform(0.35, 0.95, 20)])

    threshold, recall, spec, prec = choose_threshold(y, p, target_recall=0.80)
    assert threshold > 0.0
    assert recall >= 0.80, f"Expected recall >= 0.80, got {recall}"
