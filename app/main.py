from pathlib import Path
from datetime import datetime, timezone

import json
import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.services.database import (
    init_db,
    connect
)

from app.services.features import (
    validate_reading,
    engineer,
    aggregate_daily,
    FIXED_GOOD_VALUES,
    calculate_heat_index
)

from app.services.explainability import (
    top_drivers
)

from app.services.recommendations import (
    recommendations
)

from app.routes.cows import (
    router as cows_router
)


# =========================================================
# ROOT
# =========================================================

ROOT = Path(
    __file__
).resolve().parent.parent


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Bovine Mastitis Daily 7/14-Day Risk Forecasting API"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(
    cows_router
)


# =========================================================
# GLOBAL MODEL VARIABLES
# =========================================================

models = {}

feature_cols = []

metrics = {}


# =========================================================
# READING MODEL
# =========================================================

class Reading(BaseModel):

    # ---------------------------------------------------------
    # COW
    # ---------------------------------------------------------

    cow_id: str

    timestamp: str | None = None

    # ---------------------------------------------------------
    # MILK SENSOR DATA
    # ---------------------------------------------------------

    milk_yield_l: float = Field(
        ge=0
    )

    milk_conductivity: float = Field(
        gt=0
    )

    milk_temp_c: float

    # ---------------------------------------------------------
    # SCC
    # ---------------------------------------------------------

    scc_value: float | None = Field(
        default=None,
        ge=0
    )

    # ---------------------------------------------------------
    # SOURCE
    # ---------------------------------------------------------

    source: str = "sensor"

    # ---------------------------------------------------------
    # EXISTING ML SIGNALS
    # ---------------------------------------------------------

    activity_score: float | None = None

    rumination_min: float | None = None

    environment_heat_index: float | None = None

    hygiene_score: float | None = None

    feed_score: float | None = None

    milking_hygiene_score: float | None = None

    # ---------------------------------------------------------
    # DHT22 FARM ENVIRONMENT
    # ---------------------------------------------------------

    farm_temperature_c: float | None = None

    farm_humidity: float | None = None


# =========================================================
# LOAD MODELS
# =========================================================

def load_model():

    global models
    global feature_cols
    global metrics

    models = {

        "7d": joblib.load(
            ROOT
            / "models"
            / "mastitis_model_7d.joblib"
        ),

        "14d": joblib.load(
            ROOT
            / "models"
            / "mastitis_model_14d.joblib"
        ),
    }

    feature_cols = joblib.load(
        ROOT
        / "models"
        / "feature_cols.joblib"
    )

    metrics = json.loads(
        (
            ROOT
            / "models"
            / "metrics.json"
        ).read_text()
    )


# =========================================================
# GET COW
# =========================================================

def cow(cow_id):

    c = connect()

    row = c.execute(
        """
        SELECT *
        FROM cows
        WHERE cow_id=?
        """,
        (cow_id,)
    ).fetchone()

    c.close()

    return dict(row) if row else None


# =========================================================
# GET RAW READINGS
# =========================================================

def raw(cow_id):

    c = connect()

    rows = c.execute(
        """
        SELECT *
        FROM readings
        WHERE cow_id=?
        ORDER BY timestamp
        """,
        (cow_id,)
    ).fetchall()

    c.close()

    return pd.DataFrame(
        [dict(x) for x in rows]
    )


# =========================================================
# RISK TIER
# =========================================================

def tier(p):

    return (
        "No Risk"
        if p < .25
        else
        "Low Risk"
        if p < .50
        else
        "Moderate Risk"
        if p < .75
        else
        "High Risk"
    )


# =========================================================
# BUILD FEATURES
# =========================================================

def build_features(cow_id):

    info = cow(
        cow_id
    )

    if not info:

        raise HTTPException(
            404,
            "Cow not registered"
        )

    r = raw(
        cow_id
    )

    if r.empty:

        raise HTTPException(
            404,
            "No readings for cow"
        )

    # ---------------------------------------------------------
    # DAILY AGGREGATION
    # ---------------------------------------------------------

    d = aggregate_daily(
        r
    )

    # ---------------------------------------------------------
    # COW INFORMATION
    # ---------------------------------------------------------

    for k in [
        "age_years",
        "parity",
        "vaccination_status",
        "prior_mastitis_flag",
        "breed",
        "calving_date",
        "herd_id"
    ]:

        d[k] = info.get(k)

    # ---------------------------------------------------------
    # ENGINEER ML FEATURES
    # ---------------------------------------------------------

    f = engineer(
        d
    )

    # Keep timestamp/date information available
    # for risk history / current date.
    f["timestamp"] = pd.to_datetime(
        d["date"],
        errors="coerce"
    )

    return info, d, f


# =========================================================
# PREDICTION ROW
# =========================================================

def prediction_row(
    model_key,
    f,
    row_index=-1
):

    model = models[
        model_key
    ]

    # ---------------------------------------------------------
    # SELECT ONLY MODEL FEATURES
    # ---------------------------------------------------------

    x = f[
        feature_cols
    ].iloc[
        [row_index]
    ]

    # ---------------------------------------------------------
    # FORCE NUMERIC VALUES
    # ---------------------------------------------------------

    x = x.apply(
        pd.to_numeric,
        errors="coerce"
    )

    x = x.replace(
        [float("inf"), float("-inf")],
        0
    )

    x = x.fillna(0)

    # ---------------------------------------------------------
    # PREDICTION
    # ---------------------------------------------------------

    p = float(
        model
        .predict_proba(x)[:, 1][0]
    )

    return p, x


# =========================================================
# PREDICT CURRENT RISK
# =========================================================

def predict(cow_id):

    if not models:

        load_model()

    _, d, f = build_features(
        cow_id
    )

    p7, x7 = prediction_row(
        "7d",
        f
    )

    p14, _ = prediction_row(
        "14d",
        f
    )

    days = int(
        len(d)
    )

    # ---------------------------------------------------------
    # LATEST ENVIRONMENT VALUES
    # ---------------------------------------------------------

    latest_environment = {}

    if "farm_temperature_c" in d.columns:

        value = d[
            "farm_temperature_c"
        ].iloc[-1]

        if pd.notna(value):

            latest_environment[
                "farm_temperature_c"
            ] = round(
                float(value),
                2
            )

    if "farm_humidity" in d.columns:

        value = d[
            "farm_humidity"
        ].iloc[-1]

        if pd.notna(value):

            latest_environment[
                "farm_humidity"
            ] = round(
                float(value),
                2
            )

    if "environment_heat_index" in d.columns:

        value = d[
            "environment_heat_index"
        ].iloc[-1]

        if pd.notna(value):

            latest_environment[
                "environment_heat_index"
            ] = round(
                float(value),
                2
            )

    # ---------------------------------------------------------
    # RESPONSE
    # ---------------------------------------------------------

    return {

        "cow_id": cow_id,

        "date": str(
            f.timestamp.iloc[-1]
        ),

        "data_days": days,

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

        "forecast_horizon_days": [
            7,
            14
        ],

        "environment": latest_environment,

        "top_driver_features": top_drivers(
            x7,
            models["7d"]
        ),

        "recommendations": recommendations(
            x7.iloc[0].to_dict()
        ),

        "note": (
            "Risk is calculated using all daily "
            "information accumulated for this cow "
            "up to the latest sample. This is "
            "prototype decision support, not a diagnosis."
        )
    }


# =========================================================
# RISK HISTORY
# =========================================================

def risk_history(cow_id):

    if not models:

        load_model()

    _, d, f = build_features(
        cow_id
    )

    rows = []

    for i in range(
        len(f)
    ):

        p7, _ = prediction_row(
            "7d",
            f,
            i
        )

        p14, _ = prediction_row(
            "14d",
            f,
            i
        )

        rows.append({

            "date": str(
                f.timestamp.iloc[i]
            ),

            "data_days": i + 1,

            "risk_percent_7d": round(
                p7 * 100,
                1
            ),

            "risk_tier_7d": tier(
                p7
            ),

            "risk_percent_14d": round(
                p14 * 100,
                1
            ),

            "risk_tier_14d": tier(
                p14
            ),
        })

    return rows


# =========================================================
# ALERT
# =========================================================

def maybe_alert(res):

    """
    Create one alert per cow/day when either
    forecast horizon is high risk.
    """

    if (
        res["risk_tier_7d"] != "High Risk"
        and
        res["risk_tier_14d"] != "High Risk"
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

    day = res[
        "date"
    ][:10]

    # ---------------------------------------------------------
    # MESSAGE
    # ---------------------------------------------------------

    if high7 and high14:

        message = (
            f"High mastitis risk. "
            f"7-day: "
            f"{res['risk_percent_7d']:.1f}%, "
            f"14-day: "
            f"{res['risk_percent_14d']:.1f}%. "
            "Re-check the cow and follow "
            "veterinary protocol."
        )

    elif high7:

        message = (
            f"High 7-day mastitis risk "
            f"({res['risk_percent_7d']:.1f}%). "
            "Re-check the cow and follow "
            "veterinary protocol."
        )

    else:

        message = (
            f"High 14-day mastitis risk "
            f"({res['risk_percent_14d']:.1f}%). "
            "Increase monitoring and follow "
            "veterinary protocol."
        )

    # ---------------------------------------------------------
    # CHECK DUPLICATE
    # ---------------------------------------------------------

    c = connect()

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
        )
    ).fetchone()

    # ---------------------------------------------------------
    # CREATE ALERT
    # ---------------------------------------------------------

    if not exists:

        score = max(
            res["risk_score_7d"],
            res["risk_score_14d"]
        )

        c.execute(
            """
            INSERT INTO alerts(
                cow_id,
                timestamp,
                risk_score,
                message
            )
            VALUES(?,?,?,?)
            """,
            (
                res["cow_id"],
                datetime
                .now(timezone.utc)
                .isoformat(),

                score,
                message
            )
        )

        c.commit()

        created = True

    else:

        created = False

    c.close()

    return created


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup():

    init_db()

    load_model()


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message":
            "Bovine Mastitis Daily "
            "7/14-Day Risk Forecasting API",

        "docs":
            "/docs"
    }


# =========================================================
# METRICS
# =========================================================

@app.get("/metrics")
def get_metrics():

    return metrics


# =========================================================
# INGEST
# =========================================================

@app.post("/ingest")
def ingest(r: Reading):

    # =========================================================
    # VALIDATE
    # =========================================================

    errors = validate_reading(
        r
    )

    if errors:

        raise HTTPException(
            status_code=422,
            detail=errors
        )

    # =========================================================
    # CHECK WHETHER COW EXISTS
    # =========================================================

    existing_cow = cow(
        r.cow_id
    )

    cow_created = False

    # =========================================================
    # AUTOMATICALLY CREATE COW
    # =========================================================

    if not existing_cow:

        c = connect()

        c.execute(
            """
            INSERT INTO cows(
                cow_id,
                breed,
                age_years,
                parity,
                calving_date,
                vaccination_status,
                prior_mastitis_flag,
                herd_id
            )
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                r.cow_id,

                # Default prototype values
                "HF",
                5.0,
                2,
                None,
                1,
                0,
                "demo_herd_01"
            )
        )

        c.commit()

        c.close()

        cow_created = True

        print(
            f"[AUTO-CREATE] "
            f"Cow {r.cow_id} "
            f"created automatically."
        )

    # =========================================================
    # TIMESTAMP
    # =========================================================

    ts = (
        r.timestamp
        if r.timestamp
        else
        datetime
        .now(timezone.utc)
        .isoformat()
    )

    # =========================================================
    # DHT22 → ENVIRONMENT HEAT INDEX
    # =========================================================

    if (
        r.farm_temperature_c
        is not None
        and
        r.farm_humidity
        is not None
    ):

        environment_heat_index = (
            calculate_heat_index(
                r.farm_temperature_c,
                r.farm_humidity
            )
        )

    else:

        # Backward compatibility
        if (
            r.environment_heat_index
            is not None
        ):

            environment_heat_index = (
                r.environment_heat_index
            )

        else:

            environment_heat_index = (
                FIXED_GOOD_VALUES[
                    "environment_heat_index"
                ]
            )

    # =========================================================
    # INSERT READING
    # =========================================================

    c = connect()

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

            farm_temperature_c,
            farm_humidity,

            source
        )
        VALUES(
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?
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

            # IMPORTANT:
            # Actual DHT22-derived THI
            environment_heat_index,

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

            # Actual DHT22 values
            r.farm_temperature_c,
            r.farm_humidity,

            r.source
        )
    )

    c.commit()

    c.close()

    # =========================================================
    # PREDICT
    # =========================================================

    result = predict(
        r.cow_id
    )

    # =========================================================
    # ALERT
    # =========================================================

    maybe_alert(
        result
    )

    # =========================================================
    # RESPONSE
    # =========================================================

    return {

        "stored": True,

        "cow_id": r.cow_id,

        "cow_created_automatically":
            cow_created,

        "timestamp": ts,

        "environment": {

            "farm_temperature_c":
                r.farm_temperature_c,

            "farm_humidity":
                r.farm_humidity,

            "environment_heat_index":
                environment_heat_index
        },

        "risk": result
    }


# =========================================================
# CURRENT COW RISK
# =========================================================

@app.get("/cows/{cow_id}/risk")
def cow_risk(cow_id):

    res = predict(
        cow_id
    )

    maybe_alert(
        res
    )

    return res


# =========================================================
# RISK HISTORY
# =========================================================

@app.get("/cows/{cow_id}/risk-history")
def cow_risk_history(cow_id):

    return risk_history(
        cow_id
    )


# =========================================================
# RAW HISTORY
# =========================================================

@app.get("/cows/{cow_id}/history")
def history(cow_id):

    r = raw(
        cow_id
    )

    if r.empty:

        raise HTTPException(
            404,
            "No readings"
        )

    # JSON does not allow NaN.
    return (
        r
        .astype(object)
        .where(
            pd.notna(r),
            None
        )
        .to_dict(
            orient="records"
        )
    )


# =========================================================
# HERD RISK
# =========================================================

@app.get("/herd/risk")
def herd_risk():

    c = connect()

    ids = [
        x[0]
        for x in c.execute(
            "SELECT cow_id FROM cows"
        ).fetchall()
    ]

    c.close()

    out = []

    for cid in ids:

        try:

            out.append(
                predict(cid)
            )

        except Exception:

            pass

    return sorted(
        out,
        key=lambda x:
            x["risk_score_7d"],
        reverse=True
    )


# =========================================================
# ALERTS
# =========================================================

@app.get("/alerts")
def alerts():

    c = connect()

    rows = c.execute(
        """
        SELECT *
        FROM alerts
        ORDER BY id DESC
        LIMIT 50
        """
    ).fetchall()

    c.close()

    return [
        dict(x)
        for x in rows
    ]


# =========================================================
# CHECK ALERTS
# =========================================================

@app.post("/alerts/check")
def check_alerts():

    h = herd_risk()

    high = [
        x
        for x in h
        if
        x["risk_tier_7d"]
        == "High Risk"
        or
        x["risk_tier_14d"]
        == "High Risk"
    ]

    created = sum(
        1
        for x in high
        if maybe_alert(x)
    )

    return {

        "high_risk_count":
            len(high),

        "high_risk_cows":
            high,

        "new_alerts_created":
            created
    }


# =========================================================
# FEEDBACK
# =========================================================

@app.post("/feedback")
def feedback(body: dict):

    if "cow_id" not in body:

        raise HTTPException(
            400,
            "cow_id required"
        )

    c = connect()

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
            body.get("event_date"),
            body.get(
                "confirmed_mastitis"
            ),
            body.get(
                "notes",
                ""
            )
        )
    )

    c.commit()

    c.close()

    return {
        "stored": True,
        "message":
            "Outcome stored for future "
            "model retraining."
    }