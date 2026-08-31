"""Load demo_10_cows_14_days.csv into the local prototype.

Before running, make sure the FastAPI backend is running on port 8000.
This script resets the local demo database by default so the dashboard starts clean.
"""

from pathlib import Path
import csv
import requests

BASE = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parent

# CSV is in the same folder as this script.
CSV_PATH = ROOT / "demo_10_cows_14_days.csv"

DB_PATH = ROOT / "mastitis.db"
RESET_DB = False

if RESET_DB and DB_PATH.exists():
    DB_PATH.unlink()

with CSV_PATH.open(newline="") as f:
    rows = list(csv.DictReader(f))

# Register each cow once.
seen = set()

for row in rows:
    cid = row["cow_id"]

    if cid in seen:
        continue

    seen.add(cid)

    payload = {
        "cow_id": cid,
        "breed": "HF",
        "age_years": 4 + (int(cid[-1]) % 4),
        "parity": 2 + (int(cid[-1]) % 3),
        "vaccination_status": 1,
        "prior_mastitis_flag": 1 if cid in {"COW108", "COW109", "COW110"} else 0,
        "herd_id": "demo_herd_01",
    }

    r = requests.post(BASE + "/cows", json=payload, timeout=15)
    r.raise_for_status()

# Submit chronologically so each cow's accumulated history grows naturally.
for row in rows:
    payload = {
        "cow_id": row["cow_id"],
        "timestamp": row["timestamp"],
        "milk_yield_l": float(row["milk_yield_l"]),
        "milk_conductivity": float(row["milk_conductivity"]),
        "milk_temp_c": float(row["milk_temp_c"]),
        "scc_value": float(row["scc_value"]),
        "source": "demo_csv",
    }

    r = requests.post(BASE + "/ingest", json=payload, timeout=30)
    r.raise_for_status()

print(f"Loaded {len(seen)} cows and {len(rows)} daily samples.")
print("Open http://127.0.0.1:5500 to view the dashboard.")
print("Demo cows: " + ", ".join(sorted(seen)))