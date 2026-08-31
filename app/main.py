from pathlib import Path
from datetime import datetime, timezone
import json, joblib, pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.services.database import init_db, connect
from app.services.features import validate_reading, engineer, aggregate_daily, FIXED_GOOD_VALUES
from app.services.explainability import top_drivers
from app.services.recommendations import recommendations
from app.routes.cows import router as cows_router

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="Bovine Mastitis Daily 7/14-Day Risk Forecasting API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(cows_router)
models = {}; feature_cols = []; metrics = {}


class Reading(BaseModel):
    cow_id: str
    timestamp: str | None = None
    # Core daily sensor values.
    milk_yield_l: float = Field(ge=0)
    milk_conductivity: float = Field(gt=0)
    milk_temp_c: float
    # SCC can be supplied periodically; the latest known value is carried forward.
    scc_value: float | None = Field(default=None, ge=0)
    source: str = "sensor"
    # Optional legacy fields are accepted, but the current prototype defaults
    # these farm/behaviour inputs to fixed good values when omitted.
    activity_score: float | None = None
    rumination_min: float | None = None
    environment_heat_index: float | None = None
    hygiene_score: float | None = None
    feed_score: float | None = None
    milking_hygiene_score: float | None = None


def load_model():
    global models, feature_cols, metrics
    models = {
        "7d": joblib.load(ROOT / "models/mastitis_model_7d.joblib"),
        "14d": joblib.load(ROOT / "models/mastitis_model_14d.joblib"),
    }
    feature_cols = joblib.load(ROOT / "models/feature_cols.joblib")
    metrics = json.loads((ROOT / "models/metrics.json").read_text())


def cow(cow_id):
    c = connect(); r = c.execute("SELECT * FROM cows WHERE cow_id=?", (cow_id,)).fetchone(); c.close()
    return dict(r) if r else None


def raw(cow_id):
    c = connect(); rows = c.execute("SELECT * FROM readings WHERE cow_id=? ORDER BY timestamp", (cow_id,)).fetchall(); c.close()
    return pd.DataFrame([dict(x) for x in rows])


def tier(p):
    return "No Risk" if p < .25 else "Low Risk" if p < .50 else "Moderate Risk" if p < .75 else "High Risk"


def build_features(cow_id):
    info = cow(cow_id)
    if not info:
        raise HTTPException(404, "Cow not registered")
    r = raw(cow_id)
    if r.empty:
        raise HTTPException(404, "No readings for cow")
    d = aggregate_daily(r)
    for k in ["age_years", "parity", "vaccination_status", "prior_mastitis_flag", "breed", "calving_date", "herd_id"]:
        d[k] = info.get(k)
    return info, d, engineer(d)


def prediction_row(model_key, f, row_index=-1):
    model = models[model_key]
    x = f[feature_cols].iloc[[row_index]]
    p = float(model.predict_proba(x)[:, 1][0])
    return p, x


def predict(cow_id):
    if not models:
        load_model()
    _, d, f = build_features(cow_id)
    p7, x7 = prediction_row("7d", f)
    p14, _ = prediction_row("14d", f)
    days = int(len(d))
    return {
        "cow_id": cow_id,
        "date": str(f.timestamp.iloc[-1]),
        "data_days": days,
        "risk_score_7d": round(p7, 4),
        "risk_percent_7d": round(p7 * 100, 1),
        "risk_tier_7d": tier(p7),
        "risk_score_14d": round(p14, 4),
        "risk_percent_14d": round(p14 * 100, 1),
        "risk_tier_14d": tier(p14),
        "forecast_horizon_days": [7, 14],
        "top_driver_features": top_drivers(x7, models["7d"]),
        "recommendations": recommendations(x7.iloc[0].to_dict()),
        "note": "Risk is calculated using all daily information accumulated for this cow up to the latest sample. This is prototype decision support, not a diagnosis."
    }


def risk_history(cow_id):
    if not models:
        load_model()
    _, d, f = build_features(cow_id)
    rows = []
    for i in range(len(f)):
        p7, _ = prediction_row("7d", f, i)
        p14, _ = prediction_row("14d", f, i)
        rows.append({
            "date": str(f.timestamp.iloc[i]),
            "data_days": i + 1,
            "risk_percent_7d": round(p7 * 100, 1),
            "risk_tier_7d": tier(p7),
            "risk_percent_14d": round(p14 * 100, 1),
            "risk_tier_14d": tier(p14),
        })
    return rows


def maybe_alert(res):
    """Create one alert per cow/day when either forecast horizon is high risk."""
    if res["risk_tier_7d"] != "High Risk" and res["risk_tier_14d"] != "High Risk":
        return False

    high7 = res["risk_tier_7d"] == "High Risk"
    high14 = res["risk_tier_14d"] == "High Risk"
    day = res["date"][:10]
    if high7 and high14:
        message = (
            f"High mastitis risk. 7-day: {res['risk_percent_7d']:.1f}%, "
            f"14-day: {res['risk_percent_14d']:.1f}%. Re-check the cow and follow veterinary protocol."
        )
    elif high7:
        message = (
            f"High 7-day mastitis risk ({res['risk_percent_7d']:.1f}%). "
            "Re-check the cow and follow veterinary protocol."
        )
    else:
        message = (
            f"High 14-day mastitis risk ({res['risk_percent_14d']:.1f}%). "
            "Increase monitoring and follow veterinary protocol."
        )

    # Avoid duplicate alerts for the same cow and forecast day.
    c = connect()
    exists = c.execute(
        "SELECT 1 FROM alerts WHERE cow_id=? AND substr(timestamp,1,10)=? AND message LIKE 'High%mastitis risk%' LIMIT 1",
        (res["cow_id"], day),
    ).fetchone()
    if not exists:
        score = max(res["risk_score_7d"], res["risk_score_14d"])
        c.execute(
            "INSERT INTO alerts(cow_id,timestamp,risk_score,message) VALUES(?,?,?,?)",
            (res["cow_id"], datetime.now(timezone.utc).isoformat(), score, message),
        )
        c.commit()
        created = True
    else:
        created = False
    c.close()
    return created


@app.on_event("startup")
def startup():
    init_db(); load_model()


@app.get("/")
def root():
    return {"message": "Bovine Mastitis Daily 7/14-Day Risk Forecasting API", "docs": "/docs"}


@app.get("/metrics")
def get_metrics():
    return metrics


@app.post("/ingest")
def ingest(r: Reading):
    errors = validate_reading(r)
    if errors:
        raise HTTPException(422, errors)
    if not cow(r.cow_id):
        raise HTTPException(404, "Register cow first with POST /cows")
    ts = r.timestamp or datetime.now(timezone.utc).isoformat()
    c = connect()
    c.execute("""INSERT INTO readings(
                 cow_id,timestamp,milk_yield_l,milk_conductivity,milk_temp_c,scc_value,
                 activity_score,rumination_min,environment_heat_index,hygiene_score,
                 feed_score,milking_hygiene_score,source)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (r.cow_id, ts, r.milk_yield_l, r.milk_conductivity, r.milk_temp_c, r.scc_value,
               r.activity_score if r.activity_score is not None else FIXED_GOOD_VALUES["activity_score"],
               r.rumination_min if r.rumination_min is not None else FIXED_GOOD_VALUES["rumination_min"],
               r.environment_heat_index if r.environment_heat_index is not None else FIXED_GOOD_VALUES["environment_heat_index"],
               r.hygiene_score if r.hygiene_score is not None else FIXED_GOOD_VALUES["hygiene_score"],
               r.feed_score if r.feed_score is not None else FIXED_GOOD_VALUES["feed_score"],
               r.milking_hygiene_score if r.milking_hygiene_score is not None else FIXED_GOOD_VALUES["milking_hygiene_score"],
               r.source))
    c.commit(); c.close()

    # Every submitted sample is stored permanently. The returned risk uses the
    # complete history of this cow up to this sample/day.
    result = predict(r.cow_id)
    maybe_alert(result)
    return {"stored": True, "cow_id": r.cow_id, "timestamp": ts, "risk": result}


@app.get("/cows/{cow_id}/risk")
def cow_risk(cow_id):
    res = predict(cow_id); maybe_alert(res); return res


@app.get("/cows/{cow_id}/risk-history")
def cow_risk_history(cow_id):
    return risk_history(cow_id)


@app.get("/cows/{cow_id}/history")
def history(cow_id):
    r = raw(cow_id)
    if r.empty:
        raise HTTPException(404, "No readings")
    # JSON does not allow NaN. Return SQL NULL values as JSON null.
    return r.astype(object).where(pd.notna(r), None).to_dict(orient="records")


@app.get("/herd/risk")
def herd_risk():
    c = connect(); ids = [x[0] for x in c.execute("SELECT cow_id FROM cows").fetchall()]; c.close()
    out = []
    for cid in ids:
        try: out.append(predict(cid))
        except Exception: pass
    return sorted(out, key=lambda x: x["risk_score_7d"], reverse=True)


@app.get("/alerts")
def alerts():
    c = connect(); rows = c.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 50").fetchall(); c.close()
    return [dict(x) for x in rows]


@app.post("/alerts/check")
def check_alerts():
    """Evaluate all cows and persist alerts for high 7-day or 14-day risk."""
    h = herd_risk()
    high = [x for x in h if x["risk_tier_7d"] == "High Risk" or x["risk_tier_14d"] == "High Risk"]
    created = sum(1 for x in high if maybe_alert(x))
    return {
        "high_risk_count": len(high),
        "high_risk_cows": high,
        "new_alerts_created": created,
    }


@app.post("/feedback")
def feedback(body: dict):
    if "cow_id" not in body: raise HTTPException(400, "cow_id required")
    c = connect(); c.execute("INSERT INTO feedback(cow_id,event_date,confirmed_mastitis,notes) VALUES(?,?,?,?)",
                             (body["cow_id"], body.get("event_date"), body.get("confirmed_mastitis"), body.get("notes", "")))
    c.commit(); c.close()
    return {"stored": True, "message": "Outcome stored for future model retraining."}
