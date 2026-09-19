"""
ingest_to_server.py
====================

Feeds raw daily cow readings into YOUR RUNNING MastiSense server over
real HTTP (the same way the dashboard, a phone app, or a real sensor
gateway would) -- not a test client, not a shortcut. After running
this, open the dashboard and the cows/risk scores will be there.

Prerequisites (do these first, in separate terminals):

    # Terminal 1 -- start the API server
    cd Bovine_mastitis_V4
    python -m venv venv && source venv/bin/activate   # (Windows: venv\\Scripts\\activate)
    pip install -r requirements.txt
    uvicorn main:app --host 127.0.0.1 --port 8000 --reload

    # Terminal 2 -- start the dashboard
    cd Bovine_mastitis_V4/dashboard
    python -m http.server 5500
    # then open http://127.0.0.1:5500 in your browser
    # (the dashboard's "API URL" field should already say http://127.0.0.1:8000 --
    #  if not, set it there)

Then, in a THIRD terminal, run this script (needs `pip install requests`
if you don't already have it, and does NOT need the project's venv):

    python ingest_to_server.py 10_cows_WITH_mastitis.csv
    python ingest_to_server.py 10_cows_WITHOUT_mastitis.csv

Refresh the dashboard after each file finishes -- you'll see all 10 cows
in that file, each with a live risk score and tier computed by your
actual trained model, exactly as if a real sensor had been reporting
for that many days.

The input CSV must contain ONLY raw sensor readings -- no risk, tier,
or label columns. This script will refuse to run otherwise, since
feeding the answer back into the model would defeat the point of
checking it.
"""
import sys
import time

FORBIDDEN_COLUMNS = {
    "target_7d", "target_14d", "event_onset_day", "subclinical",
    "risk", "risk_7d", "risk_14d", "tier", "predicted_tier_7d",
    "predicted_tier_14d", "predicted_risk_7d", "predicted_risk_14d",
}

if len(sys.argv) < 2:
    print("Usage: python ingest_to_server.py <raw_readings.csv> [server_url]")
    sys.exit(1)

INPUT_CSV = sys.argv[1]
SERVER = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8000"

try:
    import requests
except ImportError:
    print("This script needs the 'requests' package: pip install requests")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("This script needs pandas: pip install pandas")
    sys.exit(1)

# ---- sanity check the server is actually up before doing anything ----
try:
    health = requests.get(f"{SERVER}/", timeout=5)
except requests.exceptions.ConnectionError:
    print(f"Could not reach {SERVER}.")
    print("Is uvicorn running? (see the instructions at the top of this file)")
    sys.exit(1)

df = pd.read_csv(INPUT_CSV)

present_forbidden = FORBIDDEN_COLUMNS & set(c.lower() for c in df.columns)
if present_forbidden:
    print(
        f"REFUSING TO RUN: input file contains label/prediction columns "
        f"{present_forbidden}. Pass only raw sensor readings."
    )
    sys.exit(1)

required = {"cow_id", "date", "milk_yield_l", "milk_conductivity", "milk_temp_c"}
missing = required - set(df.columns)
if missing:
    print(f"Input CSV is missing required columns: {missing}")
    sys.exit(1)

df["date"] = pd.to_datetime(df["date"])

OPTIONAL_SENSOR_COLS = [
    "scc_value", "activity_score", "rumination_min", "environment_heat_index",
    "hygiene_score", "feed_score", "milking_hygiene_score",
]

n_cows = df["cow_id"].nunique()
print(f"Server: {SERVER}")
print(f"Loaded {len(df)} raw readings for {n_cows} cows from {INPUT_CSV}")
print("Registering cows and posting daily readings (this talks to your real server)...\n")

for cow_id, group in df.groupby("cow_id"):
    group = group.sort_values("date").reset_index(drop=True)
    meta = group.iloc[0]

    reg_payload = {"cow_id": cow_id}
    for k in ["breed", "age_years", "parity", "vaccination_status",
              "prior_mastitis_flag", "calving_date", "herd_id"]:
        if k in group.columns and pd.notna(meta.get(k)):
            v = meta[k]
            reg_payload[k] = int(v) if k in ("age_years", "parity", "vaccination_status", "prior_mastitis_flag") else v

    r = requests.post(f"{SERVER}/cows", json=reg_payload, timeout=10)
    if r.status_code not in (200, 201, 409):  # 409 = already registered, fine
        print(f"  [!] Could not register {cow_id}: {r.status_code} {r.text[:200]}")

    last_tier7 = last_tier14 = None
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

        r = requests.post(f"{SERVER}/ingest", json=payload, timeout=15)
        if r.status_code == 200:
            risk = r.json().get("risk", {})
            last_tier7 = risk.get("risk_tier_7d")
            last_tier14 = risk.get("risk_tier_14d")
        else:
            print(f"  [!] {cow_id} {row['date'].date()}: HTTP {r.status_code} {r.text[:150]}")

    print(f"  {cow_id}: {len(group)} days posted -> latest tier = {last_tier7} (7d) / {last_tier14} (14d)")

print("\nDone. Open (or refresh) your dashboard now -- these cows and their")
print("live risk scores were computed by your real running server, not by me.")
