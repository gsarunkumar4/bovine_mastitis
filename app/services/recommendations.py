def recommendations(f):
    def v(k): return float(f.get(k, 0) or 0)
    r = []
    if v("milk_conductivity_delta_7d") > .6: r.append("Review the rising conductivity trend and re-check the cow.")
    if v("milk_yield_delta_7d") < -1: r.append("Review the recent milk-yield decline.")
    if v("scc_value_delta_7d") > 150000: r.append("Repeat/confirm SCC and review udder-health status.")
    if v("milk_temp_c_delta_3d") > .3: r.append("Check temperature and clinical signs.")
    if not r: r.append("Continue daily monitoring and follow veterinary protocol.")
    return r
