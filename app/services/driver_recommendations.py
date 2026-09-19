"""
§9a — SHAP-driver-driven recommendations.

Maps top SHAP driver feature names to deterministic, plain-language
veterinary / management explanations.  This is NOT generative — every
recommendation is a fixed lookup from a curated dictionary.

Coverage strategy:
  1. Exact match on base signal name  (e.g. ``scc_value``)
  2. Pattern match on rolling/delta variants
     (e.g. ``scc_value_mean_7d``, ``milk_yield_delta_3d``)
  3. Fallback for any unrecognised feature name

The existing threshold-based rules in recommendations.py are kept as a
floor — this module adds driver-specific context on top.
"""

import re

# ── base signal → explanation mapping ───────────────────────────────
# Keys are the raw feature column names from the model.

_BASE_EXPLANATIONS: dict[str, str] = {
    # Core sensors
    "scc_value":
        "Somatic cell count is a primary risk driver — request a "
        "fresh cow-side or lab SCC test and compare with the "
        "historical trend.",
    "milk_conductivity":
        "Milk electrical conductivity is abnormal — may indicate "
        "ion imbalance from udder tissue damage.  Inspect all "
        "four quarters individually.",
    "milk_temp_c":
        "Milk temperature is outside the normal range — check the "
        "cow for fever and clinical mastitis signs.",
    "milk_yield_l":
        "Milk yield is contributing to risk assessment — review "
        "nutrition, comfort, and lactation stage.",
    "activity_score":
        "Activity level is a factor — low activity can indicate "
        "lameness, heat stress, or systemic illness.",
    "rumination_min":
        "Rumination time is contributing — reduced rumination can "
        "signal digestive stress, pain, or illness.",
    "environment_heat_index":
        "Environmental heat index is a driver — implement heat "
        "stress mitigation (shade, fans, water access).",
    "hygiene_score":
        "Hygiene score is a risk driver — review bedding "
        "cleanliness, stall design, and udder preparation.",
    "feed_score":
        "Feed/nutrition score is contributing — review ration "
        "balance, feed availability, and body condition.",
    "milking_hygiene_score":
        "Milking hygiene is a driver — review pre/post-milking "
        "teat disinfection and milking-machine maintenance.",

    # Optional sensors
    "milk_pH":
        "Milk pH is abnormal — deviations can indicate mastitis "
        "or metabolic issues.  Cross-check with conductivity.",
    "body_temperature":
        "Body temperature is a factor — elevated temperature may "
        "indicate systemic infection or inflammation.",
    "udder_surface_temperature":
        "Udder surface temperature is elevated — localised heat "
        "can indicate quarter-level inflammation.",
    "farm_temperature_c":
        "Farm ambient temperature is a factor — extreme "
        "temperatures increase mastitis susceptibility.",
    "farm_humidity":
        "Farm humidity is contributing — high humidity promotes "
        "bacterial growth in the cow's environment.",

    # Derived / static features
    "days_in_milk":
        "Days in milk (DIM) is a factor — early and late "
        "lactation carry different risk profiles; adjust "
        "monitoring intensity accordingly.",
    "parity":
        "Parity (number of lactations) influences baseline risk "
        "— higher-parity cows generally need closer monitoring.",
    "age_years":
        "Cow age is contributing to risk — older animals may have "
        "reduced immune response.",
    "vaccination_status":
        "Vaccination status is a factor — consult your "
        "veterinarian about mastitis vaccination programmes.",
    "prior_mastitis_flag":
        "Prior mastitis history is a risk driver — cows with "
        "previous infections have higher recurrence rates; "
        "implement strict biosecurity protocols.",

    # Gap / staleness indicators
    "missed_days_3d":
        "Recent sensor gaps detected (3-day window) — ensure IoT "
        "device connectivity; predictions from stale data are "
        "less reliable.",
    "missed_days_7d":
        "Multiple sensor readings missed (7-day window) — check "
        "device battery and network; risk scores may be "
        "under-confident.",
    "scc_stale":
        "SCC measurement is stale — schedule a fresh SCC test for "
        "this cow.",
    "days_since_scc":
        "Days since last SCC test is high — laboratory "
        "confirmation is recommended.",
}

# ── pattern-based explanations for rolling / delta variants ─────────

_VARIANT_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Delta variants (trend)
    (re.compile(r"(.+)_delta_(\d+)d$"), (
        "{base_name} has been trending over the last {window} days "
        "— monitor the direction of change and correlate with "
        "clinical observations."
    )),
    # Rolling mean
    (re.compile(r"(.+)_mean_(\d+)d$"), (
        "{window}-day average of {base_name} is contributing — "
        "sustained deviations from the herd norm warrant closer "
        "inspection."
    )),
    # Rolling min
    (re.compile(r"(.+)_min_(\d+)d$"), (
        "Minimum {base_name} over the last {window} days is a "
        "factor — unusually low values may indicate a developing "
        "condition."
    )),
    # Rolling max
    (re.compile(r"(.+)_max_(\d+)d$"), (
        "Peak {base_name} over the last {window} days is elevated "
        "— spike events can precede clinical onset."
    )),
    # Rolling std
    (re.compile(r"(.+)_std_(\d+)d$"), (
        "Variability in {base_name} over the last {window} days "
        "is high — unstable readings may indicate an inconsistent "
        "or developing condition."
    )),
]


def _format_feature_name(raw: str) -> str:
    """Convert snake_case feature name to readable label."""
    name = raw.replace("_", " ").title()
    name = name.replace("Scc", "SCC")
    name = name.replace("Temp C", "Temperature (°C)")
    name = name.replace("Yield L", "Yield (L)")
    name = name.replace("Ph", "pH")
    return name


def _explain_feature(feature: str) -> str:
    """Return a plain-language explanation for a single feature."""

    # 1. Exact match
    if feature in _BASE_EXPLANATIONS:
        return _BASE_EXPLANATIONS[feature]

    # 2. Pattern match on rolling / delta variants
    for pattern, template in _VARIANT_PATTERNS:
        m = pattern.match(feature)
        if m:
            base_raw = m.group(1)
            window = m.group(2)
            base_name = _format_feature_name(base_raw)
            return template.format(base_name=base_name, window=window)

    # 3. Fallback
    return (
        f"{_format_feature_name(feature)} is contributing to the "
        f"risk score — review this parameter in context with other "
        f"clinical indicators."
    )


# ── public API ──────────────────────────────────────────────────────

# Minimum |SHAP impact| to generate a recommendation for
MIN_IMPACT_THRESHOLD = 0.005


def generate_driver_recommendations(
    top_drivers: list[dict],
    risk_tier: str = "",
) -> list[dict]:
    """
    Generate deterministic recommendations from SHAP driver features.

    Parameters
    ----------
    top_drivers : list[dict]
        Each dict has ``feature`` (str) and ``impact`` (float).
    risk_tier : str
        The risk tier (e.g. "High Risk", "Moderate Risk") for
        contextual framing.

    Returns
    -------
    list[dict]
        Each dict has keys:
        ``text``      — plain-language recommendation
        ``category``  — always ``"shap_driven"``
        ``feature``   — the raw feature name
        ``impact``    — the SHAP impact value
    """
    recs: list[dict] = []
    seen_bases: set[str] = set()

    for driver in top_drivers:
        feat = driver.get("feature", "")
        impact = abs(driver.get("impact", 0))

        if impact < MIN_IMPACT_THRESHOLD:
            continue

        # Deduplicate by base signal (e.g. scc_value_mean_7d → scc_value)
        base = re.sub(r"_(delta|mean|min|max|std)_\d+d$", "", feat)
        if base in seen_bases:
            continue
        seen_bases.add(base)

        explanation = _explain_feature(feat)
        recs.append({
            "text": explanation,
            "category": "shap_driven",
            "feature": feat,
            "impact": driver.get("impact", 0),
        })

    return recs
