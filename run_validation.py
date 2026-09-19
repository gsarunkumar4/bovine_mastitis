"""
Feeds real historical readings for 10 mastitis-positive and 10
mastitis-negative synthetic cows (from data/cleaned.csv) through the
ACTUAL running FastAPI app (real model, real feature pipeline, real
calibration) via TestClient, day by day in chronological order, and
records what the deployed model predicted on each day.

This is an end-to-end check that ingestion -> feature pipeline ->
model -> calibration -> risk tier works correctly, using an isolated
throwaway database so it never touches mastitis.db.
"""
import os
import sys
import json
import io
import contextlib
import pandas as pd
import numpy as np

# Isolate DB before importing the app
TEST_DB = "/home/claude/validation_run.db"
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
os.environ["MASTISENSE_DB"] = TEST_DB

from fastapi.testclient import TestClient  # noqa: E402
import main as app_main  # noqa: E402
from app.services.database import init_db  # noqa: E402

init_db()
client = TestClient(app_main.app)

df = pd.read_csv("data/cleaned.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"])

onset = df[df["event_onset_day"] >= 0].groupby("cow_id")["event_onset_day"].first()
mastitis_cows = onset.sort_values().index.tolist()

never = df.groupby("cow_id")["event_onset_day"].max()
healthy_cows_all = never[never < 0].index.tolist()

rng = np.random.default_rng(42)
chosen_mastitis = mastitis_cows[:10]  # first 10 by earliest onset (variety of onset days)
chosen_healthy = list(rng.choice(healthy_cows_all, size=10, replace=False))

chosen = [(c, "mastitis") for c in chosen_mastitis] + [(c, "healthy") for c in chosen_healthy]

READING_COLS = [
    "milk_yield_l", "milk_conductivity", "milk_temp_c", "scc_value",
    "activity_score", "rumination_min", "environment_heat_index",
    "hygiene_score", "feed_score", "milking_hygiene_score",
]

results = []

for cow_id, group_label in chosen:
    cow_df = df[df["cow_id"] == cow_id].sort_values("timestamp").reset_index(drop=True)
    meta = cow_df.iloc[0]

    reg = client.post("/cows", json={
        "cow_id": cow_id,
        "breed": meta["breed"],
        "age_years": int(meta["age_years"]),
        "parity": int(meta["parity"]),
        "calving_date": str(meta["calving_date"]),
        "vaccination_status": int(meta["vaccination_status"]),
        "prior_mastitis_flag": int(meta["prior_mastitis_flag"]),
        "herd_id": meta["herd_id"],
    })
    if reg.status_code not in (200, 201):
        print("REG FAIL", cow_id, reg.status_code, reg.text)
        continue

    onset_day = int(meta["event_onset_day"]) if group_label == "mastitis" else None

    day_num = 0
    for _, row in cow_df.iterrows():
        payload = {
            "cow_id": cow_id,
            "timestamp": row["timestamp"].isoformat(),
            "milk_yield_l": float(row["milk_yield_l"]),
            "milk_conductivity": float(row["milk_conductivity"]),
            "milk_temp_c": float(row["milk_temp_c"]),
            "scc_value": (None if pd.isna(row["scc_value"]) else float(row["scc_value"])),
            "activity_score": float(row["activity_score"]),
            "rumination_min": float(row["rumination_min"]),
            "environment_heat_index": float(row["environment_heat_index"]),
            "hygiene_score": float(row["hygiene_score"]),
            "feed_score": float(row["feed_score"]),
            "milking_hygiene_score": float(row["milking_hygiene_score"]),
            "source": "backfill",
        }
        with contextlib.redirect_stdout(io.StringIO()):
            resp = client.post("/ingest", json=payload)
        risk7 = risk14 = tier7 = tier14 = None
        if resp.status_code == 200:
            body = resp.json()
            risk = body.get("risk", {})
            risk7 = risk.get("risk_percent_7d")
            risk14 = risk.get("risk_percent_14d")
            tier7 = risk.get("risk_tier_7d")
            tier14 = risk.get("risk_tier_14d")
        else:
            pass  # e.g. model not ready on very first rows; leave None

        days_to_onset = (onset_day - day_num) if onset_day is not None else None

        results.append({
            "cow_id": cow_id,
            "group": group_label,
            "day": day_num,
            "date": row["timestamp"].date().isoformat(),
            "days_until_onset": days_to_onset,
            "actual_target_7d": int(row["target_7d"]),
            "actual_target_14d": int(row["target_14d"]),
            "milk_yield_l": row["milk_yield_l"],
            "milk_conductivity": row["milk_conductivity"],
            "milk_temp_c": row["milk_temp_c"],
            "scc_value": row["scc_value"],
            "predicted_risk_7d": risk7,
            "predicted_risk_14d": risk14,
            "predicted_tier_7d": tier7,
            "predicted_tier_14d": tier14,
            "http_status": resp.status_code,
        })
        day_num += 1

out = pd.DataFrame(results)
out.to_csv("/home/claude/validation_results.csv", index=False)
print("TOTAL ROWS:", len(out))
print(out["http_status"].value_counts())
print("\nSample of non-200 responses:")
bad = out[out["http_status"] != 200]
print(bad.head(3))

# quick sanity summary
print("\n--- Per-cow summary (peak predicted 7d risk vs actual) ---")
summary = out.groupby(["cow_id", "group"]).agg(
    n_days=("day", "count"),
    peak_risk_7d=("predicted_risk_7d", "max"),
    peak_tier_7d=("predicted_tier_7d", lambda s: s.dropna().tolist()[-1] if len(s.dropna()) else None),
    any_actual_positive_7d=("actual_target_7d", "max"),
).reset_index()
print(summary.to_string())
