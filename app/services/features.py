import numpy as np
import pandas as pd

# Keep the complete original ML signal set. For the current prototype,
# farm-management values are fixed to healthy baseline values rather than
# being collected from the farmer.
SIGNALS = [
    "milk_yield_l",
    "milk_conductivity",
    "milk_temp_c",
    "scc_value",
    "activity_score",
    "rumination_min",
    "environment_heat_index",
    "hygiene_score",
    "feed_score",
    "milking_hygiene_score",
]

# Prototype healthy/favourable fixed values for farm-management signals.
# These stay constant for all incoming readings until real farm inputs are added.
FIXED_GOOD_VALUES = {
    "activity_score": 0.90,
    "rumination_min": 520.0,
    "environment_heat_index": 70.0,
    "hygiene_score": 0.90,
    "feed_score": 0.90,
    "milking_hygiene_score": 0.95,
}

SCC_DEFAULT = 180_000.0


def apply_prototype_defaults(df):
    """Fill prototype-only fields while preserving the full ML feature set."""
    df = df.copy()
    for col, value in FIXED_GOOD_VALUES.items():
        if col not in df.columns:
            df[col] = value
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(value)
    return df


def prepare_signals(df):
    df = apply_prototype_defaults(df)
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["cow_id", "timestamp"])
    # SCC may be supplied periodically. Carry the latest known value forward.
    # If a cow has never supplied SCC, use a conservative prototype baseline.
    df["scc_value"] = df.groupby("cow_id")["scc_value"].ffill().fillna(SCC_DEFAULT)
    return df


def engineer(df):
    df = prepare_signals(df)
    if df.empty:
        return df
    pieces = []
    for _, g0 in df.groupby("cow_id", sort=False):
        g = g0.sort_values("timestamp").copy().reset_index(drop=True)
        base = {col: g[col].to_numpy() for col in SIGNALS}
        extra = {}
        ts = g.set_index("timestamp")
        for col in SIGNALS:
            s = ts[col]
            for w in (3, 7):
                rolled = pd.concat([
                    s.rolling(window=w, min_periods=1).mean().rename(f"{col}_mean_{w}d"),
                    s.rolling(window=w, min_periods=1).min().rename(f"{col}_min_{w}d"),
                    s.rolling(window=w, min_periods=1).max().rename(f"{col}_max_{w}d"),
                    s.rolling(window=w, min_periods=2).std().rename(f"{col}_std_{w}d"),
                ], axis=1).reset_index(drop=True)
                for name in rolled.columns:
                    extra[name] = rolled[name].to_numpy()
                # Difference from the observation w rows earlier. The input
                # workflow is one sample per day, so this corresponds to days.
                extra[f"{col}_delta_{w}d"] = (g[col] - g[col].shift(w)).to_numpy()
        extra_df = pd.DataFrame(extra, index=g.index)
        g = pd.concat([g, extra_df], axis=1)
        pieces.append(g)
    out = pd.concat(pieces, ignore_index=True).replace([np.inf, -np.inf], np.nan)
    # Keep numeric model inputs numeric and represent unavailable first-window
    # deltas/std values as 0 without pandas downcasting warnings.
    numeric_cols = out.select_dtypes(include=[np.number]).columns
    out[numeric_cols] = out[numeric_cols].fillna(0.0)
    return out


def validate_reading(r):
    checks = {
        "milk_yield_l": (0, 100),
        "milk_conductivity": (0.01, 30),
        "milk_temp_c": (30, 45),
        "scc_value": (0, 20_000_000),
    }
    errors = []
    for name, (lo, hi) in checks.items():
        v = getattr(r, name, None)
        if v is not None and not lo <= v <= hi:
            errors.append(f"{name} outside accepted range")
    return errors


def aggregate_daily(df):
    d = apply_prototype_defaults(df)
    d["timestamp"] = pd.to_datetime(d["timestamp"])
    d["date"] = d["timestamp"].dt.floor("D")
    d = d.sort_values(["cow_id", "timestamp"])

    # For SCC, use the latest value available on that day; this also supports
    # periodic SCC measurements rather than requiring SCC at every ingestion.
    d["scc_value"] = d.groupby("cow_id")["scc_value"].ffill()
    d["scc_value"] = d["scc_value"].fillna(SCC_DEFAULT)

    g = d.groupby(["cow_id", "date"])
    out = g.agg({
        "milk_yield_l": "sum",
        "milk_conductivity": "mean",
        "milk_temp_c": "mean",
        "scc_value": "last",
        "activity_score": "mean",
        "rumination_min": "mean",
        "environment_heat_index": "mean",
        "hygiene_score": "mean",
        "feed_score": "mean",
        "milking_hygiene_score": "mean",
    }).reset_index()
    out["timestamp"] = out["date"].astype(str)
    return out.drop(columns=["date"])
