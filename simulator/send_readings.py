import requests, time, random
from datetime import datetime, timezone, timedelta

BASE = "http://127.0.0.1:8000"
COW = "cow_001"

# Sends one sample per simulated day. The backend supplies fixed healthy farm-management defaults.
DEMO_SECONDS = 5
start = datetime.now(timezone.utc)
for day in range(14):
    p = day / 13
    payload = {
        "cow_id": COW,
        "timestamp": (start + timedelta(days=day)).isoformat(),
        "milk_yield_l": round(14.5 - 2.5*p + random.uniform(-.15,.15), 2),
        "milk_conductivity": round(4.5 + 1.4*p + random.uniform(-.05,.05), 2),
        "milk_temp_c": round(38.4 + .5*p + random.uniform(-.03,.03), 2),
        "scc_value": round(180000 + 700000*p),
        "source": "python_simulator"
    }
    r = requests.post(BASE + "/ingest", json=payload, timeout=10)
    print(day + 1, r.status_code, r.json().get("risk", {}))
    time.sleep(DEMO_SECONDS)
