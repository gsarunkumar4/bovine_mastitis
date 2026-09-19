import os
os.environ["MASTISENSE_DB"] = "/home/claude/bulk_score.db"
if os.path.exists("/home/claude/bulk_score.db"):
    os.remove("/home/claude/bulk_score.db")

import sqlite3
import pandas as pd
import numpy as np
import joblib

from app.services.database import init_db, connect
import config

init_db()

df = pd.read_csv("data/cleaned.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"])

# bulk insert cows
cows_meta = df.drop_duplicates("cow_id")[
    ["cow_id", "breed", "age_years", "parity", "calving_date",
     "vaccination_status", "prior_mastitis_flag", "herd_id"]
]
c = connect()
cows_meta.to_sql("cows", c, if_exists="append", index=False)

readings = df[["cow_id", "timestamp", "milk_yield_l", "milk_conductivity",
               "milk_temp_c", "scc_value", "activity_score", "rumination_min",
               "environment_heat_index", "hygiene_score", "feed_score",
               "milking_hygiene_score"]].copy()
readings["timestamp"] = readings["timestamp"].astype(str)
readings["source"] = "backfill"
readings.to_sql("readings", c, if_exists="append", index=False)
c.commit()
c.close()

import main as app_main  # noqa: E402  (loads model after DB is populated)
app_main.load_model()

feature_cols = app_main.feature_cols
model7 = app_main.models["7d"]
model14 = app_main.models["14d"]
cal7 = app_main.calibrators.get("7d")
cal14 = app_main.calibrators.get("14d")

from app.services.calibration import apply_calibration
from config import TIER_THRESHOLDS

def tier(p):
    if p < TIER_THRESHOLDS["no_risk"]:
        return "No Risk"
    elif p < TIER_THRESHOLDS["low_risk"]:
        return "Low Risk"
    elif p < TIER_THRESHOLDS["moderate_risk"]:
        return "Moderate Risk"
    return "High Risk"

all_rows = []
cow_ids = df["cow_id"].unique().tolist()
print(f"Scoring {len(cow_ids)} cows...")

for i, cid in enumerate(cow_ids):
    try:
        info, d, f = app_main.build_features(cid)
    except Exception as e:
        print("SKIP", cid, e)
        continue
    x = f[feature_cols]
    raw7 = model7.predict_proba(x)[:, 1]
    raw14 = model14.predict_proba(x)[:, 1]
    cal_p7 = apply_calibration(raw7, cal7) if cal7 is not None else raw7
    cal_p14 = apply_calibration(raw14, cal14) if cal14 is not None else raw14
    cal_p7 = np.clip(cal_p7, 0, 1)
    cal_p14 = np.clip(cal_p14, 0, 1)

    sub = f[["cow_id", "timestamp"]].copy()
    sub["target_7d"] = d["target_7d"].values if "target_7d" in d.columns else np.nan
    # target_7d/14d in original df, join by timestamp
    sub["risk7"] = cal_p7
    sub["risk14"] = cal_p14
    sub["tier7"] = [tier(p) for p in cal_p7]
    sub["tier14"] = [tier(p) for p in cal_p14]
    all_rows.append(sub)
    if i % 100 == 0:
        print(i, cid)

out = pd.concat(all_rows, ignore_index=True)

# merge actual targets from original df
targets = df[["cow_id", "timestamp", "target_7d", "target_14d"]].copy()
out = out.drop(columns=["target_7d"]).merge(targets, on=["cow_id", "timestamp"], how="left")

out.to_csv("/home/claude/bulk_scored.csv", index=False)
print("\n=== TIER DISTRIBUTION (7d) overall ===")
print(out["tier7"].value_counts())
print("\n=== TIER DISTRIBUTION (14d) overall ===")
print(out["tier14"].value_counts())

print("\n=== Among rows where target_7d==1 (true positive days) ===")
pos = out[out["target_7d"] == 1]
print(pos["tier7"].value_counts())
print("max risk7 among positives:", pos["risk7"].max())
print("mean risk7 among positives:", pos["risk7"].mean())

print("\n=== Among rows where target_7d==0 (true negative days) ===")
neg = out[out["target_7d"] == 0]
print(neg["tier7"].value_counts())
print("max risk7 among negatives:", neg["risk7"].max())
