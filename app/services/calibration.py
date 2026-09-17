"""Probability calibration for MastiSense risk scores.

Workflow (§8):
  1. Train XGBoost on training data.
  2. Obtain raw ``predict_proba`` on the **validation** set (never train, never test).
  3. Fit a calibrator (Platt/sigmoid or isotonic) on those validation predictions.
  4. At inference, apply: raw_prob → calibrator → calibrated_prob.
  5. Persist the calibrator alongside the model version.

The calibrator is a thin sklearn estimator saved via joblib so it can be
loaded independently of the original model.
"""

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss


# ── calibrator fitting ─────────────────────────────────────────────────

def fit_calibrator(y_true, raw_probs, method="sigmoid"):
    """Fit a calibrator on *out-of-sample* (validation) predictions.

    Parameters
    ----------
    y_true : array-like
        True binary labels from the validation set.
    raw_probs : array-like
        Uncalibrated ``predict_proba[:, 1]`` from the validation set.
    method : str
        ``"sigmoid"`` (Platt scaling) or ``"isotonic"``.

    Returns
    -------
    calibrator
        A fitted sklearn estimator with a ``.predict()`` (isotonic) or
        ``.predict_proba()`` (sigmoid/logistic) method.
    """
    raw_probs = np.asarray(raw_probs, dtype=float)
    y_true = np.asarray(y_true, dtype=int)

    if method == "sigmoid":
        cal = LogisticRegression(solver="lbfgs", max_iter=2000, C=1e10)
        cal.fit(raw_probs.reshape(-1, 1), y_true)
    elif method == "isotonic":
        cal = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        cal.fit(raw_probs, y_true)
    else:
        raise ValueError(f"Unknown calibration method: {method!r}")
    return cal


def apply_calibration(raw_probs, calibrator):
    """Apply a fitted calibrator to raw probabilities.

    Returns the original probabilities unchanged if *calibrator* is None.
    """
    if calibrator is None:
        return np.asarray(raw_probs, dtype=float)
    raw_probs = np.asarray(raw_probs, dtype=float)
    if isinstance(calibrator, LogisticRegression):
        return calibrator.predict_proba(raw_probs.reshape(-1, 1))[:, 1]
    # IsotonicRegression
    return calibrator.predict(raw_probs)


# ── evaluation helpers ─────────────────────────────────────────────────

def compute_brier_score(y_true, probs):
    """Brier score (lower is better; 0 = perfect, 0.25 = uninformative)."""
    return float(brier_score_loss(y_true, probs))


def compute_reliability_curve(y_true, probs, n_bins=10):
    """Return binned reliability-curve data for reporting."""
    prob_true, prob_pred = calibration_curve(
        y_true, probs, n_bins=n_bins, strategy="uniform"
    )
    return {
        "fraction_of_positives": prob_true.tolist(),
        "mean_predicted_value": prob_pred.tolist(),
        "n_bins": n_bins,
    }
