/**
 * ============================================================================
 * MastiSense — Precision Agriculture & AI-IoT Monitoring Dashboard
 * Modular Client-Side Application Logic (app.js)
 * Supports: PWA (§1), Storage (§2), Subclinical SCC (§3), Real-Time SSE (§4),
 * Notifications (§5), Biosecurity (§6), Readable Charts (§7),
 * Notifications Center (§8), SHAP & Climate Advisories (§9a, §9b),
 * GIS Farm Map with GPS movement throttle (§10), 6-Language i18n (§11).
 * ============================================================================
 */

(function () {
  "use strict";

  // --------------------------------------------------------------------------
  // 1. Centralized Multilingual Dictionary (§11 — 6 Languages)
  // --------------------------------------------------------------------------
  const I18N = {
    en: {
      appTitle: "MastiSense",
      appSubtitle: "AI-IoT Bovine Mastitis Early Risk Forecasting",
      modelBadgeAudit: "Audit Governance Mode: Inactive",
      modelBadgeActive: "Production Model: ",
      syntheticBadge: "Synthetic Prototype (Decision Support Only)",
      connectedStatus: "Connected",
      disconnectedStatus: "Offline",
      lastSyncLabel: "Last sync:",
      refreshBtn: "Refresh",
      evalAlertsBtn: "Evaluate Alerts",
      apiSettingsBtn: "API Config",
      navOverview: "Executive Overview",
      navHerd: "Herd Surveillance",
      navCowAnalysis: "Cow Analysis & Forecast",
      navTelemetry: "Sensor Telemetry",
      navNotifications: "Notifications Center",
      navFarmMap: "Farm & Herd Map",
      navAlerts: "Alerts Center",
      navGovernance: "Model Governance",
      heroHeadline: "AI-IoT Precision Mastitis Risk Forecasting",
      heroDesc: "Continuous decision-support forecasting for dairy herds. Combining automated in-line sensors, animal history, and calibrated XGBoost machine learning to provide actionable 7-day early warnings and 14-day watch list trends before clinical symptoms manifest.",
      heroIndSystem: "System Status",
      heroIndModel: "Model Serving",
      heroIndGateway: "ESP32 Gateway",
      heroIndSource: "Data Source",
      kpiTotalCows: "Total Monitored Cows",
      kpiTotalSub: "Registered herd cohort",
      kpiHighRisk: "High Risk (7d / 14d)",
      kpiHighRiskSub: "Immediate attention recommended",
      kpiModerateRisk: "Moderate Risk (Watch List)",
      kpiModerateRiskSub: "Elevated physiological drift",
      kpiHealthyCows: "Healthy / Low Risk",
      kpiHealthySub: "Within baseline parameters",
      herdDistTitle: "Herd Health Distribution",
      legendHealthy: "Healthy / Low Risk",
      legendModerate: "Moderate Risk",
      legendHigh: "High Risk",
      legendLow: "Low Risk / Healthy Cow",
      legendMod: "Moderate Risk Cow",
      legendVet: "Veterinary Clinic",
      cowAnalysisTitle: "Selected Cow Analysis & Dual-Horizon Forecast",
      cowAnalysisSubtitle: "Individual cow risk trajectory, longitudinal multi-sensor signals, and explainability",
      selectCowLabel: "Select Cow:",
      cowIdLabel: "Cow ID",
      breedLabel: "Breed",
      ageLabel: "Age",
      parityLabel: "Parity (Lactation #)",
      vaccinationLabel: "Vaccination Status",
      priorMastitisLabel: "Prior Mastitis History",
      dataDaysLabel: "Accumulated History",
      forecast7dTitle: "7-Day Mastitis Risk Forecast",
      forecast7dRole: "Primary Clinical Warning Alarm",
      forecast7dDesc: "Authoritative decision-support trigger (1 to 7 calendar days). Designed for immediate physical udder inspection, CMT testing, and hygiene review.",
      forecast14dTitle: "14-Day Mastitis Risk Forecast",
      forecast14dRole: "Exploratory Watch Signal",
      forecast14dDesc: "Longer-term surveillance indicator (1 to 14 days). Flags subtle multi-sensor drift for visual monitoring during milking.",
      sccIndicatorTitle: "Subclinical SCC Clinical Indicator",
      sccIndicatorSubtitle: "Rule-Based Deterministic Marker • Separate from ML Forecasts",
      latestSccValLabel: "Latest Recorded SCC",
      thresholdGuideLabel: "Clinical Thresholds",
      sccIndicatorDesc: "Rule-based veterinary screening cutoff. Evaluates persistent subclinical inflammation independently from 7d/14d multi-sensor XGBoost projections.",
      dataWarningTitle: "Limited History Notice",
      dataWarningDesc: "This animal has limited historical telemetry (< 7 days). Early warning precision improves as daily observations accumulate.",
      sccStaleTitle: "SCC Data Stale / Missing",
      sccStaleDesc: "No recent laboratory or cow-side SCC test (>7 days). Somatic cell count features are using baseline assumptions.",
      predInactiveTitle: "Model Serving Inactive",
      predInactiveDesc: "Forecast predictions are currently paused because no candidate model has met clinical promotion gates. Review raw sensor trends below.",
      latestTelemetryTitle: "Latest Recorded Telemetry",
      latestTelemetrySubtitle: "Physical and environmental sensor readings captured during the most recent observation",
      sensorCondTitle: "Milk Conductivity",
      sensorCondRef: "Normal baseline: 4.0 - 5.5 mS/cm",
      sensorTempTitle: "Milk Temperature",
      sensorTempRef: "Fever threshold: > 39.2 °C",
      sensorYieldTitle: "Milk Yield",
      sensorYieldRef: "Sharp decline flags health stress",
      sensorSccTitle: "Somatic Cell Count",
      sensorSccRef: "Subclinical threshold: 200k cells/mL",
      sensorHiTitle: "Current Heat Index (sensor-derived)",
      sensorHiRef: "Sensor formula: T + 0.36×H − 10.0 • ML feature",
      trendsTitle: "Longitudinal Sensor & Risk Trajectories",
      tabGrid: "All Sensors (Grid)",
      tabRisk: "Calibrated Risk History",
      tabCond: "Conductivity (mS/cm)",
      tabTemp: "Milk Temp (°C)",
      tabYield: "Yield (Litres)",
      tabScc: "SCC (Cells/mL)",
      chartRiskTitle: "7-Day & 14-Day Calibrated Risk History",
      chartCondTitle: "Milk Electrical Conductivity Trend (mS/cm)",
      chartTempTitle: "In-Line Milk Temperature Trend (°C)",
      chartYieldTitle: "Daily Milk Yield Trajectory (L)",
      chartSccTitle: "Somatic Cell Count History (cells/mL)",
      driversTitle: "Top Risk Driver Features (SHAP Explainability)",
      driversSubtitle: "Multi-sensor features contributing most to this cow's prediction",
      noDrivers: "No significant risk drivers identified for this observation.",
      recsTitle: "Actionable Herd Recommendations",
      recsSubtitle: "Rule-based decision support derived from identified risk drivers",
      noRecs: "All monitored parameters are within acceptable baseline bounds. Maintain standard herd protocol.",
      disclaimerText: "MastiSense is an AI-IoT decision-support tool, not a diagnostic medical device. Never replace physical veterinary examinations with automated predictions.",
      herdTableTitle: "Herd Surveillance & Monitoring Matrix",
      herdTableSubtitle: "Complete individual cow health tracking and forecast early warning table",
      colCowId: "Cow ID",
      colBreedParity: "Breed & Parity",
      col7DayRisk: "7-Day Risk Forecast",
      col14DayRisk: "14-Day Risk Forecast",
      colHistory: "History",
      colDrivers: "Key Influencing Signals",
      colActions: "Action",
      inspectBtn: "Inspect",
      searchPlaceholder: "Search by Cow ID or Breed...",
      noCowsFound: "No cow records matching the specified search criteria.",
      notifCenterTitle: "Integrated Notifications Center",
      notifCenterSubtitle: "Consolidated feed of acute risk subjects, climate advisories, veterinary recommendations, and channel dispatch logs",
      notifTabRisk: "Acute Risk Watch",
      notifTabClimate: "Climate & THI Advisories",
      notifTabRecs: "Recommendations Digest",
      notifTabLog: "Notification Log",
      loadingRiskItems: "Loading acute risk items...",
      thiAdvisoryTitle: "Heat Stress Forecast (THI — standard livestock heat-stress index)",
      thiAdvisorySubtitle: "7-Day Forward Regional Weather Projection (Open-Meteo Integration)",
      peakThiLabel: "Peak Forecast THI",
      stressHoursLabel: "Stress Hours (THI ≥ 72)",
      forecastPeriodLabel: "Forecast Window",
      reconTitle: "Heat Index Reconciliation Note",
      reconBody: "This forward-looking Heat Stress Forecast uses regional meteorological forecasts to compute the dairy-science standard livestock THI (THI = T − (0.55 − 0.0055×RH)(T − 14.5)). It is distinct from the per-cow sensor-derived Current Heat Index (HI = T + 0.36×RH − 10.0) displayed in the telemetry section. The sensor HI feeds real-time stall micro-climate into the ML model, while the forecast THI guides forward-looking environmental management (shading, ventilation, water provisions). Both are legitimate measures that serve distinct and complementary operational roles.",
      loadingDigest: "Loading recommendations digest...",
      notifLogSubtitle: "Audit history of all dispatched webhook and console early warning alerts",
      testNotifBtn: "Send Test Webhook",
      farmMapTitle: "Farm & Herd Map View",
      farmMapSubtitle: "Geographic tracking of pastured cows, risk distribution, and nearby veterinary services (OSM Overpass)",
      useLocationBtn: "Use My Location",
      findVetsBtn: "Find Nearby Vets",
      vetRadiusLabel: "Vet Search Radius:",
      activeGpsLabel: "Active Center Coordinates:",
      assignCowCoordsBtn: "Assign Cow Location",
      selectCowCoordLabel: "Cow:",
      saveLocationBtn: "Save Location",
      nearbyVetsTitle: "Nearby Veterinary Clinics",
      noVetsQueried: "Set location and click 'Find Nearby Vets' to query OpenStreetMap Overpass.",
      alertsTitle: "Active Alerts & Incident Center",
      alertsSubtitle: "Real-time alerts triggered by high risk forecasts or critical sensor anomalies",
      noAlerts: "No open critical risk alerts at this time. Herd operating within nominal variance.",
      resolveBtn: "Resolve",
      cancelBtn: "Cancel",
      confirmResolveBtn: "Confirm Resolution",
      resolvePlaceholder: "Enter resolution clinical notes...",
      govTitle: "ML Model Governance & Drift Surveillance",
      govSubtitle: "Transparent model validation performance, test cohort metrics, and sensor drift audit",
      govCandidateAudit: "Model Candidate Audit History",
      auditColVersion: "Model Version",
      auditCol7d: "7-Day Metrics",
      auditCol14d: "14-Day Metrics",
      auditColStatus: "Promotion Status",
      auditColReasons: "Audit Reasons",
      driftTitle: "Sensor Population Stability (PSI Drift Audit):",
      driftStatusLabel: "Status:",
      driftWindowLabel: "Window:",
      driftLoading: "Checking drift summary...",
      modalApiTitle: "Configure FastAPI Server URL",
      modalApiDesc: "Specify the base HTTP address for the MastiSense backend API.",
      modalSaveBtn: "Save & Connect",
      modalCancelBtn: "Cancel",
      yes: "Yes",
      no: "No",
      daysUnit: "days",
      readingsUnit: "readings"
    },

    ta: {
      appTitle: "மாஸ்டிசென்ஸ்",
      appSubtitle: "AI-IoT மாடுகளுக்கான மடிநோய் ஆரம்ப இடர் முன்கணிப்பு",
      modelBadgeAudit: "மாதிரி தணிக்கை முறை: செயலற்றது",
      modelBadgeActive: "உற்பத்தி மாதிரி: ",
      syntheticBadge: "செயற்கை முன்மாதிரி (முடிவெடுக்கும் ஆதரவு மட்டுமே)",
      connectedStatus: "இணைக்கப்பட்டது",
      disconnectedStatus: "இணைப்பில்லை",
      lastSyncLabel: "கடைசி ஒத்திசைவு:",
      refreshBtn: "புதுப்பி",
      evalAlertsBtn: "எச்சரிக்கைகளை மதிப்பிடு",
      apiSettingsBtn: "API கட்டமைப்பு",
      navOverview: "செயல்பாட்டு சுருக்கம்",
      navHerd: "மந்தை கண்காணிப்பு",
      navCowAnalysis: "மாட்டு ஆய்வு & முன்கணிப்பு",
      navTelemetry: "உணரி தொலை அளவியல்",
      navNotifications: "அறிவிப்புகள் மையம்",
      navFarmMap: "பண்ணை மற்றும் மந்தை வரைபடம்",
      navAlerts: "எச்சரிக்கை மையம்",
      navGovernance: "மாதிரி நிர்வாகம்",
      heroHeadline: "AI-IoT துல்லியமான மடிநோய் இடர் முன்கணிப்பு",
      heroDesc: "பால் பண்ணைகளுக்கான தொடர்ச்சியான முடிவெடுக்கும் ஆதரவு முன்கணிப்பு. தானியங்கி உணரி தரவுகள், மாட்டின் வரலாற்றுப் பதிவுகள் மற்றும் அளவீடு செய்யப்பட்ட XGBoost மெஷின் லேர்னிங் மூலம் நோய் அறிகுறிகள் தோன்றுவதற்கு முன்பே 7-நாள் ஆரம்ப எச்சரிக்கை மற்றும் 14-நாள் கண்காணிப்பு வழிகாட்டுதலை வழங்குகிறது.",
      heroIndSystem: "கணினி நிலை",
      heroIndModel: "மாதிரி சேவை",
      heroIndGateway: "ESP32 நுழைவாயில்",
      heroIndSource: "தரவு ஆதாரம்",
      kpiTotalCows: "மொத்த கண்காணிக்கப்படும் மாடுகள்",
      kpiTotalSub: "பதிவு செய்யப்பட்ட மந்தை குழு",
      kpiHighRisk: "அதிதீவிர ஆபத்து (7 நாள் / 14 நாள்)",
      kpiHighRiskSub: "உடனடி கவனம் தேவைப்படுகிறது",
      kpiModerateRisk: "மிதமான ஆபத்து (கண்காணிப்பு பட்டியல்)",
      kpiModerateRiskSub: "உடலியல் மாறுபாடுகள் காணப்படுகின்றன",
      kpiHealthyCows: "ஆரோக்கியமானது / குறைந்த ஆபத்து",
      kpiHealthySub: "இயல்பான அளவீடுகளில் உள்ளன",
      herdDistTitle: "மந்தை ஆரோக்கியப் பரவல்",
      legendHealthy: "ஆரோக்கியமானது / குறைந்த ஆபத்து",
      legendModerate: "மிதமான ஆபத்து",
      legendHigh: "அதிதீவிர ஆபத்து",
      legendLow: "குறைந்த ஆபத்து / ஆரோக்கியமான மாடு",
      legendMod: "மிதமான ஆபத்துள்ள மாடு",
      legendVet: "கால்நடை மருந்தகம்",
      cowAnalysisTitle: "தேர்ந்தெடுக்கப்பட்ட மாட்டு ஆய்வு & இரட்டை முன்கணிப்பு",
      cowAnalysisSubtitle: "தனிப்பட்ட மாட்டின் இடர் பாதை, பல உணரி சிக்னல்கள் மற்றும் விளக்கங்கள்",
      selectCowLabel: "மாட்டைத் தேர்ந்தெடுக்கவும்:",
      cowIdLabel: "மாடு எண்",
      breedLabel: "இனம்",
      ageLabel: "வயது",
      parityLabel: "ஈற்று முறை (கறவை எண்)",
      vaccinationLabel: "தடுப்பூசி நிலை",
      priorMastitisLabel: "முந்தைய மடிநோய் வரலாறு",
      dataDaysLabel: "திரட்டப்பட்ட வரலாறு",
      forecast7dTitle: "7-நாள் மடிநோய் இடர் முன்கணிப்பு",
      forecast7dRole: "முதன்மை மருத்துவ எச்சரிக்கை அலாரம்",
      forecast7dDesc: "உடனடி மருத்துவ முடிவெடுக்கும் தூண்டுதல் (1 முதல் 7 நாட்கள் வரை). மடி பரிசோதனை, CMT சோதனை மற்றும் சுகாதார ஆய்வுக்கு வடிவமைக்கப்பட்டது.",
      forecast14dTitle: "14-நாள் மடிநோய் இடர் முன்கணிப்பு",
      forecast14dRole: "ஆராய்ச்சி கண்காணிப்பு சிக்னல்",
      forecast14dDesc: "நீண்ட கால கண்காணிப்பு காட்டி (1 முதல் 14 நாட்கள் வரை). கறவையின் போது நுட்பமான உணரி மாறுபாடுகளை கண்காணிக்கப் பயன்படுகிறது.",
      sccIndicatorTitle: "சப்-கிளினிக்கல் SCC மருத்துவ காட்டி",
      sccIndicatorSubtitle: "விதி அடிப்படையிலான துல்லியமான குறிப்பான் • ML கணிப்புகளிலிருந்து தனிப்பட்டது",
      latestSccValLabel: "சமீபத்திய SCC பதிவு",
      thresholdGuideLabel: "மருத்துவ வரம்புகள்",
      sccIndicatorDesc: "மருத்துவ வரம்பு விதி. 7-நாள் / 14-நாள் XGBoost கணிப்புகளிலிருந்து சுயாதீனமாக தொடர்ந்து இருக்கும் வீக்கத்தை மதிப்பிடுகிறது.",
      dataWarningTitle: "குறைந்த வரலாற்றுத் தகவல் அறிவிப்பு",
      dataWarningDesc: "இந்த மாட்டிற்கு 7 நாட்களுக்கும் குறைவான தரவுகளே உள்ளன. தினசரி பதிவுகள் கூடும் போது கணிப்பின் துல்லியம் அதிகரிக்கும்.",
      sccStaleTitle: "SCC தரவு காலாவதியானது / கிடைக்கவில்லை",
      sccStaleDesc: "சமீபத்திய ஆய்வக SCC சோதனை இல்லை (>7 நாட்கள்). இயல்புநிலை அனுமானங்கள் பயன்படுத்தப்படுகின்றன.",
      predInactiveTitle: "மாதிரி சேவை செயலற்றது",
      predInactiveDesc: "மருத்துவ பதவி உயர்வு அளவுகோல்களை பூர்த்தி செய்யாததால் முன்கணிப்புகள் இடைநிறுத்தப்பட்டுள்ளன.",
      latestTelemetryTitle: "சமீபத்திய உணரி அளவீடுகள்",
      latestTelemetrySubtitle: "கடைசி ஆய்வின் போது பதிவு செய்யப்பட்ட இயற்பியல் மற்றும் சுற்றுச்சூழல் அளவீடுகள்",
      sensorCondTitle: "பால் மின்கடத்துத்திறன்",
      sensorCondRef: "இயல்பான வரம்பு: 4.0 - 5.5 mS/cm",
      sensorTempTitle: "பால் வெப்பநிலை",
      sensorTempRef: "காய்ச்சல் வரம்பு: > 39.2 °C",
      sensorYieldTitle: "பால் மகசூல்",
      sensorYieldRef: "திடீர் வீழ்ச்சி உடல்நலக் குறைவைக் குறிக்கும்",
      sensorSccTitle: "சொமாடிக் செல் எண்ணிக்கை (SCC)",
      sensorSccRef: "உட்கிளினிக்கல் வரம்பு: 200k செல்கள்/மிலி",
      sensorHiTitle: "தற்போதைய வெப்பக் குறியீடு (உணரி அடிப்படையிலானது)",
      sensorHiRef: "உணரி சூத்திரம்: T + 0.36×H − 10.0 • ML உள்ளீடு",
      trendsTitle: "நீண்டகால உணரி & இடர் போக்குகள்",
      tabGrid: "அனைத்து உணரிகள் (கட்டம்)",
      tabRisk: "அளவீடு செய்யப்பட்ட இடர் வரலாறு",
      tabCond: "மின்கடத்துத்திறன் (mS/cm)",
      tabTemp: "பால் வெப்பநிலை (°C)",
      tabYield: "மகசூல் (லிட்டர்)",
      tabScc: "SCC (செல்கள்/மிலி)",
      chartRiskTitle: "7-நாள் & 14-நாள் இடர் வரலாற்றுப் போக்கு",
      chartCondTitle: "பால் மின்கடத்துத்திறன் போக்கு (mS/cm)",
      chartTempTitle: "பால் வெப்பநிலை போக்கு (°C)",
      chartYieldTitle: "தினசரி பால் மகசூல் போக்கு (L)",
      chartSccTitle: "சொமாடிக் செல் எண்ணிக்கை வரலாறு (செல்கள்/மிலி)",
      driversTitle: "முக்கிய இடர் காரணிகள் (SHAP விளக்கம்)",
      driversSubtitle: "இந்த மாட்டின் கணிப்புக்கு அதிகம் பங்களித்த உணரி அம்சங்கள்",
      noDrivers: "இந்த பதிவிற்கு குறிப்பிடத்தக்க இடர் காரணிகள் எதுவும் கண்டறியப்படவில்லை.",
      recsTitle: "செயல்படுத்தக்கூடிய மந்தை பரிந்துரைகள்",
      recsSubtitle: "கண்டறியப்பட்ட இடர் காரணிகளின் அடிப்படையில் அமைந்த முடிவெடுக்கும் பரிந்துரைகள்",
      noRecs: "அனைத்து அளவீடுகளும் இயல்பான வரம்பிற்குள் உள்ளன. நிலையான பராமரிப்பு முறைகளைத் தொடரவும்.",
      disclaimerText: "மாஸ்டிசென்ஸ் என்பது AI-IoT முடிவெடுக்கும் ஆதரவுக் கருவி மட்டுமே, நோயறிதல் மருத்துவ சாதனம் அல்ல. நேரடி கால்நடை மருத்துவ பரிசோதனைக்கு மாற்றாக பயன்படுத்தக்கூடாது.",
      herdTableTitle: "மந்தை கண்காணிப்பு அட்டவணை",
      herdTableSubtitle: "தனிப்பட்ட மாடுகளின் சுகாதார கண்காணிப்பு மற்றும் ஆரம்ப எச்சரிக்கை அட்டவணை",
      colCowId: "மாடு எண்",
      colBreedParity: "இனம் & ஈற்று முறை",
      col7DayRisk: "7-நாள் இடர் முன்கணிப்பு",
      col14DayRisk: "14-நாள் இடர் முன்கணிப்பு",
      colHistory: "வரலாறு",
      colDrivers: "முக்கிய காரணிகள்",
      colActions: "செயல்",
      inspectBtn: "ஆய்வு செய்",
      searchPlaceholder: "மாடு எண் அல்லது இனம் மூலம் தேடவும்...",
      noCowsFound: "தேடல் நிபந்தனைகளுக்கு ஏற்ற மாடுகள் எதுவும் கிடைக்கவில்லை.",
      notifCenterTitle: "ஒருங்கிணைந்த அறிவிப்புகள் மையம்",
      notifCenterSubtitle: "தீவிர இடர் மாடுகள், வானிலை வெப்ப அழுத்த ஆலோசனைகள் மற்றும் அறிவிப்புப் பதிவு",
      notifTabRisk: "அதிதீவிர இடர் கண்காணிப்பு",
      notifTabClimate: "வானிலை & THI ஆலோசனைகள்",
      notifTabRecs: "பரிந்துரைகள் சுருக்கம்",
      notifTabLog: "அறிவிப்பு பதிவு",
      loadingRiskItems: "அதிதீவிர இடர் பதிவுகள் ஏற்றப்படுகின்றன...",
      thiAdvisoryTitle: "வெப்ப அழுத்த முன்னறிவிப்பு (THI — கால்நடை வெப்பக் குறியீடு)",
      thiAdvisorySubtitle: "7-நாள் பிராந்திய வானிலை கணிப்பு (Open-Meteo இணைப்பு)",
      peakThiLabel: "அதிகபட்ச முன்னறிவிப்பு THI",
      stressHoursLabel: "அழுத்த நேரம் (THI ≥ 72)",
      forecastPeriodLabel: "கணிப்புக் காலம்",
      reconTitle: "வெப்பக் குறியீட்டு ஒப்பீட்டு விளக்கம்",
      reconBody: "இந்த வெப்ப அழுத்த முன்னறிவிப்பு பிராந்திய வானிலை அடிப்படையில் கணக்கிடப்படும் THI சூத்திரத்தைப் பயன்படுத்துகிறது. இது உணரி அடிப்படையிலான தற்போதைய வெப்பக் குறியீட்டிலிருந்து (HI = T + 0.36×RH − 10.0) வேறுபட்டது. இரண்டுமே தகுதியான மற்றும் வெவ்வேறு செயல்பாட்டுப் பணிகளுக்குத் தேவையான அளவீடுகள் ஆகும்.",
      loadingDigest: "பரிந்துரைகள் சுருக்கம் ஏற்றப்படுகிறது...",
      notifLogSubtitle: "அனுப்பப்பட்ட அனைத்து எச்சரிக்கைகளின் வரலாற்று தணிக்கை பதிவு",
      testNotifBtn: "சோதனை அறிவிப்பை அனுப்பு",
      farmMapTitle: "பண்ணை மற்றும் மந்தை வரைபடம்",
      farmMapSubtitle: "மேய்ச்சல் மாடுகளின் புவியியல் இருப்பிடம் மற்றும் அருகிலுள்ள கால்நடை மருத்துவ மையங்கள் (OpenStreetMap)",
      useLocationBtn: "எனது இருப்பிடத்தைப் பயன்படுத்து",
      findVetsBtn: "அருகிலுள்ள மருத்துவர்களைக் கண்டுபிடி",
      vetRadiusLabel: "தேடல் ஆரம்:",
      activeGpsLabel: "செயலில் உள்ள அச்சுப்பொறி:",
      assignCowCoordsBtn: "மாட்டு இருப்பிடத்தை ஒதுக்கு",
      selectCowCoordLabel: "மாடு:",
      saveLocationBtn: "இருப்பிடத்தை சேமி",
      nearbyVetsTitle: "அருகிலுள்ள கால்நடை மருந்தகங்கள்",
      noVetsQueried: "இருப்பிடத்தை அமைத்து கால்நடை மருத்துவர்களைத் தேட பொத்தானைக் கிளிக் செய்யவும்.",
      alertsTitle: "செயலில் உள்ள எச்சரிக்கைகள் & சம்பவ மையம்",
      alertsSubtitle: "அதிக ஆபத்து முன்கணிப்புகள் அல்லது உணரி முரண்பாடுகளால் தூண்டப்பட்ட நிகழ்நேர எச்சரிக்கைகள்",
      noAlerts: "தற்போது தீவிர எச்சரிக்கைகள் எதுவும் இல்லை. மந்தை இயல்பாக செயல்படுகிறது.",
      resolveBtn: "தீர்க்கப்பட்டது",
      cancelBtn: "ரத்து செய்",
      confirmResolveBtn: "தீர்வை உறுதிப்படுத்து",
      resolvePlaceholder: "மருத்துவ தீர்வு குறிப்புகளை உள்ளிடவும்...",
      govTitle: "ML மாதிரி நிர்வாகம் & விலகல் கண்காணிப்பு",
      govSubtitle: "மாதிரி சரிபார்ப்பு செயல்திறன் மற்றும் உணரி விலகல் தணிக்கை",
      govCandidateAudit: "மாதிரி வேட்பாளர் தணிக்கை வரலாறு",
      auditColVersion: "மாதிரி பதிப்பு",
      auditCol7d: "7-நாள் அளவீடுகள்",
      auditCol14d: "14-நாள் அளவீடுகள்",
      auditColStatus: "பதவி உயர்வு நிலை",
      auditColReasons: "தணிக்கை முடிவு & காரணங்கள்",
      driftTitle: "உணரி தரவு நிலைத்தன்மை (PSI தணிக்கை):",
      driftStatusLabel: "நிலை:",
      driftWindowLabel: "கால அளவு:",
      driftLoading: "தரவு விலகல் சரிபார்க்கப்படுகிறது...",
      modalApiTitle: "FastAPI சேவையக முகவரி",
      modalApiDesc: "மாஸ்டிசென்ஸ் பின்தள சேவையகத்தின் HTTP முகவரியை உள்ளிடவும்.",
      modalSaveBtn: "சேமித்து இணை",
      modalCancelBtn: "ரத்து செய்",
      yes: "ஆம்",
      no: "இல்லை",
      daysUnit: "நாட்கள்",
      readingsUnit: "பதிவுகள்"
    },

    hi: {
      appTitle: "मास्टीसेंस",
      appSubtitle: "AI-IoT गोजातीय थनेला रोग प्रारंभिक जोखिम पूर्वानुमान",
      modelBadgeAudit: "ऑडिट शासन मोड: निष्क्रिय",
      modelBadgeActive: "उत्पादन मॉडल: ",
      syntheticBadge: "सिंथेटिक प्रोटोटाइप (केवल निर्णय समर्थन)",
      connectedStatus: "सक्रिय जुड़ा हुआ",
      disconnectedStatus: "ऑफ़लाइन",
      lastSyncLabel: "अंतिम सिंक:",
      refreshBtn: "रिफ्रेश करें",
      evalAlertsBtn: "अलर्ट मूल्यांकन",
      apiSettingsBtn: "API सेटिंग्स",
      navOverview: "कार्यकारी सारांश",
      navHerd: "झुंड निगरानी",
      navCowAnalysis: "गाय विश्लेषण और पूर्वानुमान",
      navTelemetry: "सेंसर टेलीमेट्री",
      navNotifications: "अधिसूचना केंद्र",
      navFarmMap: "फार्म और झुंड मानचित्र",
      navAlerts: "अलर्ट केंद्र",
      navGovernance: "मॉडल गवर्नेंस",
      heroHeadline: "AI-IoT सटीक थनेला जोखिम पूर्वानुमान",
      heroDesc: "डेयरी पशुओं के लिए निरंतर निर्णय समर्थन प्रणाली। स्वचालित सेंसर, पशु इतिहास और कैलिब्रेटेड XGBoost मशीन लर्निंग के संयोजन से लक्षण दिखने से पहले 7-दिवसीय प्रारंभिक चेतावनी और 14-दिवसीय रुझान प्रदान करता है।",
      heroIndSystem: "सिस्टम स्थिति",
      heroIndModel: "मॉडल सेवा",
      heroIndGateway: "ESP32 गेटवे",
      heroIndSource: "डेटा स्रोत",
      kpiTotalCows: "कुल मॉनिटर की गई गायें",
      kpiTotalSub: "पंजीकृत झुंड समूह",
      kpiHighRisk: "उच्च जोखिम (7-दिन / 14-दिन)",
      kpiHighRiskSub: "तत्काल ध्यान देने की आवश्यकता",
      kpiModerateRisk: "मध्यम जोखिम (वॉच लिस्ट)",
      kpiModerateRiskSub: "शारीरिक विचलन देखा गया",
      kpiHealthyCows: "स्वस्थ / कम जोखिम",
      kpiHealthySub: "सामान्य सीमा के भीतर",
      herdDistTitle: "झुंड स्वास्थ्य वितरण",
      legendHealthy: "स्वस्थ / कम जोखिम",
      legendModerate: "मध्यम जोखिम",
      legendHigh: "उच्च जोखिम",
      legendLow: "कम जोखिम / स्वस्थ गाय",
      legendMod: "मध्यम जोखिम वाली गाय",
      legendVet: "पशु चिकित्सालय",
      cowAnalysisTitle: "चयनित गाय विश्लेषण और दोहरा पूर्वानुमान",
      cowAnalysisSubtitle: "व्यक्तिगत गाय जोखिम प्रक्षेपवक्र, मल्टी-सेंसर सिग्नल और व्याख्यात्मकता",
      selectCowLabel: "गाय चुनें:",
      cowIdLabel: "गाय आईडी",
      breedLabel: "नस्ल",
      ageLabel: "आयु",
      parityLabel: "ब्यात (दुग्धपान संख्या)",
      vaccinationLabel: "टीकाकरण स्थिति",
      priorMastitisLabel: "पूर्व थनेला इतिहास",
      dataDaysLabel: "संचित इतिहास",
      forecast7dTitle: "7-दिवसीय थनेला जोखिम पूर्वानुमान",
      forecast7dRole: "प्राथमिक नैदानिक चेतावनी अलार्म",
      forecast7dDesc: "तत्काल नैदानिक निर्णय समर्थन (1 से 7 दिन)। शारीरिक थन परीक्षण, सीएमटी परीक्षण और स्वच्छता समीक्षा के लिए।",
      forecast14dTitle: "14-दिवसीय थनेला जोखिम पूर्वानुमान",
      forecast14dRole: "अन्वेषणात्मक निगरानी संकेत",
      forecast14dDesc: "दीर्घकालिक निगरानी संकेतक (1 से 14 दिन)। दूध निकालने के दौरान सूक्ष्म सेंसर बदलावों की निगरानी के लिए।",
      sccIndicatorTitle: "सबक्लिनिकल SCC नैदानिक संकेतक",
      sccIndicatorSubtitle: "नियम आधारित निर्धारक मार्कर • ML पूर्वानुमानों से अलग",
      latestSccValLabel: "नवीनतम दर्ज SCC",
      thresholdGuideLabel: "नैदानिक सीमाएं",
      sccIndicatorDesc: "नियम-आधारित पशु चिकित्सा स्क्रीनिंग कटऑफ। 7-दिन/14-दिन XGBoost अनुमानों से स्वतंत्र रूप से लगातार उप-नैदानिक सूजन का मूल्यांकन करता है।",
      dataWarningTitle: "सीमित इतिहास सूचना",
      dataWarningDesc: "इस पशु का 7 दिनों से कम डेटा उपलब्ध है। दैनिक अवलोकन बढ़ने पर सटीकता बेहतर होगी।",
      sccStaleTitle: "SCC डेटा पुराना / अनुपलब्ध",
      sccStaleDesc: "हाल का कोई प्रयोगशाला SCC परीक्षण नहीं (>7 दिन)। डिफ़ॉल्ट मान्यताओं का उपयोग किया जा रहा है।",
      predInactiveTitle: "मॉडल सेवा निष्क्रिय",
      predInactiveDesc: "पूर्वानुमान वर्तमान में रोके गए हैं क्योंकि किसी भी मॉडल ने नैदानिक पदोन्नति मानदंडों को पूरा नहीं किया है।",
      latestTelemetryTitle: "नवीनतम सेंसर टेलीमेट्री",
      latestTelemetrySubtitle: "हालिया अवलोकन के दौरान कैप्चर किए गए भौतिक और पर्यावरणीय सेंसर रीडिंग",
      sensorCondTitle: "दूध विद्युत चालकता",
      sensorCondRef: "सामान्य आधार: 4.0 - 5.5 mS/cm",
      sensorTempTitle: "दूध का तापमान",
      sensorTempRef: "बुखार सीमा: > 39.2 °C",
      sensorYieldTitle: "दूध की पैदावार",
      sensorYieldRef: "अचानक गिरावट स्वास्थ्य तनाव दर्शाती है",
      sensorSccTitle: "सोमैटिक सेल काउंट (SCC)",
      sensorSccRef: "सबक्लिनिकल सीमा: 200k सेल्स/मिली",
      sensorHiTitle: "वर्तमान ताप सूचकांक (सेंसर आधारित)",
      sensorHiRef: "सेंसर सूत्र: T + 0.36×H − 10.0 • ML इनपुट",
      trendsTitle: "सेंसर और जोखिम रुझान",
      tabGrid: "सभी सेंसर (ग्रिड)",
      tabRisk: "कैलिब्रेटेड जोखिम इतिहास",
      tabCond: "चालकता (mS/cm)",
      tabTemp: "दूध तापमान (°C)",
      tabYield: "पैदावार (लीटर)",
      tabScc: "SCC (सेल्स/मिली)",
      chartRiskTitle: "7-दिन और 14-दिन जोखिम इतिहास",
      chartCondTitle: "दूध चालकता रुझान (mS/cm)",
      chartTempTitle: "दूध तापमान रुझान (°C)",
      chartYieldTitle: "दैनिक दूध पैदावार (L)",
      chartSccTitle: "सोमैटिक सेल काउंट इतिहास (cells/mL)",
      driversTitle: "प्रमुख जोखिम कारक (SHAP व्याख्या)",
      driversSubtitle: "इस भविष्यवाणी में सबसे अधिक योगदान देने वाले सेंसर कारक",
      noDrivers: "इस अवलोकन के लिए कोई महत्वपूर्ण जोखिम कारक नहीं मिला।",
      recsTitle: "कार्रवाई योग्य झुंड सिफारिशें",
      recsSubtitle: "पहचाने गए जोखिम कारकों के आधार पर नियम-संचालित निर्णय समर्थन",
      noRecs: "सभी पैरामीटर सामान्य सीमा के भीतर हैं। मानक प्रोटोकॉल बनाए रखें।",
      disclaimerText: "मास्टीसेंस एक AI-IoT निर्णय समर्थन उपकरण है, नैदानिक चिकित्सा उपकरण नहीं। प्रत्यक्ष पशु चिकित्सा परीक्षा को कभी न बदलें।",
      herdTableTitle: "झुंड निगरानी मैट्रिक्स",
      herdTableSubtitle: "व्यक्तिगत गाय स्वास्थ्य ट्रैकिंग और प्रारंभिक चेतावनी तालिका",
      colCowId: "गाय आईडी",
      colBreedParity: "नस्ल और ब्यात",
      col7DayRisk: "7-दिवसीय जोखिम",
      col14DayRisk: "14-दिवसीय जोखिम",
      colHistory: "इतिहास",
      colDrivers: "मुख्य प्रभावित कारक",
      colActions: "कार्रवाई",
      inspectBtn: "जांचें",
      searchPlaceholder: "गाय आईडी या नस्ल से खोजें...",
      noCowsFound: "कोई रिकॉर्ड नहीं मिला।",
      notifCenterTitle: "एकीकृत अधिसूचना केंद्र",
      notifCenterSubtitle: "गंभीर जोखिम वाली गायों, जलवायु सलाह, पशु चिकित्सा सिफारिशों और प्रेषण लॉग का एकीकृत फ़ीड",
      notifTabRisk: "गंभीर जोखिम निगरानी",
      notifTabClimate: "मौसम और THI सलाह",
      notifTabRecs: "सिफारिशें सारांश",
      notifTabLog: "अधिसूचना लॉग",
      loadingRiskItems: "गंभीर जोखिम वाली गायों को लोड किया जा रहा है...",
      thiAdvisoryTitle: "गर्मी तनाव पूर्वानुमान (THI — मानक पशुधन ताप सूचकांक)",
      thiAdvisorySubtitle: "7-दिवसीय क्षेत्रीय मौसम पूर्वानुमान (Open-Meteo एकीकरण)",
      peakThiLabel: "अधिकतम पूर्वानुमानित THI",
      stressHoursLabel: "तनाव घंटे (THI ≥ 72)",
      forecastPeriodLabel: "पूर्वानुमान अवधि",
      reconTitle: "ताप सूचकांक सामंजस्य नोट",
      reconBody: "यह गर्मी तनाव पूर्वानुमान क्षेत्रीय मौसम के आधार पर पशुधन मानक THI की गणना करता है। यह सेंसर-आधारित वर्तमान ताप सूचकांक (HI = T + 0.36×RH − 10.0) से अलग है। दोनों का अलग-अलग और महत्वपूर्ण परिचालन उद्देश्य है।",
      loadingDigest: "सिफारिशों का सारांश लोड हो रहा है...",
      notifLogSubtitle: "भेजे गए सभी वेबहुक और कंसोल अलर्ट का ऑडिट इतिहास",
      testNotifBtn: "परीक्षण वेबहुक भेजें",
      farmMapTitle: "फार्म और झुंड मानचित्र",
      farmMapSubtitle: "गाय की भौगोलिक स्थिति, जोखिम वितरण और नजदीकी पशु चिकित्सा सेवाएं (OpenStreetMap)",
      useLocationBtn: "मेरा स्थान उपयोग करें",
      findVetsBtn: "नजदीकी पशु चिकित्सक खोजें",
      vetRadiusLabel: "खोज दायरा:",
      activeGpsLabel: "सक्रिय केंद्र निर्देशांक:",
      assignCowCoordsBtn: "गाय का स्थान निर्धारित करें",
      selectCowCoordLabel: "गाय:",
      saveLocationBtn: "स्थान सहेजें",
      nearbyVetsTitle: "निकटतम पशु चिकित्सालय",
      noVetsQueried: "स्थान सेट करें और 'नजदीकी पशु चिकित्सक खोजें' पर क्लिक करें।",
      alertsTitle: "सक्रिय अलर्ट और घटना केंद्र",
      alertsSubtitle: "उच्च जोखिम या असामान्य सेंसर डेटा द्वारा ट्रिगर किए गए रीयल-टाइम अलर्ट",
      noAlerts: "इस समय कोई गंभीर अलर्ट नहीं है। झुंड सामान्य है।",
      resolveBtn: "हल करें",
      cancelBtn: "रद्द करें",
      confirmResolveBtn: "समाधान की पुष्टि करें",
      resolvePlaceholder: "समाधान संबंधी नैदानिक नोट दर्ज करें...",
      govTitle: "ML मॉडल गवर्नेंस और ड्रिफ्ट सर्विलांस",
      govSubtitle: "पारदर्शी मॉडल सत्यापन प्रदर्शन और सेंसर ड्रिफ्ट ऑडिट",
      govCandidateAudit: "मॉडल उम्मीदवार ऑडिट इतिहास",
      auditColVersion: "मॉडल संस्करण",
      auditCol7d: "7-दिवसीय मेट्रिक्स",
      auditCol14d: "14-दिवसीय मेट्रिक्स",
      auditColStatus: "पदोन्नति स्थिति",
      auditColReasons: "ऑडिट कारण",
      driftTitle: "सेंसर स्थिरता (PSI ड्रिफ्ट ऑडिट):",
      driftStatusLabel: "स्थिति:",
      driftWindowLabel: "अवधि:",
      driftLoading: "ड्रिफ्ट सारांश जांचा जा रहा है...",
      modalApiTitle: "FastAPI सर्वर पता कॉन्फ़िगर करें",
      modalApiDesc: "मास्टीसेंस बैकएंड API का HTTP पता दर्ज करें।",
      modalSaveBtn: "सहेजें और कनेक्ट करें",
      modalCancelBtn: "रद्द करें",
      yes: "हाँ",
      no: "नहीं",
      daysUnit: "दिन",
      readingsUnit: "रीडिंग"
    },

    bn: {
      appTitle: "মাস্টীসেন্স",
      appSubtitle: "AI-IoT গবাদি পশুর ওলানপ্রদাহ প্রাথমিক ঝুঁকি পূর্বাভাস",
      modelBadgeAudit: "অডিট শাসন মোড: নিষ্ক্রিয়",
      modelBadgeActive: "উৎপাদন মডেল: ",
      syntheticBadge: "সিন্থেটিক প্রোটোটাইপ (কেবল সিদ্ধান্ত সমর্থন)",
      connectedStatus: "সংযুক্ত",
      disconnectedStatus: "অফলাইন",
      lastSyncLabel: "সর্বশেষ সিঙ্ক:",
      refreshBtn: "রিফ্রেশ করুন",
      evalAlertsBtn: "সতর্কতা মূল্যায়ন",
      apiSettingsBtn: "API কনফিগ",
      navOverview: "সারসংক্ষেপ",
      navHerd: "পশুপাল নজরদারি",
      navCowAnalysis: "গাভী বিশ্লেষণ ও পূর্বাভাস",
      navTelemetry: "সেন্সর টেলিমেট্রি",
      navNotifications: "বিজ্ঞপ্তি কেন্দ্র",
      navFarmMap: "খামার ও পশুপাল মানচিত্র",
      navAlerts: "সতর্কতা কেন্দ্র",
      navGovernance: "মডেল গভর্ন্যান্স",
      heroHeadline: "AI-IoT নির্ভুল ওলানপ্রদাহ ঝুঁকি পূর্বাভাস",
      heroDesc: "দুগ্ধ খামারের জন্য সার্বক্ষণিক সিদ্ধান্ত সমর্থন ব্যবস্থা। স্বয়ংক্রিয় সেন্সর ও ক্যালিব্রেটেড XGBoost মেশিন লার্নিং ব্যবহার করে লক্ষণ প্রকাশের আগেই ৭-দিনের আগাম সতর্কতা এবং ১৪-দিনের প্রবণতা প্রদান করে।",
      heroIndSystem: "সিস্টেমের অবস্থা",
      heroIndModel: "মডেল পরিবেশন",
      heroIndGateway: "ESP32 গেটওয়ে",
      heroIndSource: "উপাত্তের উৎস",
      kpiTotalCows: "মোট নজরদারিকৃত গাভী",
      kpiTotalSub: "নিবন্ধিত পশুপাল গোষ্ঠী",
      kpiHighRisk: "উচ্চ ঝুঁকি (৭ দিন / ১৪ দিন)",
      kpiHighRiskSub: "অবিলম্বে মনোযোগ প্রয়োজন",
      kpiModerateRisk: "মাঝারি ঝুঁকি (নজরদারি তালিকা)",
      kpiModerateRiskSub: "শারীরবৃত্তীয় পরিবর্তন দেখা যাচ্ছে",
      kpiHealthyCows: "সুস্থ / কম ঝুঁকি",
      kpiHealthySub: "স্বাভাবিক সীমার মধ্যে",
      herdDistTitle: "পশুপালের স্বাস্থ্য বণ্টন",
      legendHealthy: "সুস্থ / কম ঝুঁকি",
      legendModerate: "মাঝারি ঝুঁকি",
      legendHigh: "উচ্চ ঝুঁকি",
      legendLow: "কম ঝুঁকি / সুস্থ গাভী",
      legendMod: "মাঝারি ঝুঁকিপূর্ণ গাভী",
      legendVet: "পশু চিকিৎসা কেন্দ্র",
      cowAnalysisTitle: "নির্বাচিত গাভীর বিশ্লেষণ ও পূর্বাভাস",
      cowAnalysisSubtitle: "ব্যক্তিগত গাভীর ঝুঁকি প্রক্ষেপণ ও সেন্সর ডেটা",
      selectCowLabel: "গাভী নির্বাচন করুন:",
      cowIdLabel: "গাভীর আইডি",
      breedLabel: "জাত",
      ageLabel: "বয়স",
      parityLabel: "বিয়ানের সংখ্যা",
      vaccinationLabel: "টিকা অবস্থা",
      priorMastitisLabel: "পূর্ববর্তী ওলানপ্রদাহ ইতিহাস",
      dataDaysLabel: "সঞ্চিত ইতিহাস",
      forecast7dTitle: "৭-দিনের ওলানপ্রদাহ ঝুঁকি পূর্বাভাস",
      forecast7dRole: "প্রাথমিক ক্লিনিক্যাল অ্যালার্ম",
      forecast7dDesc: "১ থেকে ৭ দিনের তাৎক্ষণিক সিদ্ধান্ত সহায়তা। ওলান পরীক্ষা এবং স্বাস্থ্যবিধি পর্যালোচনার জন্য।",
      forecast14dTitle: "১৪-দিনের ওলানপ্রদাহ ঝুঁকি পূর্বাভাস",
      forecast14dRole: "অন্বেষণমূলক নজরদারি সংকেত",
      forecast14dDesc: "দীর্ঘমেয়াদী নজরদারি সূচক (১ থেকে ১৪ দিন)। দুধ দোহনের সময় সূক্ষ্ম পরিবর্তন পর্যবেক্ষণ করতে।",
      sccIndicatorTitle: "সাবক্লিনিক্যাল এসসিসি সূচক",
      sccIndicatorSubtitle: "নিয়ম-ভিত্তিক নির্ধারক মার্কার • ML পূর্বাভাস থেকে পৃথক",
      latestSccValLabel: "সর্বশেষ রেকর্ডকৃত SCC",
      thresholdGuideLabel: "ক্লিনিক্যাল থ্রেশহোল্ড",
      sccIndicatorDesc: "নিয়ম-ভিত্তিক ভেটেরিনারি স্ক্রীনিং কাটঅফ। 7-দিন/14-দিন XGBoost অনুমান থেকে স্বাধীনভাবে ক্রমাগত সাবক্লিনিক্যাল প্রদাহ মূল্যায়ন করে।",
      dataWarningTitle: "সীমিত ইতিহাসের বিজ্ঞপ্তি",
      dataWarningDesc: "এই গাভীর ৭ দিনের কম ডেটা রয়েছে। পর্যবেক্ষণ বাড়লে নির্ভুলতা বৃদ্ধি পাবে।",
      sccStaleTitle: "SCC ডেটা পুরানো / অনুপস্থিত",
      sccStaleDesc: "সাম্প্রতিক কোনো ল্যাব SCC পরীক্ষা নেই (>৭ দিন)। ডিফল্ট অনুমান ব্যবহৃত হচ্ছে।",
      predInactiveTitle: "মডেল পরিবেশন নিষ্ক্রিয়",
      predInactiveDesc: "কোনো মডেল পদোন্নতি পরীক্ষায় উত্তীর্ণ না হওয়ায় পূর্বাভাস স্থগিত রয়েছে।",
      latestTelemetryTitle: "সর্বশেষ সেন্সর টেলিমেট্রি",
      latestTelemetrySubtitle: "সাম্প্রতিক পর্যবেক্ষণে ক্যাপচার করা ভৌত ও পরিবেশগত সেন্সর রিডিং",
      sensorCondTitle: "দুধের বৈদ্যুতিক পরিবাহিতা",
      sensorCondRef: "স্বাভাবিক সীমা: 4.0 - 5.5 mS/cm",
      sensorTempTitle: "দুধের তাপমাত্রা",
      sensorTempRef: "জ্বর থ্রেশহোল্ড: > 39.2 °C",
      sensorYieldTitle: "দুধের উৎপাদন",
      sensorYieldRef: "হঠাৎ হ্রাস স্বাস্থ্য সংকট নির্দেশ করে",
      sensorSccTitle: "সোম্যাটিক সেল কাউন্ট (SCC)",
      sensorSccRef: "সাবক্লিনিক্যাল সীমা: 200k কোষ/মিলি",
      sensorHiTitle: "বর্তমান তাপ সূচক (সেন্সর ভিত্তিক)",
      sensorHiRef: "সেন্সর সূত্র: T + 0.36×H − 10.0 • ML ইনপুট",
      trendsTitle: "সেন্সর ও ঝুঁকির গতিপথ",
      tabGrid: "সকল সেন্সর (গ্রিড)",
      tabRisk: "ক্যালিব্রেটেড ঝুঁকির ইতিহাস",
      tabCond: "পরিবাহিতা (mS/cm)",
      tabTemp: "দুধের তাপমাত্রা (°C)",
      tabYield: "উৎপাদন (লিটার)",
      tabScc: "SCC (কোষ/মিলি)",
      chartRiskTitle: "৭-দিন ও ১৪-দিনের ঝুঁকি ইতিহাস",
      chartCondTitle: "দুধের পরিবাহিতা প্রবণতা (mS/cm)",
      chartTempTitle: "দুধের তাপমাত্রা প্রবণতা (°C)",
      chartYieldTitle: "দৈনিক দুধ উৎপাদন প্রবণতা (L)",
      chartSccTitle: "সোম্যাটিক সেল কাউন্ট ইতিহাস (cells/mL)",
      driversTitle: "শীর্ষ ঝুঁকির কারণ (SHAP ব্যাখ্যা)",
      driversSubtitle: "এই ভবিষ্যদ্বাণীতে সবচেয়ে বেশি অবদান রাখা সেন্সর বৈশিষ্ট্য",
      noDrivers: "এই পর্যবেক্ষণের জন্য কোনো গুরুত্বপূর্ণ ঝুঁকির কারণ পাওয়া যায়নি।",
      recsTitle: "কার্যকর পশুপাল সুপারিশ",
      recsSubtitle: "শনাক্তকৃত ঝুঁকির কারণের ভিত্তিতে সিদ্ধান্ত সহায়তা",
      noRecs: "সকল প্যারামিটার স্বাভাবিক সীমার মধ্যে রয়েছে। মানক প্রোটোকল বজায় রাখুন।",
      disclaimerText: "মাস্টীসেন্স একটি AI-IoT সিদ্ধান্ত সমর্থন ব্যবস্থা, রোগ নির্ণয়কারী চিকিৎসা সরঞ্জাম নয়। সরাসরি পশুচিকিৎসক পরীক্ষার বিকল্প নয়।",
      herdTableTitle: "পশুপাল নজরদারি ম্যাট্রিক্স",
      herdTableSubtitle: "ব্যক্তিগত গাভীর স্বাস্থ্য ট্র্যাকিং এবং প্রাথমিক সতর্কতা সারণী",
      colCowId: "গাভীর আইডি",
      colBreedParity: "জাত ও বিয়ান",
      col7DayRisk: "৭-দিনের ঝুঁকি",
      col14DayRisk: "১৪-দিনের ঝুঁকি",
      colHistory: "ইতিহাস",
      colDrivers: "প্রধান প্রভাবক",
      colActions: "পদক্ষেপ",
      inspectBtn: "পরিদর্শন",
      searchPlaceholder: "আইডি বা জাত দিয়ে খুঁজুন...",
      noCowsFound: "কোনো তথ্য পাওয়া যায়নি।",
      notifCenterTitle: "সমন্বিত বিজ্ঞপ্তি কেন্দ্র",
      notifCenterSubtitle: "তীব্র ঝুঁকিপূর্ণ গাভী, আবহাওয়া পরামর্শ ও প্রেরণ লগের সমন্বিত ফিড",
      notifTabRisk: "তীব্র ঝুঁকি নজরদারি",
      notifTabClimate: "আবহাওয়া ও THI পরামর্শ",
      notifTabRecs: "সুপারিশ সারাংশ",
      notifTabLog: "বিজ্ঞপ্তি লগ",
      loadingRiskItems: "ঝুঁকিপূর্ণ গাভীর তালিকা লোড হচ্ছে...",
      thiAdvisoryTitle: "তাপ চাপ পূর্বাভাস (টিএইচআই — প্রাণিসম্পদ তাপ সূচক)",
      thiAdvisorySubtitle: "৭-দিনের আঞ্চলিক আবহাওয়া প্রক্ষেপণ (Open-Meteo একীকরণ)",
      peakThiLabel: "সর্বোচ্চ পূর্বাভাসিত THI",
      stressHoursLabel: "চাপের সময় (THI ≥ 72)",
      forecastPeriodLabel: "পূর্বাভাস উইন্ডো",
      reconTitle: "তাপ সূচক সমন্বয় নোট",
      reconBody: "এই তাপ চাপ পূর্বাভাস আঞ্চলিক আবহাওয়ার ওপর ভিত্তি করে প্রাণিসম্পদ আদর্শ THI গণনা করে। এটি সেন্সর-ভিত্তিক বর্তমান তাপ সূচক থেকে পৃথক। উভয়ের আলাদা এবং গুরুত্বপূর্ণ ব্যবহার রয়েছে।",
      loadingDigest: "সুপারিশের সারাংশ লোড হচ্ছে...",
      notifLogSubtitle: "প্রেরিত সমস্ত সতর্কতার অডিট ইতিহাস",
      testNotifBtn: "পরীক্ষামূলক ওয়েবহুক পাঠান",
      farmMapTitle: "খামার ও পশুপাল মানচিত্র",
      farmMapSubtitle: "গাভীর ভৌগোলিক অবস্থান, ঝুঁকি বণ্টন ও নিকটস্থ পশুচিকিৎসা পরিষেবা (OpenStreetMap)",
      useLocationBtn: "আমার অবস্থান ব্যবহার করুন",
      findVetsBtn: "নিকটস্থ পশুচিকিৎসক খুঁজুন",
      vetRadiusLabel: "অনুসন্ধান ব্যাসার্ধ:",
      activeGpsLabel: "সক্রিয় কেন্দ্র স্থানাঙ্ক:",
      assignCowCoordsBtn: "গাভীর অবস্থান নির্ধারণ করুন",
      selectCowCoordLabel: "গাভী:",
      saveLocationBtn: "অবস্থান সংরক্ষণ করুন",
      nearbyVetsTitle: "নিকটবর্তী পশু চিকিৎসা কেন্দ্র",
      noVetsQueried: "অবস্থান সেট করুন এবং 'নিকটস্থ পশুচিকিৎসক খুঁজুন'-এ ক্লিক করুন।",
      alertsTitle: "সক্রিয় সতর্কতা কেন্দ্র",
      alertsSubtitle: "উচ্চ ঝুঁকি দ্বারা ট্রিগার হওয়া রিয়েল-টাইম সতর্কতা",
      noAlerts: "এই মুহূর্তে কোনো জরুরি সতর্কতা নেই। পশুপাল স্বাভাবিক।",
      resolveBtn: "সমাধান",
      cancelBtn: "বাতিল",
      confirmResolveBtn: "সমাধান নিশ্চিত করুন",
      resolvePlaceholder: "সমাধান নোট লিখুন...",
      govTitle: "মডেল গভর্ন্যান্স ও ড্রিফ্ট নজরদারি",
      govSubtitle: "স্বচ্ছ মডেল বৈধতা এবং সেন্সর ড্রিফ্ট অডিট",
      govCandidateAudit: "মডেল প্রার্থী অডিট ইতিহাস",
      auditColVersion: "মডেল সংস্করণ",
      auditCol7d: "৭-দিনের মেট্রিক্স",
      auditCol14d: "১৪-দিনের মেট্রিক্স",
      auditColStatus: "অবস্থা",
      auditColReasons: "অডিট কারণ",
      driftTitle: "সেন্সর স্থিতিশীলতা (PSI ড্রিফ্ট অডিট):",
      driftStatusLabel: "অবস্থা:",
      driftWindowLabel: "সময়কাল:",
      driftLoading: "ড্রিফ্ট সারাংশ পরীক্ষা করা হচ্ছে...",
      modalApiTitle: "FastAPI সার্ভার ঠিকানা কনফিগার করুন",
      modalApiDesc: "মাস্টীসেন্স ব্যাকএন্ড API-এর HTTP ঠিকানা লিখুন।",
      modalSaveBtn: "সংরক্ষণ ও সংযোগ",
      modalCancelBtn: "বাতিল",
      yes: "হ্যাঁ",
      no: "না",
      daysUnit: "দিন",
      readingsUnit: "রিডিং"
    },

    mr: {
      appTitle: "मास्टीसेन्स",
      appSubtitle: "AI-IoT गोवंशीय स्तनदाह (मस्टाइटिस) प्रारंभिक जोखीम अंदाज",
      modelBadgeAudit: "ऑडिट गव्हर्नन्स मोड: निष्क्रिय",
      modelBadgeActive: "उत्पादन मॉडेल: ",
      syntheticBadge: "सिंथेटिक प्रोटोटाइप (केवळ निर्णय समर्थन)",
      connectedStatus: "कनेक्ट केलेले",
      disconnectedStatus: "ऑफलाइन",
      lastSyncLabel: "शेवटचे सिंक:",
      refreshBtn: "रिफ्रेश करा",
      evalAlertsBtn: "अलर्ट मूल्यांकन",
      apiSettingsBtn: "API कॉन्फिगर",
      navOverview: "कार्यकारी सारांश",
      navHerd: "कळप देखरेख",
      navCowAnalysis: "गाय विश्लेषण आणि अंदाज",
      navTelemetry: "सेन्सर टेलिमेट्री",
      navNotifications: "सूचना केंद्र",
      navFarmMap: "फार्म आणि कळप नकाशा",
      navAlerts: "अलर्ट केंद्र",
      navGovernance: "मॉडेल गव्हर्नन्स",
      heroHeadline: "AI-IoT अचूक स्तनदाह जोखीम अंदाज",
      heroDesc: "डेअरी फार्मसाठी सतत निर्णय समर्थन प्रणाली. स्वयंचलित सेन्सर्स आणि कॅलिब्रेटेड XGBoost मशीन लर्निंग वापरून लक्षणे दिसण्यापूर्वी 7-दिवसीय पूर्वसूचना आणि 14-दिवसीय ट्रेंड प्रदान करते.",
      heroIndSystem: "सिस्टम स्थिती",
      heroIndModel: "मॉडेल सेवा",
      heroIndGateway: "ESP32 गेटवे",
      heroIndSource: "डेटा स्रोत",
      kpiTotalCows: "एकूण निरीक्षण केलेल्या गायी",
      kpiTotalSub: "नोंदणीकृत कळप गट",
      kpiHighRisk: "उच्च जोखीम (7 दिवस / 14 दिवस)",
      kpiHighRiskSub: "त्वरित लक्ष देणे आवश्यक",
      kpiModerateRisk: "मध्यम जोखीम (वॉच लिस्ट)",
      kpiModerateRiskSub: "शारीरिक बदल दिसून येत आहेत",
      kpiHealthyCows: "निरोगी / कमी जोखीम",
      kpiHealthySub: "सामान्य मर्यादेत आहेत",
      herdDistTitle: "कळप आरोग्य वितरण",
      legendHealthy: "निरोगी / कमी जोखीम",
      legendModerate: "मध्यम जोखीम",
      legendHigh: "उच्च जोखीम",
      legendLow: "कमी जोखीम / निरोगी गाय",
      legendMod: "मध्यम जोखीम असलेली गाय",
      legendVet: "पशुवैद्यकीय दवाखाना",
      cowAnalysisTitle: "निवडलेल्या गाईचे विश्लेषण आणि अंदाज",
      cowAnalysisSubtitle: "वैयक्तिक गायीचा जोखीम मार्ग आणि सेन्सर डेटा",
      selectCowLabel: "गाय निवडा:",
      cowIdLabel: "गाय आयडी",
      breedLabel: "जात",
      ageLabel: "वय",
      parityLabel: "वेताची संख्या",
      vaccinationLabel: "लसीकरण स्थिती",
      priorMastitisLabel: "मागील स्तनदाह इतिहास",
      dataDaysLabel: "संचित इतिहास",
      forecast7dTitle: "7-दिवसीय स्तनदाह जोखीम अंदाज",
      forecast7dRole: "प्राथमिक क्लिनिकल चेतावणी अलार्म",
      forecast7dDesc: "1 ते 7 दिवसांसाठी त्वरित क्लिनिकल निर्णय समर्थन. सड तपासणी, सीएमटी चाचणी आणि स्वच्छता पुनरावलोकनासाठी.",
      forecast14dTitle: "14-दिवसीय स्तनदाह जोखीम अंदाज",
      forecast14dRole: "अन्वेषणात्मक देखरेख सिग्नल",
      forecast14dDesc: "दीर्घकालीन देखरेख निर्देशक (1 ते 14 दिवस). दूध काढताना सूक्ष्म सेन्सर बदल पाहण्यासाठी.",
      sccIndicatorTitle: "सबक्लिनिकल एससीसी वैद्यकीय निर्देशक",
      sccIndicatorSubtitle: "नियम-आधारित निर्धारक मार्कर • ML अंदाजापेक्षा वेगळे",
      latestSccValLabel: "नवीनतम नोंदवलेली SCC",
      thresholdGuideLabel: "क्लिनिकल मर्यादा",
      sccIndicatorDesc: "नियम-आधारित पशुवैद्यकीय स्क्रीनिंग मर्यादा. 7-दिवस/14-दिवस XGBoost अंदाजांपासून स्वतंत्रपणे सततच्या सबक्लिनिकल जळजळीचे मूल्यांकन करते.",
      dataWarningTitle: "मर्यादित इतिहास सूचना",
      dataWarningDesc: "या जनावराचा 7 दिवसांपेक्षा कमी डेटा आहे. दैनंदिन नोंदी वाढल्यावर अचूकता सुधारेल.",
      sccStaleTitle: "SCC डेटा जुना / अनुपलब्ध",
      sccStaleDesc: "अलीकडील कोणतीही लॅब SCC चाचणी नाही (>7 दिवस). डीफॉल्ट गृहीतके वापरली जात आहेत.",
      predInactiveTitle: "मॉडेल सेवा निष्क्रिय",
      predInactiveDesc: "कोणत्याही मॉडेलने पदोन्नती निकष पूर्ण न केल्यामुळे अंदाज तात्पुरते थांबवले आहेत.",
      latestTelemetryTitle: "नवीनतम सेन्सर टेलिमेट्री",
      latestTelemetrySubtitle: "अलीकडील निरीक्षणादरम्यान नोंदवलेले भौतिक आणि पर्यावरणीय वाचन",
      sensorCondTitle: "दूध विद्युत वाहकता",
      sensorCondRef: "सामान्य आधार: 4.0 - 5.5 mS/cm",
      sensorTempTitle: "दूध तापमान",
      sensorTempRef: "ताप मर्यादा: > 39.2 °C",
      sensorYieldTitle: "दूध उत्पादन",
      sensorYieldRef: "अचानक घट आरोग्याचा ताण दर्शवते",
      sensorSccTitle: "सोमॅटिक सेल काउंट (SCC)",
      sensorSccRef: "सबक्लिनिकल मर्यादा: 200k सेल्स/मिली",
      sensorHiTitle: "सध्याचा उष्णता निर्देशांक (सेन्सर आधारित)",
      sensorHiRef: "सेन्सर सूत्र: T + 0.36×H − 10.0 • ML इनपुट",
      trendsTitle: "सेन्सर आणि जोखीम मार्ग",
      tabGrid: "सर्व सेन्सर्स (ग्रिड)",
      tabRisk: "कॅलिब्रेटेड जोखीम इतिहास",
      tabCond: "वाहकता (mS/cm)",
      tabTemp: "दूध तापमान (°C)",
      tabYield: "उत्पादन (लिटर)",
      tabScc: "SCC (सेल्स/मिली)",
      chartRiskTitle: "7-दिवस आणि 14-दिवस जोखीम इतिहास",
      chartCondTitle: "दूध वाहकता ट्रेंड (mS/cm)",
      chartTempTitle: "दूध तापमान ट्रेंड (°C)",
      chartYieldTitle: "दैनिक दूध उत्पादन ट्रेंड (L)",
      chartSccTitle: "सोमॅटिक सेल काउंट इतिहास (cells/mL)",
      driversTitle: "मुख्य जोखीम घटक (SHAP स्पष्टीकरण)",
      driversSubtitle: "या अंदाजात सर्वाधिक योगदान देणारे सेन्सर घटक",
      noDrivers: "या निरीक्षणासाठी कोणताही महत्त्वपूर्ण जोखीम घटक आढळला नाही.",
      recsTitle: "कृती करण्यायोग्य कळप शिफारसी",
      recsSubtitle: "ओळखलेल्या जोखीम घटकांवर आधारित निर्णय समर्थन",
      noRecs: "सर्व बाबी सामान्य मर्यादेत आहेत. मानक व्यवस्थापन चालू ठेवा.",
      disclaimerText: "मास्टीसेन्स हे AI-IoT निर्णय समर्थन साधन आहे, वैद्यकीय उपकरण नाही. प्रत्यक्ष पशुवैद्यकीय तपासणीस पर्याय नाही.",
      herdTableTitle: "कळप देखरेख मॅट्रिक्स",
      herdTableSubtitle: "वैयक्तिक गाय आरोग्य ट्रॅकिंग आणि पूर्वसूचना सारणी",
      colCowId: "गाय आयडी",
      colBreedParity: "जात आणि वेत",
      col7DayRisk: "7-दिवसीय जोखीम",
      col14DayRisk: "14-दिवसीय जोखीम",
      colHistory: "इतिहास",
      colDrivers: "मुख्य घटक",
      colActions: "कृती",
      inspectBtn: "तपासा",
      searchPlaceholder: "गाय आयडी किंवा जातीनुसार शोधा...",
      noCowsFound: "कोणतीही नोंद आढळली नाही.",
      notifCenterTitle: "एकीकृत सूचना केंद्र",
      notifCenterSubtitle: "गंभीर जोखीम असलेल्या गायी, हवामान सल्ला आणि सूचना लॉगचे एकत्रित केंद्र",
      notifTabRisk: "गंभीर जोखीम देखरेख",
      notifTabClimate: "हवामान आणि THI सल्ला",
      notifTabRecs: "शिफारसी सारांश",
      notifTabLog: "सूचना लॉग",
      loadingRiskItems: "गंभीर जोखीम नोंदी लोड होत आहेत...",
      thiAdvisoryTitle: "उष्णता ताण अंदाज (THI — मानक पशुधन निर्देशांक)",
      thiAdvisorySubtitle: "7-दिवसीय प्रादेशिक हवामान अंदाज (Open-Meteo एकत्रीकरण)",
      peakThiLabel: "कमाल अंदाजित THI",
      stressHoursLabel: "ताण तास (THI ≥ 72)",
      forecastPeriodLabel: "अंदाज कालावधी",
      reconTitle: "उष्णता निर्देशांक स्पष्टीकरण",
      reconBody: "हा उष्णता ताण अंदाज प्रादेशिक हवामानावर आधारित THI ची गणना करतो. हा सेन्सर-आधारित चालू उष्णता निर्देशांकापेक्षा वेगळा आहे. दोन्ही उपायांचे स्वतंत्र आणि महत्त्वाचे महत्त्व आहे.",
      loadingDigest: "शिफारसी सारांश लोड होत आहे...",
      notifLogSubtitle: "पाठवलेल्या सर्व वेबहुक आणि कन्सोल अलर्टचा ऑडिट इतिहास",
      testNotifBtn: "चाचणी वेबहुक पाठवा",
      farmMapTitle: "फार्म आणि कळप नकाशा",
      farmMapSubtitle: "गायींचे भौगोलिक स्थान, जोखीम वितरण आणि जवळचे पशुवैद्यकीय दवाखाने (OpenStreetMap)",
      useLocationBtn: "माझे स्थान वापरा",
      findVetsBtn: "जवळचे पशुवैद्यक शोधा",
      vetRadiusLabel: "शोध त्रिज्या:",
      activeGpsLabel: "सक्रिय केंद्र समन्वय:",
      assignCowCoordsBtn: "गायीचे स्थान नियुक्त करा",
      selectCowCoordLabel: "गाय:",
      saveLocationBtn: "स्थान जतन करा",
      nearbyVetsTitle: "जवळचे पशुवैद्यकीय दवाखाने",
      noVetsQueried: "स्थान निश्चित करा आणि 'जवळचे पशुवैद्यक शोधा' वर क्लिक करा.",
      alertsTitle: "सक्रिय अलर्ट आणि घटना केंद्र",
      alertsSubtitle: "उच्च जोखीम किंवा असामान्य सेन्सर डेटामुळे ट्रिगर केलेले रिअल-टाइम अलर्ट",
      noAlerts: "सध्या कोणतेही गंभीर अलर्ट नाहीत. कळप सामान्य आहे.",
      resolveBtn: "निवारण",
      cancelBtn: "रद्द करा",
      confirmResolveBtn: "निवारणाची पुष्टी करा",
      resolvePlaceholder: "क्लिनिकल नोंदी प्रविष्ट करा...",
      govTitle: "ML मॉडेल गव्हर्नन्स आणि ड्रिफ्ट सर्व्हिलन्स",
      govSubtitle: "पारदर्शक मॉडेल प्रमाणीकरण आणि सेन्सर ड्रिफ्ट ऑडिट",
      govCandidateAudit: "मॉडेल उमेदवार ऑडिट इतिहास",
      auditColVersion: "मॉडेल आवृत्ती",
      auditCol7d: "7-दिवसीय मेट्रिक्स",
      auditCol14d: "14-दिवसीय मेट्रिक्स",
      auditColStatus: "स्थिती",
      auditColReasons: "ऑडिट कारणे",
      driftTitle: "सेन्सर स्थिरता (PSI ड्रिफ्ट ऑडिट):",
      driftStatusLabel: "स्थिती:",
      driftWindowLabel: "कालावधी:",
      driftLoading: "ड्रिफ्ट सारांश तपासत आहे...",
      modalApiTitle: "FastAPI सर्व्हर पत्ता कॉन्फिगर करा",
      modalApiDesc: "मास्टीसेन्स बॅकएंड API चा HTTP पत्ता प्रविष्ट करा.",
      modalSaveBtn: "जतन करा आणि कनेक्ट करा",
      modalCancelBtn: "रद्द करा",
      yes: "होय",
      no: "नाही",
      daysUnit: "दिवस",
      readingsUnit: "नोंदी"
    },

    ml: {
      appTitle: "മാസ്റ്റിസെൻസ്",
      appSubtitle: "AI-IoT പശുക്കളിലെ അകിടുവീക്ക സാധ്യത മുൻകൂട്ടി പ്രവചിക്കൽ",
      modelBadgeAudit: "ഓഡിറ്റ് ഭരണ മോഡ്: നിർജ്ജീവം",
      modelBadgeActive: "പ്രൊഡക്ഷൻ മോഡൽ: ",
      syntheticBadge: "സിന്തറ്റിക് പ്രോട്ടോടൈപ്പ് (തീരുമാന പിന്തുണ മാത്രം)",
      connectedStatus: "കണക്റ്റുചെയ്‌തു",
      disconnectedStatus: "ഓഫ്‌ലൈൻ",
      lastSyncLabel: "അവസാന സിങ്ക്:",
      refreshBtn: "പുതുക്കുക",
      evalAlertsBtn: "മുന്നറിയിപ്പുകൾ വിലയിരുത്തുക",
      apiSettingsBtn: "API ക്രമീകരണം",
      navOverview: "പ്രവർത്തന സംഗ്രഹം",
      navHerd: "കന്നുകാലി നിരീക്ഷണം",
      navCowAnalysis: "പശു വിശകലനവും പ്രവചനവും",
      navTelemetry: "സെൻസർ ടെലിമെട്രി",
      navNotifications: "അറിയിപ്പ് കേന്ദ്രം",
      navFarmMap: "ഫാം & കന്നുകാലി ഭൂപടം",
      navAlerts: "മുന്നറിയിപ്പ് കേന്ദ്രം",
      navGovernance: "മോഡൽ ഗവേണൻസ്",
      heroHeadline: "AI-IoT കൃത്യതയുള്ള അകിടുവീക്ക സാധ്യത മുൻകൂട്ടി അറിയൽ",
      heroDesc: "ഡയറി ഫാമുകൾക്കായുള്ള തുടർച്ചയായ തീരുമാന പിന്തുണ സംവിധാനം. സെൻസർ വിവരങ്ങളും കാലിബ്രേറ്റ് ചെയ്ത XGBoost മെഷീൻ ലേണിംഗും ഉപയോഗിച്ച് രോഗലക്ഷണങ്ങൾ പ്രകടമാകുന്നതിന് മുൻപ് തന്നെ 7 ദിവസത്തെ മുന്നറിയിപ്പും 14 ദിവസത്തെ ട്രെൻഡും നൽകുന്നു.",
      heroIndSystem: "സിസ്റ്റം നില",
      heroIndModel: "മോഡൽ സേവനം",
      heroIndGateway: "ESP32 ഗേറ്റ്‌വേ",
      heroIndSource: "ഡാറ്റ ഉറവിടം",
      kpiTotalCows: "ആകെ നിരീക്ഷിക്കുന്ന പശുക്കൾ",
      kpiTotalSub: "രജിസ്റ്റർ ചെയ്ത കന്നുകാലികൾ",
      kpiHighRisk: "ഉയർന്ന അപകടസാധ്യത (7 ദിവസം / 14 ദിവസം)",
      kpiHighRiskSub: "ഉടൻ ശ്രദ്ധിക്കേണ്ടവ",
      kpiModerateRisk: "മിതമായ അപകടസാധ്യത (നിരീക്ഷണ പട്ടിക)",
      kpiModerateRiskSub: "ശാരീരിക വ്യതിയാനങ്ങൾ കാണുന്നു",
      kpiHealthyCows: "ആരോഗ്യമുള്ളത് / കുറഞ്ഞ അപകടം",
      kpiHealthySub: "സാധാരണ നിലയിലുള്ളവ",
      herdDistTitle: "കന്നുകാലികളുടെ ആരോഗ്യ വിതരണം",
      legendHealthy: "ആരോഗ്യമുള്ളത് / കുറഞ്ഞ അപകടം",
      legendModerate: "മിതമായ അപകടസാധ്യത",
      legendHigh: "ഉയർന്ന അപകടസാധ്യത",
      legendLow: "കുറഞ്ഞ അപകടസാധ്യത / ആരോഗ്യമുള്ള പശു",
      legendMod: "മിതമായ അപകടസാധ്യതയുള്ള പശു",
      legendVet: "വെറ്ററിനറി ക്ലിനിക്ക്",
      cowAnalysisTitle: "തിരഞ്ഞെടുത്ത പശു വിശകലനവും പ്രവചനവും",
      cowAnalysisSubtitle: "വ്യക്തിഗത പശു അപകടസാധ്യതയും സെൻസർ ഡാറ്റയും",
      selectCowLabel: "പശുവിനെ തിരഞ്ഞെടുക്കുക:",
      cowIdLabel: "പശു ഐഡി",
      breedLabel: "ഇനം",
      ageLabel: "പ്രായം",
      parityLabel: "പ്രസവങ്ങളുടെ എണ്ണം",
      vaccinationLabel: "വാക്സിനേഷൻ നില",
      priorMastitisLabel: "മുമ്പത്തെ അകിടുവീക്ക ചരിത്രം",
      dataDaysLabel: "ശേഖരിച്ച ചരിത്രം",
      forecast7dTitle: "7-ദിവസത്തെ അകിടുവീക്ക അപകടസാധ്യത പ്രവചനം",
      forecast7dRole: "പ്രാഥമിക ക്ലിനിക്കൽ മുന്നറിയിപ്പ് അലാറം",
      forecast7dDesc: "ഉടൻ നടപടി സ്വീകരിക്കേണ്ട 1 മുതൽ 7 ദിവസത്തെ പ്രവചനം. അകിട് പരിശോധന, സിഎംടി ടെസ്റ്റ് എന്നിവയ്ക്കായി രൂപകൽപ്പന ചെയ്തത്.",
      forecast14dTitle: "14-ദിവസത്തെ അകിടുവീക്ക അപകടസാധ്യത പ്രവചനം",
      forecast14dRole: "നിരീക്ഷണ സിഗ്നൽ",
      forecast14dDesc: "ദീർഘകാല നിരീക്ഷണ സൂചകം (1 മുതൽ 14 ദിവസം). കറവ സമയത്ത് സെൻസർ വ്യതിയാനങ്ങൾ നിരീക്ഷിക്കാൻ സഹായിക്കുന്നു.",
      sccIndicatorTitle: "സബ്-ക്ലിനിക്കൽ എസ്.സി.സി സൂചകം",
      sccIndicatorSubtitle: "നിയമാധിഷ്ഠിത കൃത്യമായ അടയാളം • ML പ്രവചനങ്ങളിൽ നിന്ന് വേറിട്ടത്",
      latestSccValLabel: "ഏറ്റവും പുതിയ SCC രേഖ",
      thresholdGuideLabel: "ക്ലിനിക്കൽ പരിധികൾ",
      sccIndicatorDesc: "നിയമാധിഷ്ഠിത വെറ്ററിനറി സ്ക്രീനിംഗ് പരിധി. 7-ദിവസ/14-ദിവസത്തെ XGBoost പ്രവചനങ്ങളിൽ നിന്ന് സ്വതന്ത്രമായി അണുബാധ വിലയിരുത്തുന്നു.",
      dataWarningTitle: "പരിമിതമായ ചരിത്ര വിവര അറിയിപ്പ്",
      dataWarningDesc: "ഈ പശുവിന് 7 ദിവസത്തിൽ താഴെയുള്ള വിവരങ്ങൾ മാത്രമേയുള്ളൂ. ദിവസേനയുള്ള രേഖകൾ കൂടുന്നതോടെ കൃത്യത വർദ്ധിക്കും.",
      sccStaleTitle: "SCC ഡാറ്റ പഴയതാണ് / ലഭ്യമല്ല",
      sccStaleDesc: "അടുത്തകാലത്തൊന്നും SCC പരിശോധന നടത്തിയിട്ടില്ല (>7 ദിവസം). സ്ഥിരസ്ഥിതി അനുമാനങ്ങളാണ് ഉപയോഗിക്കുന്നത്.",
      predInactiveTitle: "മോഡൽ സേവനം നിർജ്ജീവമാണ്",
      predInactiveDesc: "ഗുണനിലവാര മാനദണ്ഡങ്ങൾ പാലിക്കാത്തതിനാൽ പ്രവചനങ്ങൾ താൽക്കാലികമായി നിർത്തിവച്ചിരിക്കുന്നു.",
      latestTelemetryTitle: "ഏറ്റവും പുതിയ സെൻസർ വിവരങ്ങൾ",
      latestTelemetrySubtitle: "ഏറ്റവും പുതിയ പരിശോധനയിൽ രേഖപ്പെടുത്തിയ പാരിസ്ഥിതിക സെൻസർ വിവരങ്ങൾ",
      sensorCondTitle: "പാൽ വൈദ്യുതചാലകത",
      sensorCondRef: "സാധാരണ നില: 4.0 - 5.5 mS/cm",
      sensorTempTitle: "പാലിന്റെ താപനില",
      sensorTempRef: "പനി പരിധി: > 39.2 °C",
      sensorYieldTitle: "പാൽ ഉൽപ്പാദനം",
      sensorYieldRef: "പെട്ടെന്നുള്ള കുറവ് ആരോഗ്യപ്രശ്നങ്ങൾ സൂചിപ്പിക്കുന്നു",
      sensorSccTitle: "സോമാറ്റിക് സെൽ കൗണ്ട് (SCC)",
      sensorSccRef: "സബ്ക്ലിനിക്കൽ പരിധി: 200k കോശങ്ങൾ/മില്ലി",
      sensorHiTitle: "നിലവിലെ താപ സൂചിക (സെൻസർ അധിഷ്ഠിതം)",
      sensorHiRef: "സെൻസർ ഫോർമുല: T + 0.36×H − 10.0 • ML ഇൻപുട്ട്",
      trendsTitle: "സെൻസർ & അപകടസാധ്യതാ ട്രെൻഡുകൾ",
      tabGrid: "എല്ലാ സെൻസറുകളും (ഗ്രിഡ്)",
      tabRisk: "അപകടസാധ്യതാ ചരിത്രം",
      tabCond: "ചാലകത (mS/cm)",
      tabTemp: "പാൽ താപനില (°C)",
      tabYield: "ഉൽപ്പാദനം (ലിറ്റർ)",
      tabScc: "SCC (കോശങ്ങൾ/മില്ലി)",
      chartRiskTitle: "7-ദിവസ & 14-ദിവസ അപകടസാധ്യതാ ചരിത്രം",
      chartCondTitle: "പാൽ ചാലകതാ ട്രെൻഡ് (mS/cm)",
      chartTempTitle: "പാൽ താപനില ട്രെൻഡ് (°C)",
      chartYieldTitle: "പ്രതിദിന പാൽ ഉൽപ്പാദനം (L)",
      chartSccTitle: "സോമാറ്റിക് സെൽ കൗണ്ട് ചരിത്രം (cells/mL)",
      driversTitle: "പ്രധാന അപകട ഘടകങ്ങൾ (SHAP വിശദീകരണം)",
      driversSubtitle: "ഈ പ്രവചനത്തിലേക്ക് ഏറ്റവും കൂടുതൽ സംഭാവന നൽകിയ സെൻസർ ഘടകങ്ങൾ",
      noDrivers: "ശ്രദ്ധേയമായ അപകട ഘടകങ്ങളൊന്നും കണ്ടെത്തിയിട്ടില്ല.",
      recsTitle: "നടപ്പിലാക്കാവുന്ന കന്നുകാലി നിർദ്ദേശങ്ങൾ",
      recsSubtitle: "കണ്ടെത്തിയ അപകട ഘടകങ്ങളെ അടിസ്ഥാനമാക്കിയുള്ള തീരുമാന പിന്തുണ",
      noRecs: "എല്ലാ ഘടകങ്ങളും സാധാരണ പരിധിക്കുള്ളിലാണ്. നിലവിലെ രീതി തുടരുക.",
      disclaimerText: "മാസ്റ്റിസെൻസ് ഒരു AI-IoT തീരുമാന പിന്തുണ ഉപകരണം മാത്രമാണ്, രോഗനിർണ്ണയ മെഡിക്കൽ ഉപകരണമല്ല. നേരിട്ടുള്ള വെറ്ററിനറി പരിശോധനയ്ക്ക് പകരമാവില്ല.",
      herdTableTitle: "കന്നുകാലി നിരീക്ഷണ മാട്രിക്സ്",
      herdTableSubtitle: "വ്യക്തിഗത പശു ആരോഗ്യ വിവരങ്ങളും മുൻകൂർ മുന്നറിയിപ്പ് പട്ടികയും",
      colCowId: "പശു ഐഡി",
      colBreedParity: "ഇനം & പ്രസവം",
      col7DayRisk: "7-ദിവസത്തെ സാധ്യത",
      col14DayRisk: "14-ദിവസത്തെ സാധ്യത",
      colHistory: "ചരിത്രം",
      colDrivers: "പ്രധാന ഘടകങ്ങൾ",
      colActions: "നടപടി",
      inspectBtn: "പരിശോധിക്കുക",
      searchPlaceholder: "ഐഡിയോ ഇനമോ നൽകി തിരയുക...",
      noCowsFound: "വിവരങ്ങളൊന്നും കണ്ടെത്തിയില്ല.",
      notifCenterTitle: "സംയോജിത അറിയിപ്പ് കേന്ദ്രം",
      notifCenterSubtitle: "അപകടസാധ്യതയുള്ള പശുക്കൾ, കാലാവസ്ഥാ മുന്നറിയിപ്പുകൾ എന്നിവയുടെ ഏകീകൃത ഫീഡ്",
      notifTabRisk: "തീവ്ര അപകട നിരീക്ഷണം",
      notifTabClimate: "കാലാവസ്ഥ & THI മുന്നറിയിപ്പുകൾ",
      notifTabRecs: "നിർദ്ദേശങ്ങളുടെ സംഗ്രഹം",
      notifTabLog: "അറിയിപ്പ് ലോഗ്",
      loadingRiskItems: "വിവരങ്ങൾ ലഭ്യമാക്കുന്നു...",
      thiAdvisoryTitle: "താപ സമ്മർദ്ദ പ്രവചനം (ടി.എച്ച്.ഐ — സ്റ്റാൻഡേർഡ് സൂചിക)",
      thiAdvisorySubtitle: "7 ദിവസത്തെ പ്രാദേശിക കാലാവസ്ഥാ പ്രവചനം (Open-Meteo ലിങ്ക്)",
      peakThiLabel: "പ്രവചിച്ച പരമാവധി THI",
      stressHoursLabel: "സമ്മർദ്ദ സമയം (THI ≥ 72)",
      forecastPeriodLabel: "പ്രവചന കാലയളവ്",
      reconTitle: "താപ സൂചിക വിശദീകരണ കുറിപ്പ്",
      reconBody: "ഈ താപ സമ്മർദ്ദ പ്രവചനം പ്രാദേശിക കാലാവസ്ഥയെ അടിസ്ഥാനമാക്കി ടി.എച്ച്.ഐ കണക്കാക്കുന്നു. ഇത് സെൻസർ അടിസ്ഥാനമാക്കിയുള്ള നിലവിലെ താപ സൂചികയിൽ നിന്ന് വേറിട്ടതാണ്. രണ്ടിനും വ്യത്യസ്തവും പ്രധാനപ്പെട്ടതുമായ ഉപയോഗങ്ങളുണ്ട്.",
      loadingDigest: "നിർദ്ദേശങ്ങൾ ശേഖരിക്കുന്നു...",
      notifLogSubtitle: "അയച്ച എല്ലാ മുന്നറിയിപ്പുകളുടെയും ചരിത്രം",
      testNotifBtn: "ടെസ്റ്റ് വെബ്‌ഹുക്ക് അയക്കുക",
      farmMapTitle: "ഫാം & കന്നുകാലി ഭൂപടം",
      farmMapSubtitle: "പശുക്കളുടെ സ്ഥാനം, രോഗസാധ്യത, അടുത്തുള്ള വെറ്ററിനറി ക്ലിനിക്കുകൾ (OpenStreetMap)",
      useLocationBtn: "എന്റെ സ്ഥാനം ഉപയോഗിക്കുക",
      findVetsBtn: "അടുത്തുള്ള ഡോക്ടർമാരെ കണ്ടെത്തുക",
      vetRadiusLabel: "തിരയൽ പരിധി:",
      activeGpsLabel: "സജീവ കേന്ദ്ര കോർഡിനേറ്റുകൾ:",
      assignCowCoordsBtn: "പശുവിന്റെ സ്ഥാനം നൽകുക",
      selectCowCoordLabel: "പശു:",
      saveLocationBtn: "സ്ഥാനം സംരക്ഷിക്കുക",
      nearbyVetsTitle: "അടുത്തുള്ള വെറ്ററിനറി ക്ലിനിക്കുകൾ",
      noVetsQueried: "സ്ഥാനം നിശ്ചയിച്ച് 'അടുത്തുള്ള ഡോക്ടർമാരെ കണ്ടെത്തുക' ക്ലിക്ക് ചെയ്യുക.",
      alertsTitle: "സജീവ മുന്നറിയിപ്പുകൾ",
      alertsSubtitle: "ഉയർന്ന അപകടസാധ്യതയുള്ള റിയൽ-ടൈം മുന്നറിയിപ്പുകൾ",
      noAlerts: "ഈ സമയത്ത് അടിയന്തര മുന്നറിയിപ്പുകളൊന്നുമില്ല. കന്നുകാലികൾ സാധാരണ നിലയിലാണ്.",
      resolveBtn: "പരിഹരിക്കുക",
      cancelBtn: "റദ്ദാക്കുക",
      confirmResolveBtn: "പരിഹാരം സ്ഥിരീകരിക്കുക",
      resolvePlaceholder: "കുറിപ്പുകൾ നൽകുക...",
      govTitle: "മോഡൽ ഭരണവും ഡ്രിഫ്റ്റ് നിരീക്ഷണവും",
      govSubtitle: "സുതാര്യമായ മോഡൽ പ്രകടനവും സെൻസർ ഡ്രിഫ്റ്റ് ഓഡിറ്റും",
      govCandidateAudit: "മോഡൽ ഓഡിറ്റ് ചരിത്രം",
      auditColVersion: "മോഡൽ പതിപ്പ്",
      auditCol7d: "7-ദിവസത്തെ മെട്രിക്സ്",
      auditCol14d: "14-ദിവസത്തെ മെട്രിക്സ്",
      auditColStatus: "പദവി",
      auditColReasons: "ഓഡിറ്റ് കാരണങ്ങൾ",
      driftTitle: "സെൻസർ സ്ഥിരത (PSI ഓഡിറ്റ്):",
      driftStatusLabel: "നില:",
      driftWindowLabel: "കാലയളവ്:",
      driftLoading: "ഡ്രിഫ്റ്റ് വിവരങ്ങൾ പരിശോധിക്കുന്നു...",
      modalApiTitle: "FastAPI സെർവർ വിലാസം ക്രമീകരിക്കുക",
      modalApiDesc: "മാസ്റ്റിസെൻസ് ബാക്കെൻഡ് API-യുടെ HTTP വിലാസം നൽകുക.",
      modalSaveBtn: "സംരക്ഷിച്ച് ബന്ധിപ്പിക്കുക",
      modalCancelBtn: "റദ്ദാക്കുക",
      yes: "അതെ",
      no: "അല്ല",
      daysUnit: "ദിവസങ്ങൾ",
      readingsUnit: "റീഡിംഗുകൾ"
    }
  };

  // --------------------------------------------------------------------------
  // 2. Application State Single Source of Truth
  // --------------------------------------------------------------------------
  const State = {
    apiBase: localStorage.getItem("mastitis_api_base") || "http://127.0.0.1:8000",
    currentLang: localStorage.getItem("mastitis_lang") || "en",
    isConnected: false,
    isModelActive: false,
    activeModelVersion: null,
    candidateVersions: [],
    featurePipelineVersion: null,
    dataType: "synthetic",
    registeredCows: [],
    herdRiskList: [],
    alertsList: [],
    metrics: {},
    candidateSummaries: [],
    driftReport: {},
    selectedCowId: null,
    selectedCowProfile: null,
    selectedCowHistory: [],
    selectedCowRisk: null,
    selectedCowRiskHistory: [],
    currentChartMode: "grid",
    lastSyncTime: null,
    charts: {
      risk: null,
      cond: null,
      temp: null,
      yield: null,
      scc: null
    },
    // §8 Notifications Center state
    activeNotifTab: "risk",
    weatherAdvisories: null,
    notificationLogs: [],
    // §10 GIS Map state
    activeMap: null,
    cowMarkersLayer: null,
    vetMarkersLayer: null,
    userGpsMarker: null,
    lastGpsPosition: null,      // For ~2km movement throttle gate confirmation!
    activeVetRadius: 5,
    userLocationCenter: null,
    eventSource: null           // §4 Real-time SSE stream
  };

  // --------------------------------------------------------------------------
  // 3. Multilingual Translation Helper (§11)
  // --------------------------------------------------------------------------
  function t(key) {
    const lang = State.currentLang;
    if (I18N[lang] && I18N[lang][key] !== undefined) return I18N[lang][key];
    if (I18N["en"] && I18N["en"][key] !== undefined) return I18N["en"][key];
    return key;
  }

  function setLanguage(lang) {
    if (!I18N[lang]) return;
    State.currentLang = lang;
    localStorage.setItem("mastitis_lang", lang);
    applyLanguage();
    showToast(`Language switched: ${getLanguageDisplayName(lang)}`);
  }

  function getLanguageDisplayName(code) {
    const names = {
      en: "English",
      ta: "தமிழ் (Tamil)",
      hi: "हिन्दी (Hindi)",
      bn: "বাংলা (Bengali)",
      mr: "मराठी (Marathi)",
      ml: "മലയാളം (Malayalam)"
    };
    return names[code] || code;
  }

  function toggleLanguage() {
    // Cycles through 6 languages
    const langs = ["en", "ta", "hi", "bn", "mr", "ml"];
    const idx = langs.indexOf(State.currentLang);
    const nextLang = langs[(idx + 1) % langs.length];
    setLanguage(nextLang);
  }

  function applyLanguage() {
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      el.textContent = t(key);
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
      const key = el.getAttribute("data-i18n-placeholder");
      el.placeholder = t(key);
    });

    const langSelect = document.getElementById("langSelect");
    if (langSelect && langSelect.value !== State.currentLang) {
      langSelect.value = State.currentLang;
    }

    const langBtnText = document.getElementById("langBtnText");
    if (langBtnText) {
      langBtnText.textContent = getLanguageDisplayName(State.currentLang);
    }

    // Re-render localized dynamic components
    renderKpis();
    renderHerdDistribution();
    renderHerdTable();
    if (State.selectedCowId) {
      renderSelectedCow();
    }
    renderNotificationsCenter();
    renderAlerts();
    renderAuditTable();
    renderDriftStatus();
  }

  // --------------------------------------------------------------------------
  // 4. API Client Wrapper
  // --------------------------------------------------------------------------
  const ApiClient = {
    async fetchWithTimeout(endpoint, options = {}, timeoutMs = 8000) {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), timeoutMs);
      const url = `${State.apiBase}${endpoint}`;

      try {
        const res = await fetch(url, { ...options, signal: controller.signal });
        clearTimeout(id);
        return res;
      } catch (err) {
        clearTimeout(id);
        throw err;
      }
    },

    async getRoot() {
      const r = await this.fetchWithTimeout("/");
      if (!r.ok) throw new Error(`Root error: ${r.statusText}`);
      return r.json();
    },

    async getCows() {
      const r = await this.fetchWithTimeout("/cows");
      if (!r.ok) return [];
      return r.json();
    },

    async getHerdRisk() {
      const r = await this.fetchWithTimeout("/herd/risk");
      if (!r.ok) return [];
      return r.json();
    },

    async getCowRisk(cowId) {
      const r = await this.fetchWithTimeout(`/cows/${encodeURIComponent(cowId)}/risk`);
      if (!r.ok) return null;
      return r.json();
    },

    async getCowHistory(cowId) {
      const r = await this.fetchWithTimeout(`/cows/${encodeURIComponent(cowId)}/history`);
      if (!r.ok) return [];
      return r.json();
    },

    async getCowRiskHistory(cowId) {
      const r = await this.fetchWithTimeout(`/cows/${encodeURIComponent(cowId)}/risk-history`);
      if (!r.ok) return [];
      return r.json();
    },

    async getMetrics() {
      const r = await this.fetchWithTimeout("/metrics");
      if (!r.ok) return {};
      return r.json();
    },

    async getAlerts() {
      const r = await this.fetchWithTimeout("/alerts");
      if (!r.ok) return [];
      return r.json();
    },

    async checkAlerts() {
      const r = await this.fetchWithTimeout("/alerts/check", { method: "POST" });
      return r.json();
    },

    async resolveAlert(alertId, note) {
      const r = await this.fetchWithTimeout(`/alerts/${alertId}/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note: note || "Resolved via MastiSense Dashboard" })
      });
      return r.ok;
    },

    async getDriftSummary() {
      const r = await this.fetchWithTimeout("/drift/summary");
      if (!r.ok) return {};
      return r.json();
    },

    // §9b Weather & Climate Advisories
    async getWeatherAdvisory(lat, lon) {
      const query = (lat !== undefined && lon !== undefined && lat !== null && lon !== null)
        ? `?lat=${lat}&lon=${lon}`
        : "";
      const r = await this.fetchWithTimeout(`/weather/advisory${query}`);
      if (!r.ok) return null;
      return r.json();
    },

    // §10 GIS Locations & Vets
    async getCowLocations() {
      const r = await this.fetchWithTimeout("/cows/locations");
      if (!r.ok) return [];
      return r.json();
    },

    async updateCowLocation(cowId, lat, lon, label) {
      const r = await this.fetchWithTimeout(`/cows/${encodeURIComponent(cowId)}/location`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ latitude: lat, longitude: lon, location_label: label })
      });
      return r.json();
    },

    async getNearbyVets(lat, lon, radiusKm = 5) {
      const r = await this.fetchWithTimeout(`/geo/nearby-vets?lat=${lat}&lon=${lon}&radius_km=${radiusKm}`, {}, 15000);
      if (!r.ok) return { vets: [] };
      return r.json();
    },

    // §5 Notifications
    async getNotificationLog(limit = 50) {
      const r = await this.fetchWithTimeout(`/notifications/log?limit=${limit}`);
      if (!r.ok) return [];
      return r.json();
    },

    async sendTestNotification() {
      const r = await this.fetchWithTimeout("/notifications/test", { method: "POST" });
      return r.json();
    },

    // §4 Real-time SSE Stream
    initEventStream() {
      if (typeof EventSource !== "undefined") {
        if (State.eventSource) {
          State.eventSource.close();
        }
        try {
          const es = new EventSource(`${State.apiBase}/events/stream`);
          es.addEventListener("connected", () => {
            console.log("[SSE] Connected to real-time events");
          });
          es.addEventListener("alert", (e) => {
            try {
              const alert = JSON.parse(e.data);
              showToast(`🚨 Acute Alert: Cow ${alert.cow_id} (${alert.message})`, true);
              refreshAlertsAndNotifications();
            } catch (err) {}
          });
          es.addEventListener("heartbeat", () => {
            State.lastSyncTime = new Date();
            updateLastSyncDisplay();
          });
          es.onerror = () => {
            // Keep silent; 30s polling handles background sync
          };
          State.eventSource = es;
        } catch (e) {
          console.warn("[SSE] EventSource init failed:", e);
        }
      }
    }
  };

  // --------------------------------------------------------------------------
  // 5. Toast Notifications & Utility Helpers
  // --------------------------------------------------------------------------
  function showToast(message, isError = false) {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${isError ? "toast-error" : ""}`;
    toast.innerHTML = `<span>${isError ? "⚠" : "✓"}</span><span>${escapeHtml(message)}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = "slideUp 0.3s ease reverse forwards";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text !== undefined && text !== null ? text : "-";
  }

  function updateLastSyncDisplay() {
    const el = document.getElementById("lastSyncTime");
    if (el) {
      if (State.lastSyncTime) {
        el.textContent = State.lastSyncTime.toLocaleTimeString();
      } else {
        el.textContent = "--:--:--";
      }
    }
  }

  // --------------------------------------------------------------------------
  // 6. Master Data Refresh Orchestrator
  // --------------------------------------------------------------------------
  async function refreshData(silent = false) {
    const refreshBtn = document.getElementById("refreshBtn");
    const spinner = document.getElementById("refreshSpinnerIcon");

    if (!silent && spinner) {
      spinner.style.display = "inline-block";
      spinner.style.animation = "spin 0.8s linear infinite";
    }

    try {
      // 1. Query Root
      let root;
      try {
        root = await ApiClient.getRoot();
        State.isConnected = true;
        updateConnectionStatus(true);
      } catch (err) {
        State.isConnected = false;
        updateConnectionStatus(false, err.message);
        renderErrorState("FastAPI backend is unreachable. Verify that the server is running on " + State.apiBase);
        return;
      }

      // 2. Set Model Provenance State
      State.isModelActive = root.model_status === "active";
      State.activeModelVersion = root.model_version || null;
      State.candidateVersions = root.candidate_versions || [];
      State.featurePipelineVersion = root.feature_pipeline_version || "4.1";
      State.dataType = root.data_type || "synthetic";

      updateHeaderBadges();

      // 3. Load Datasets Concurrently
      const [cows, herdRisk, alerts, metrics, drift] = await Promise.all([
        ApiClient.getCows(),
        ApiClient.getHerdRisk(),
        ApiClient.getAlerts(),
        ApiClient.getMetrics(),
        ApiClient.getDriftSummary()
      ]);

      State.registeredCows = cows;
      State.herdRiskList = herdRisk;
      State.alertsList = alerts;
      State.metrics = metrics;
      State.driftReport = drift;
      State.candidateSummaries = metrics.candidate_summaries || [];
      State.lastSyncTime = new Date();

      updateLastSyncDisplay();

      // 4. Render Core Views
      renderKpis();
      renderHerdDistribution();
      populateCowDropdown();
      renderHerdTable();
      renderAlerts();
      renderAuditTable();
      renderGovernanceMetrics();
      renderDriftStatus();

      // 5. Select Default Cow
      if (!State.selectedCowId && cows.length > 0) {
        await selectCow(cows[0].cow_id, false);
      } else if (State.selectedCowId) {
        await selectCow(State.selectedCowId, false);
      }

      // 6. Render Notifications Center (§8)
      renderNotificationsCenter();

      // 7. Update GIS Map if Active (§10)
      if (State.activeMap) {
        MapManager.plotCows();
      }

      if (!silent) {
        showToast("Synchronized with MastiSense platform");
      }
    } catch (err) {
      console.error("[Refresh Error]:", err);
      if (!silent) {
        showToast("Failed to fetch updated data: " + err.message, true);
      }
    } finally {
      if (spinner) {
        spinner.style.animation = "none";
      }
    }
  }

  async function refreshAlertsAndNotifications() {
    try {
      const [alerts, logs] = await Promise.all([
        ApiClient.getAlerts(),
        ApiClient.getNotificationLog(25)
      ]);
      State.alertsList = alerts;
      State.notificationLogs = logs;
      renderAlerts();
      renderNotificationsCenter();
    } catch (e) {}
  }

  // --------------------------------------------------------------------------
  // 7. Connection and Header Badges
  // --------------------------------------------------------------------------
  function updateConnectionStatus(connected, errDetail) {
    const pill = document.getElementById("connectionStatusPill");
    const text = document.getElementById("connectionStatusText");
    const dot = document.getElementById("connectionDot");

    if (connected) {
      if (pill) {
        pill.className = "status-pill pill-connected";
      }
      if (text) text.textContent = t("connectedStatus");
      if (dot) dot.style.backgroundColor = "var(--brand-accent)";
    } else {
      if (pill) {
        pill.className = "status-pill pill-disconnected";
      }
      if (text) text.textContent = t("disconnectedStatus");
      if (dot) dot.style.backgroundColor = "var(--risk-high-solid)";
    }
  }

  function updateHeaderBadges() {
    const modelBadge = document.getElementById("headerModelBadge");
    const modelText = document.getElementById("headerModelText");
    const heroModelStatus = document.getElementById("heroModelStatus");
    const heroSystemStatus = document.getElementById("heroSystemStatus");
    const heroSource = document.getElementById("heroIndSource");

    if (State.isModelActive) {
      if (modelBadge) {
        modelBadge.className = "status-pill pill-active-model";
      }
      if (modelText) {
        modelText.textContent = `${t("modelBadgeActive")}${State.activeModelVersion}`;
      }
      if (heroModelStatus) heroModelStatus.textContent = `${State.activeModelVersion} (Serving)`;
    } else {
      if (modelBadge) {
        modelBadge.className = "status-pill pill-audit-mode";
      }
      if (modelText) {
        modelText.textContent = t("modelBadgeAudit");
      }
      if (heroModelStatus) heroModelStatus.textContent = "Data Audit Mode";
    }

    if (heroSystemStatus) heroSystemStatus.textContent = State.isConnected ? "Online • Monitoring" : "Disconnected";
    if (heroSource) heroSource.textContent = "ESP32 Sensor Stream";
  }

  // --------------------------------------------------------------------------
  // 8. Herd KPIs & Distribution
  // --------------------------------------------------------------------------
  function renderKpis() {
    const total = State.registeredCows.length;
    let high = 0;
    let mod = 0;
    let healthy = 0;

    State.herdRiskList.forEach(r => {
      const t7 = r.risk_tier_7d;
      const t14 = r.risk_tier_14d;
      if (t7 === "High Risk" || t14 === "High Risk") {
        high++;
      } else if (t7 === "Moderate Risk" || t14 === "Moderate Risk") {
        mod++;
      } else {
        healthy++;
      }
    });

    setText("kpiTotalVal", total);
    setText("kpiHighVal", high);
    setText("kpiModVal", mod);
    setText("kpiHealthyVal", healthy);

    setText("kpiHighSub", `${high} ${t("daysUnit")} ${t("kpiHighRiskSub")}`);
    setText("kpiModSub", `${mod} ${t("daysUnit")} ${t("kpiModerateRiskSub")}`);
  }

  function renderHerdDistribution() {
    const total = State.herdRiskList.length || 1;
    let high = 0, mod = 0, healthy = 0;

    State.herdRiskList.forEach(r => {
      const t7 = r.risk_tier_7d;
      const t14 = r.risk_tier_14d;
      if (t7 === "High Risk" || t14 === "High Risk") high++;
      else if (t7 === "Moderate Risk" || t14 === "Moderate Risk") mod++;
      else healthy++;
    });

    const pctHealthy = Math.round((healthy / total) * 100);
    const pctMod = Math.round((mod / total) * 100);
    const pctHigh = 100 - pctHealthy - pctMod;

    const segHealthy = document.getElementById("distSegHealthy");
    const segMod = document.getElementById("distSegMod");
    const segHigh = document.getElementById("distSegHigh");

    if (segHealthy) segHealthy.style.width = `${pctHealthy}%`;
    if (segMod) segMod.style.width = `${pctMod}%`;
    if (segHigh) segHigh.style.width = `${pctHigh}%`;

    const lblHealthy = document.getElementById("distHealthyLabel");
    const lblMod = document.getElementById("distModLabel");
    const lblHigh = document.getElementById("distHighLabel");

    if (lblHealthy) lblHealthy.textContent = `${t("legendHealthy")}: ${pctHealthy}%`;
    if (lblMod) lblMod.textContent = `${t("legendModerate")}: ${pctMod}%`;
    if (lblHigh) lblHigh.textContent = `${t("legendHigh")}: ${pctHigh}%`;
  }

  // --------------------------------------------------------------------------
  // 9. Cow Selection & Profile Panel
  // --------------------------------------------------------------------------
  function populateCowDropdown() {
    const dropdown = document.getElementById("cowSelectDropdown");
    const mapSelect = document.getElementById("mapCowSelect");
    if (!dropdown) return;

    dropdown.innerHTML = "";
    if (mapSelect) mapSelect.innerHTML = "";

    State.registeredCows.forEach(cow => {
      const opt = document.createElement("option");
      opt.value = cow.cow_id;
      opt.textContent = `${cow.cow_id} — ${cow.breed || "Crossbreed"} (P${cow.parity})`;
      dropdown.appendChild(opt);

      if (mapSelect) {
        const optMap = document.createElement("option");
        optMap.value = cow.cow_id;
        optMap.textContent = `${cow.cow_id} (${cow.location_label || "No label"})`;
        mapSelect.appendChild(optMap);
      }
    });

    if (State.selectedCowId) {
      dropdown.value = State.selectedCowId;
      if (mapSelect) mapSelect.value = State.selectedCowId;
    }
  }

  async function selectCow(cowId, updateUrl = true) {
    State.selectedCowId = cowId;

    const dropdown = document.getElementById("cowSelectDropdown");
    if (dropdown && dropdown.value !== cowId) {
      dropdown.value = cowId;
    }

    // Highlight row in matrix table
    document.querySelectorAll("#herdTableBody tr").forEach(tr => {
      if (tr.getAttribute("data-cow-id") === cowId) {
        tr.classList.add("active-row");
      } else {
        tr.classList.remove("active-row");
      }
    });

    // Fetch individual cow details concurrently
    try {
      const [history, risk, riskHistory] = await Promise.all([
        ApiClient.getCowHistory(cowId),
        ApiClient.getCowRisk(cowId),
        ApiClient.getCowRiskHistory(cowId)
      ]);

      State.selectedCowHistory = history;
      State.selectedCowRisk = risk;
      State.selectedCowRiskHistory = riskHistory;
      State.selectedCowProfile = State.registeredCows.find(c => c.cow_id === cowId) || null;

      renderSelectedCow();
    } catch (err) {
      console.error("[Cow Details Error]:", err);
    }
  }

  function renderSelectedCow() {
    const prof = State.selectedCowProfile;
    const risk = State.selectedCowRisk;
    const history = State.selectedCowHistory;
    const riskHistory = State.selectedCowRiskHistory;

    if (!prof) return;

    setText("profAvatarCowId", prof.cow_id);
    setText("profCowIdText", prof.cow_id);
    setText("profBreedText", prof.breed || "Standard Dairy");
    setText("profAgeVal", prof.age_years ? `${prof.age_years} yrs` : "-");
    setText("profParityVal", `Lactation #${prof.parity}`);
    setText("profCalvingVal", prof.calving_date ? prof.calving_date.substring(0, 10) : "-");
    setText("profVaccineVal", prof.vaccination_status === 1 ? t("yes") : t("no"));
    setText("profPriorMastitisVal", prof.prior_mastitis_flag === 1 ? t("yes") : t("no"));
    setText("profHistoryDaysVal", `${history.length} ${t("readingsUnit")}`);

    // Render Dual-Horizon Risk Gauges
    renderRiskGauges(risk, history.length);

    // Render §3 Subclinical SCC Indicator
    renderSubclinicalIndicator(risk, history);

    // Render Latest Telemetry Metric Cards
    renderLatestTelemetry(history);

    // Render Trend Charts (§7 Readable Charts)
    renderCharts(history, riskHistory);

    // Render Drivers & Categorized Recommendations (§6 & §9a)
    renderExplainability(risk);
  }

  // --------------------------------------------------------------------------
  // 10. Dual-Horizon Risk Gauges (7-Day & 14-Day)
  // --------------------------------------------------------------------------
  function renderRiskGauges(risk, dataDays) {
    const gauge7d = document.getElementById("gaugeProg7d");
    const gauge14d = document.getElementById("gaugeProg14d");
    const text7d = document.getElementById("gaugeText7d");
    const text14d = document.getElementById("gaugeText14d");
    const tier7d = document.getElementById("riskTierBadge7d");
    const tier14d = document.getElementById("riskTierBadge14d");
    const calloutBox7d = document.getElementById("warningCallout7d");
    const calloutBox14d = document.getElementById("warningCallout14d");

    const circumference = 263.89;

    if (!State.isModelActive || !risk) {
      if (gauge7d) gauge7d.style.strokeDashoffset = `${circumference}`;
      if (gauge14d) gauge14d.style.strokeDashoffset = `${circumference}`;
      if (text7d) text7d.textContent = "--";
      if (text14d) text14d.textContent = "--";
      if (tier7d) {
        tier7d.className = "risk-tier-badge tier-NoRisk";
        tier7d.textContent = t("predInactiveTitle");
      }
      if (tier14d) {
        tier14d.className = "risk-tier-badge tier-NoRisk";
        tier14d.textContent = t("predInactiveTitle");
      }
      if (calloutBox7d) {
        calloutBox7d.style.display = "flex";
        calloutBox7d.className = "warning-callout data-sufficiency";
        calloutBox7d.innerHTML = `<span>⚖️</span><span>${t("predInactiveDesc")}</span>`;
      }
      if (calloutBox14d) calloutBox14d.style.display = "none";
      return;
    }

    // 7-Day Forecast Rendering
    const pct7 = risk.risk_percent_7d !== undefined ? risk.risk_percent_7d : 0;
    const tierName7 = risk.risk_tier_7d || "No Risk";
    const offset7 = circumference - (pct7 / 100) * circumference;

    if (gauge7d) {
      gauge7d.style.strokeDasharray = `${circumference}`;
      gauge7d.style.strokeDashoffset = `${offset7}`;
      gauge7d.style.stroke = getTierColor(tierName7);
    }
    if (text7d) text7d.textContent = `${pct7.toFixed(1)}`;
    if (tier7d) {
      tier7d.className = `risk-tier-badge tier-${tierName7.replace(/\s+/g, "")}`;
      tier7d.textContent = `${tierName7} (${pct7.toFixed(1)}%)`;
    }

    // 14-Day Forecast Rendering
    const pct14 = risk.risk_percent_14d !== undefined ? risk.risk_percent_14d : 0;
    const tierName14 = risk.risk_tier_14d || "No Risk";
    const offset14 = circumference - (pct14 / 100) * circumference;

    if (gauge14d) {
      gauge14d.style.strokeDasharray = `${circumference}`;
      gauge14d.style.strokeDashoffset = `${offset14}`;
      gauge14d.style.stroke = getTierColor(tierName14);
    }
    if (text14d) text14d.textContent = `${pct14.toFixed(1)}`;
    if (tier14d) {
      tier14d.className = `risk-tier-badge tier-${tierName14.replace(/\s+/g, "")}`;
      tier14d.textContent = `${tierName14} (${pct14.toFixed(1)}%)`;
    }

    // Warnings
    let warn7Html = "";
    if (risk.data_sufficiency_warning) {
      warn7Html += `<div class="warning-callout data-sufficiency"><span>⚠</span><span>${escapeHtml(risk.data_sufficiency_warning)}</span></div>`;
    }
    if (risk.scc_staleness_warning) {
      warn7Html += `<div class="warning-callout scc-stale" style="margin-top:6px;"><span>🧪</span><span>${escapeHtml(risk.scc_staleness_warning)}</span></div>`;
    }

    if (calloutBox7d) {
      if (warn7Html) {
        calloutBox7d.style.display = "block";
        calloutBox7d.innerHTML = warn7Html;
      } else {
        calloutBox7d.style.display = "none";
      }
    }

    if (calloutBox14d) {
      calloutBox14d.style.display = "none";
    }
  }

  function getTierColor(tier) {
    if (tier === "High Risk") return "#dc2626";
    if (tier === "Moderate Risk") return "#d97706";
    if (tier === "Low Risk") return "#0284c7";
    return "#16a34a";
  }

  // --------------------------------------------------------------------------
  // 11. §3 Dedicated Subclinical SCC Indicator Rendering
  // --------------------------------------------------------------------------
  function renderSubclinicalIndicator(risk, history) {
    const sccCard = document.getElementById("subclinicalSccCard");
    const valEl = document.getElementById("subclinicalSccVal");
    const badgeEl = document.getElementById("subclinicalTierBadge");
    const noteEl = document.getElementById("subclinicalNoteText");

    if (!sccCard) return;

    let sccVal = null;
    let level = "normal";
    let note = "Somatic Cell Count is within standard baseline (≤ 200k cells/mL).";

    if (risk && risk.subclinical_scc_risk) {
      sccVal = risk.subclinical_scc_risk.scc;
      level = risk.subclinical_scc_risk.level;
      note = risk.subclinical_scc_risk.note;
    } else if (history && history.length > 0) {
      const latest = history[history.length - 1];
      if (latest.scc_value) {
        sccVal = latest.scc_value;
        if (sccVal >= 400000) level = "high";
        else if (sccVal >= 200000) level = "elevated";
      }
    }

    if (valEl) {
      valEl.textContent = sccVal ? `${Math.round(sccVal).toLocaleString()} cells/mL` : "-- cells/mL";
    }

    if (badgeEl) {
      if (level === "high") {
        badgeEl.className = "subclinical-tier-pill scc-tier-high";
        badgeEl.textContent = "High / Clinical";
      } else if (level === "elevated") {
        badgeEl.className = "subclinical-tier-pill scc-tier-elevated";
        badgeEl.textContent = "Elevated Subclinical";
      } else {
        badgeEl.className = "subclinical-tier-pill scc-tier-normal";
        badgeEl.textContent = "Normal Baseline";
      }
    }

    if (noteEl) {
      noteEl.textContent = `${note} (Rule-based clinical screening cutoff • Independent from ML forecast models).`;
    }
  }

  // --------------------------------------------------------------------------
  // 12. Latest Sensor Telemetry Cards
  // --------------------------------------------------------------------------
  function renderLatestTelemetry(history) {
    if (!history || history.length === 0) {
      setText("sensorCondVal", "--");
      setText("sensorTempVal", "--");
      setText("sensorYieldVal", "--");
      setText("sensorSccVal", "--");
      setText("sensorHeatIndexVal", "--");
      return;
    }

    const latest = history[history.length - 1];

    // Milk Conductivity
    if (latest.milk_conductivity !== undefined && latest.milk_conductivity !== null) {
      setText("sensorCondVal", Number(latest.milk_conductivity).toFixed(2));
      const dot = document.getElementById("condRefDot");
      if (dot) {
        dot.className = latest.milk_conductivity > 5.8 ? "ref-status-dot elevated" : "ref-status-dot";
      }
    } else {
      setText("sensorCondVal", "--");
    }

    // Milk Temperature
    if (latest.milk_temp_c !== undefined && latest.milk_temp_c !== null) {
      setText("sensorTempVal", Number(latest.milk_temp_c).toFixed(1));
      const dot = document.getElementById("tempRefDot");
      if (dot) {
        dot.className = latest.milk_temp_c > 39.2 ? "ref-status-dot elevated" : "ref-status-dot";
      }
    } else {
      setText("sensorTempVal", "--");
    }

    // Daily Milk Yield
    if (latest.milk_yield_l !== undefined && latest.milk_yield_l !== null) {
      setText("sensorYieldVal", Number(latest.milk_yield_l).toFixed(1));
    } else {
      setText("sensorYieldVal", "--");
    }

    // Somatic Cell Count (SCC)
    if (latest.scc_value !== undefined && latest.scc_value !== null) {
      const scc = Math.round(Number(latest.scc_value));
      setText("sensorSccVal", scc.toLocaleString());
      const dot = document.getElementById("sccRefDot");
      if (dot) {
        dot.className = scc >= 200000 ? "ref-status-dot elevated" : "ref-status-dot";
      }
    } else {
      setText("sensorSccVal", "--");
    }

    // Current Heat Index (sensor-derived) — Required Fix #2
    const hi = latest.environment_heat_index;
    if (hi !== undefined && hi !== null) {
      setText("sensorHeatIndexVal", Number(hi).toFixed(1));
      const dot = document.getElementById("heatIndexRefDot");
      if (dot) {
        dot.className = hi >= 75.0 ? "ref-status-dot elevated" : "ref-status-dot";
      }
    } else {
      setText("sensorHeatIndexVal", "--");
    }
  }

  // --------------------------------------------------------------------------
  // 13. §7 Chart Readability Enhancements
  // --------------------------------------------------------------------------
  function renderCharts(history, riskHistory) {
    if (!history || history.length === 0) return;

    const labels = history.map(h => (h.timestamp ? h.timestamp.substring(5, 10) : ""));

    // Common Scale with Explicit "Date" X-Axis Title (§7)
    const commonScales = {
      x: {
        grid: { color: "#f1f5f9" },
        ticks: { font: { size: 10 }, color: "#64748b" },
        title: {
          display: true,
          text: "Date",
          color: "#475569",
          font: { size: 11, weight: "bold" }
        }
      },
      y: {
        grid: { color: "#f1f5f9" },
        ticks: { font: { size: 10 }, color: "#64748b" }
      }
    };

    const commonPlugins = {
      legend: { display: false },
      tooltip: {
        mode: "index",
        intersect: false,
        backgroundColor: "#0f172a",
        titleFont: { size: 11, weight: "bold" },
        bodyFont: { size: 10 },
        padding: 8,
        cornerRadius: 6
      }
    };

    // 1. Calibrated Risk History Chart (Dual Series with Legend)
    const riskCard = document.getElementById("cardChartRisk");
    const riskTab = document.getElementById("tabBtnRisk");

    if (State.isModelActive && riskHistory && riskHistory.length > 0) {
      if (riskCard) riskCard.style.display = "flex";
      if (riskTab) riskTab.style.display = "inline-block";

      const riskLabels = riskHistory.map(r => (r.date ? r.date.substring(5, 10) : ""));
      const r7Data = riskHistory.map(r => r.risk_percent_7d);
      const r14Data = riskHistory.map(r => r.risk_percent_14d);

      if (State.charts.risk) State.charts.risk.destroy();
      const ctxRisk = document.getElementById("chartCanvasRisk").getContext("2d");
      State.charts.risk = new Chart(ctxRisk, {
        type: "line",
        data: {
          labels: riskLabels,
          datasets: [
            {
              label: "7-Day Risk Forecast",
              data: r7Data,
              borderColor: "#dc2626",
              backgroundColor: "rgba(220, 38, 38, 0.06)",
              fill: true,
              tension: 0.25,
              pointRadius: 3,
              pointBackgroundColor: "#dc2626"
            },
            {
              label: "14-Day Risk Forecast",
              data: r14Data,
              borderColor: "#3b82f6",
              backgroundColor: "rgba(59, 130, 246, 0.04)",
              fill: true,
              tension: 0.25,
              pointRadius: 3,
              pointBackgroundColor: "#3b82f6"
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            ...commonPlugins,
            legend: {
              display: true,
              position: "top",
              labels: { boxWidth: 12, font: { size: 11, weight: "bold" } }
            },
            tooltip: {
              ...commonPlugins.tooltip,
              callbacks: {
                label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}%`
              }
            }
          },
          scales: {
            ...commonScales,
            y: {
              ...commonScales.y,
              min: 0,
              max: 100,
              title: {
                display: true,
                text: "Risk Probability (%)",
                color: "#475569",
                font: { size: 11, weight: "bold" }
              }
            }
          }
        }
      });
    } else {
      if (riskCard) riskCard.style.display = "none";
      if (riskTab) riskTab.style.display = "none";
    }

    // 2. Milk Conductivity Chart (Explicit Unit in Y-axis and Tooltip)
    if (State.charts.cond) State.charts.cond.destroy();
    const ctxCond = document.getElementById("chartCanvasCond").getContext("2d");
    State.charts.cond = new Chart(ctxCond, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Conductivity",
          data: history.map(h => h.milk_conductivity),
          borderColor: "#7c3aed",
          backgroundColor: "rgba(124, 58, 237, 0.06)",
          fill: true,
          tension: 0.25,
          pointRadius: 3,
          pointBackgroundColor: "#7c3aed"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          ...commonPlugins,
          tooltip: {
            ...commonPlugins.tooltip,
            callbacks: {
              label: (ctx) => `Conductivity: ${ctx.parsed.y.toFixed(2)} mS/cm`
            }
          }
        },
        scales: {
          ...commonScales,
          y: {
            ...commonScales.y,
            title: {
              display: true,
              text: "Conductivity (mS/cm)",
              color: "#475569",
              font: { size: 11, weight: "bold" }
            }
          }
        }
      }
    });

    // 3. Milk Temperature Chart (Explicit Unit in Y-axis and Tooltip)
    if (State.charts.temp) State.charts.temp.destroy();
    const ctxTemp = document.getElementById("chartCanvasTemp").getContext("2d");
    State.charts.temp = new Chart(ctxTemp, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Milk Temperature",
          data: history.map(h => h.milk_temp_c),
          borderColor: "#ea580c",
          backgroundColor: "rgba(234, 88, 12, 0.06)",
          fill: true,
          tension: 0.25,
          pointRadius: 3,
          pointBackgroundColor: "#ea580c"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          ...commonPlugins,
          tooltip: {
            ...commonPlugins.tooltip,
            callbacks: {
              label: (ctx) => `Temperature: ${ctx.parsed.y.toFixed(1)} °C`
            }
          }
        },
        scales: {
          ...commonScales,
          y: {
            ...commonScales.y,
            title: {
              display: true,
              text: "Temperature (°C)",
              color: "#475569",
              font: { size: 11, weight: "bold" }
            }
          }
        }
      }
    });

    // 4. Somatic Cell Count (SCC) Chart (SpanGaps + Explicit Unit)
    if (State.charts.scc) State.charts.scc.destroy();
    const ctxScc = document.getElementById("chartCanvasScc").getContext("2d");
    State.charts.scc = new Chart(ctxScc, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "SCC",
          data: history.map(h => h.scc_value),
          borderColor: "#0284c7",
          backgroundColor: "rgba(2, 132, 199, 0.06)",
          fill: true,
          spanGaps: true,
          tension: 0.2,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: "#0284c7"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          ...commonPlugins,
          tooltip: {
            ...commonPlugins.tooltip,
            callbacks: {
              label: (ctx) => `SCC: ${ctx.parsed.y ? Math.round(ctx.parsed.y).toLocaleString() : "N/A"} cells/mL`
            }
          }
        },
        scales: {
          ...commonScales,
          y: {
            ...commonScales.y,
            title: {
              display: true,
              text: "SCC (cells/mL)",
              color: "#475569",
              font: { size: 11, weight: "bold" }
            },
            suggestedMax: 400000
          }
        }
      }
    });

    // 5. Daily Milk Yield Chart (Explicit Unit)
    if (State.charts.yield) State.charts.yield.destroy();
    const ctxYield = document.getElementById("chartCanvasYield").getContext("2d");
    State.charts.yield = new Chart(ctxYield, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Daily Yield",
          data: history.map(h => h.milk_yield_l),
          borderColor: "#16a34a",
          backgroundColor: "rgba(22, 163, 74, 0.06)",
          fill: true,
          tension: 0.25,
          pointRadius: 3,
          pointBackgroundColor: "#16a34a"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          ...commonPlugins,
          tooltip: {
            ...commonPlugins.tooltip,
            callbacks: {
              label: (ctx) => `Milk Yield: ${ctx.parsed.y.toFixed(1)} L/day`
            }
          }
        },
        scales: {
          ...commonScales,
          y: {
            ...commonScales.y,
            min: 0,
            title: {
              display: true,
              text: "Milk Yield (L / day)",
              color: "#475569",
              font: { size: 11, weight: "bold" }
            }
          }
        }
      }
    });
  }

  function switchChartTab(mode) {
    State.currentChartMode = mode;

    ["Grid", "Risk", "Cond", "Temp", "Yield", "Scc"].forEach(k => {
      const btn = document.getElementById(`tabBtn${k}`);
      if (btn) {
        if (k.toLowerCase() === mode) {
          btn.classList.add("active");
        } else {
          btn.classList.remove("active");
        }
      }
    });

    const grid = document.getElementById("chartsGridContainer");
    const cards = {
      risk: document.getElementById("cardChartRisk"),
      cond: document.getElementById("cardChartCond"),
      temp: document.getElementById("cardChartTemp"),
      yield: document.getElementById("cardChartYield"),
      scc: document.getElementById("cardChartScc")
    };

    if (mode === "grid") {
      grid.classList.remove("single-mode");
      Object.keys(cards).forEach(k => {
        if (cards[k]) {
          if (k === "risk" && !State.isModelActive) {
            cards[k].style.display = "none";
          } else {
            cards[k].style.display = "flex";
          }
        }
      });
    } else {
      grid.classList.add("single-mode");
      Object.keys(cards).forEach(k => {
        if (cards[k]) {
          cards[k].style.display = k === mode ? "flex" : "none";
        }
      });
    }
  }

  // --------------------------------------------------------------------------
  // 14. §6 & §9a Explainability & Categorized Recommendations
  // --------------------------------------------------------------------------
  function renderExplainability(risk) {
    const driversList = document.getElementById("topDriversList");
    const recsList = document.getElementById("recommendationsList");

    if (!driversList || !recsList) return;

    // 1. Render SHAP Driver Bars
    const drivers = (risk && risk.top_driver_features) ? risk.top_driver_features : [];

    if (drivers.length === 0) {
      driversList.innerHTML = `
        <div class="state-container" style="padding:16px;">
          <span class="state-desc">${t("noDrivers")}</span>
        </div>`;
    } else {
      const maxImpact = Math.max(...drivers.map(d => Math.abs(d.impact)), 0.0001);
      driversList.innerHTML = drivers.map(d => {
        const absImpact = Math.abs(d.impact);
        const barPct = Math.min(Math.max((absImpact / maxImpact) * 100, 12), 100);
        const isRiskIncreasing = d.impact >= 0;
        const barClass = isRiskIncreasing ? "positive-risk" : "mitigating";
        const signStr = isRiskIncreasing ? "+" : "";

        return `
          <div class="driver-item-row">
            <div class="driver-meta">
              <span class="driver-name">${escapeHtml(formatFeatureName(d.feature))}</span>
              <span class="driver-val">${signStr}${d.impact.toFixed(4)}</span>
            </div>
            <div class="driver-bar-track">
              <div class="driver-bar-fill ${barClass}" style="width: ${barPct}%;"></div>
            </div>
          </div>`;
      }).join("");
    }

    // 2. Render Categorized Recommendations (§6 Biosecurity + §9a SHAP)
    let recsHtml = "";

    // Prefer recommendations_detailed if present
    if (risk && risk.recommendations_detailed && risk.recommendations_detailed.length > 0) {
      recsHtml = risk.recommendations_detailed.map(r => {
        let catClass = "cat-clinical";
        let catLabel = "Clinical";
        if (r.category === "biosecurity") {
          catClass = "cat-biosecurity";
          catLabel = "Biosecurity";
        } else if (r.category === "management") {
          catClass = "cat-management";
          catLabel = "Management";
        }

        return `
          <div class="rec-item">
            <span class="rec-category-badge ${catClass}">${catLabel}</span>
            <span>${escapeHtml(r.text)}</span>
          </div>`;
      }).join("");
    } else if (risk && risk.recommendations && risk.recommendations.length > 0) {
      // Fallback to legacy string recommendations
      recsHtml = risk.recommendations.map(r => `
        <div class="rec-item">
          <span class="rec-category-badge cat-clinical">Clinical</span>
          <span>${escapeHtml(r)}</span>
        </div>`).join("");
    } else {
      recsHtml = `
        <div class="rec-item">
          <span class="rec-icon">✓</span>
          <span>${t("noRecs")}</span>
        </div>`;
    }

    // Append §9a SHAP driver recommendations if available
    if (risk && risk.driver_recommendations && risk.driver_recommendations.length > 0) {
      const shapRecs = risk.driver_recommendations.slice(0, 3).map(dr => `
        <div class="rec-item" style="border-left-color: var(--brand-accent);">
          <span class="rec-category-badge cat-shap">SHAP Driver</span>
          <span>${escapeHtml(dr.text)}</span>
        </div>`).join("");
      recsHtml += shapRecs;
    }

    recsList.innerHTML = recsHtml;
  }

  function formatFeatureName(raw) {
    if (!raw) return "";
    let name = raw.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
    name = name.replace(/Scc/g, "SCC")
      .replace(/Temp C/g, "Temp (°C)")
      .replace(/Yield L/g, "Yield (L)")
      .replace(/Ph/g, "pH")
      .replace(/Delta/g, "Δ");
    return name;
  }

  // --------------------------------------------------------------------------
  // 15. Herd Surveillance Matrix Table
  // --------------------------------------------------------------------------
  function renderHerdTable() {
    const tbody = document.getElementById("herdTableBody");
    const searchInput = document.getElementById("cowSearchInput");
    if (!tbody) return;

    const query = (searchInput ? searchInput.value : "").toLowerCase().trim();

    const filtered = State.registeredCows.filter(c => {
      if (!query) return true;
      return (
        (c.cow_id && c.cow_id.toLowerCase().includes(query)) ||
        (c.breed && c.breed.toLowerCase().includes(query)) ||
        (c.location_label && c.location_label.toLowerCase().includes(query))
      );
    });

    if (filtered.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="state-container">
            <span class="state-desc">${t("noCowsFound")}</span>
          </td>
        </tr>`;
      return;
    }

    const rowsHtml = filtered.map(cow => {
      const risk = State.herdRiskList.find(r => r.cow_id === cow.cow_id) || {};
      const t7 = risk.risk_tier_7d || "No Risk";
      const p7 = risk.risk_percent_7d !== undefined ? `${risk.risk_percent_7d.toFixed(1)}%` : "-";
      const t14 = risk.risk_tier_14d || "No Risk";
      const p14 = risk.risk_percent_14d !== undefined ? `${risk.risk_percent_14d.toFixed(1)}%` : "-";
      const days = risk.data_days !== undefined ? `${risk.data_days}d` : "-";

      const drivers = (risk.top_driver_features || []).slice(0, 3);
      const driverChips = drivers.map(d => `<span class="driver-chip">${escapeHtml(formatFeatureName(d.feature))}</span>`).join("");

      const isSelected = cow.cow_id === State.selectedCowId;
      const activeClass = isSelected ? "active-row" : "";

      return `
        <tr data-cow-id="${escapeHtml(cow.cow_id)}" class="${activeClass}" onclick="window.MastiSenseApp.selectCow('${escapeHtml(cow.cow_id)}', true)">
          <td>
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="cow-badge-avatar" style="width:28px; height:28px; font-size:0.75rem;">${escapeHtml(cow.cow_id)}</span>
              <b>${escapeHtml(cow.cow_id)}</b>
            </div>
          </td>
          <td>${escapeHtml(cow.breed || "Crossbreed")} <span style="color:var(--text-muted); font-size:0.75rem;">(P${cow.parity})</span></td>
          <td><span class="risk-tier-badge tier-${t7.replace(/\s+/g, "")}">${t7} (${p7})</span></td>
          <td><span class="risk-tier-badge tier-${t14.replace(/\s+/g, "")}">${t14} (${p14})</span></td>
          <td><span style="font-size:0.8rem; font-weight:600;">${days}</span></td>
          <td><div class="driver-chips-wrapper">${driverChips || '<span style="color:var(--text-muted); font-size:0.72rem;">Nominal</span>'}</div></td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); window.MastiSenseApp.selectCow('${escapeHtml(cow.cow_id)}', true)">
              ${t("inspectBtn")}
            </button>
          </td>
        </tr>`;
    }).join("");

    tbody.innerHTML = rowsHtml;
  }

  // --------------------------------------------------------------------------
  // 16. §8 Notifications Center Manager
  // --------------------------------------------------------------------------
  function switchNotifTab(mode) {
    State.activeNotifTab = mode;

    ["risk", "climate", "recs", "log"].forEach(k => {
      const btn = document.getElementById(`notifTabBtn${k.charAt(0).toUpperCase() + k.slice(1)}`);
      const content = document.getElementById(`notifContent${k.charAt(0).toUpperCase() + k.slice(1)}`);

      if (btn) {
        if (k === mode) btn.classList.add("active");
        else btn.classList.remove("active");
      }
      if (content) {
        content.style.display = k === mode ? "block" : "none";
      }
    });

    if (mode === "climate" && !State.weatherAdvisories) {
      loadClimateAdvisories();
    } else if (mode === "log" && State.notificationLogs.length === 0) {
      loadNotificationLogs();
    }
  }

  async function loadClimateAdvisories() {
    try {
      const data = await ApiClient.getWeatherAdvisory();
      State.weatherAdvisories = data;
      renderClimateTab(data);
    } catch (e) {
      console.error("[Weather Advisory Error]:", e);
    }
  }

  async function loadNotificationLogs() {
    try {
      const logs = await ApiClient.getNotificationLog(30);
      State.notificationLogs = logs;
      renderNotificationLogs(logs);
    } catch (e) {
      console.error("[Notif Log Error]:", e);
    }
  }

  function renderNotificationsCenter() {
    // 1. Acute Risk Watch List (Moderate + High cows)
    const acuteList = document.getElementById("acuteRiskList");
    let acuteCount = 0;

    if (acuteList) {
      const acuteCows = State.herdRiskList.filter(r => {
        return (
          r.risk_tier_7d === "High Risk" ||
          r.risk_tier_7d === "Moderate Risk" ||
          r.risk_tier_14d === "High Risk" ||
          r.risk_tier_14d === "Moderate Risk"
        );
      });
      acuteCount = acuteCows.length;

      if (acuteCows.length === 0) {
        acuteList.innerHTML = `
          <div class="state-container" style="padding:24px; grid-column:1/-1;">
            <span class="state-desc">✓ All cows currently monitored are in the healthy/low-risk tier.</span>
          </div>`;
      } else {
        acuteList.innerHTML = acuteCows.map(r => {
          const isHigh = r.risk_tier_7d === "High Risk" || r.risk_tier_14d === "High Risk";
          const cardClass = isHigh ? "acute-risk-card high" : "acute-risk-card mod";
          const cowId = escapeHtml(r.cow_id);

          return `
            <div class="${cardClass}">
              <div class="acute-card-top">
                <span class="acute-cow-id">🐄 Cow ${cowId}</span>
                <span class="risk-tier-badge tier-${(r.risk_tier_7d || "").replace(/\s+/g, "")}">
                  7d: ${r.risk_tier_7d}
                </span>
              </div>
              <div class="acute-forecast-row">
                <div class="acute-forecast-item">
                  <span class="acute-forecast-lbl">7-Day Horizon:</span>
                  <span class="acute-forecast-val" style="color:${getTierColor(r.risk_tier_7d)};">
                    ${r.risk_percent_7d ? r.risk_percent_7d.toFixed(1) : "-"}%
                  </span>
                </div>
                <div class="acute-forecast-item">
                  <span class="acute-forecast-lbl">14-Day Horizon:</span>
                  <span class="acute-forecast-val" style="color:${getTierColor(r.risk_tier_14d)};">
                    ${r.risk_percent_14d ? r.risk_percent_14d.toFixed(1) : "-"}%
                  </span>
                </div>
              </div>
              <div style="font-size:0.75rem; color:var(--text-muted);">
                ${r.data_days} accumulated days • ${r.recommendations ? r.recommendations.length : 0} active protocols
              </div>
              <button class="btn btn-secondary btn-sm" style="margin-top:auto;" onclick="window.MastiSenseApp.selectCow('${cowId}', true); location.hash='#cow-analysis';">
                Inspect Cow
              </button>
            </div>`;
        }).join("");
      }
    }

    // 2. Update Sidebar Badge
    const badge = document.getElementById("notifNavBadge");
    const openAlerts = State.alertsList.filter(a => a.status === "open").length;
    const totalNotifs = acuteCount + openAlerts;

    if (badge) {
      if (totalNotifs > 0) {
        badge.style.display = "inline-block";
        badge.textContent = totalNotifs;
      } else {
        badge.style.display = "none";
      }
    }

    // 3. Digest tab: Group recommendations across herd
    renderRecommendationsDigest();

    // 4. Climate Tab: load if not yet fetched
    if (!State.weatherAdvisories) {
      loadClimateAdvisories();
    } else {
      renderClimateTab(State.weatherAdvisories);
    }

    // 5. Render logs if available
    renderNotificationLogs(State.notificationLogs);
  }

  function renderClimateTab(data) {
    if (!data) return;

    const badge = document.getElementById("thiStressBadge");
    const peakEl = document.getElementById("peakThiVal");
    const stressEl = document.getElementById("stressHoursVal");
    const periodEl = document.getElementById("forecastPeriodVal");
    const summaryEl = document.getElementById("climateAdvisorySummary");
    const feed = document.getElementById("weatherAdvisoriesList");

    if (data.heat_stress) {
      const hs = data.heat_stress;
      if (peakEl) peakEl.textContent = hs.peak_thi ? `${hs.peak_thi}` : "--";
      if (stressEl) stressEl.textContent = `${hs.stress_hours || 0} hrs`;
      if (periodEl) periodEl.textContent = "7 Days";

      if (badge) {
        const lvl = hs.peak_level || "normal";
        if (lvl === "severe_stress") {
          badge.className = "thi-badge badge-severe";
          badge.textContent = "Severe Heat Stress";
        } else if (lvl === "moderate_stress") {
          badge.className = "thi-badge badge-mod";
          badge.textContent = "Moderate Heat Stress";
        } else if (lvl === "mild_stress") {
          badge.className = "thi-badge badge-mild";
          badge.textContent = "Mild Heat Stress";
        } else {
          badge.className = "thi-badge badge-normal";
          badge.textContent = "Normal Comfort Zone";
        }
      }

      if (summaryEl) {
        summaryEl.textContent = hs.advisory_text || "Forecast within normal dairy comfort zone.";
      }
    } else if (!data.configured) {
      if (badge) {
        badge.className = "thi-badge badge-mild";
        badge.textContent = "Location Needed";
      }
      if (summaryEl) {
        summaryEl.textContent = "Farm coordinates are not yet configured. Set cow GPS locations on the Farm Map to activate automated Open-Meteo climate surveillance.";
      }
    }

    // Advisories Feed
    if (feed && data.advisories) {
      feed.innerHTML = data.advisories.map(adv => {
        return `
          <div class="advisory-card ${adv.type}">
            <span style="font-size:1.4rem;">${getAdvisoryIcon(adv.type)}</span>
            <div style="display:flex; flex-direction:column; gap:2px;">
              <div style="font-size:0.8rem; font-weight:800; color:var(--text-main);">
                ${adv.type.toUpperCase().replace(/_/g, " ")} ${adv.date ? "(" + adv.date + ")" : ""}
              </div>
              <div style="font-size:0.75rem; color:var(--text-secondary); line-height:1.4;">
                ${escapeHtml(adv.text)}
              </div>
            </div>
          </div>`;
      }).join("");
    }
  }

  function getAdvisoryIcon(type) {
    if (type === "heat_stress") return "☀️";
    if (type === "humidity") return "💧";
    if (type === "rainfall") return "🌧️";
    return "ℹ️";
  }

  function renderRecommendationsDigest() {
    const container = document.getElementById("recsDigestList");
    if (!container) return;

    const clinicalMap = new Map();
    const biosecurityMap = new Map();
    const managementMap = new Map();

    State.herdRiskList.forEach(r => {
      const cid = r.cow_id;
      if (r.recommendations_detailed) {
        r.recommendations_detailed.forEach(item => {
          const map = item.category === "biosecurity"
            ? biosecurityMap
            : item.category === "management"
            ? managementMap
            : clinicalMap;

          if (!map.has(item.text)) map.set(item.text, []);
          map.get(item.text).push(cid);
        });
      }
    });

    const renderGroup = (title, icon, map, badgeClass) => {
      if (map.size === 0) return "";
      const itemsHtml = Array.from(map.entries()).map(([text, cows]) => `
        <div class="digest-item-row">
          <span>→</span>
          <div>
            <b>${escapeHtml(text)}</b>
            <div style="font-size:0.72rem; color:var(--text-muted); margin-top:2px;">
              Applicable to: ${cows.slice(0, 5).map(c => `<code>${escapeHtml(c)}</code>`).join(", ")} ${cows.length > 5 ? `(+${cows.length - 5} more)` : ""}
            </div>
          </div>
        </div>`).join("");

      return `
        <div class="digest-category-block">
          <div class="digest-category-header">
            <span>${icon}</span>
            <span>${title} (${map.size} Actionable Rules)</span>
          </div>
          <div class="digest-items-list">${itemsHtml}</div>
        </div>`;
    };

    let html = "";
    html += renderGroup("Biosecurity & Quarantine Protocols (§6)", "🛡️", biosecurityMap, "cat-biosecurity");
    html += renderGroup("Clinical Veterinary Directives", "🩺", clinicalMap, "cat-clinical");
    html += renderGroup("Housing & Environmental Management", "🚜", managementMap, "cat-management");

    if (!html) {
      container.innerHTML = `
        <div class="state-container" style="padding:20px;">
          <span class="state-desc">No acute recommendations currently triggered for the herd.</span>
        </div>`;
    } else {
      container.innerHTML = html;
    }
  }

  function renderNotificationLogs(logs) {
    const tbody = document.getElementById("notifLogTableBody");
    if (!tbody) return;

    if (!logs || logs.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="state-container"><span class="state-desc">No dispatch logs recorded yet.</span></td>
        </tr>`;
      return;
    }

    tbody.innerHTML = logs.map(l => {
      const statusPill = l.success === 1
        ? '<span style="color:#16a34a; font-weight:700;">✓ Delivered</span>'
        : '<span style="color:#dc2626; font-weight:700;">⚠ Failed</span>';

      return `
        <tr>
          <td><code>#${l.id}</code></td>
          <td>${l.alert_id ? "#" + l.alert_id : "-"}</td>
          <td><span class="status-pill pill-synthetic">${escapeHtml(l.channel)}</span></td>
          <td>${statusPill}</td>
          <td>${l.created_at ? l.created_at.substring(0, 19).replace("T", " ") : "-"}</td>
        </tr>`;
    }).join("");
  }

  async function sendTestNotification() {
    const btn = document.getElementById("btnTestNotif");
    if (btn) btn.disabled = true;

    try {
      const res = await ApiClient.sendTestNotification();
      showToast("Test webhook notification triggered!");
      await loadNotificationLogs();
    } catch (e) {
      showToast("Test webhook dispatch failed: " + e.message, true);
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  // --------------------------------------------------------------------------
  // 17. §10 GIS Farm & Herd Map View with ~2km Throttle Gate Confirmation
  // --------------------------------------------------------------------------
  const MapManager = {
    map: null,
    cowLayer: null,
    vetLayer: null,
    userMarker: null,
    watchId: null,

    init() {
      const mapFrame = document.getElementById("mapContainer");
      if (!mapFrame || this.map || typeof L === "undefined") return;

      // Default center: India or first cow's coordinates
      const defaultLat = 13.0827;
      const defaultLon = 80.2707;

      this.map = L.map("mapContainer").setView([defaultLat, defaultLon], 13);
      State.activeMap = this.map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
      }).addTo(this.map);

      this.cowLayer = L.layerGroup().addTo(this.map);
      this.vetLayer = L.layerGroup().addTo(this.map);

      this.plotCows();
    },

    async plotCows() {
      if (!this.map) return;
      this.cowLayer.clearLayers();

      try {
        const locations = await ApiClient.getCowLocations();
        if (locations.length === 0) return;

        const bounds = [];

        locations.forEach(c => {
          const risk = State.herdRiskList.find(r => r.cow_id === c.cow_id) || {};
          const t7 = risk.risk_tier_7d || "No Risk";
          const color = getTierColor(t7);

          const marker = L.circleMarker([c.latitude, c.longitude], {
            radius: 9,
            fillColor: color,
            color: "#ffffff",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.9
          });

          const popupContent = `
            <div style="font-family:var(--font-family); font-size:0.8rem; padding:4px;">
              <b>🐄 Cow ${escapeHtml(c.cow_id)}</b><br>
              <span>${escapeHtml(c.location_label || "Pasture")}</span><br>
              <span style="color:${color}; font-weight:800;">7d Risk: ${t7}</span><br>
              <button onclick="window.MastiSenseApp.selectCow('${escapeHtml(c.cow_id)}', true); location.hash='#cow-analysis';" style="margin-top:6px; font-size:0.7rem; padding:2px 8px; cursor:pointer;">
                Inspect Telemetry
              </button>
            </div>`;

          marker.bindPopup(popupContent);
          this.cowLayer.addLayer(marker);
          bounds.push([c.latitude, c.longitude]);
        });

        if (bounds.length > 0 && !State.userLocationCenter) {
          this.map.fitBounds(bounds, { padding: [30, 30], maxZoom: 15 });
        }
      } catch (e) {
        console.error("[Plot Cows Error]:", e);
      }
    },

    /**
     * CRITICAL USER REQUIREMENT:
     * Wired ~2km movement throttle gate inside watchPosition callback
     * to prevent GPS jitter from spamming Overpass API!
     */
    useMyLocation() {
      if (!navigator.geolocation) {
        showToast("Geolocation is not supported by this browser.", true);
        return;
      }

      showToast("Activating browser GPS positioning...");

      if (this.watchId !== null) {
        navigator.geolocation.clearWatch(this.watchId);
      }

      this.watchId = navigator.geolocation.watchPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;

          // Check movement throttle gate
          if (State.lastGpsPosition) {
            const distKm = haversineDistance(
              State.lastGpsPosition.lat,
              State.lastGpsPosition.lon,
              lat,
              lon
            );

            // GATING CONDITION: Throttle re-queries if movement < 2.0 km
            if (distKm < 2.0) {
              console.log(`[GIS Throttle Gate] Movement: ${distKm.toFixed(3)} km (< 2.0 km throttle threshold). Skipping Overpass API re-query.`);
              this.updateUserMarker(lat, lon);
              return;
            } else {
              console.log(`[GIS Throttle Gate] Movement: ${distKm.toFixed(3)} km (>= 2.0 km threshold). Re-querying Overpass API nearby vets.`);
            }
          }

          // Update position center and trigger nearby vets
          State.lastGpsPosition = { lat, lon };
          State.userLocationCenter = { lat, lon };

          this.updateUserMarker(lat, lon);
          this.findNearbyVets(lat, lon);
        },
        (err) => {
          console.warn("[GPS Error]:", err);
          showToast(`GPS position unavailable: ${err.message}`, true);
        },
        { enableHighAccuracy: true, maximumAge: 10000, timeout: 15000 }
      );
    },

    updateUserMarker(lat, lon) {
      if (!this.map) return;

      const coordsBadge = document.getElementById("activeMapCoords");
      if (coordsBadge) {
        coordsBadge.textContent = `${lat.toFixed(4)}, ${lon.toFixed(4)} (GPS)`;
      }

      if (this.userMarker) {
        this.userMarker.setLatLng([lat, lon]);
      } else {
        this.userMarker = L.circleMarker([lat, lon], {
          radius: 11,
          fillColor: "#3b82f6",
          color: "#ffffff",
          weight: 3,
          opacity: 1,
          fillOpacity: 0.9
        }).bindPopup("<b>📍 Current Position</b>").addTo(this.map);
      }

      this.map.setView([lat, lon], 13);
    },

    async findNearbyVets(customLat, customLon) {
      if (!this.map) return;

      let lat = customLat;
      let lon = customLon;

      if (lat === undefined || lon === undefined) {
        if (State.userLocationCenter) {
          lat = State.userLocationCenter.lat;
          lon = State.userLocationCenter.lon;
        } else {
          // Use current map center
          const c = this.map.getCenter();
          lat = c.lat;
          lon = c.lng;
        }
      }

      const radius = State.activeVetRadius || 5;
      const btn = document.getElementById("btnFindVets");
      const listEl = document.getElementById("vetsList");
      const badgeEl = document.getElementById("vetsCountBadge");

      if (btn) btn.disabled = true;
      if (listEl) {
        listEl.innerHTML = `<div class="state-container" style="padding:20px;"><span class="state-desc">Querying OpenStreetMap Overpass API within ${radius} km...</span></div>`;
      }

      try {
        const data = await ApiClient.getNearbyVets(lat, lon, radius);
        const vets = data.vets || [];

        if (badgeEl) badgeEl.textContent = `${vets.length} Found`;

        this.vetLayer.clearLayers();

        if (vets.length === 0) {
          if (listEl) {
            listEl.innerHTML = `
              <div class="state-container" style="padding:20px;">
                <span class="state-desc">No veterinary clinics found within ${radius} km radius on OpenStreetMap. Try expanding the search radius.</span>
              </div>`;
          }
          return;
        }

        // Plot vets
        vets.forEach(v => {
          const vetMarker = L.marker([v.latitude, v.longitude], {
            title: v.name
          });

          const popup = `
            <div style="font-family:var(--font-family); font-size:0.78rem;">
              <b>🏥 ${escapeHtml(v.name)}</b><br>
              <span>Distance: ${v.distance_km} km</span><br>
              ${v.phone ? `<span>📞 ${escapeHtml(v.phone)}</span><br>` : ""}
              ${v.address ? `<span>📍 ${escapeHtml(v.address)}</span>` : ""}
            </div>`;

          vetMarker.bindPopup(popup);
          this.vetLayer.addLayer(vetMarker);
        });

        // Populate list
        if (listEl) {
          listEl.innerHTML = vets.map(v => `
            <div class="vet-item-card">
              <span class="vet-item-name">${escapeHtml(v.name)}</span>
              <span class="vet-item-dist">📍 ${v.distance_km} km away</span>
              ${v.phone ? `<span class="vet-item-phone">📞 ${escapeHtml(v.phone)}</span>` : ""}
              ${v.address ? `<span style="font-size:0.68rem; color:var(--text-muted);">${escapeHtml(v.address)}</span>` : ""}
            </div>`).join("");
        }

        showToast(`Found ${vets.length} veterinary services within ${radius} km`);
      } catch (e) {
        console.error("[Find Vets Error]:", e);
        showToast("Overpass API query failed: " + e.message, true);
      } finally {
        if (btn) btn.disabled = false;
      }
    }
  };

  function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth radius in km
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * (Math.PI / 180)) *
        Math.cos(lat2 * (Math.PI / 180)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  function updateVetRadius(val) {
    State.activeVetRadius = Number(val);
    const display = document.getElementById("vetRadiusDisplay");
    if (display) display.textContent = `${val} km`;
  }

  function toggleCoordForm() {
    const box = document.getElementById("cowCoordFormBox");
    if (box) {
      box.style.display = box.style.display === "none" ? "block" : "none";
    }
  }

  async function saveCowLocation() {
    const cowSelect = document.getElementById("mapCowSelect");
    const latInput = document.getElementById("mapCowLat");
    const lonInput = document.getElementById("mapCowLon");
    const labelInput = document.getElementById("mapCowLabel");

    if (!cowSelect || !latInput || !lonInput) return;

    const cowId = cowSelect.value;
    const lat = parseFloat(latInput.value);
    const lon = parseFloat(lonInput.value);
    const label = labelInput ? labelInput.value.trim() : "";

    if (isNaN(lat) || isNaN(lon)) {
      showToast("Please enter valid latitude and longitude numbers", true);
      return;
    }

    try {
      await ApiClient.updateCowLocation(cowId, lat, lon, label);
      showToast(`Coordinates saved for Cow ${cowId}!`);
      toggleCoordForm();
      if (MapManager.map) {
        MapManager.plotCows();
      }
    } catch (e) {
      showToast("Failed to save coordinates: " + e.message, true);
    }
  }

  // --------------------------------------------------------------------------
  // 18. Alerts Management
  // --------------------------------------------------------------------------
  function renderAlerts() {
    const container = document.getElementById("alertsContainer");
    if (!container) return;

    if (!State.alertsList || State.alertsList.length === 0) {
      container.innerHTML = `
        <div class="state-container">
          <span class="state-desc">${t("noAlerts")}</span>
        </div>`;
      return;
    }

    const cardsHtml = State.alertsList.map(a => {
      const isResolved = a.status === "resolved";
      const statusClass = isResolved ? "resolved" : "open";
      const scorePct = (a.risk_score * 100).toFixed(1);

      return `
        <div class="alert-card-item ${statusClass}">
          <div class="alert-card-header">
            <div class="alert-cow-badge">🐄 Cow ${escapeHtml(a.cow_id)}</div>
            <span class="alert-score-badge">${scorePct}% Risk</span>
          </div>
          <div class="alert-meta-time">${escapeHtml(a.timestamp ? a.timestamp.substring(0, 19).replace("T", " ") : "")}</div>
          <div class="alert-msg-body">${escapeHtml(a.message)}</div>
          ${
            isResolved
              ? `<div class="alert-resolved-note">
                   <b>Resolved:</b> ${escapeHtml(a.resolved_note || "Resolved")} 
                   <span style="font-size:0.7rem; color:var(--text-muted);">(${escapeHtml(a.resolved_at ? a.resolved_at.substring(0, 16).replace("T", " ") : "")})</span>
                 </div>`
              : `<div style="margin-top: 10px;">
                   <button class="btn btn-secondary btn-sm" onclick="window.MastiSenseApp.toggleResolveBox(${a.id}, true)">
                     ${t("resolveBtn")}
                   </button>
                   <div class="alert-resolve-box" id="resolveBox_${a.id}" style="display:none;">
                     <input type="text" id="resolveInput_${a.id}" class="search-field-input" placeholder="${t("resolvePlaceholder")}" style="border: 1px solid var(--border-medium); border-radius: var(--radius-xs); padding: 4px 8px; font-size: 0.75rem;">
                     <div style="display:flex; gap:6px;">
                       <button class="btn btn-primary btn-sm" onclick="window.MastiSenseApp.confirmResolveAlert(${a.id})">${t("confirmResolveBtn")}</button>
                       <button class="btn btn-secondary btn-sm" onclick="window.MastiSenseApp.toggleResolveBox(${a.id}, false)">${t("cancelBtn")}</button>
                     </div>
                   </div>
                 </div>`
          }
        </div>`;
    }).join("");

    container.innerHTML = cardsHtml;
  }

  function toggleResolveBox(alertId, show) {
    const box = document.getElementById(`resolveBox_${alertId}`);
    if (box) box.style.display = show ? "flex" : "none";
  }

  async function confirmResolveAlert(alertId) {
    const input = document.getElementById(`resolveInput_${alertId}`);
    const note = input ? input.value.trim() : "";

    const ok = await ApiClient.resolveAlert(alertId, note);
    if (ok) {
      showToast(`Alert #${alertId} marked as resolved`);
      await refreshData(true);
    } else {
      showToast("Failed to resolve alert", true);
    }
  }

  async function evaluateAlertsNow() {
    const btn = document.getElementById("btnEvalAlerts");
    if (btn) btn.disabled = true;

    try {
      const res = await ApiClient.checkAlerts();
      if (res.status === "skipped") {
        showToast(res.note || "Alert check skipped: no validated model", true);
      } else {
        showToast(`Evaluation complete: ${res.new_alerts_created} new alerts triggered`);
        await refreshData(true);
      }
    } catch (e) {
      showToast("Evaluation error: " + e.message, true);
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  // --------------------------------------------------------------------------
  // 19. Governance & Drift Audit
  // --------------------------------------------------------------------------
  function renderAuditTable() {
    const tbody = document.getElementById("auditTableBody");
    if (!tbody) return;

    if (State.candidateSummaries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="state-container">No model candidates found in models/</td></tr>`;
      return;
    }

    tbody.innerHTML = State.candidateSummaries.map(c => {
      const isPromoted = c.status === "promoted";
      const statusBadge = isPromoted
        ? '<span class="status-pill pill-active-model">Promoted</span>'
        : '<span class="status-pill pill-audit-mode">Rejected</span>';

      const m7 = c.metrics_7d || {};
      const m14 = c.metrics_14d || {};

      const str7 = m7.auc ? `AUC: ${m7.auc.toFixed(3)} | Recall: ${(m7.recall * 100).toFixed(1)}%` : "-";
      const str14 = m14.auc ? `AUC: ${m14.auc.toFixed(3)} | Recall: ${(m14.recall * 100).toFixed(1)}%` : "-";

      const reasons = (c.reasons || []).map(r => `<div style="font-size:0.7rem; color:var(--text-muted);">• ${escapeHtml(r)}</div>`).join("");

      return `
        <tr>
          <td><b>${escapeHtml(c.version)}</b></td>
          <td><span style="font-size:0.75rem;">${str7}</span></td>
          <td><span style="font-size:0.75rem;">${str14}</span></td>
          <td>${statusBadge}</td>
          <td>${reasons || "-"}</td>
        </tr>`;
    }).join("");
  }

  function renderGovernanceMetrics() {
    const m = State.metrics["7d"] || {};
    const auc = m.auc ? m.auc.toFixed(3) : "-";
    const recallVal = m.sensitivity_recall !== undefined ? m.sensitivity_recall : m.recall;
    const recall = recallVal !== undefined ? `${(recallVal * 100).toFixed(1)}%` : "-";
    const spec = m.specificity ? `${(m.specificity * 100).toFixed(1)}%` : "-";

    setText("govAucVal", auc);
    setText("govAucSub", m.auc ? "Valid holdout split" : "Pending");

    setText("govRecallVal", recall);
    setText("govRecallSub", "Target floor: 80.0%");

    setText("govSpecVal", spec);
    setText("govSpecSub", "Clinical specificity");

    if (m.brier_score && m.baseline_logistic_brier) {
      const delta = m.baseline_logistic_brier - m.brier_score;
      setText("govBrierVal", `${(delta * 100).toFixed(2)}%`);
      setText("govBrierSub", "vs baseline log-reg");
    } else {
      setText("govBrierVal", "-");
      setText("govBrierSub", "Calibration");
    }
  }

  function renderDriftStatus() {
    const textEl = document.getElementById("driftStatusText");
    if (!textEl) return;

    const r = State.driftReport;
    if (!r || !r.status) {
      textEl.innerHTML = '<span class="status-pill pill-synthetic">STABLE</span> No anomalous sensor drift detected across 30-day baseline.';
      return;
    }

    const pillClass = r.status === "stable" ? "pill-active-model" : "pill-audit-mode";
    textEl.innerHTML = `<span class="status-pill ${pillClass}">${r.status.toUpperCase()}</span> Evaluated across ${r.days || 30} days of continuous sensor records.`;
  }

  function renderErrorState(message) {
    const tbody = document.getElementById("herdTableBody");
    const alerts = document.getElementById("alertsContainer");
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="7" class="state-container" style="color:var(--risk-high-solid); padding:24px;">⚠ ${escapeHtml(message)}</td></tr>`;
    }
    if (alerts) {
      alerts.innerHTML = `<div class="state-container" style="color:var(--risk-high-solid); padding:24px;">⚠ ${escapeHtml(message)}</div>`;
    }
  }

  // --------------------------------------------------------------------------
  // 20. API Base URL Config Dialog
  // --------------------------------------------------------------------------
  function openApiModal() {
    const modal = document.getElementById("apiModalBackdrop");
    const input = document.getElementById("modalApiInput");
    if (input) input.value = State.apiBase;
    if (modal) modal.style.display = "flex";
  }

  function closeApiModal() {
    const modal = document.getElementById("apiModalBackdrop");
    if (modal) modal.style.display = "none";
  }

  function saveApiBase() {
    const input = document.getElementById("modalApiInput");
    if (input && input.value.trim()) {
      let base = input.value.trim().replace(/\/+$/, "");
      State.apiBase = base;
      localStorage.setItem("mastitis_api_base", base);
      closeApiModal();
      showToast(`Target API set to ${base}`);
      refreshData(false);
      ApiClient.initEventStream();
    }
  }

  // --------------------------------------------------------------------------
  // 21. Navigation Setup
  // --------------------------------------------------------------------------
  function setupNavigation() {
    const navLinks = document.querySelectorAll(".sidebar-nav .nav-link");
    const sidebar = document.getElementById("appSidebar");
    const toggleBtn = document.getElementById("sidebarToggleBtn");

    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener("click", () => {
        sidebar.classList.toggle("mobile-open");
      });
    }

    const updateActiveNav = () => {
      const hash = window.location.hash || "#overview";
      navLinks.forEach(link => {
        if (link.getAttribute("href") === hash) {
          link.classList.add("active");
        } else {
          link.classList.remove("active");
        }
      });

      // Lazy load GIS Map when navigating to #farm-map
      if (hash === "#farm-map") {
        setTimeout(() => {
          MapManager.init();
        }, 100);
      }
    };

    window.addEventListener("hashchange", updateActiveNav);
    updateActiveNav();
  }

  // --------------------------------------------------------------------------
  // 22. Application Bootstrap
  // --------------------------------------------------------------------------
  function init() {
    setupNavigation();
    applyLanguage();
    refreshData(true);

    // Attach search event
    const search = document.getElementById("cowSearchInput");
    if (search) {
      search.addEventListener("input", renderHerdTable);
    }

    // Connect real-time Server-Sent Events stream (§4)
    ApiClient.initEventStream();

    // 30-Second Polling Fallback Timer (§4)
    setInterval(() => {
      refreshData(true);
    }, 30000);
  }

  // Public Namespace
  window.MastiSenseApp = {
    init,
    refreshData,
    setLanguage,
    toggleLanguage,
    selectCow,
    switchChartTab,
    switchNotifTab,
    useMyLocation: () => MapManager.useMyLocation(),
    findNearbyVets: () => MapManager.findNearbyVets(),
    updateVetRadius,
    toggleCoordForm,
    saveCowLocation,
    sendTestNotification,
    toggleResolveBox,
    confirmResolveAlert,
    evaluateAlertsNow,
    openApiModal,
    closeApiModal,
    saveApiBase
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
