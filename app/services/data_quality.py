"""Data-quality checks for incoming sensor readings.

These are *warnings*, not hard rejections — impossible values are flagged
and returned alongside the prediction so the dashboard/user is aware,
rather than silently dropped or silently accepted.
"""

from datetime import datetime, timezone
from config import SENSOR_LIMITS


def check_reading_quality(reading) -> list[str]:
    """Return a list of human-readable quality warnings for *reading*.

    Parameters
    ----------
    reading : pydantic model or dict-like
        An ingested sensor reading (the ``Reading`` Pydantic model from main.py).
    """
    warnings: list[str] = []

    # Range checks for every field with defined limits.
    for field, (lo, hi) in SENSOR_LIMITS.items():
        val = getattr(reading, field, None) if hasattr(reading, field) else None
        if val is not None and not (lo <= val <= hi):
            warnings.append(
                f"{field}={val} is outside the accepted range [{lo}, {hi}]"
            )

    return warnings


def check_timestamp_sanity(ts_str: str) -> list[str]:
    """Warn if a timestamp is in the future or suspiciously old."""
    warnings: list[str] = []
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if ts > now:
            warnings.append(f"Timestamp {ts_str} is in the future")
        # More than 1 year old is suspicious for a daily reading.
        if (now - ts).days > 365:
            warnings.append(f"Timestamp {ts_str} is more than 1 year old")
    except (ValueError, TypeError):
        warnings.append(f"Could not parse timestamp: {ts_str!r}")
    return warnings


def check_duplicate_day(cow_id: str, date_str: str, db_conn) -> bool:
    """Return True if a reading already exists for this cow on this calendar day."""
    row = db_conn.execute(
        "SELECT 1 FROM readings WHERE cow_id=? AND substr(timestamp,1,10)=? LIMIT 1",
        (cow_id, date_str[:10]),
    ).fetchone()
    return row is not None


def check_scc_staleness(cow_id: str, db_conn, threshold_days: int = 7) -> str | None:
    """Return a warning string if the latest SCC for *cow_id* is older
    than *threshold_days*, or None if SCC is fresh or unavailable."""
    row = db_conn.execute(
        "SELECT timestamp FROM readings WHERE cow_id=? AND scc_value IS NOT NULL "
        "ORDER BY timestamp DESC LIMIT 1",
        (cow_id,),
    ).fetchone()
    if row is None:
        return f"No SCC test on record for {cow_id} — SCC features use the conservative default"
    try:
        last = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - last).days
        if age > threshold_days:
            return f"Last SCC test for {cow_id} was {age} days ago (stale; threshold={threshold_days}d)"
    except (ValueError, TypeError):
        pass
    return None


def check_abnormal_jump(cow_id: str, reading, db_conn) -> list[str]:
    """Detect suspiciously large day-over-day jumps for key sensors."""
    warnings: list[str] = []
    prev = db_conn.execute(
        "SELECT milk_yield_l, milk_conductivity, milk_temp_c FROM readings "
        "WHERE cow_id=? ORDER BY timestamp DESC LIMIT 1",
        (cow_id,),
    ).fetchone()
    if prev is None:
        return warnings

    jump_thresholds = {
        "milk_yield_l": 8.0,          # litres
        "milk_conductivity": 2.5,     # mS/cm
        "milk_temp_c": 1.5,           # °C
    }
    for field, max_jump in jump_thresholds.items():
        new_val = getattr(reading, field, None)
        old_val = prev[field] if prev[field] is not None else None
        if new_val is not None and old_val is not None:
            delta = abs(new_val - old_val)
            if delta > max_jump:
                warnings.append(
                    f"{field} jumped {delta:.2f} in one reading "
                    f"(previous={old_val:.2f}, current={new_val:.2f}; threshold={max_jump})"
                )
    return warnings
