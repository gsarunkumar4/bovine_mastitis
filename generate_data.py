"""
Synthetic daily-sensor dataset generator for the mastitis forecasting prototype.

Design goals for this revision (see ARCHITECTURE.md for rationale):
  1. Individual cow variability in onset kinetics, severity and noise, so the
     7d/14d classification task is learnable but NOT trivially separable.
     (The previous generator produced a near-deterministic linear ramp with
     tiny noise, which is why the trained model scored an unrealistic
     AUC ~0.9999 on held-out cows -- that number reflects an easy synthetic
     function, not real-world skill, and would not survive contact with real
     farm data or a technical review panel.)
  2. Static risk factors (parity, prior mastitis, vaccination, age) now have a
     small but real influence on event probability, so the model has an
     actual reason to use them -- matching the brief's ask to correlate
     animal history with risk, instead of carrying uninformative columns.
  3. SCC is sampled periodically (every 3-6 days), not daily, matching real
     cow-side/lab testing cadence and actually exercising the
     carry-forward/staleness logic in features.py.
  4. Random sensor dropout days (connectivity loss) are injected so the
     pipeline is trained and evaluated under the same conditions it will see
     in the field (GSM/LoRa/Wi-Fi drop-outs are common in Indian field
     conditions per the brief).
  5. "Hard negative" cows get transient noise blips that resemble early
     mastitis signs but resolve on their own (e.g. heat stress, a single bad
     milking) -- this stops the model from treating "any conductivity blip"
     as a certain positive, and gives the recommendation/alert layer
     something realistic to be cautious about.
  6. Farm-management / environment / behaviour columns (activity, rumination,
     environment heat index, hygiene, feed, milking hygiene) are now
     generated with real variability and a mild coupling to risk, so the
     dataset is ready for the day this prototype is upgraded to collect real
     wearable/farm-management data. train_model.py still overwrites them
     with the fixed prototype baselines by default (USE_REAL_FARM_FEATURES
     = False) -- nothing about the current fixed-value prototype behaviour
     is removed, this only makes the richer data available for later.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

rng = np.random.default_rng(2026)
N_COWS, DAYS = 600, 150
breeds = ["HF", "Jersey", "Crossbred", "Indigenous"]

SCC_DEFAULT = 180_000.0


def ar1_noise(n, sigma, rho, rng):
    """Autocorrelated (AR1) daily noise -- real sensor noise is not i.i.d.,
    consecutive days tend to drift together (weather, feed batch, etc.)."""
    e = rng.normal(0, sigma, n)
    x = np.empty(n)
    x[0] = e[0]
    for i in range(1, n):
        x[i] = rho * x[i - 1] + np.sqrt(1 - rho ** 2) * e[i]
    return x


rows = []
for c in range(1, N_COWS + 1):
    cow_id = f"cow_{c:03d}"
    breed = rng.choice(breeds)
    age_years = int(rng.integers(3, 9))
    parity = int(rng.integers(1, 6))
    prior_mastitis = int(rng.random() < 0.25)
    vaccinated = int(rng.random() > 0.08)
    calving_date = datetime(2025, 12, 1) + timedelta(days=int(rng.integers(0, 50)))

    # Static risk factors nudge event probability instead of being pure
    # noise: higher parity, prior mastitis and no vaccination modestly raise
    # risk, matching known dairy-epidemiology risk factors.
    base_risk = 0.22
    base_risk += 0.10 if prior_mastitis else 0
    base_risk += 0.015 * max(0, parity - 2)
    base_risk += 0.06 if not vaccinated else 0
    base_risk = float(np.clip(base_risk, 0.05, 0.65))
    has_event = rng.random() < base_risk

    base_yield = max(8, rng.normal(15, 2.3))
    base_cond = max(2.8, rng.normal(4.5, 0.3))
    base_temp = rng.normal(38.5, 0.18)

    # Farm/environment/behaviour baselines with real variability, generated
    # for future use (see module docstring). Mildly coupled to risk so they
    # are meaningful once real data collection is switched on.
    base_activity = float(np.clip(rng.normal(0.82, 0.08) - (0.08 if prior_mastitis else 0), 0.4, 1.0))
    base_rumination = float(np.clip(rng.normal(500, 35), 350, 600))
    base_hygiene = float(np.clip(rng.normal(0.82, 0.09), 0.3, 1.0))
    base_feed = float(np.clip(rng.normal(0.83, 0.08), 0.3, 1.0))
    base_milking_hygiene = float(np.clip(rng.normal(0.85, 0.08), 0.3, 1.0))

    onset = int(rng.integers(35, DAYS - 15)) if has_event else None
    # Individual kinetics: ramp length and severity vary cow to cow, and a
    # fraction of positive cows are "subclinical-leaning" -- SCC rises but
    # conductivity/temperature barely move, which is the harder case the
    # brief specifically calls out ("algorithms to predict subclinical
    # mastitis with SCC").
    ramp_days = int(rng.integers(10, 18)) if has_event else 0
    subclinical = has_event and rng.random() < 0.35
    severity = rng.uniform(0.6, 1.4) * (0.5 if subclinical else 1.0)

    # Occasional transient "hard negative" blips on otherwise healthy cows
    # (heat stress day, one rough milking) that must NOT look like a genuine
    # 7-14 day ramp to a well-generalising model.
    blip_day = int(rng.integers(10, DAYS - 5)) if (not has_event and rng.random() < 0.18) else None

    cond_noise = ar1_noise(DAYS, 0.16, 0.55, rng)
    temp_noise = ar1_noise(DAYS, 0.10, 0.55, rng)
    yield_noise = ar1_noise(DAYS, 0.55, 0.45, rng)
    scc_noise = ar1_noise(DAYS, 45_000, 0.5, rng)

    # SCC is only actually measured periodically (cow-side test / lab visit),
    # not every day.
    scc_test_days = set()
    d0 = int(rng.integers(0, 5))
    while d0 < DAYS:
        scc_test_days.add(d0)
        d0 += int(rng.integers(3, 7))

    # Random connectivity/sensor dropout days -- reading simply never arrives.
    dropout_days = set(rng.choice(DAYS, size=int(DAYS * 0.03), replace=False))

    for d in range(DAYS):
        if d in dropout_days:
            continue
        dt = datetime(2026, 1, 1) + timedelta(days=d)

        p = 0.0
        if has_event and onset - ramp_days <= d <= onset:
            # Smooth (sigmoid-like) approach instead of a hard linear ramp.
            frac = (d - (onset - ramp_days)) / ramp_days
            p = severity * (frac ** 1.6)

        blip = 0.0
        if blip_day is not None and abs(d - blip_day) <= 1:
            blip = rng.uniform(0.15, 0.35) * (1 - abs(d - blip_day) / 2)

        yield_l = base_yield + yield_noise[d] - 4.2 * p - 1.5 * blip
        cond = base_cond + cond_noise[d] + 1.9 * p * (0.55 if subclinical else 1.0) + 0.9 * blip
        temp = base_temp + temp_noise[d] + 0.70 * p * (0.5 if subclinical else 1.0) + 0.35 * blip
        scc_true = max(30_000, SCC_DEFAULT + scc_noise[d] + 1_150_000 * p + 250_000 * blip)

        activity = float(np.clip(base_activity + rng.normal(0, 0.03) - 0.18 * p - 0.08 * blip, 0.1, 1.0))
        rumination = float(np.clip(base_rumination + rng.normal(0, 8) - 80 * p - 30 * blip, 150, 650))
        heat_index = float(np.clip(rng.normal(68, 9), 30, 100))
        hygiene = float(np.clip(base_hygiene + rng.normal(0, 0.02) - 0.05 * p, 0.1, 1.0))
        feed = float(np.clip(base_feed + rng.normal(0, 0.02) - 0.05 * p, 0.1, 1.0))
        milking_hygiene = float(np.clip(base_milking_hygiene + rng.normal(0, 0.02) - 0.04 * p, 0.1, 1.0))

        scc_value = round(scc_true) if d in scc_test_days else None

        rows.append({
            "cow_id": cow_id, "timestamp": dt.isoformat(),
            "milk_yield_l": round(max(1.5, yield_l), 3),
            "milk_conductivity": round(max(.5, cond), 3),
            "milk_temp_c": round(temp, 3),
            "scc_value": scc_value,
            "activity_score": round(activity, 3),
            "rumination_min": round(rumination, 1),
            "environment_heat_index": round(heat_index, 1),
            "hygiene_score": round(hygiene, 3),
            "feed_score": round(feed, 3),
            "milking_hygiene_score": round(milking_hygiene, 3),
            "target_7d": int(has_event and 1 <= onset - d <= 7),
            "target_14d": int(has_event and 1 <= onset - d <= 14),
            "event_onset_day": onset if has_event else -1,
            "subclinical": int(subclinical) if has_event else 0,
            "breed": breed, "age_years": age_years, "parity": parity,
            "vaccination_status": vaccinated, "prior_mastitis_flag": prior_mastitis,
            "calving_date": calving_date.date().isoformat(), "herd_id": "demo_herd_01"
        })

df = pd.DataFrame(rows)
Path("data").mkdir(exist_ok=True)
df.to_csv("data/raw.csv", index=False)

# "cleaned" = raw here (no external-source cleaning step yet in the
# prototype), kept as a separate artifact so a future real-data cleaning step
# has an obvious place to write to without touching raw.csv.
df.to_csv("data/cleaned.csv", index=False)

print(f"Created {len(df):,} daily observations for {N_COWS} cows over {DAYS} days.")
print("Rows with a same-day SCC test:", int(df.scc_value.notna().sum()),
      f"({df.scc_value.notna().mean():.1%} of rows)")
print("Cows with a mastitis event:", int(df.groupby('cow_id')['event_onset_day'].first().gt(0).sum()), "/", N_COWS)
print("7-day positive rows:", int(df.target_7d.sum()), f"({df.target_7d.mean():.2%})")
print("14-day positive rows:", int(df.target_14d.sum()), f"({df.target_14d.mean():.2%})")
print("Subclinical-leaning positive cows:",
      int(df.loc[df.event_onset_day > 0].groupby('cow_id').subclinical.first().sum()))
