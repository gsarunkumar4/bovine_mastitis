"""
§9b — Climate / weather-based advisories.

Uses the **Open-Meteo API** (free, no API key required) to fetch a
7-day hourly weather forecast and compute livestock-standard
Temperature-Humidity Index (THI) heat-stress advisories.

IMPORTANT — two different heat-index measures exist in MastiSense:

1. **Current Heat Index (sensor-derived)**
   Formula:  HI = T + 0.36 × RH − 10.0  (simplified Steadman)
   Source:   ``app/services/features.py → derive_heat_index()``
   Purpose:  Per-reading feature for the ML model, calculated from
             the cow's immediate sensor environment.

2. **Heat Stress Forecast (THI — standard livestock heat-stress index)**
   Formula:  THI = T − (0.55 − 0.0055 × RH) × (T − 14.5)
   Source:   This module (``compute_thi()``)
   Purpose:  Forward-looking advisory based on the regional weather
             forecast, using the dairy-science standard THI scale.

Both are legitimate and serve different purposes.  The sensor-derived
HI feeds the ML pipeline; the THI forecast provides herd-wide
climate advisories.  They should NEVER be merged or confused in the UI.
"""

import json
import time
import traceback
import urllib.request
from datetime import datetime, timezone

# ── THI thresholds (standard livestock scale) ───────────────────────
THI_NORMAL = 72
THI_MILD = 79
THI_MODERATE = 89
# ≥ 89 = severe stress

# ── in-memory cache ─────────────────────────────────────────────────
_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL_S = 3600  # 1 hour


def _cache_key(lat: float, lon: float) -> str:
    return f"{round(lat, 2)}:{round(lon, 2)}"


# ── THI computation ─────────────────────────────────────────────────

def compute_thi(temp_c: float, rh: float) -> float:
    """
    Livestock Temperature-Humidity Index (THI).

    THI = T − (0.55 − 0.0055 × RH) × (T − 14.5)

    This is the standard dairy-science THI used in heat-stress
    research (NRC 1971; Bohmanova et al. 2007).
    """
    return temp_c - (0.55 - 0.0055 * rh) * (temp_c - 14.5)


def thi_level(thi: float) -> str:
    if thi < THI_NORMAL:
        return "normal"
    if thi < THI_MILD:
        return "mild_stress"
    if thi < THI_MODERATE:
        return "moderate_stress"
    return "severe_stress"


# ── Open-Meteo fetch ────────────────────────────────────────────────

def fetch_weather_forecast(
    lat: float, lon: float
) -> dict | None:
    """
    Fetch 7-day hourly forecast from Open-Meteo (free, no key).

    Returns parsed JSON or None on failure.
    """
    key = _cache_key(lat, lon)
    now = time.time()

    # Check cache
    if key in _cache:
        ts, data = _cache[key]
        if now - ts < CACHE_TTL_S:
            return data

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,relative_humidity_2m,"
        f"precipitation,wind_speed_10m"
        f"&forecast_days=7&timezone=auto"
    )

    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "MastiSense/1.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        _cache[key] = (now, data)
        return data
    except Exception as exc:
        print(f"[Weather] Open-Meteo fetch failed: {exc!r}")
        traceback.print_exc()
        return None


# ── heat-stress advisory ───────────────────────────────────────────

def compute_heat_stress_advisory(forecast: dict) -> dict:
    """
    Analyse hourly forecast and compute THI-based heat stress
    advisory.

    Returns a dict with:
      - peak_thi, peak_thi_time, peak_level
      - stress_hours (count of hours with THI ≥ 72)
      - daily_summary (per-day max THI + level)
      - advisory_text
      - method_note (explains this is THI, not sensor HI)
    """
    hourly = forecast.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    rhs = hourly.get("relative_humidity_2m", [])

    if not times or not temps or not rhs:
        return {
            "peak_thi": None,
            "stress_hours": 0,
            "daily_summary": [],
            "advisory_text": "Insufficient weather data.",
            "method_note": _method_note(),
        }

    # Compute hourly THI
    peak_thi = -999.0
    peak_time = ""
    stress_hours = 0
    daily: dict[str, list[float]] = {}

    for i, t_str in enumerate(times):
        if i >= len(temps) or i >= len(rhs):
            break
        temp = temps[i]
        rh = rhs[i]
        if temp is None or rh is None:
            continue
        thi = compute_thi(temp, rh)
        if thi > peak_thi:
            peak_thi = thi
            peak_time = t_str
        if thi >= THI_NORMAL:
            stress_hours += 1
        day = t_str[:10]
        daily.setdefault(day, []).append(thi)

    # Daily summaries
    daily_summary = []
    for day, vals in sorted(daily.items()):
        max_thi = max(vals)
        daily_summary.append({
            "date": day,
            "max_thi": round(max_thi, 1),
            "level": thi_level(max_thi),
        })

    # Advisory text
    peak_level = thi_level(peak_thi) if peak_thi > -999 else "unknown"
    advisory_text = _build_advisory_text(
        peak_thi, peak_time, peak_level, stress_hours
    )

    return {
        "peak_thi": round(peak_thi, 1) if peak_thi > -999 else None,
        "peak_thi_time": peak_time,
        "peak_level": peak_level,
        "stress_hours": stress_hours,
        "daily_summary": daily_summary,
        "advisory_text": advisory_text,
        "method_note": _method_note(),
    }


def _method_note() -> str:
    return (
        "This advisory uses the livestock-standard Temperature-"
        "Humidity Index (THI = T − (0.55 − 0.0055×RH)(T − 14.5)), "
        "computed from the regional weather forecast.  It is distinct "
        "from the sensor-derived 'Current Heat Index' "
        "(HI = T + 0.36×RH − 10.0) used per-reading in the ML "
        "feature pipeline.  Both are legitimate measures serving "
        "different purposes."
    )


def _build_advisory_text(
    peak_thi: float,
    peak_time: str,
    peak_level: str,
    stress_hours: int,
) -> str:
    if peak_thi < THI_NORMAL:
        return (
            "No heat stress forecast for the coming week.  "
            "Conditions are within the normal comfort zone for "
            "dairy cattle."
        )

    parts = [
        f"Heat stress forecast: peak THI of {peak_thi:.1f} "
        f"expected around {peak_time}."
    ]

    if stress_hours > 0:
        parts.append(
            f"A total of {stress_hours} hours with THI ≥ {THI_NORMAL} "
            f"are forecast over the next 7 days."
        )

    if peak_level == "severe_stress":
        parts.append(
            "SEVERE heat stress expected — provide maximum shade, "
            "constant water access, and consider shifting milking "
            "to cooler hours.  Monitor all cows for signs of "
            "heat exhaustion."
        )
    elif peak_level == "moderate_stress":
        parts.append(
            "Moderate heat stress expected — ensure adequate "
            "ventilation and shade, increase water availability, "
            "and monitor high-producing cows closely."
        )
    else:  # mild
        parts.append(
            "Mild heat stress expected — ensure normal shade and "
            "water provisions.  No special intervention required "
            "for most cows."
        )

    return "  ".join(parts)


# ── climate advisories (herd-wide) ──────────────────────────────────

def generate_climate_advisories(
    lat: float, lon: float
) -> list[dict]:
    """
    Generate herd-wide climate advisories based on the weather
    forecast.

    Returns a list of advisory dicts, each with:
      ``type``, ``severity``, ``text``, ``date`` (if applicable)
    """
    forecast = fetch_weather_forecast(lat, lon)
    if not forecast:
        return [{
            "type": "error",
            "severity": "info",
            "text": (
                "Unable to retrieve weather forecast.  "
                "Climate advisories are temporarily unavailable."
            ),
            "date": None,
        }]

    advisories: list[dict] = []
    hourly = forecast.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    rhs = hourly.get("relative_humidity_2m", [])
    precips = hourly.get("precipitation", [])

    # ── Heat stress advisories ──────────────────────────────────
    heat_advisory = compute_heat_stress_advisory(forecast)
    if heat_advisory["peak_thi"] and heat_advisory["peak_thi"] >= THI_NORMAL:
        advisories.append({
            "type": "heat_stress",
            "severity": heat_advisory["peak_level"],
            "text": heat_advisory["advisory_text"],
            "date": heat_advisory["peak_thi_time"][:10],
            "method_note": heat_advisory["method_note"],
        })

    # ── Humidity advisory ───────────────────────────────────────
    daily_rh: dict[str, list[float]] = {}
    for i, t_str in enumerate(times):
        if i >= len(rhs) or rhs[i] is None:
            continue
        day = t_str[:10]
        daily_rh.setdefault(day, []).append(rhs[i])

    for day, vals in sorted(daily_rh.items()):
        avg_rh = sum(vals) / len(vals)
        if avg_rh > 85:
            # Check if also warm
            day_temps = [
                temps[j] for j, t in enumerate(times)
                if t[:10] == day and j < len(temps) and temps[j] is not None
            ]
            avg_temp = sum(day_temps) / len(day_temps) if day_temps else 0
            if avg_temp > 25:
                advisories.append({
                    "type": "humidity",
                    "severity": "moderate_stress",
                    "text": (
                        f"High humidity ({avg_rh:.0f}% avg) combined "
                        f"with warm conditions ({avg_temp:.1f}°C avg) "
                        f"forecast for {day} — elevated mastitis risk "
                        "due to bacterial growth.  Ensure adequate "
                        "ventilation and clean, dry bedding."
                    ),
                    "date": day,
                })
                break  # One humidity advisory is sufficient

    # ── Rainfall advisory ───────────────────────────────────────
    daily_rain: dict[str, float] = {}
    for i, t_str in enumerate(times):
        if i >= len(precips) or precips[i] is None:
            continue
        day = t_str[:10]
        daily_rain[day] = daily_rain.get(day, 0) + precips[i]

    for day, total in sorted(daily_rain.items()):
        if total > 15:  # > 15mm = significant rain
            advisories.append({
                "type": "rainfall",
                "severity": "mild_stress",
                "text": (
                    f"Significant rainfall ({total:.1f}mm) forecast "
                    f"for {day} — inspect drainage, prevent muddy "
                    "lying areas, and ensure dry bedding to reduce "
                    "environmental mastitis pathogen exposure."
                ),
                "date": day,
            })
            break  # One rain advisory is sufficient

    if not advisories:
        advisories.append({
            "type": "clear",
            "severity": "normal",
            "text": (
                "No adverse weather conditions forecast for the "
                "coming week.  Continue standard herd management."
            ),
            "date": None,
        })

    return advisories
