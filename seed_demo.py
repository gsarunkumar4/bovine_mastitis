import pandas as pd, requests
BASE="http://127.0.0.1:8000"
df=pd.read_csv("data/cleaned.csv")
for cid,g in df.groupby("cow_id"):
    r=g.iloc[0]
    requests.post(BASE+"/cows",json={"cow_id":cid,"breed":r.breed,"age_years":int(r.age_years),
      "parity":int(r.parity),"calving_date":r.calving_date,"vaccination_status":int(r.vaccination_status),
      "prior_mastitis_flag":int(r.prior_mastitis_flag),"herd_id":r.herd_id},timeout=10)
selected=df.cow_id.drop_duplicates().head(40)
for _,r in df[df.cow_id.isin(selected)].iterrows():
    payload = {k: (float(r[k]) if k in ["milk_yield_l","milk_conductivity","milk_temp_c","scc_value"] else r[k])
               for k in ["cow_id","timestamp","milk_yield_l","milk_conductivity","milk_temp_c","scc_value"]}
    payload["source"] = "synthetic_seed"
    requests.post(BASE+"/ingest", json=payload, timeout=10)
print("Demo cow registry and history loaded.")
