"""Shared feature-engineering pipeline (§6).

Used identically by training, validation, testing, prediction, and
retraining — never duplicated between scripts.

Pipeline: raw DB records → calendar-day normalization → missing-data
handling → availability/staleness features → rolling statistics (3d/7d:
mean, min, max, std) → trend/delta features → static feature join (DIM,
breed, parity, etc.) → final feature vector.
"""

import numpy as np
import pandas as pd
from config import (
    CORE_SIGNALS, OPTIONAL_SIGNALS, FIXED_GOOD_VALUES,
    SCC_DEFAULT, MAX_SENSOR_FFILL_DAYS, SCC_STALENESS_DAYS,
)

# Re-export for backward compatibility — existing code imports from here.
SIGNALS = list(CORE_SIGNALS)
FIXED_GOOD_VALUES = dict(FIXED_GOOD_VALUES)


def active_signals(df):
    """Return the subset of CORE_SIGNALS + OPTIONAL_SIGNALS that actually
    exist as columns in *df*, so the pipeline adapts to whatever columns
    are present without requiring a code change for new sensors."""
    all_possible = CORE_SIGNALS + OPTIONAL_SIGNALS
    return [c for c in all_possible if c in df.columns]


# ── prototype defaults ─────────────────────────────────────────────────

def apply_prototype_defaults(df):
    """Fill prototype-only fields while preserving the full ML feature set."""
    df = df.copy()
    for col, value in FIXED_GOOD_VALUES.items():
        if col not in df.columns:
            df[col] = value
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(value)
    return df


# ── heat-index derivation ─────────────────────────────────────────────

def derive_heat_index(df):
    """If both farm_temperature_c and farm_humidity are present, derive
    environment_heat_index from them using a simplified Steadman formula.
    Otherwise leave the existing value (fixed baseline) unchanged.

    The latest ESP32 (DHT22 on GPIO16) sends both farm_temperature_c and
    farm_humidity; the older ESP32 does not, and the baseline is used.
    """
    if "farm_temperature_c" in df.columns and "farm_humidity" in df.columns:
        t = pd.to_numeric(df["farm_temperature_c"], errors="coerce")
        h = pd.to_numeric(df["farm_humidity"], errors="coerce")
        has_both = t.notna() & h.notna()
        # Simplified heat index (Celsius-based, common in livestock welfare)
        # HI ≈ T + 0.33 × (H/100 × 6.105 × exp(17.27×T/(237.7+T))) − 4.0
        # For simplicity and robustness, use: HI = T + 0.36 × H − 10.0
        # (values typically 30-100 range, matches the baseline ~70 range)
        hi = t + 0.36 * h - 10.0
        df.loc[has_both, "environment_heat_index"] = hi[has_both].round(1)
    return df


# ── SCC staleness features ────────────────────────────────────────────

def add_scc_staleness(df):
    """Add ``days_since_scc`` and ``scc_stale`` features per cow.

    For each animal-day, ``days_since_scc`` counts how many calendar days
    have passed since the last *real* SCC measurement (not a carried-forward
    value).  ``scc_stale`` is 1 when ``days_since_scc > SCC_STALENESS_DAYS``.

    An old SCC value must never be treated as equivalent to a fresh one (§5).
    """
    if "scc_value" not in df.columns:
        df["days_since_scc"] = np.nan
        df["scc_stale"] = 1
        return df

    df = df.copy()
    df["_scc_observed"] = df["scc_value"].notna().astype(int)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601", utc=True).dt.tz_localize(None)

    pieces = []
    for _, g in df.groupby("cow_id", sort=False):
        g = g.sort_values("timestamp")
        last_scc_date = pd.NaT
        days_since = []
        for _, row in g.iterrows():
            if row["_scc_observed"]:
                last_scc_date = row["timestamp"]
                days_since.append(0)
            elif pd.notna(last_scc_date):
                days_since.append((row["timestamp"] - last_scc_date).days)
            else:
                days_since.append(np.nan)
        g = g.copy()
        g["days_since_scc"] = days_since
        pieces.append(g)

    df = pd.concat(pieces, ignore_index=True)
    df["days_since_scc"] = df["days_since_scc"].fillna(999)  # no SCC ever → very stale
    df["scc_stale"] = (df["days_since_scc"] > SCC_STALENESS_DAYS).astype(int)
    df.drop(columns=["_scc_observed"], inplace=True)
    return df


# ── days in milk (DIM) ─────────────────────────────────────────────────

def add_dim(df):
    """Add ``days_in_milk`` derived from ``calving_date`` if available.

    DIM = current_date − calving_date.  Never uses future calving info (§5).
    """
    if "calving_date" not in df.columns:
        return df
    df = df.copy()
    ts = pd.to_datetime(df["timestamp"], utc=True).dt.tz_localize(None)
    calving = pd.to_datetime(df["calving_date"], errors="coerce", utc=True).dt.tz_localize(None)
    dim = (ts - calving).dt.days
    # DIM should be non-negative; negative means calving is in the future
    # relative to this reading (should not happen with correct data).
    df["days_in_milk"] = dim.clip(lower=0).fillna(0.0)
    return df


# ── signal preparation ─────────────────────────────────────────────────

def prepare_signals(df):
    df = apply_prototype_defaults(df)
    df = derive_heat_index(df)
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601", utc=True).dt.tz_localize(None)
    df = df.sort_values(["cow_id", "timestamp"])
    # SCC is measured periodically — carry the latest known value forward;
    # if a cow has never had an SCC test, use a conservative baseline.
    df["scc_value"] = df.groupby("cow_id")["scc_value"].ffill().fillna(SCC_DEFAULT)
    return df


# ── calendar-day reindexing ────────────────────────────────────────────

def _reindex_daily(g, signals):
    """Re-express one cow's readings on a continuous one-row-per-calendar-day
    grid so that rolling windows and "N days ago" deltas mean what their
    names say even when a reading was missed."""
    g = g.sort_values("timestamp")
    idx = pd.date_range(
        g["timestamp"].min().normalize(),
        g["timestamp"].max().normalize(),
        freq="D",
    )
    observed_dates = pd.DatetimeIndex(g["timestamp"].dt.normalize().unique())
    grid = g.set_index(g["timestamp"].dt.normalize())[signals].reindex(idx)

    gap_flag = grid.isna().any(axis=1).astype(int)
    # Short dropouts (≤2 days): carry last reading forward rather than
    # losing the whole rolling window. Longer gaps stay NaN (true missing
    # data) — never silently extrapolated.
    grid[signals] = grid[signals].ffill(limit=MAX_SENSOR_FFILL_DAYS)
    # SCC carries forward indefinitely (periodic test); staleness tracked
    # separately by days_since_scc / scc_stale.
    if "scc_value" in signals:
        grid["scc_value"] = (
            g.set_index(g["timestamp"].dt.normalize())["scc_value"]
            .reindex(idx).ffill()
        )
        grid["scc_value"] = grid["scc_value"].fillna(SCC_DEFAULT)
    grid["_gap"] = gap_flag
    return grid, observed_dates


# ── main pipeline ──────────────────────────────────────────────────────

def engineer(df):
    """Run the full feature-engineering pipeline.

    Returns a DataFrame with one row per observed animal-day, enriched with
    rolling statistics, trend/delta features, static attributes, DIM, and
    SCC staleness indicators.
    """
    if df.empty:
        return df

    # Add SCC staleness before forward-filling if not already present
    if "days_since_scc" not in df.columns:
        df = add_scc_staleness(df)

    df = prepare_signals(df)
    # scc_value rows which are preserved in the input df before prepare_signals
    # fills them.

    # Determine which signals are actually present in this dataset.
    sigs = active_signals(df)

    pieces = []
    for cow_id, g0 in df.groupby("cow_id", sort=False):
        grid, observed_dates = _reindex_daily(g0, sigs)

        extra = {}
        for col in sigs:
            s = grid[col]
            for w in (3, 7):
                extra[f"{col}_mean_{w}d"] = s.rolling(window=w, min_periods=1).mean()
                extra[f"{col}_min_{w}d"] = s.rolling(window=w, min_periods=1).min()
                extra[f"{col}_max_{w}d"] = s.rolling(window=w, min_periods=1).max()
                extra[f"{col}_std_{w}d"] = s.rolling(window=w, min_periods=2).std()
                # Value ~w calendar days ago vs. now.
                extra[f"{col}_delta_{w}d"] = s - s.shift(w)

        # Monitoring-quality signals.
        extra["missed_days_7d"] = grid["_gap"].rolling(window=7, min_periods=1).sum()
        extra["missed_days_3d"] = grid["_gap"].rolling(window=3, min_periods=1).sum()

        extra_df = pd.DataFrame(extra, index=grid.index)
        combined = pd.concat([grid[sigs], extra_df], axis=1)
        # Keep only rows for actual observation dates.
        combined = combined.loc[combined.index.isin(observed_dates)].copy()
        combined.insert(0, "cow_id", cow_id)
        combined.insert(1, "timestamp", combined.index)
        combined = combined.reset_index(drop=True)
        pieces.append(combined)

    out = pd.concat(pieces, ignore_index=True).replace([np.inf, -np.inf], np.nan)

    # Re-attach every other original column (age, parity, breed, targets, …)
    # by an exact (cow_id, timestamp) join — NOT a per-cow "first value".
    other_cols = [c for c in df.columns if c not in sigs and c not in ("cow_id", "timestamp")]
    if other_cols:
        keyed = df[["cow_id", "timestamp"] + other_cols].copy()
        keyed["timestamp"] = keyed["timestamp"].dt.normalize()
        keyed = keyed.drop_duplicates(subset=["cow_id", "timestamp"], keep="last")
        out = out.merge(keyed, on=["cow_id", "timestamp"], how="left")

    # Add DIM if calving_date is present.
    out = add_dim(out)

    for col in out.columns:
        if col not in ("cow_id", "timestamp", "breed", "calving_date", "herd_id"):
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    return out


# ── SCC staleness for training data ────────────────────────────────────

def add_scc_staleness_to_training(raw_df):
    """Compute days_since_scc and scc_stale on the *raw* (pre-ffill) data
    so the staleness feature reflects actual measurement frequency, not
    the filled values."""
    return add_scc_staleness(raw_df)


# ── validation ─────────────────────────────────────────────────────────

def validate_reading(r):
    """Validate range constraints on a Reading.  Returns a list of errors."""
    from config import SENSOR_LIMITS
    checks = {
        "milk_yield_l": SENSOR_LIMITS["milk_yield_l"],
        "milk_conductivity": SENSOR_LIMITS["milk_conductivity"],
        "milk_temp_c": SENSOR_LIMITS["milk_temp_c"],
        "scc_value": SENSOR_LIMITS["scc_value"],
    }
    errors = []
    for name, (lo, hi) in checks.items():
        v = getattr(r, name, None)
        if v is not None and not lo <= v <= hi:
            errors.append(f"{name} outside accepted range")
    return errors


# ── aggregation ────────────────────────────────────────────────────────

def aggregate_daily(df):
    d = apply_prototype_defaults(df)
    d = derive_heat_index(d)
    ts = pd.to_datetime(d["timestamp"], format="ISO8601", utc=True).dt.tz_localize(None)
    d["timestamp"] = ts
    d["date"] = ts.dt.floor("D")
    d = d.sort_values(["cow_id", "timestamp"])

    # Compute SCC staleness on raw observations before aggregation
    if "days_since_scc" not in d.columns:
        d = add_scc_staleness(d)

    d["scc_value"] = d.groupby("cow_id")["scc_value"].ffill()
    d["scc_value"] = d["scc_value"].fillna(SCC_DEFAULT)

    agg_cols = {c: "mean" for c in active_signals(d) if c != "milk_yield_l" and c != "scc_value"}
    agg_cols["milk_yield_l"] = "sum"
    agg_cols["scc_value"] = "last"
    if "days_since_scc" in d.columns:
        agg_cols["days_since_scc"] = "last"
        agg_cols["scc_stale"] = "last"

    g = d.groupby(["cow_id", "date"])
    out = g.agg(agg_cols).reset_index()
    out["timestamp"] = out["date"].astype(str)
    return out.drop(columns=["date"])