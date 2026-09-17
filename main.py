from pathlib import Path
from datetime import datetime, timezone
import json
import traceback

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import (
    ROOT,
    MODELS_DIR,
    FEATURE_PIPELINE_VERSION,
    DATA_TYPE,
    USE_REAL_FARM_FEATURES,
    FIXED_GOOD_VALUES,
    TIER_THRESHOLDS,
)

from app.services.database import init_db, connect

from app.services.features import (
    validate_reading,
    engineer,
    aggregate_daily,
    derive_heat_index,
)

from app.services.explainability import top_drivers
from app.services.recommendations import recommendations
from app.services.versioning import (
    has_current_model,
    load_current_model,
    list_versions,
)
from app.services.calibration import apply_calibration

from app.services.data_quality import (
    check_reading_quality,
    check_timestamp_sanity,
    check_scc_staleness,
    check_abnormal_jump,
)

from app.services.drift import summarize_drift

from app.routes.cows import router as cows_router


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="MastiSense Daily 7/14-Day Mastitis Risk Forecasting API"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(cows_router)


# ============================================================
# GLOBAL MODEL VARIABLES
# ============================================================

models = {}
calibrators = {}
feature_cols = []
metrics = {}
active_version = None
metadata = {}


# ============================================================
# READING MODEL
# ============================================================

class Reading(BaseModel):
    cow_id: str

    timestamp: str | None = None

    # --------------------------------------------------------
    # Core daily sensor values
    # --------------------------------------------------------

    milk_yield_l: float = Field(ge=0)

    # Must be greater than zero.
    # ESP32 currently sends minimum value 0.010.
    milk_conductivity: float = Field(gt=0)

    milk_temp_c: float

    # SCC is supplied periodically.
    scc_value: float | None = Field(default=None, ge=0)

    source: str = "sensor"

    # --------------------------------------------------------
    # Optional farm / behaviour inputs
    # --------------------------------------------------------

    activity_score: float | None = None

    rumination_min: float | None = None

    environment_heat_index: float | None = None

    hygiene_score: float | None = None

    feed_score: float | None = None

    milking_hygiene_score: float | None = None

    # --------------------------------------------------------
    # Extended sensor inputs
    # --------------------------------------------------------

    farm_temperature_c: float | None = None

    farm_humidity: float | None = None

    milk_pH: float | None = None

    body_temperature: float | None = None

    udder_surface_temperature: float | None = None


# ============================================================
# MODEL LOADING
# ============================================================

def load_model():
    """
    Load the currently promoted production model.

    If no validated production model exists, prediction remains
    disabled but data ingestion continues to work.
    """

    global models
    global calibrators
    global feature_cols
    global metrics
    global active_version
    global metadata

    if has_current_model(MODELS_DIR):

        try:

            info = load_current_model(MODELS_DIR)

            models = info["models"]

            calibrators = info.get(
                "calibrators",
                {}
            )

            feature_cols = info["feature_cols"]

            metrics = info["metrics"]

            active_version = info["version"]

            metadata = info.get(
                "metadata",
                {}
            )

            print(
                f"[MastiSense] Active production model loaded: "
                f"version {active_version}"
            )

            print(
                f"[MastiSense] Models available: "
                f"{list(models.keys())}"
            )

            print(
                f"[MastiSense] Feature columns: "
                f"{len(feature_cols)}"
            )

        except Exception as e:

            models = {}

            calibrators = {}

            feature_cols = []

            metrics = {}

            active_version = None

            metadata = {}

            print(
                "[MastiSense] Error loading models/current:"
            )

            print(repr(e))

            traceback.print_exc()

    else:

        models = {}

        calibrators = {}

        feature_cols = []

        metrics = {}

        active_version = None

        metadata = {}

        print(
            "[MastiSense] Notice: No validated production "
            "model in models/current/"
        )

        print(
            "[MastiSense] Predictions disabled."
        )


# ============================================================
# COW DATABASE HELPER
# ============================================================

def cow(cow_id):

    c = connect()

    try:

        r = c.execute(
            """
            SELECT *
            FROM cows
            WHERE cow_id=?
            """,
            (cow_id,),
        ).fetchone()

        return dict(r) if r else None

    finally:

        c.close()


# ============================================================
# RAW READINGS
# ============================================================

def raw(cow_id):

    c = connect()

    try:

        rows = c.execute(
            """
            SELECT *
            FROM readings
            WHERE cow_id=?
            ORDER BY timestamp
            """,
            (cow_id,),
        ).fetchall()

        return pd.DataFrame(
            [dict(x) for x in rows]
        )

    finally:

        c.close()


# ============================================================
# RISK TIER
# ============================================================

def tier(p):

    if p < TIER_THRESHOLDS["no_risk"]:

        return "No Risk"

    elif p < TIER_THRESHOLDS["low_risk"]:

        return "Low Risk"

    elif p < TIER_THRESHOLDS["moderate_risk"]:

        return "Moderate Risk"

    return "High Risk"


# ============================================================
# BUILD FEATURES
# ============================================================

def build_features(cow_id):

    # --------------------------------------------------------
    # Check cow
    # --------------------------------------------------------

    info = cow(cow_id)

    if not info:

        raise HTTPException(
            404,
            "Cow not registered"
        )

    # --------------------------------------------------------
    # Get raw readings
    # --------------------------------------------------------

    r = raw(cow_id)

    if r.empty:

        raise HTTPException(
            404,
            "No readings for cow"
        )

    # --------------------------------------------------------
    # Aggregate daily
    # --------------------------------------------------------

    d = aggregate_daily(r)

    # --------------------------------------------------------
    # Add cow metadata
    # --------------------------------------------------------

    for k in [
        "age_years",
        "parity",
        "vaccination_status",
        "prior_mastitis_flag",
        "breed",
        "calving_date",
        "herd_id",
    ]:

        d[k] = info.get(k)

    # --------------------------------------------------------
    # Feature engineering
    # --------------------------------------------------------

    f = engineer(d)

    # --------------------------------------------------------
    # Check model feature compatibility
    # --------------------------------------------------------

    missing = [
        c
        for c in feature_cols
        if c not in f.columns
    ]

    if missing:

        raise HTTPException(
            500,
            (
                "Model/feature mismatch: retrain the models "
                f"(missing columns: {missing[:5]}"
                + (
                    ", ..."
                    if len(missing) > 5
                    else ""
                )
                + ")"
            ),
        )

    return info, d, f


# ============================================================
# SINGLE MODEL PREDICTION
# ============================================================

def prediction_row(
    model_key,
    f,
    row_index=-1
):

    # --------------------------------------------------------
    # Check requested model
    # --------------------------------------------------------

    if model_key not in models:

        raise RuntimeError(
            f"Model '{model_key}' is not available. "
            f"Available models: {list(models.keys())}"
        )

    model = models[model_key]

    # --------------------------------------------------------
    # Select feature columns
    # --------------------------------------------------------

    x = f[feature_cols].iloc[
        [row_index]
    ]

    # --------------------------------------------------------
    # Debug information
    # --------------------------------------------------------

    print(
        f"[MastiSense] Predicting using {model_key}"
    )

    print(
        f"[MastiSense] Input shape: {x.shape}"
    )

    # --------------------------------------------------------
    # Raw probability
    # --------------------------------------------------------

    raw_probability = model.predict_proba(
        x
    )

    raw_p = float(
        raw_probability[:, 1][0]
    )

    # --------------------------------------------------------
    # Calibration
    # --------------------------------------------------------

    cal = calibrators.get(
        model_key
    )

    if cal is not None:

        p = float(
            apply_calibration(
                [raw_p],
                cal
            )[0]
        )

        p = max(
            0.0,
            min(
                1.0,
                p
            )
        )

    else:

        p = raw_p

    return (
        p,
        x,
        raw_p
    )


# ============================================================
# PREDICT
# ============================================================

def predict(cow_id):

    # --------------------------------------------------------
    # Load model if necessary
    # --------------------------------------------------------

    if not models:

        load_model()

    # --------------------------------------------------------
    # No model
    # --------------------------------------------------------

    if not models:

        raise HTTPException(
            503,
            detail=(
                "No validated production model is "
                "currently approved for serving. "
                "Trained candidates exist under models/ "
                "for audit but failed promotion gates."
            ),
        )

    # --------------------------------------------------------
    # Build features
    # --------------------------------------------------------

    info, d, f = build_features(
        cow_id
    )

    # --------------------------------------------------------
    # 7-day prediction
    # --------------------------------------------------------

    p7, x7, raw_p7 = prediction_row(
        "7d",
        f
    )

    # --------------------------------------------------------
    # 14-day prediction
    # --------------------------------------------------------

    p14, x14, raw_p14 = prediction_row(
        "14d",
        f
    )

    # --------------------------------------------------------
    # Number of days
    # --------------------------------------------------------

    days = int(
        len(d)
    )

    # --------------------------------------------------------
    # Data sufficiency warning
    # --------------------------------------------------------

    data_warning = (

        f"Limited history ({days} days) — "
        "early warning reliability is reduced; "
        "accumulating >= 7 daily readings "
        "improves forecast precision."

        if days < 7

        else None
    )

    # --------------------------------------------------------
    # SCC staleness
    # --------------------------------------------------------

    c = connect()

    try:

        scc_staleness_warn = check_scc_staleness(
            cow_id,
            c
        )

    finally:

        c.close()

    # --------------------------------------------------------
    # Build response
    # --------------------------------------------------------

    resp = {

        # ----------------------------------------------------
        # Core fields
        # ----------------------------------------------------

        "cow_id": cow_id,

        "date": str(
            f.timestamp.iloc[-1]
        ),

        "data_days": days,

        # ----------------------------------------------------
        # 7-day risk
        # ----------------------------------------------------

        "risk_score_7d": round(
            p7,
            4
        ),

        "risk_percent_7d": round(
            p7 * 100,
            1
        ),

        "risk_tier_7d": tier(
            p7
        ),

        # ----------------------------------------------------
        # 14-day risk
        # ----------------------------------------------------

        "risk_score_14d": round(
            p14,
            4
        ),

        "risk_percent_14d": round(
            p14 * 100,
            1
        ),

        "risk_tier_14d": tier(
            p14
        ),

        # ----------------------------------------------------
        # Forecast horizon
        # ----------------------------------------------------

        "forecast_horizon_days": [
            7,
            14
        ],

        # ----------------------------------------------------
        # Explainability
        # ----------------------------------------------------

        "top_driver_features": top_drivers(
            x7,
            models["7d"]
        ),

        "top_driver_features_14d": top_drivers(
            x14,
            models["14d"]
        ),

        # ----------------------------------------------------
        # Recommendations
        # ----------------------------------------------------

        "recommendations": recommendations(
            x7.iloc[0].to_dict()
        ),

        # ----------------------------------------------------
        # Note
        # ----------------------------------------------------

        "note": (
            "Risk is calculated using all daily "
            "information accumulated for this cow "
            "up to the latest sample. This is prototype "
            "decision support, not a clinical diagnosis."
        ),

        # ----------------------------------------------------
        # Model provenance
        # ----------------------------------------------------

        "model_version": active_version,

        "training_data_type": DATA_TYPE,

        "feature_pipeline_version":
            FEATURE_PIPELINE_VERSION,

        "calibration_method": "sigmoid",

        "raw_risk_score_7d": round(
            raw_p7,
            4
        ),

        "raw_risk_score_14d": round(
            raw_p14,
            4
        ),

        "baseline_mode":
            not USE_REAL_FARM_FEATURES,

        "prediction_timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),

        # ----------------------------------------------------
        # Data quality
        # ----------------------------------------------------

        "data_sufficiency_warning":
            data_warning,

        "scc_staleness_warning":
            scc_staleness_warn,
    }

    return resp


# ============================================================
# RISK HISTORY
# ============================================================

def risk_history(cow_id):

    if not models:

        load_model()

    if not models:

        return []

    _, d, f = build_features(
        cow_id
    )

    rows = []

    for i in range(
        len(f)
    ):

        p7, _, raw_p7 = prediction_row(
            "7d",
            f,
            i
        )

        p14, _, raw_p14 = prediction_row(
            "14d",
            f,
            i
        )

        rows.append({

            "date": str(
                f.timestamp.iloc[i]
            ),

            "data_days":
                i + 1,

            "risk_percent_7d":
                round(
                    p7 * 100,
                    1
                ),

            "risk_tier_7d":
                tier(p7),

            "risk_percent_14d":
                round(
                    p14 * 100,
                    1
                ),

            "risk_tier_14d":
                tier(p14),

            "raw_risk_score_7d":
                round(
                    raw_p7,
                    4
                ),

            "raw_risk_score_14d":
                round(
                    raw_p14,
                    4
                ),
        })

    return rows


# ============================================================
# ALERT CREATION
# ============================================================

def maybe_alert(res):

    """
    Create one alert per cow/day when either
    forecast horizon is high risk.
    """

    if not res:

        return False

    if (
        res.get("risk_tier_7d") != "High Risk"
        and
        res.get("risk_tier_14d") != "High Risk"
    ):

        return False

    high7 = (
        res["risk_tier_7d"]
        == "High Risk"
    )

    high14 = (
        res["risk_tier_14d"]
        == "High Risk"
    )

    day = res["date"][:10]

    # --------------------------------------------------------
    # Build alert message
    # --------------------------------------------------------

    if high7 and high14:

        message = (
            f"High mastitis risk. "
            f"7-day: {res['risk_percent_7d']:.1f}%, "
            f"14-day: {res['risk_percent_14d']:.1f}%. "
            "Re-check the cow and follow veterinary protocol."
        )

    elif high7:

        message = (
            f"High 7-day mastitis risk "
            f"({res['risk_percent_7d']:.1f}%). "
            "Re-check the cow and follow veterinary protocol."
        )

    else:

        message = (
            f"High 14-day mastitis risk "
            f"({res['risk_percent_14d']:.1f}%). "
            "Increase monitoring and follow veterinary protocol."
        )

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    c = connect()

    try:

        exists = c.execute(
            """
            SELECT 1
            FROM alerts
            WHERE cow_id=?
              AND substr(timestamp,1,10)=?
              AND message LIKE 'High%mastitis risk%'
            LIMIT 1
            """,
            (
                res["cow_id"],
                day
            ),
        ).fetchone()

        if exists:

            return False

        score = max(
            res["risk_score_7d"],
            res["risk_score_14d"]
        )

        m_version = (
            res.get("model_version")
            or
            active_version
            or
            "unvalidated"
        )

        c.execute(
            """
            INSERT INTO alerts(
                cow_id,
                timestamp,
                risk_score,
                message,
                model_version
            )
            VALUES(?,?,?,?,?)
            """,
            (
                res["cow_id"],
                datetime.now(
                    timezone.utc
                ).isoformat(),
                score,
                message,
                m_version,
            ),
        )

        c.commit()

        return True

    finally:

        c.close()


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():

    print(
        "[MastiSense] Initializing database..."
    )

    init_db()

    print(
        "[MastiSense] Loading model..."
    )

    load_model()

    print(
        "[MastiSense] Startup complete."
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    cands = [
        v["version"]
        for v in list_versions()
    ]

    return {

        "message":
            "MastiSense Daily 7/14-Day "
            "Mastitis Risk Forecasting API",

        "docs":
            "/docs",

        "model_status":
            "active"
            if active_version
            else
            "no_active_model",

        "model_version":
            active_version,

        "candidate_versions":
            cands,

        "note": (

            f"Production model "
            f"{active_version} active."

            if active_version

            else

            "No validated production model "
            "is currently approved for serving. "
            "Trained candidates exist in models/ "
            "for audit."
        ),

        "feature_pipeline_version":
            FEATURE_PIPELINE_VERSION,

        "data_type":
            DATA_TYPE,
    }


# ============================================================
# METRICS
# ============================================================

@app.get("/metrics")
def get_metrics():

    if metrics:

        return metrics

    return {

        "status":
            "no_active_production_model",

        "note":
            "No model candidate has passed "
            "the promotion quality bar for "
            "production serving.",

        "candidate_summaries":
            list_versions(),
    }


# ============================================================
# DRIFT SUMMARY
# ============================================================

@app.get("/drift/summary")
def get_drift_summary(
    days: int = 30
):

    c = connect()

    try:

        report = summarize_drift(
            c,
            recent_days=days
        )

        return report

    finally:

        c.close()


# ============================================================
# INGEST
# ============================================================

@app.post("/ingest")
def ingest(r: Reading):

    print()
    print("=" * 70)

    print(
        "[MastiSense] /ingest request received"
    )

    print(
        f"[MastiSense] Cow ID: {r.cow_id}"
    )

    print(
        f"[MastiSense] Milk yield: {r.milk_yield_l}"
    )

    print(
        f"[MastiSense] Conductivity: "
        f"{r.milk_conductivity}"
    )

    print(
        f"[MastiSense] Milk temperature: "
        f"{r.milk_temp_c}"
    )

    print("=" * 70)

    # ========================================================
    # VALIDATE READING
    # ========================================================

    errors = validate_reading(
        r
    )

    if errors:

        print(
            "[MastiSense] Reading validation failed:"
        )

        print(errors)

        raise HTTPException(
            422,
            errors
        )

    # ========================================================
    # CHECK COW
    # ========================================================

    if not cow(r.cow_id):

        print(
            f"[MastiSense] Cow not registered: "
            f"{r.cow_id}"
        )

        raise HTTPException(
            404,
            "Register cow first with POST /cows"
        )

    # ========================================================
    # TIMESTAMP
    # ========================================================

    ts = (
        r.timestamp
        or
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    try:

        datetime.fromisoformat(
            ts.replace(
                "Z",
                "+00:00"
            )
        )

    except ValueError:

        raise HTTPException(
            422,
            "timestamp must be ISO 8601"
        )

    # ========================================================
    # DATA QUALITY
    # ========================================================

    quality_warnings = []

    try:

        quality_warnings.extend(
            check_reading_quality(r)
        )

    except Exception as e:

        print(
            "[MastiSense] Warning: "
            "reading quality check failed:"
        )

        print(repr(e))

        quality_warnings.append(
            f"Reading quality check failed: {e}"
        )

    try:

        quality_warnings.extend(
            check_timestamp_sanity(ts)
        )

    except Exception as e:

        print(
            "[MastiSense] Warning: "
            "timestamp sanity check failed:"
        )

        print(repr(e))

        quality_warnings.append(
            f"Timestamp check failed: {e}"
        )

    # ========================================================
    # DATABASE CONNECTION
    # ========================================================

    c = connect()

    try:

        # ----------------------------------------------------
        # Abnormal jump detection
        # ----------------------------------------------------

        try:

            jump_warnings = check_abnormal_jump(
                r.cow_id,
                r,
                c
            )

            quality_warnings.extend(
                jump_warnings
            )

        except Exception as e:

            print(
                "[MastiSense] Warning: "
                "abnormal jump check failed:"
            )

            print(repr(e))

            quality_warnings.append(
                f"Abnormal jump check failed: {e}"
            )

        # ----------------------------------------------------
        # Derive heat index
        # ----------------------------------------------------

        heat_index = (
            r.environment_heat_index
        )

        if (
            heat_index is None
            and
            r.farm_temperature_c is not None
            and
            r.farm_humidity is not None
        ):

            heat_index = round(
                r.farm_temperature_c
                +
                0.36 * r.farm_humidity
                -
                10.0,
                1
            )

        # ----------------------------------------------------
        # Insert reading
        # ----------------------------------------------------

        c.execute(
            """
            INSERT INTO readings(
                cow_id,
                timestamp,
                milk_yield_l,
                milk_conductivity,
                milk_temp_c,
                scc_value,
                activity_score,
                rumination_min,
                environment_heat_index,
                hygiene_score,
                feed_score,
                milking_hygiene_score,
                source,
                farm_temperature_c,
                farm_humidity,
                milk_pH,
                body_temperature,
                udder_surface_temperature
            )
            VALUES(
                ?,?,?,?,?,?,
                ?,?,?,?,?,?,
                ?,?,?,?,?,?
            )
            """,
            (
                r.cow_id,
                ts,
                r.milk_yield_l,
                r.milk_conductivity,
                r.milk_temp_c,
                r.scc_value,

                (
                    r.activity_score
                    if r.activity_score is not None
                    else
                    FIXED_GOOD_VALUES[
                        "activity_score"
                    ]
                ),

                (
                    r.rumination_min
                    if r.rumination_min is not None
                    else
                    FIXED_GOOD_VALUES[
                        "rumination_min"
                    ]
                ),

                (
                    heat_index
                    if heat_index is not None
                    else
                    FIXED_GOOD_VALUES[
                        "environment_heat_index"
                    ]
                ),

                (
                    r.hygiene_score
                    if r.hygiene_score is not None
                    else
                    FIXED_GOOD_VALUES[
                        "hygiene_score"
                    ]
                ),

                (
                    r.feed_score
                    if r.feed_score is not None
                    else
                    FIXED_GOOD_VALUES[
                        "feed_score"
                    ]
                ),

                (
                    r.milking_hygiene_score
                    if r.milking_hygiene_score is not None
                    else
                    FIXED_GOOD_VALUES[
                        "milking_hygiene_score"
                    ]
                ),

                r.source,

                r.farm_temperature_c,

                r.farm_humidity,

                r.milk_pH,

                r.body_temperature,

                r.udder_surface_temperature,
            ),
        )

        c.commit()

        print(
            "[MastiSense] Reading stored successfully."
        )

    except Exception as e:

        c.rollback()

        print(
            "[MastiSense] DATABASE ERROR:"
        )

        print(repr(e))

        traceback.print_exc()

        raise HTTPException(
            500,
            f"Database error while storing reading: {e}"
        )

    finally:

        c.close()

    # ========================================================
    # MODEL LOADING
    # ========================================================

    if not models:

        print(
            "[MastiSense] No model currently loaded."
        )

        try:

            load_model()

        except Exception as e:

            print(
                "[MastiSense] Model loading failed:"
            )

            print(repr(e))

            traceback.print_exc()

    # ========================================================
    # PREDICTION
    # ========================================================

    result = None

    prediction_error = None

    alert_created = False

    alert_error = None

    if models:

        print(
            "[MastiSense] Active model detected."
        )

        print(
            "[MastiSense] Starting prediction..."
        )

        try:

            result = predict(
                r.cow_id
            )

            print(
                "[MastiSense] Prediction successful."
            )

            print(
                f"[MastiSense] 7-day risk: "
                f"{result.get('risk_percent_7d')}%"
            )

            print(
                f"[MastiSense] 14-day risk: "
                f"{result.get('risk_percent_14d')}%"
            )

            print(
                f"[MastiSense] 7-day tier: "
                f"{result.get('risk_tier_7d')}"
            )

            print(
                f"[MastiSense] 14-day tier: "
                f"{result.get('risk_tier_14d')}"
            )

        except HTTPException as e:

            prediction_error = (
                f"Prediction HTTP error "
                f"{e.status_code}: {e.detail}"
            )

            print(
                "[MastiSense] PREDICTION ERROR:"
            )

            print(
                prediction_error
            )

            traceback.print_exc()

        except Exception as e:

            prediction_error = (
                f"{type(e).__name__}: {str(e)}"
            )

            print(
                "[MastiSense] PREDICTION ERROR:"
            )

            print(
                prediction_error
            )

            traceback.print_exc()

    else:

        print(
            "[MastiSense] No active production model."
        )

        print(
            "[MastiSense] Prediction skipped."
        )

    # ========================================================
    # ALERT
    # ========================================================

    if result is not None:

        print(
            "[MastiSense] Checking alerts..."
        )

        try:

            alert_created = maybe_alert(
                result
            )

            print(
                f"[MastiSense] Alert created: "
                f"{alert_created}"
            )

        except Exception as e:

            alert_error = (
                f"{type(e).__name__}: {str(e)}"
            )

            print(
                "[MastiSense] ALERT ERROR:"
            )

            print(
                alert_error
            )

            traceback.print_exc()

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    response = {

        "stored": True,

        "cow_id":
            r.cow_id,

        "timestamp":
            ts,

        "risk":
            result,

        "model_status":
            "active"
            if models
            else
            "no_active_model",

        "model_version":
            active_version,

        "quality_warnings":
            (
                quality_warnings
                if quality_warnings
                else
                None
            ),

        "prediction_error":
            prediction_error,

        "alert_created":
            alert_created,

        "alert_error":
            alert_error,

        "note": (

            "Reading recorded and risk predicted."

            if result is not None

            else

            "Reading recorded permanently. "
            "Risk prediction was skipped or failed. "
            "Check prediction_error for details."
        ),
    }

    print(
        "[MastiSense] /ingest completed."
    )

    print(
        f"[MastiSense] Response: "
        f"{json.dumps(response, default=str)}"
    )

    print("=" * 70)
    print()

    return response


# ============================================================
# COW RISK
# ============================================================

@app.get("/cows/{cow_id}/risk")
def cow_risk(
    cow_id
):

    try:

        res = predict(
            cow_id
        )

        try:

            maybe_alert(
                res
            )

        except Exception as e:

            print(
                "[MastiSense] Alert creation failed:"
            )

            print(repr(e))

        return res

    except HTTPException:

        raise

    except Exception as e:

        print(
            "[MastiSense] Cow risk prediction failed:"
        )

        print(repr(e))

        traceback.print_exc()

        raise HTTPException(
            500,
            f"Prediction failed: {e}"
        )


# ============================================================
# RISK HISTORY
# ============================================================

@app.get("/cows/{cow_id}/risk-history")
def cow_risk_history(
    cow_id
):

    try:

        return risk_history(
            cow_id
        )

    except HTTPException:

        raise

    except Exception as e:

        print(
            "[MastiSense] Risk history failed:"
        )

        print(repr(e))

        traceback.print_exc()

        raise HTTPException(
            500,
            f"Risk history prediction failed: {e}"
        )


# ============================================================
# COW HISTORY
# ============================================================

@app.get("/cows/{cow_id}/history")
def history(
    cow_id
):

    r = raw(
        cow_id
    )

    if r.empty:

        raise HTTPException(
            404,
            "No readings"
        )

    return (
        r.astype(object)
        .where(
            pd.notna(r),
            None
        )
        .to_dict(
            orient="records"
        )
    )


# ============================================================
# HERD RISK
# ============================================================

@app.get("/herd/risk")
def herd_risk():

    if not models:

        try:

            load_model()

        except Exception as e:

            print(
                "[herd/risk] Model loading failed:"
            )

            print(repr(e))

    if not models:

        return []

    c = connect()

    try:

        ids = [
            x[0]
            for x in c.execute(
                "SELECT cow_id FROM cows"
            ).fetchall()
        ]

    finally:

        c.close()

    out = []

    for cid in ids:

        try:

            out.append(
                predict(cid)
            )

        except HTTPException:

            continue

        except Exception as e:

            print(
                f"[herd/risk] prediction failed "
                f"for {cid}: {e!r}"
            )

            traceback.print_exc()

    return sorted(
        out,
        key=lambda x:
            x.get(
                "risk_score_7d",
                0
            ),
        reverse=True
    )


# ============================================================
# ALERTS
# ============================================================

@app.get("/alerts")
def alerts(
    status: str | None = None
):

    c = connect()

    try:

        if status:

            rows = c.execute(
                """
                SELECT *
                FROM alerts
                WHERE status=?
                ORDER BY id DESC
                LIMIT 50
                """,
                (status,),
            ).fetchall()

        else:

            rows = c.execute(
                """
                SELECT *
                FROM alerts
                ORDER BY id DESC
                LIMIT 50
                """
            ).fetchall()

        return [
            dict(x)
            for x in rows
        ]

    finally:

        c.close()


# ============================================================
# RESOLVE ALERT
# ============================================================

@app.post(
    "/alerts/{alert_id}/resolve"
)
def resolve_alert(
    alert_id: int,
    body: dict | None = None
):

    note = (
        body or {}
    ).get(
        "note",
        ""
    )

    c = connect()

    try:

        row = c.execute(
            """
            SELECT id
            FROM alerts
            WHERE id=?
            """,
            (alert_id,),
        ).fetchone()

        if not row:

            raise HTTPException(
                404,
                "Alert not found"
            )

        c.execute(
            """
            UPDATE alerts
            SET
                status='resolved',
                resolved_at=?,
                resolved_note=?
            WHERE id=?
            """,
            (
                datetime.now(
                    timezone.utc
                ).isoformat(),
                note,
                alert_id,
            ),
        )

        c.commit()

        return {
            "status":
                "resolved",

            "alert_id":
                alert_id,
        }

    finally:

        c.close()


# ============================================================
# CHECK ALERTS
# ============================================================

@app.post("/alerts/check")
def check_alerts():

    """
    Evaluate all cows and persist alerts
    for high 7-day or 14-day risk.
    """

    if not models:

        try:

            load_model()

        except Exception as e:

            print(
                "[alerts/check] "
                "Model loading failed:"
            )

            print(repr(e))

    if not models:

        return {

            "status":
                "skipped",

            "high_risk_count":
                0,

            "high_risk_cows":
                [],

            "new_alerts_created":
                0,

            "note":
                "Alert check skipped: "
                "no validated production model "
                "approved for serving.",
        }

    h = herd_risk()

    high = [

        x

        for x in h

        if (
            x.get("risk_tier_7d")
            ==
            "High Risk"
        )

        or

        (
            x.get("risk_tier_14d")
            ==
            "High Risk"
        )
    ]

    created = 0

    for x in high:

        try:

            if maybe_alert(x):

                created += 1

        except Exception as e:

            print(
                "[alerts/check] "
                "Failed to create alert:"
            )

            print(repr(e))

    return {

        "status":
            "evaluated",

        "high_risk_count":
            len(high),

        "high_risk_cows":
            high,

        "new_alerts_created":
            created,
    }


# ============================================================
# FEEDBACK
# ============================================================

@app.post("/feedback")
def feedback(
    body: dict
):

    if "cow_id" not in body:

        raise HTTPException(
            400,
            "cow_id required"
        )

    c = connect()

    try:

        c.execute(
            """
            INSERT INTO feedback(
                cow_id,
                event_date,
                confirmed_mastitis,
                notes
            )
            VALUES(?,?,?,?)
            """,
            (
                body["cow_id"],
                body.get(
                    "event_date"
                ),
                body.get(
                    "confirmed_mastitis"
                ),
                body.get(
                    "notes",
                    ""
                ),
            ),
        )

        c.commit()

        return {

            "stored":
                True,

            "message":
                "Outcome stored for future "
                "model retraining.",
        }

    finally:

        c.close()