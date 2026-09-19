# MastiSense

**AI-IoT Based Early Mastitis Risk Forecasting System for Dairy Cattle**

MastiSense forecasts the probability that an individual cow will develop
mastitis within the next **7 days** and **14 days**, using daily IoT sensor
readings that accumulate over time. It provides animal-level and herd-level
risk scores, explainable risk drivers, management recommendations, and early
warning alerts through a bilingual (English / தமிழ்) dashboard.

> ⚠️ **Prototype decision-support system — not a clinical diagnostic tool.**
> Models are trained on **synthetic data**. Risk percentages are model
> probabilities, not diagnostic certainty. Real-world validation on farm data
> with veterinary-confirmed outcomes is required before any production use.

---

## Table of contents

- [Architecture](#architecture)
- [Quick start](#quick-start)
- [Hardware setup](#hardware-setup)
- [Model performance](#model-performance)
- [Model governance](#model-governance)
- [Project structure](#project-structure)
- [API endpoints](#api-endpoints)
- [Known limitations](#known-limitations)

---

## Architecture

```
ESP32 (DS18B20 + TDS + DHT22)
        │  HTTP POST /ingest
        ▼
FastAPI backend
   ├── Data quality & validation
   ├── SQLite permanent store
   ├── Shared feature pipeline
   │     ├── Calendar-day normalization (handles missed readings)
   │     ├── 3d/7d rolling statistics & deltas
   │     └── Days-in-milk + SCC staleness indicators
   ├── Model engine (models/current/)
   │     ├── 7-day XGBoost + Platt calibration
   │     ├── 14-day XGBoost + Platt calibration
   │     └── SHAP explainability
   ├── Recommendations & alerting
   └── Bilingual dashboard
```

---

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/gsarunkumar4/bovine_mastitis.git
cd bovine_mastitis

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Generate the synthetic dataset

The CSVs are not committed (≈23 MB). Regenerate them — the generator is
seeded, so output is identical every time:

```bash
python generate_data.py
```

### 3. Train the models (optional)

`models/current/` ships with a promoted model, so you can skip this. To
retrain from scratch:

```bash
python train_model.py
```

A newly trained candidate is **only** promoted to `models/current/` if it
passes the quality gates (see [Model governance](#model-governance)).

### 4. Run the backend

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive API docs: <http://127.0.0.1:8000/docs>

### 5. Load demo data (optional)

```bash
python seed_demo.py
```

### 6. Open the dashboard

Open `dashboard/index.html` in a browser, or serve it:

```bash
cd dashboard && python -m http.server 5500
```

Then visit <http://127.0.0.1:5500>.

### 7. Run tests

```bash
python -m pytest tests/ -v
```

---

## Hardware setup

| Component | Pin | Measures |
|---|---|---|
| DS18B20 | GPIO 4 | Milk temperature |
| TDS sensor | GPIO 34 | Milk conductivity |
| DHT22 | GPIO 16 | Farm temperature & humidity |
| Push button | GPIO 27 | Trigger a sample |

### Firmware configuration

```bash
cd hardware
cp secrets_example.h secrets.h
```

Edit `secrets.h` with your Blynk token, WiFi credentials, and your laptop's
IPv4 address. **`secrets.h` is gitignored — never commit it.**

Open the `.ino` in Arduino IDE, install the required libraries (`DHT sensor
library`, `OneWire`, `DallasTemperature`, `Blynk`), select your ESP32 board,
and upload.

### Usage

1. Open Serial Monitor at **115200 baud**.
2. Enter a Cow ID and parity when prompted — the ESP32 registers the cow
   automatically via `POST /cows`.
3. Press the button to take a sample. You'll be asked for milk yield and
   (optionally) SCC.
4. The reading is sent to `/ingest` and the returned 7-day / 14-day risk is
   printed.
5. Type `NEW` to register another cow.

**Values the hardware actually measures:** milk temperature, milk
conductivity, farm temperature, farm humidity. Milk yield and SCC are entered
manually. All other model inputs (activity, rumination, hygiene, feed scores)
use documented fixed baselines until real sensors are added — see
`config.py → FIXED_GOOD_VALUES`.

---

## Model performance

Trained on **synthetic data** (600 cows × 150 days). Evaluated on a held-out
test set of 91 cows with **zero animal overlap** with training or validation.

### 7-day horizon — primary early-warning alarm

| Metric | Test value |
|---|---|
| ROC-AUC | 0.9890 |
| AUPRC | 0.8025 |
| Recall (sensitivity) | 73.5% |
| Precision | 77.2% |
| Specificity | 99.7% |
| Brier score (calibrated) | 0.0050 |
| Logistic-regression baseline AUC | 0.9853 |

Confusion matrix: TP 125 · FP 37 · FN 45 · TN 12,456

### 14-day horizon — lower-confidence early-trend signal

| Metric | Test value |
|---|---|
| ROC-AUC | 0.8789 |
| AUPRC | 0.5628 |
| Recall (sensitivity) | 56.2% |
| Precision | 60.4% |
| Specificity | 98.9% |
| Brier score (calibrated) | 0.0165 |
| Logistic-regression baseline AUC | 0.8158 |

Confusion matrix: TP 191 · FP 125 · FN 149 · TN 11,577

**Why the 14-day target is lower:** forcing ≥80% recall at 14 days collapsed
precision below 10% (over 1,100 false alarms). Physiological changes two weeks
before clinical onset are genuinely subtle. The 14-day model is therefore
presented as a **watchlist / trend indicator**, not a primary alarm — the
7-day model is the authoritative clinical trigger.

---

## Model governance

Models are **never** auto-promoted just because training succeeded. A
candidate must pass explicit quality gates before serving predictions:

- Test recall ≥ the configured floor per horizon
- ROC-AUC not materially worse than the logistic-regression baseline
  (max deficit 0.02)
- Calibrated Brier score ≤ 0.05
- No leakage or data-quality findings

Failed candidates remain versioned for audit and **do not** become
`models/current/`. If no model is promoted, prediction endpoints return
HTTP 503 and the dashboard enters **Audit Mode** rather than showing an
unvalidated risk number.

`models/v001/` is preserved in this repo as a **rejected** candidate — its
`promotion_status.json` documents exactly why it failed. `models/v002/` is
the promoted model currently serving.

Other safeguards: animal-level train/val/test splitting, incomplete-window
label exclusion (rows whose forward horizon is unobserved are dropped, never
defaulted to negative), calendar-day-correct rolling features, threshold
tuning and probability calibration fitted on validation data only, and an
automatic audit triggered if AUC exceeds 0.99.

---

## Project structure

```
├── main.py                  FastAPI application
├── config.py                Centralized configuration
├── train_model.py           Training + promotion gating
├── retrain.py               Retraining orchestration
├── generate_data.py         Synthetic data generator
├── seed_demo.py             Demo data loader
├── app/
│   ├── routes/cows.py       Cow registration endpoints
│   └── services/
│       ├── features.py      Shared feature pipeline
│       ├── database.py      SQLite schema & migrations
│       ├── versioning.py    Model version registry
│       ├── calibration.py   Platt scaling & Brier score
│       ├── explainability.py SHAP drivers
│       ├── recommendations.py Decision-support rules
│       ├── data_quality.py  Ingestion audits
│       └── drift.py         PSI drift monitoring
├── dashboard/index.html     Bilingual dashboard
├── hardware/                ESP32 firmware
├── models/                  Versioned model artifacts
└── tests/                   Pytest suite
```

---

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/cows` | Register a cow |
| GET | `/cows` | List all cows |
| POST | `/ingest` | Submit a sensor reading |
| GET | `/cows/{id}/risk` | Current 7d/14d risk |
| GET | `/cows/{id}/risk-history` | Day-by-day risk trajectory |
| GET | `/cows/{id}/history` | Raw sensor history |
| GET | `/herd/risk` | Herd ranked by risk |
| GET | `/alerts` | Recent alerts |
| POST | `/alerts/check` | Evaluate herd, create alerts |
| POST | `/alerts/{id}/resolve` | Acknowledge an alert |
| POST | `/feedback` | Record confirmed outcome |
| GET | `/metrics` | Model metrics |
| GET | `/drift/summary` | Drift monitoring |

---

## Known limitations

- **Synthetic training data.** No public dataset exists with longitudinal
  daily sensor readings paired with forward-dated mastitis events. All
  reported metrics reflect simulated data and are not clinical validation.
- **Baseline-mode inputs.** Activity, rumination, hygiene, feed, and
  milking-hygiene scores use fixed healthy baselines. Real values supplied
  per-reading override them automatically; set
  `USE_REAL_FARM_FEATURES = True` once real collection exists.
- **Sensors not yet present:** milk pH, body temperature, udder surface
  temperature. Schema columns exist and are nullable.
- **Prototype sensor calibration.** The TDS-to-conductivity conversion is an
  approximation and requires calibration against a reference meter.
- **No authentication.** Suitable for local/offline demo only.
- **14-day forecast is lower confidence** — see
  [Model performance](#model-performance).

---

## License

Add a license file before public release (MIT is a common choice for
academic prototypes).