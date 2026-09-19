# Recommendation thresholds. The delta_* checks catch a worsening trend even
# if the absolute value is still "normal"; the absolute checks catch a cow
# that is already outside a safe range. Both matter for early (7-14 day)
# warning: trends usually appear before an absolute threshold is crossed.
SCC_SUBCLINICAL_THRESHOLD = 200_000   # cells/mL - standard subclinical cutoff
SCC_HIGH_THRESHOLD = 400_000
NORMAL_TEMP_C = 38.6


def recommendations(f):
    """
    Generate threshold-based recommendations.

    Returns list[str] — this return type is part of the public API
    contract and MUST NOT be changed.
    """
    def v(k):
        return float(f.get(k, 0) or 0)

    r = []

    # -- Trend-based (rate of change over the last few days) ----------------
    if v("milk_conductivity_delta_7d") > .6:
        r.append("Rising milk conductivity over the last week — re-check the cow and inspect the udder for early signs of inflammation.")
    if v("milk_yield_delta_7d") < -1:
        r.append("Milk yield has been declining over the last week — review feed intake and general health.")
    if v("scc_value_delta_7d") > 150_000:
        r.append("Somatic cell count is rising sharply — repeat/confirm SCC testing and review udder-health status.")
    if v("milk_temp_c_delta_3d") > .3:
        r.append("Milk temperature has risen over the last 3 days — check body temperature and clinical signs.")

    # -- Absolute-level checks (matter once real values differ from the
    #    fixed prototype baselines, or whenever SCC is supplied) -----------
    scc = v("scc_value")
    if scc >= SCC_HIGH_THRESHOLD:
        r.append(f"SCC is at {scc:,.0f} cells/mL, above the high-risk threshold — likely active mastitis; escalate to veterinary review.")
    elif scc >= SCC_SUBCLINICAL_THRESHOLD:
        r.append(f"SCC is at {scc:,.0f} cells/mL, above the subclinical mastitis threshold — increase monitoring frequency for this cow.")

    if v("milk_temp_c") >= NORMAL_TEMP_C + 0.8:
        r.append("Milk temperature is notably above the herd-normal range — check for fever and clinical mastitis signs.")

    # -- Missed-monitoring flag (from the calendar-gap-aware feature set) --
    if v("missed_days_7d") >= 2:
        r.append("Several sensor readings were missed in the last week — check device connectivity; risk scores based on stale data are less reliable.")

    # -- Farm-management drivers. These stay silent under the fixed
    #    prototype baselines (activity/hygiene/feed/milking-hygiene never
    #    move) and switch on automatically once real values are supplied,
    #    either per-reading or once USE_REAL_FARM_FEATURES is enabled. -----
    if v("activity_score") < 0.6:
        r.append("Activity/rumination is low — review comfort, heat stress and lameness as contributing factors.")
    if v("hygiene_score") < 0.6:
        r.append("Housing/udder hygiene score is low — review bedding, stall cleanliness and general hygiene practices.")
    if v("milking_hygiene_score") < 0.6:
        r.append("Milking-hygiene score is low — review pre/post-milking teat disinfection and milking-machine maintenance.")
    if v("feed_score") < 0.6:
        r.append("Feed/nutrition score is low — review ration balance and feed availability.")

    # -- Animal status & monitoring staleness ----------------------------
    if 0 < v("days_in_milk") <= 30:
        r.append("Early lactation (DIM <= 30 days) is a vulnerable window for udder health — adhere strictly to pre/post milking hygiene.")
    if v("scc_stale") >= 1 or v("days_since_scc") > 7:
        r.append("SCC measurement is stale (>7 days) — schedule a fresh cow-side or lab SCC test for updated risk assessment.")

    if not r:
        r.append("Continue daily monitoring and follow veterinary protocol.")
    return r


def recommendations_detailed(f, cow_profile=None):
    """
    Generate categorised recommendations including biosecurity.

    Returns list[dict], each with keys:
      - ``text``     : human-readable recommendation string
      - ``category`` : one of "clinical", "management", "biosecurity"

    This is a NEW field (``recommendations_detailed``) added alongside
    the existing ``recommendations`` (list[str]) to preserve backward
    compatibility.  See §6 requirement.
    """
    def v(k):
        return float(f.get(k, 0) or 0)

    detailed: list[dict] = []

    # ── Clinical recommendations (same logic as recommendations()) ───
    if v("milk_conductivity_delta_7d") > .6:
        detailed.append({"text": "Rising milk conductivity over the last week — re-check the cow and inspect the udder for early signs of inflammation.", "category": "clinical"})
    if v("milk_yield_delta_7d") < -1:
        detailed.append({"text": "Milk yield has been declining over the last week — review feed intake and general health.", "category": "clinical"})
    if v("scc_value_delta_7d") > 150_000:
        detailed.append({"text": "Somatic cell count is rising sharply — repeat/confirm SCC testing and review udder-health status.", "category": "clinical"})
    if v("milk_temp_c_delta_3d") > .3:
        detailed.append({"text": "Milk temperature has risen over the last 3 days — check body temperature and clinical signs.", "category": "clinical"})

    scc = v("scc_value")
    if scc >= SCC_HIGH_THRESHOLD:
        detailed.append({"text": f"SCC is at {scc:,.0f} cells/mL, above the high-risk threshold — likely active mastitis; escalate to veterinary review.", "category": "clinical"})
    elif scc >= SCC_SUBCLINICAL_THRESHOLD:
        detailed.append({"text": f"SCC is at {scc:,.0f} cells/mL, above the subclinical mastitis threshold — increase monitoring frequency for this cow.", "category": "clinical"})

    if v("milk_temp_c") >= NORMAL_TEMP_C + 0.8:
        detailed.append({"text": "Milk temperature is notably above the herd-normal range — check for fever and clinical mastitis signs.", "category": "clinical"})

    # ── Management recommendations ──────────────────────────────────
    if v("missed_days_7d") >= 2:
        detailed.append({"text": "Several sensor readings were missed in the last week — check device connectivity; risk scores based on stale data are less reliable.", "category": "management"})
    if v("activity_score") < 0.6:
        detailed.append({"text": "Activity/rumination is low — review comfort, heat stress and lameness as contributing factors.", "category": "management"})
    if v("hygiene_score") < 0.6:
        detailed.append({"text": "Housing/udder hygiene score is low — review bedding, stall cleanliness and general hygiene practices.", "category": "management"})
    if v("milking_hygiene_score") < 0.6:
        detailed.append({"text": "Milking-hygiene score is low — review pre/post-milking teat disinfection and milking-machine maintenance.", "category": "management"})
    if v("feed_score") < 0.6:
        detailed.append({"text": "Feed/nutrition score is low — review ration balance and feed availability.", "category": "management"})
    if 0 < v("days_in_milk") <= 30:
        detailed.append({"text": "Early lactation (DIM ≤ 30 days) is a vulnerable window for udder health — adhere strictly to pre/post milking hygiene.", "category": "management"})
    if v("scc_stale") >= 1 or v("days_since_scc") > 7:
        detailed.append({"text": "SCC measurement is stale (>7 days) — schedule a fresh cow-side or lab SCC test for updated risk assessment.", "category": "management"})

    # ── §6 Biosecurity recommendations ──────────────────────────────
    prof = cow_profile or {}

    if prof.get("prior_mastitis_flag", 0) == 1:
        detailed.append({
            "text": (
                "This cow has a prior mastitis history — implement "
                "strict teat-end hygiene and consider individual "
                "milking order (milk last in the sequence)."
            ),
            "category": "biosecurity",
        })

    if prof.get("vaccination_status", 1) == 0:
        detailed.append({
            "text": (
                "Vaccination status is not current — consult your "
                "veterinarian about mastitis vaccination programmes "
                "suitable for your herd."
            ),
            "category": "biosecurity",
        })

    data_days = prof.get("data_days", 999)
    if data_days < 14:
        detailed.append({
            "text": (
                "Observation period is short — enforce biosecurity "
                "quarantine protocols for newly introduced animals "
                "until sufficient monitoring history is established."
            ),
            "category": "biosecurity",
        })

    if not detailed:
        detailed.append({
            "text": "Continue daily monitoring and follow veterinary protocol.",
            "category": "management",
        })

    return detailed

