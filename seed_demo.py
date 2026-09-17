import pandas as pd, requests

BASE = "http://127.0.0.1:8000"
df = pd.read_csv("data/cleaned.csv")

for cid, g in df.groupby("cow_id"):
    r = g.iloc[0]
    requests.post(BASE + "/cows", json={
        "cow_id": cid, "breed": r.breed, "age_years": int(r.age_years),
        "parity": int(r.parity), "calving_date": r.calving_date,
        "vaccination_status": int(r.vaccination_status),
        "prior_mastitis_flag": int(r.prior_mastitis_flag), "herd_id": r.herd_id,
    }, timeout=10)

# Seed a manageable demo subset rather than the whole synthetic herd.
selected = df.cow_id.drop_duplicates().head(40)
for _, r in df[df.cow_id.isin(selected)].iterrows():
    payload = {
        "cow_id": r.cow_id,
        "timestamp": r.timestamp,
        "milk_yield_l": float(r.milk_yield_l),
        "milk_conductivity": float(r.milk_conductivity),
        "milk_temp_c": float(r.milk_temp_c),
        # SCC is periodic in the generated data (pd.NA/NaN on days it wasn't
        # tested) -- send it as JSON null rather than the non-standard
        # "NaN" literal so the request is valid JSON either way.
        "scc_value": None if pd.isna(r.scc_value) else float(r.scc_value),
        "source": "synthetic_seed",
    }
    resp = requests.post(BASE + "/ingest", json=payload, timeout=10)
    if resp.status_code >= 400:
        print("ingest failed for", r.cow_id, r.timestamp, resp.status_code, resp.text)

print("Demo cow registry and history loaded.")
