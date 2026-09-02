import pandas as pd
import numpy as np


# =========================================================
# FIXED GOOD VALUES
# =========================================================

FIXED_GOOD_VALUES = {
    "activity_score": 0.90,
    "rumination_min": 520.0,

    # Used only when DHT22 temperature/humidity
    # are unavailable.
    "environment_heat_index": 70.0,

    "hygiene_score": 0.90,
    "feed_score": 0.90,
    "milking_hygiene_score": 0.95,
}


# =========================================================
# EXISTING ML SIGNALS
# =========================================================
# IMPORTANT:
# Keep these unchanged because the existing trained model
# expects the existing 114 engineered features.

SIGNALS = [
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


# =========================================================
# VALIDATE READING
# =========================================================

def validate_reading(r):
    errors = []

    if not r.cow_id:
        errors.append("cow_id is required")

    if r.milk_yield_l is None:
        errors.append("milk_yield_l is required")
    elif r.milk_yield_l < 0:
        errors.append("milk_yield_l must be >= 0")

    if r.milk_conductivity is None:
        errors.append("milk_conductivity is required")
    elif r.milk_conductivity <= 0:
        errors.append("milk_conductivity must be > 0")

    if r.milk_temp_c is None:
        errors.append("milk_temp_c is required")

    if r.scc_value is not None and r.scc_value < 0:
        errors.append("scc_value must be >= 0")

    # ---------------------------------------------------------
    # DHT22 VALIDATION
    # ---------------------------------------------------------

    if r.farm_temperature_c is not None:

        if (
            r.farm_temperature_c < -20
            or r.farm_temperature_c > 60
        ):
            errors.append(
                "farm_temperature_c is outside valid range"
            )

    if r.farm_humidity is not None:

        if (
            r.farm_humidity < 0
            or r.farm_humidity > 100
        ):
            errors.append(
                "farm_humidity must be between 0 and 100"
            )

    return errors


# =========================================================
# CALCULATE ENVIRONMENT HEAT INDEX
# =========================================================

def calculate_heat_index(
    temperature_c,
    humidity
):
    """
    Calculate Temperature-Humidity Index (THI)
    from actual DHT22 temperature and humidity.

    temperature_c:
        Farm/environment temperature in Celsius.

    humidity:
        Relative humidity in percentage.
    """

    if (
        temperature_c is None
        or humidity is None
    ):
        return FIXED_GOOD_VALUES[
            "environment_heat_index"
        ]

    try:

        temperature_c = float(
            temperature_c
        )

        humidity = float(
            humidity
        )

        thi = (
            (1.8 * temperature_c + 32)
            -
            (
                (
                    0.55
                    -
                    0.0055 * humidity
                )
                *
                (
                    1.8 * temperature_c
                    -
                    26.8
                )
            )
        )

        return float(thi)

    except (
        TypeError,
        ValueError
    ):

        return FIXED_GOOD_VALUES[
            "environment_heat_index"
        ]


# =========================================================
# DAILY AGGREGATION
# =========================================================

def aggregate_daily(df):

    if df.empty:
        return df

    df = df.copy()

    # ---------------------------------------------------------
    # TIMESTAMP
    # ---------------------------------------------------------

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df["date"] = (
        df["timestamp"]
        .dt.strftime("%Y-%m-%d")
    )

    # ---------------------------------------------------------
    # NUMERIC COLUMNS
    # ---------------------------------------------------------

    numeric_columns = [
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
        "farm_temperature_c",
        "farm_humidity",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # =========================================================
    # DHT22 → ENVIRONMENT HEAT INDEX
    # =========================================================

    if (
        "farm_temperature_c" in df.columns
        and "farm_humidity" in df.columns
    ):

        valid_environment = (
            df["farm_temperature_c"].notna()
            &
            df["farm_humidity"].notna()
        )

        df.loc[
            valid_environment,
            "environment_heat_index"
        ] = df.loc[
            valid_environment
        ].apply(
            lambda row:
                calculate_heat_index(
                    row["farm_temperature_c"],
                    row["farm_humidity"]
                ),
            axis=1
        )

    # =========================================================
    # DAILY AGGREGATION
    # =========================================================

    aggregation = {

        # Milk
        "milk_yield_l": "sum",
        "milk_conductivity": "mean",
        "milk_temp_c": "mean",

        # SCC
        "scc_value": "last",

        # Existing ML signals
        "activity_score": "mean",
        "rumination_min": "mean",
        "environment_heat_index": "mean",

        "hygiene_score": "mean",
        "feed_score": "mean",
        "milking_hygiene_score": "mean",

        # Actual DHT22 values stored for display/history
        "farm_temperature_c": "mean",
        "farm_humidity": "mean",
    }

    available_aggregation = {
        key: value
        for key, value in aggregation.items()
        if key in df.columns
    }

    result = (
        df
        .groupby(
            "date",
            as_index=False
        )
        .agg(
            available_aggregation
        )
    )

    # =========================================================
    # DEFAULT EXISTING ML VALUES
    # =========================================================

    for column, value in FIXED_GOOD_VALUES.items():

        if column not in result.columns:

            result[column] = value

        else:

            result[column] = (
                result[column]
                .fillna(value)
            )

    # =========================================================
    # SCC DEFAULT
    # =========================================================

    if "scc_value" not in result.columns:

        result["scc_value"] = 180000.0

    else:

        result["scc_value"] = (
            result["scc_value"]
            .fillna(180000.0)
        )

    return result


# =========================================================
# FEATURE ENGINEERING
# =========================================================

def engineer(daily):

    d = daily.copy()

    # ---------------------------------------------------------
    # SORT BY DATE
    # ---------------------------------------------------------

    if "date" in d.columns:

        d = (
            d
            .sort_values("date")
            .reset_index(drop=True)
        )

    # ---------------------------------------------------------
    # ENSURE EXISTING ML SIGNALS EXIST
    # ---------------------------------------------------------

    for signal in SIGNALS:

        if signal not in d.columns:

            d[signal] = FIXED_GOOD_VALUES.get(
                signal,
                0.0
            )

        d[signal] = pd.to_numeric(
            d[signal],
            errors="coerce"
        )

        d[signal] = (
            d[signal]
            .fillna(
                d[signal].median()
            )
        )

        d[signal] = (
            d[signal]
            .fillna(0.0)
        )

    # =========================================================
    # ROLLING FEATURES
    # =========================================================

    for signal in SIGNALS:

        s = d[signal]

        # -----------------------------------------------------
        # 3-DAY FEATURES
        # -----------------------------------------------------

        d[
            f"{signal}_mean_3d"
        ] = (
            s
            .rolling(
                3,
                min_periods=1
            )
            .mean()
        )

        d[
            f"{signal}_min_3d"
        ] = (
            s
            .rolling(
                3,
                min_periods=1
            )
            .min()
        )

        d[
            f"{signal}_max_3d"
        ] = (
            s
            .rolling(
                3,
                min_periods=1
            )
            .max()
        )

        d[
            f"{signal}_std_3d"
        ] = (
            s
            .rolling(
                3,
                min_periods=1
            )
            .std()
            .fillna(0)
        )

        d[
            f"{signal}_delta_3d"
        ] = (
            s - s.shift(2)
        ).fillna(0)

        # -----------------------------------------------------
        # 7-DAY FEATURES
        # -----------------------------------------------------

        d[
            f"{signal}_mean_7d"
        ] = (
            s
            .rolling(
                7,
                min_periods=1
            )
            .mean()
        )

        d[
            f"{signal}_min_7d"
        ] = (
            s
            .rolling(
                7,
                min_periods=1
            )
            .min()
        )

        d[
            f"{signal}_max_7d"
        ] = (
            s
            .rolling(
                7,
                min_periods=1
            )
            .max()
        )

        d[
            f"{signal}_std_7d"
        ] = (
            s
            .rolling(
                7,
                min_periods=1
            )
            .std()
            .fillna(0)
        )

        d[
            f"{signal}_delta_7d"
        ] = (
            s - s.shift(6)
        ).fillna(0)

    # =========================================================
    # NUMERIC CLEANUP
    # =========================================================

    for column in d.columns:

        if column not in [
            "date",
            "breed",
            "calving_date",
            "herd_id"
        ]:

            d[column] = pd.to_numeric(
                d[column],
                errors="coerce"
            )

    d = d.replace(
        [np.inf, -np.inf],
        np.nan
    )

    d = d.fillna(0)

    return d