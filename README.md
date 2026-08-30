# Bovine Mastitis Forecasting V3

## Current prototype workflow

The prototype now focuses on the **animal's own accumulated history**. Farm-management parameters are not required for the current version.

Each daily sample is permanently stored against a `cow_id`. When a new sample is received, the backend:

1. Stores the sample.
2. Aggregates all samples for that cow by calendar day.
3. Builds rolling 3-day and 7-day features using only data available up to each day.
4. Calculates both **7-day and 14-day mastitis risk**.
5. Returns the latest risk immediately from `/ingest`.
6. Exposes `/cows/{cow_id}/risk-history` so the dashboard can show how risk changed day by day.

### Core parameters entered for the current prototype

- Milk yield (L/day)
- Milk electrical conductivity
- Milk temperature
- SCC, when available (periodic is supported; latest known SCC is carried forward)

Animal registry information such as age, parity, vaccination status and previous mastitis history is also available to the model.

### Full ML feature set is retained

The ML model still contains the original farm/behaviour feature set: activity, rumination, environmental heat index, farm hygiene, feed quality, and milking hygiene. Because these farm details are out of scope for the current prototype, the backend automatically fills them with fixed healthy baseline values for every reading:

- Activity score: `0.90`
- Rumination: `520 min/day`
- Environmental heat index: `70`
- Hygiene score: `0.90`
- Feed score: `0.90`
- Milking hygiene score: `0.95`

These are prototype defaults, not measured farm conditions. They can be replaced later with real farm inputs without changing the overall model interface.

### ESP32

The ESP32 is configured for **one daily sample**. It currently has placeholder values for milk yield and conductivity; replace those with the calibrated sensor readings. For a quick demo, change `SAMPLE_INTERVAL_MS` in `hardware/esp32_v2.ino` to `10000UL`.

## Run

```text
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -r requirements.txt
python generate_data.py
python train_model.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

New terminal:

```text
python seed_demo.py
```

Dashboard:

```text
python -m http.server 5500 --directory frontend
```

Open `http://127.0.0.1:5500`.

## API example

Register a cow once:

```json
{"cow_id":"cow_001","breed":"HF","age_years":5,"parity":2,"vaccination_status":1,"prior_mastitis_flag":0}
```

Then send one sample each day:

```json
{"cow_id":"cow_001","milk_yield_l":14.2,"milk_conductivity":4.8,"milk_temp_c":38.5,"scc_value":250000,"source":"esp32"}
```

The `/ingest` response contains the current **7-day and 14-day risk** and the number of daily observations accumulated for that cow. Each new sample is appended to the cow's history, and the returned prediction is based only on information available for that cow up to the latest submitted sample.

## Important limitation

The training data is synthetic. The prototype demonstrates the end-to-end forecasting workflow, but real dairy-farm data and field validation are required before clinical or veterinary performance claims are made.
