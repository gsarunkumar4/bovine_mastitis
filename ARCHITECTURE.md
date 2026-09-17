# MastiSense Architecture & Technical Specification
## AI-IoT Bovine Mastitis Early Risk Forecasting (7 & 14 Day Horizons)

---

### 1. System Overview & Data Flow

```text
+-----------------------------------------------------------------------------------+
| HARDWARE DATA LAYER                                                               |
|                                                                                   |
|  Current Workspace Firmware (hardware/esp32_v2.ino):                              |
|    - DS18B20 on GPIO4  --> milk_temp_c (real physical measurement)                |
|    - Calibrated placeholders --> milk_yield_l, milk_conductivity                  |
|                                                                                   |
|  Latest Hardware Design (to be copied into workspace later):                      |
|    - DHT22 on GPIO16   --> farm_temperature_c, farm_humidity (real ambient)       |
|    - DS18B20 on GPIO4  --> milk_temp_c (real milk temperature)                    |
|    - Analog TDS GPIO34 --> milk_conductivity (real milk conductivity)             |
|    - Push Button GPIO27--> triggers batch data collection & POST transmission     |
|                                                                                   |
|  Periodic Off-line Testing (Cow-side California Mastitis Test / Lab Diagnostic):  |
|    - scc_value         --> Somatic Cell Count (intermittent, e.g. every 3-7 days) |
+-----------------------------------------------------------------------------------+
                                         |
                                         | HTTP POST /ingest (JSON)
                                         v
+-----------------------------------------------------------------------------------+
| FASTAPI BACKEND & DATA QUALITY LAYER (main.py, app/services/data_quality.py)      |
|                                                                                   |
|  1. Range Validation: physically impossible sensor values reject with 422         |
|  2. Timestamp Sanity: checks for future or suspiciously stale timestamps          |
|  3. Sensor Jump Auditing: flags sudden non-physiological deltas in yield/temp/EC  |
|  4. Heat Index Derivation: computes Steadman HI when DHT22 T & H are present      |
|  5. Persistence: permanent storage in SQLite readings table (indexed by cow + ts) |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| SHARED FEATURE-ENGINEERING PIPELINE (app/services/features.py)                    |
|                                                                                   |
|  1. Calendar-Day Normalization: continuous 1-row-per-calendar-day grid per cow    |
|  2. Missing-Data Policy (Non-Negotiable):                                         |
|     - Directly observed: sensor reading present                                   |
|     - Short gap (<=2 days): carried forward, flagged as gap                       |
|     - Long gap (>2 days): left missing, surfaced via missed_days_3d/7d features   |
|  3. Dynamic Rolling Statistics (3d and 7d windows):                               |
|     - mean, min, max, std across all available animal history                     |
|     - rate-of-change trend deltas (vs. prior day, vs. 3d, vs. 7d)                |
|  4. Biological & Staleness Features:                                              |
|     - days_in_milk (DIM = current_date - calving_date; strictly no future info)   |
|     - days_since_scc & scc_stale flag (>7 days without a test flagged as stale)   |
|  5. Static animal features join: breed, age_years, parity, prior_mastitis_flag    |
+-----------------------------------------------------------------------------------+
                                         |
                     +-------------------+-------------------+
                     |                                       |
                     v                                       v
+--------------------------------------+ +--------------------------------------+
| 7-DAY FORECAST ENGINE (XGBoost)      | | 14-DAY FORECAST ENGINE (XGBoost)     |
| Target: mastitis onset in (t, t+7]   | | Target: mastitis onset in (t, t+14]  |
| PRIMARY CLINICAL EARLY WARNING ALARM | | LOWER-CONFIDENCE EARLY-TREND SIGNAL  |
| Independent incomplete-window cut    | | Independent incomplete-window cut    |
| Tuned validation threshold: 0.960    | | Tuned validation threshold: 0.705    |
| Sigmoid probability calibration      | | Sigmoid probability calibration      |
| Top SHAP drivers per prediction      | | Top SHAP drivers per prediction      |
+--------------------------------------+ +--------------------------------------+
                     |                                       |
                     +-------------------+-------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| DECISION-SUPPORT & PRESENTATION LAYER (main.py, dashboard/index.html)             |
|                                                                                   |
|  - Calibrated Risk Probabilities (7d & 14d) & Configurable Risk Tiers             |
|  - Model Version & Provenance Tracking (model_version, training_data_type)        |
|  - Data-Sufficiency Warnings (for cows with <7 days of historical monitoring)     |
|  - Actionable Management Recommendations (rule-based linking to top drivers)      |
|  - Herd-Wide Ranked Risk & Automated Deduplicated Alerts                         |
|  - Bilingual English / Tamil UI with Chart.js longitudinal sensor trends          |
+-----------------------------------------------------------------------------------+
```

---

### 2. Database Schema (SQLite `mastitis.db`)

The database is initialized in `app/services/database.py` with foreign key enforcement and idempotent additive column migrations:

#### Table: `cows`
- `cow_id` TEXT PRIMARY KEY — Unique animal identifier.
- `breed` TEXT — e.g. Holstein Friesian (HF), Jersey, Crossbred, Indigenous.
- `age_years` INTEGER — Animal chronological age.
- `parity` INTEGER NOT NULL — Lactation cycle number (>= 1).
- `calving_date` TEXT — Date of most recent calving (ISO 8601 YYYY-MM-DD).
- `vaccination_status` INTEGER DEFAULT 1 — 1 if up-to-date, 0 otherwise.
- `prior_mastitis_flag` INTEGER DEFAULT 0 — 1 if historical mastitis documented.
- `herd_id` TEXT DEFAULT 'demo_herd_01' — Management unit identifier.

#### Table: `readings`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `cow_id` TEXT NOT NULL (FK -> `cows.cow_id`)
- `timestamp` TEXT NOT NULL — ISO 8601 reading timestamp
- `milk_yield_l` REAL NOT NULL — Daily / per-milking yield (litres)
- `milk_conductivity` REAL NOT NULL — Electrical conductivity (mS/cm)
- `milk_temp_c` REAL NOT NULL — In-line milk temperature (°C)
- `scc_value` REAL — Somatic cell count (cells/mL, periodic)
- `activity_score` REAL — Cow activity metric [0.0 - 1.0]
- `rumination_min` REAL — Daily rumination duration (minutes)
- `environment_heat_index` REAL — Derived heat index or baseline
- `hygiene_score` REAL — Housing hygiene index [0.0 - 1.0]
- `feed_score` REAL — Feed quality/ration score [0.0 - 1.0]
- `milking_hygiene_score` REAL — Teat prep / cluster hygiene [0.0 - 1.0]
- `source` TEXT DEFAULT 'sensor' — Origin (`esp32`, `sensor`, `synthetic_seed`, etc.)
- `farm_temperature_c` REAL — Real DHT22 ambient farm temperature (°C)
- `farm_humidity` REAL — Real DHT22 ambient farm relative humidity (%)
- `milk_pH` REAL — In-line milk pH (deferred hardware)
- `body_temperature` REAL — Core cow body temperature (deferred hardware)
- `udder_surface_temperature` REAL — IR thermography temperature (deferred hardware)

#### Table: `alerts`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `cow_id` TEXT — Reference to animal
- `timestamp` TEXT — Alert generation timestamp (ISO 8601)
- `risk_score` REAL — Maximum calibrated probability across 7d/14d
- `message` TEXT — Diagnostic notice
- `model_version` TEXT — Version ID of model generating the alert
- `status` TEXT DEFAULT 'open' — `open` or `resolved`
- `resolved_at` TEXT — Resolution timestamp
- `resolved_note` TEXT — Clinical or management note

#### Table: `feedback`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `cow_id` TEXT NOT NULL
- `event_date` TEXT — Date clinical mastitis was confirmed
- `confirmed_mastitis` INTEGER — 1 for confirmed mastitis, 0 for negative
- `notes` TEXT — Veterinary / laboratory notes
- `created_at` TEXT DEFAULT CURRENT_TIMESTAMP

---

### 3. Non-Negotiable Target Definitions & Incomplete-Window Rule

For animal-day $t$:
- **7-Day Risk Target (`target_7d`)**:
  $$\text{target\_7d}_t = 1 \iff \exists \text{ confirmed mastitis event at } t_{event} \in (t, t + 7], \text{ else } 0$$
- **14-Day Risk Target (`target_14d`)**:
  $$\text{target\_14d}_t = 1 \iff \exists \text{ confirmed mastitis event at } t_{event} \in (t, t + 14], \text{ else } 0$$

#### Incomplete-Window Exclusion (§3)
A critical source of label contamination in longitudinal medical datasets is right-censoring: if an animal's recorded history ends at day $D_{max}$, rows where $D_{max} - t < \text{horizon}$ cannot determine whether an event occurred during the unobserved future window.
- **Implementation**: The pipeline excludes these rows from training rather than defaulting them to 0 (negative).
- **Independent exclusion**: The 7-day model excludes rows where $D_{max} - t < 7$ days (~5.8% of data); the 14-day model independently excludes rows where $D_{max} - t < 14$ days (~11.6% of data).

---

### 4. Shared Feature Pipeline & Missing Data Policy

The feature engineering logic in `app/services/features.py` is shared across training, validation, testing, prediction, and retraining.

1. **Continuous Calendar Grid**: `_reindex_daily()` constructs a daily date index between the animal's first and last timestamp.
2. **Missing-Data Hierarchy**:
   - **Directly Observed**: Real sensor measurement on calendar day $t$.
   - **Short Dropout ($\le 2$ calendar days)**: Forward-filled to prevent losing an entire rolling window due to an isolated drop.
   - **Extended Gap ($> 2$ calendar days)**: Remains NaN. Rolling calculations properly exclude missing days. Surfaced via `missed_days_3d` and `missed_days_7d` flags.
3. **Staleness Tracking**:
   - `days_since_scc`: Integer count of elapsed calendar days since the last real laboratory or cow-side SCC test.
   - `scc_stale`: Binary indicator set to `1` when `days_since_scc > 7`.
4. **Days in Milk (DIM)**:
   - Evaluated as `(timestamp - calving_date).days`. Strictly uses historical calving dates; capped at non-negative values.

---

### 5. Leakage Prevention & Splitting Strategy

- **Stratified Cow-Level Splitting**: Animals are split into Train (70%), Validation (15%), and Test (15%) cohorts. **Zero animal overlap exists across splits.**
- **Feature Exclusion (`NON_FEATURE_COLS`)**:
  - `cow_id`, `timestamp`, `target_7d`, `target_14d`, `event_onset_day`, `subclinical`, `breed`, `calving_date`, `herd_id`.
  - No target information, future sensor readings, or simulation flags ever enter model training.
- **Preprocessing Isolation**: Normalization, threshold tuning, and calibration fitting are executed **strictly on validation data**, never on the test set.

---

### 6. Model Training, Calibration, & Validation Performance

Both models are trained using XGBoost with early stopping on validation AUCPR (`eval_metric="aucpr"`). The active production model (`v002`) was trained on the standardized 600-cow / 150-day dataset (87,600 daily records, 163 cows with mastitis events) using cow-level stratified splits (Train: 419 cows, Validation: 90 cows, Holdout Test: 91 cows).

#### Distinct Operational Roles: 7-Day vs. 14-Day Horizons

> [!IMPORTANT]
> **Operational Horizon Distinction**:
> - **7-Day Model (Primary Clinical Early Warning Alarm)**: High confidence, high precision ($77.16\%$), high specificity ($99.70\%$). This is the authoritative clinical decision-support trigger designed to prompt immediate veterinary action: physical udder examination, California Mastitis Test (CMT), teat disinfection review, and targeted milk sampling before clinical symptoms emerge.
> - **14-Day Model (Lower-Confidence Early-Trend Signal)**: Lower confidence ($56.18\%$ recall, $60.44\%$ precision), longer time horizon. This is an **exploratory trend indicator, NOT a primary alarm**. Physiological deviations two weeks prior to onset are subtle and diffuse; forcing an 80% recall floor at 14 days causes threshold collapse and severe false-alarm fatigue (precision dropping to $<10\%$). Setting `TARGET_RECALL_14D = 0.60` preserves actionable precision ($60.44\%$) and high specificity ($98.93\%$). This signal places cows on an internal farm observation/watch list for visual monitoring during milking rather than triggering disruptive clinical interventions.

#### 7-Day Forecasting Model (`model_7d.joblib`)
- **Role**: Primary Clinical Early Warning Alarm
- **Objective**: Predict clinical/subclinical onset within 1 to 7 calendar days ahead.
- **Target Recall Setting**: `0.80` (Validation Recall: `81.37%`, Specificity: `99.73%`, Precision: `79.39%`)
- **Validation-Tuned Decision Threshold**: `0.960` (precision/specificity prioritized tie-break)
- **Holdout Test Set Performance (91 cows, 12,663 daily rows)**:
  - **Test ROC-AUC**: `0.9890` (Baseline Logistic Regression: `0.9853`, XGBoost advantage: `+0.0037`)
  - **Test Average Precision (AUPRC)**: `0.8025`
  - **Test Recall (Sensitivity)**: `73.53%` (125 / 170 positive episodes detected)
  - **Test Specificity**: `99.70%` (12,456 / 12,493 healthy days correctly cleared)
  - **Test Precision**: `77.16%` (125 / 162 predicted alerts are true positives)
  - **Test F1 Score**: `0.7530`
  - **Confusion Matrix**: TP=125, FP=37, FN=45, TN=12,456
  - **Brier Score**: `0.0050` (Calibrated) vs `0.0426` (Baseline)

#### 14-Day Forecasting Model (`model_14d.joblib`)
- **Role**: Lower-Confidence Early-Trend Exploratory Signal (Watch List Indicator)
- **Objective**: Early trend warning of subtle physiological deterioration within 1 to 14 days ahead.
- **Target Recall Setting**: `0.60` (lowered per validation trade-off; empirical data supports 60% recall with ~60% precision)
- **Validation-Tuned Decision Threshold**: `0.705` (Validation Recall: `60.25%`, Specificity: `98.78%`, Precision: `57.91%`)
- **Holdout Test Set Performance (91 cows, 12,042 daily rows)**:
  - **Test ROC-AUC**: `0.8789` (Baseline Logistic Regression: `0.8158`, XGBoost advantage: `+0.0631`)
  - **Test Average Precision (AUPRC)**: `0.5628`
  - **Test Recall (Sensitivity)**: `56.18%` (191 / 340 positive episodes detected)
  - **Test Specificity**: `98.93%` (11,577 / 11,702 healthy days correctly cleared)
  - **Test Precision**: `60.44%` (191 / 316 predicted alerts are true positives)
  - **Test F1 Score**: `0.5823`
  - **Confusion Matrix**: TP=191, FP=125, FN=149, TN=11,577
  - **Brier Score**: `0.0165` (Calibrated) vs `0.1388` (Baseline)

#### Probability Calibration Workflow
Raw XGBoost decision margins are calibrated using Platt scaling (sigmoid logistic regression) fitted exclusively on validation out-of-sample predictions (`app/services/calibration.py`). Calibrated probabilities are clamped to $[0.0, 1.0]$ and stored as joblib artifacts. Both models demonstrate excellent calibration reliability with low Brier scores ($0.0050$ for 7d, $0.0165$ for 14d).

---

### 7. Model Versioning & Safe Promotion Architecture

Model artifacts are stored in an immutable, versioned directory structure (`app/services/versioning.py`):

```text
models/
  v001/                       # Historical baseline candidate (archived, rejected from production)
  v002/                       # Active production candidate (promoted)
    model_7d.joblib           # Trained XGBoost 7d classifier
    model_14d.joblib          # Trained XGBoost 14d classifier
    calibrator_7d.joblib      # Fitted Platt calibrator for 7d
    calibrator_14d.joblib     # Fitted Platt calibrator for 14d
    feature_cols.joblib       # Exact list of 120 input features
    metrics.json              # Full test metrics, confusion matrix, Brier
    calibration_info.json     # Calibration parameters & reliability curve
    config.json               # Full hyperparameter configuration
    training_metadata.json    # Commit hash, data hash, timestamp
  current/                    # Active production copy (mirror of v002)
```

#### Version History
- **`v001` (Archived Baseline / Rejected Candidate)**: Trained on initial 220-cow / 120-day dataset. Reached $62.5\%$ (7d) and $65.5\%$ (14d) test recall, with 14d XGBoost underperforming baseline Logistic Regression (0.7726 vs 0.8265). Archived permanently for audit and regression comparison; excluded from production serving.
- **`v002` (Current Active Production Model)**: Trained on regenerated 600-cow / 150-day dataset with horizon-specific recall targets (`TARGET_RECALL_7D = 0.80`, `TARGET_RECALL_14D = 0.60`) and precision-prioritizing threshold tie-breaking. Passed all promotion safety criteria and automatically promoted to `models/current/`.

#### Safe Promotion Gates (`check_promotion_safety` & `check_first_promotion_safety`)
A candidate model produced by `train_model.py` or `retrain.py` is promoted to `models/current` **only if**:
1. **Cold-Start Promotion (`check_first_promotion_safety`)**:
   - 7-day test recall $\ge 0.70$ (`MIN_PROMOTION_RECALL["7d"]`)
   - 14-day test recall $\ge 0.50$ (`MIN_PROMOTION_RECALL["14d"]`)
   - Model ROC-AUC must not underperform linear baseline by $>0.02$
   - Calibrated Brier score $\le 0.05$
   - Zero feature leakage detected
2. **Subsequent Retraining Promotion (`check_promotion_safety`)**:
   - Candidate test recall does not drop by $>5\%$ relative to the active model.
   - Candidate test AUPRC does not drop by $>0.05$ relative to the active model.
3. If gates fail, the candidate remains archived in `models/vXXX/` with promotion status logged as `rejected`, while `models/current/` remains untouched.

---

### 8. Drift Monitoring Foundation (`app/services/drift.py`)

Accessible via `GET /drift/summary`:
- **Population Stability Index (PSI)**: Monitors continuous distributions for all core sensor signals against the training baseline.
  - $\text{PSI} < 0.10$: Stable
  - $0.10 \le \text{PSI} < 0.25$: Moderate distribution shift
  - $\text{PSI} \ge 0.25$: Significant drift triggering retraining recommendation
- **Missing Data Tracking**: Audits percentage of null/missing values per sensor over the last 30 days.
- **Sensor Availability**: Measures active cows $\times$ expected daily readings vs. actual received records.

---

### 9. Hardware Status & Integration Roadmap

#### Current Workspace State (`hardware/esp32_v2.ino`)
- **DS18B20 on GPIO4**: Operational milk temperature sensor (`milk_temp_c`).
- **Hardcoded Values**: `milk_conductivity` (4.8 mS/cm) and `milk_yield_l` (14.0 L) are sent as placeholders.
- **WiFi Reconnection**: 5-minute backoff retry loop on packet failure.

#### Planned Hardware Integration (To Be Copied Later)
- **DHT22 on GPIO16**: Real-time ambient farm temperature (`farm_temperature_c`) and relative humidity (`farm_humidity`).
- **Analog TDS on GPIO34**: Real milk electrical conductivity reading.
- **Push Button on GPIO27**: Physical milking trigger for transmission to `POST /ingest`.

---

### 10. Explicit Limitations & Disclaimers

1. **Prototype Decision Support Only**: This system is a risk-forecasting prototype and decision-support tool. It is **not a clinical diagnostic device** and must never replace qualified veterinary diagnosis.
2. **Synthetic Training Data**: Present model artifacts were trained on simulated longitudinal time series (`data/cleaned.csv`). Real-world farm validation and clinical calibration are required before commercial or clinical deployment.
3. **Application Tiers**: Risk tiers (No $<25\%$, Low $25\text{--}<50\%$, Moderate $50\text{--}<75\%$, High $\ge 75\%$) are user-interface thresholding conventions, not medical diagnostic cutoffs.
4. **Deferred Sensors**: In-line milk pH, cow core body temperature, and udder infrared thermography are schema-ready but deferred due to physical hardware absence.
