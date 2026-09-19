"""MastiSense — Centralized configuration.

All configurable values in one place. Existing modules continue to
re-export the values their callers already import (backward-compatible);
new modules import from here.
"""

from pathlib import Path
import os


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent

DATABASE_PATH = Path(
    os.getenv("MASTISENSE_DB", str(ROOT / "mastitis.db"))
)

MODELS_DIR = Path(
    os.getenv("MASTISENSE_MODELS", str(ROOT / "models"))
)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

API_HOST = os.getenv("MASTISENSE_HOST", "127.0.0.1")
API_PORT = int(os.getenv("MASTISENSE_PORT", "8000"))

CORS_ORIGINS = os.getenv(
    "MASTISENSE_CORS",
    "*"
).split(",")


# ---------------------------------------------------------------------------
# Feature pipeline
# ---------------------------------------------------------------------------

FEATURE_PIPELINE_VERSION = "4.1"


# ---------------------------------------------------------------------------
# Core signals — always present in readings table.
# ---------------------------------------------------------------------------

CORE_SIGNALS = [
    "milk_yield_l",
    "milk_conductivity",
    "milk_temp_c",
    "scc_value",
    "activity_score",
    "rumination_min",
    "environment_heat_index",
    "hygiene_score",
    "feed_score",
    "milking_hygiene_score",
]


# ---------------------------------------------------------------------------
# Optional/extensible signals
# ---------------------------------------------------------------------------

OPTIONAL_SIGNALS = [
    "milk_pH",
    "body_temperature",
    "udder_surface_temperature",
    "farm_temperature_c",
    "farm_humidity",
]


# ---------------------------------------------------------------------------
# Fixed healthy baseline values for prototype mode
# ---------------------------------------------------------------------------

# Used when real farm/behaviour inputs are not yet physically collected.

FIXED_GOOD_VALUES = {
    "activity_score": 0.90,
    "rumination_min": 520.0,
    "environment_heat_index": 70.0,
    "hygiene_score": 0.90,
    "feed_score": 0.90,
    "milking_hygiene_score": 0.95,
}


# ---------------------------------------------------------------------------
# SCC configuration
# ---------------------------------------------------------------------------

SCC_DEFAULT = 180_000.0

MAX_SENSOR_FFILL_DAYS = 2

SCC_SUBCLINICAL_THRESHOLD = 200_000
SCC_HIGH_THRESHOLD = 400_000

SCC_STALENESS_DAYS = 7


# ---------------------------------------------------------------------------
# Risk tier thresholds
# ---------------------------------------------------------------------------

# These are application/UI thresholds,
# not veterinary diagnostic cutoffs.
#
# CHANGED (validation finding, see IMPLEMENTATION_REPORT.md):
# The sigmoid/Platt calibrator's output saturates well below 1.0 — across
# the full 600-cow / 87,600-day synthetic dataset, calibrated risk_7d never
# exceeds ~0.726 and calibrated risk_14d never exceeds ~0.704, even for the
# most obvious confirmed-mastitis days. With the previous thresholds
# (0.25/0.50/0.75) "High Risk" was mathematically unreachable — 0 rows out
# of 87,600 ever reached it, including true-positive days right before
# onset. These thresholds are rescaled to the calibrator's actual output
# range so all four tiers are reachable and meaningful:
#   - ~84% of true 7-day-positive days now correctly reach "High Risk"
#   - only ~0.3% of true-negative days are misclassified as "High Risk"
# Re-check these numbers (see bulk_score.py) after any retrain, since a
# different calibration fit will shift the achievable probability range.

TIER_THRESHOLDS = {
    "no_risk": 0.15,
    "low_risk": 0.35,
    "moderate_risk": 0.60,
}


# ---------------------------------------------------------------------------
# Sensor-range validation limits
# ---------------------------------------------------------------------------

SENSOR_LIMITS = {
    # Milk production
    "milk_yield_l": (0, 100),

    # Milk conductivity
    "milk_conductivity": (0.01, 30),

    # Milk temperature
    #
    # CHANGED:
    # Previous range = 30–45 °C
    # New prototype range = 20–45 °C
    #
    # This allows the actual DS18B20 readings from the ESP32,
    # such as 28.06 °C, 28.12 °C, 29.06 °C, etc.
    "milk_temp_c": (20, 45),

    # Somatic Cell Count
    "scc_value": (0, 20_000_000),

    # Farm/environment
    "farm_temperature_c": (-10, 55),
    "farm_humidity": (0, 100),

    # Optional milk pH
    "milk_pH": (4.0, 9.0),

    # Optional body temperature
    "body_temperature": (35, 43),

    # Optional udder surface temperature
    "udder_surface_temperature": (25, 45),
}


# ---------------------------------------------------------------------------
# Training configuration
# ---------------------------------------------------------------------------

TRAINING_SEED = 2026

TARGET_RECALL_7D = 0.80
TARGET_RECALL_14D = 0.60

TARGET_RECALL = TARGET_RECALL_7D

TARGET_RECALLS = {
    "7d": TARGET_RECALL_7D,
    "14d": TARGET_RECALL_14D,
}

MIN_PROMOTION_RECALL = {
    "7d": 0.70,
    "14d": 0.50,
}

USE_REAL_FARM_FEATURES = False


# ---------------------------------------------------------------------------
# Data type label
# ---------------------------------------------------------------------------

# Attached to all metrics/predictions for transparency.

DATA_TYPE = "synthetic"


# ---------------------------------------------------------------------------
# §2 — Storage backend
# ---------------------------------------------------------------------------

STORAGE_BACKEND = os.getenv("MASTISENSE_STORAGE", "local")
BACKUP_DIR = ROOT / "data" / "backups"


# ---------------------------------------------------------------------------
# §5 — Notification channels
# ---------------------------------------------------------------------------

# Webhook URL — leave empty to disable webhook notifications.
WEBHOOK_URL = os.getenv("MASTISENSE_WEBHOOK", "")

# SMS — hardcoded off.  This is a non-functional stub placeholder.
# Set to True AND supply real Twilio credentials to activate.
SMS_ENABLED = False

# Active channels (console is always on; webhook added if URL configured).
NOTIFICATION_CHANNELS = ["console"]