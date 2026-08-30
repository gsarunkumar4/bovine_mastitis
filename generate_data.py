import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

rng = np.random.default_rng(2026)
N_COWS, DAYS = 160, 100
rows = []
breeds = ["HF", "Jersey", "Crossbred", "Indigenous"]

for c in range(1, N_COWS + 1):
    cow_id = f"cow_{c:03d}"
    breed = rng.choice(breeds)
    age_years = int(rng.integers(3, 9))
    parity = int(rng.integers(1, 6))
    prior_mastitis = int(rng.random() < 0.25)
    vaccinated = int(rng.random() > 0.08)
    calving_date = datetime(2025, 12, 1) + timedelta(days=int(rng.integers(0, 50)))
    base_yield = max(8, rng.normal(15, 2.3))
    base_cond = max(2.8, rng.normal(4.5, 0.3))
    base_temp = rng.normal(38.5, 0.18)
    has_event = rng.random() < 0.30
    onset = int(rng.integers(45, 90)) if has_event else None

    for d in range(DAYS):
        dt = datetime(2026, 1, 1) + timedelta(days=d)
        p = (d - (onset - 14)) / 14 if has_event and onset - 14 <= d <= onset else 0
        yield_l = base_yield + rng.normal(0, .45) - 4*p
        cond = base_cond + rng.normal(0, .08) + 1.9*p
        temp = base_temp + rng.normal(0, .06) + .70*p
        scc = max(30_000, 180_000 + rng.normal(0, 35_000) + 1_200_000*p)
        rows.append({
            "cow_id": cow_id, "timestamp": dt.isoformat(),
            "milk_yield_l": round(max(2, yield_l), 3),
            "milk_conductivity": round(max(.5, cond), 3),
            "milk_temp_c": round(temp, 3), "scc_value": round(scc),
            "target_7d": int(has_event and 1 <= onset-d <= 7),
            "target_14d": int(has_event and 1 <= onset-d <= 14),
            "event_onset_day": onset if has_event else -1,
            "breed": breed, "age_years": age_years, "parity": parity,
            "vaccination_status": vaccinated, "prior_mastitis_flag": prior_mastitis,
            "calving_date": calving_date.date().isoformat(), "herd_id": "demo_herd_01"
        })

df = pd.DataFrame(rows)
Path("data").mkdir(exist_ok=True)
df.to_csv("data/raw.csv", index=False)
df.to_csv("data/cleaned.csv", index=False)
print(f"Created {len(df):,} daily observations for {N_COWS} cows.")
print("7-day positive rows:", int(df.target_7d.sum()))
print("14-day positive rows:", int(df.target_14d.sum()))
