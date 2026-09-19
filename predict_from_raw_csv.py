"""
predict_from_raw_csv.py
========================

Purpose
-------
Takes a CSV of RAW daily sensor readings only (no risk labels, no
predictions) and runs it through the actual MastiSense pipeline
(same code as the live API: /cows registration -> /ingest ->
feature engineering -> XGBoost model -> Platt calibration -> risk
tier) so you can see the ML compute the risk tier itself, live,
with nothing pre-filled.

The input CSV must NOT contain any of: target_7d, target_14d,
event_onset_day, subclinical, risk, tier. If it does, this script
will refuse to run, because that would mean you're feeding the
answer back into the model.

Usage
-----
    python predict_from_raw_csv.py raw_readings_only.csv predictions_out.csv

Required input columns (one row = one cow, one day):
    cow_id, date, milk_yield_l, milk_conductivity, milk_temp_c
Optional (used if present, else filled from config.FIXED_GOOD_VALUES
per the README's documented prototype behaviour):
    scc_value, activity_score, rumination_min, environment_heat_index,
    hygiene_score, feed_score, milking_hygiene_score
Optional cow metadata (used once per cow, first row wins):
    breed, age_years, parity, vaccination_status, prior_mastitis_flag,
    calving_date, herd_id

Output columns added by the model (nothing else is written):
    predicted_risk_7d_pct, predicted_tier_7d,
    predicted_risk_14d_pct, predicted_tier_14d

Run this from inside the project folder, with the project's venv
active, after `pip install -r requirements.txt`.
"""
import os
import sys
import io
import contextlib

FORBIDDEN_COLUMNS = {
    "target_7d", "target_14d", "event_onset_day", "subclinical",
    "risk", "risk_7d", "risk_14d", "tier", "predicted_tier_7d",
    "predicted_tier_14d", "predicted_risk_7d", "predicted_risk_14d",
}

if len(sys.argv) < 2:
    print("Usage: python predict_from_raw_csv.py <input_raw.csv> [output.csv]")
    sys.exit(1)

INPUT_CSV = sys.argv[1]
OUTPUT_CSV = sys.argv[2] if len(sys.argv) > 2 else "predictions_out.csv"

# Isolated, throwaway database so this never touches your real mastitis.db
TEMP_DB = os.path.abspath("./_manual_check.db")
if os.path.exists(TEMP_DB):
    os.remove(TEMP_DB)
os.environ["MASTISENSE_DB"] = TEMP_DB

import pandas as pd  # noqa: E402

df = pd.read_csv(INPUT_CSV)

present_forbidden = FORBIDDEN_COLUMNS & set(c.lower() for c in df.columns)
if present_forbidden:
    print(
        f"REFUSING TO RUN: input file contains label/prediction columns "
        f"{present_forbidden}. Remove them and pass only raw sensor readings "
        f"-- otherwise you'd be feeding the answer back into the model."
    )
    sys.exit(1)

required = {"cow_id", "date", "milk_yield_l", "milk_conductivity", "milk_temp_c"}
missing = required - set(df.columns)
if missing:
    print(f"Input CSV is missing required columns: {missing}")
    sys.exit(1)

df["date"] = pd.to_datetime(df["date"])

from fastapi.testclient import TestClient  # noqa: E402
import main as app_main  # noqa: E402
from app.services.database import init_db  # noqa: E402

init_db()
client = TestClient(app_main.app)

OPTIONAL_SENSOR_COLS = [
    "scc_value", "activity_score", "rumination_min", "environment_heat_index",
    "hygiene_score", "feed_score", "milking_hygiene_score",
]

results = []
n_cows = df["cow_id"].nunique()
print(f"Loaded {len(df)} raw readings for {n_cows} cows from {INPUT_CSV}")
print("Registering cows and feeding readings day-by-day through the live model...\n")

for cow_id, group in df.groupby("cow_id"):
    group = group.sort_values("date").reset_index(drop=True)
    meta = group.iloc[0]

    reg_payload = {
        "cow_id": cow_id,
        "parity": int(meta["parity"]) if "parity" in group.columns and pd.notna(meta.get("parity")) else 1,
    }
    for k in ["breed", "age_years", "vaccination_status", "prior_mastitis_flag",
              "calving_date", "herd_id"]:
        if k in group.columns and pd.notna(meta.get(k)):
            v = meta[k]
            reg_payload[k] = int(v) if k in ("age_years", "vaccination_status", "prior_mastitis_flag") else v

    with contextlib.redirect_stdout(io.StringIO()):
        client.post("/cows", json=reg_payload)

    for _, row in group.iterrows():
        payload = {
            "cow_id": cow_id,
            "timestamp": row["date"].isoformat(),
            "milk_yield_l": float(row["milk_yield_l"]),
            "milk_conductivity": float(row["milk_conductivity"]),
            "milk_temp_c": float(row["milk_temp_c"]),
            "source": "manual_check",
        }
        for col in OPTIONAL_SENSOR_COLS:
            if col in group.columns and pd.notna(row[col]):
                payload[col] = float(row[col])

        with contextlib.redirect_stdout(io.StringIO()):
            resp = client.post("/ingest", json=payload)
        risk7 = risk14 = tier7 = tier14 = None
        if resp.status_code == 200:
            r = resp.json().get("risk", {})
            risk7 = r.get("risk_percent_7d")
            risk14 = r.get("risk_percent_14d")
            tier7 = r.get("risk_tier_7d")
            tier14 = r.get("risk_tier_14d")

        results.append({
            "cow_id": cow_id,
            "date": row["date"].date().isoformat(),
            "predicted_risk_7d_pct": risk7,
            "predicted_tier_7d": tier7,
            "predicted_risk_14d_pct": risk14,
            "predicted_tier_14d": tier14,
        })

    print(f"  {cow_id}: {len(group)} days processed -> "
          f"latest tier = {tier7} (7d) / {tier14} (14d)")

out = pd.DataFrame(results)
out.to_csv(OUTPUT_CSV, index=False)
print(f"\nDone. Fresh model predictions written to: {OUTPUT_CSV}")
print("Nothing in this output was pre-filled -- every value came from a live")
print("/ingest call against the trained model in models/current/.")
