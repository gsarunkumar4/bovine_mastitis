# Recommendation thresholds. The delta_* checks catch a worsening trend even
# if the absolute value is still "normal"; the absolute checks catch a cow
# that is already outside a safe range. Both matter for early (7-14 day)
# warning: trends usually appear before an absolute threshold is crossed.
SCC_SUBCLINICAL_THRESHOLD = 200_000   # cells/mL - standard subclinical cutoff
SCC_HIGH_THRESHOLD = 400_000
NORMAL_TEMP_C = 38.6


def recommendations(f):
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
