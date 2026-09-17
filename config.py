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

TIER_THRESHOLDS = {
    "no_risk": 0.25,
    "low_risk": 0.50,
    "moderate_risk": 0.75,
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