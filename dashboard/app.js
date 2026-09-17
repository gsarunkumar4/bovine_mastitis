/**
 * ============================================================================
 * MastiSense — Precision Agriculture & AI-IoT Monitoring Dashboard
 * Modular Client-Side Application Logic (app.js)
 * ============================================================================
 */

(function () {
  "use strict";

  // --------------------------------------------------------------------------
  // 1. Centralized Bilingual Dictionary (English / தமிழ்)
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
      noCowsFound: "No cows registered in the database yet.",
      alertsTitle: "Active Alerts & Incident Center",
      alertsSubtitle: "Real-time alerts triggered by high risk forecasts or critical sensor anomalies",
      noAlerts: "No active alerts. Herd parameters are normal.",
      markResolved: "Resolve",
      confirmResolve: "Confirm",
      cancelResolve: "Cancel",
      resolveNotePlaceholder: "Enter veterinary or management action taken...",
      resolvedBadge: "Resolved",
      govTitle: "ML Model Governance & Drift Surveillance",
      govSubtitle: "Transparent model validation performance, test cohort metrics, and sensor drift audit",
      govCandidateAudit: "Candidate Model Promotion Audit Log",
      auditColVersion: "Model Version",
      auditCol7d: "7-Day Test Metrics",
      auditCol14d: "14-Day Test Metrics",
      auditColStatus: "Promotion Status",
      auditColReasons: "Quality Gate Decision & Audit Log",
      driftTitle: "Sensor Population Stability (PSI Drift Audit):",
      driftStatusLabel: "Distribution Status:",
      driftWindowLabel: "Window:",
      driftLoading: "Evaluating sensor drift report...",
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
      appTitle: "மாஸ்டிசென்ஸ் (MastiSense)",
      appSubtitle: "AI-IoT முலையழற்சி ஆரம்ப அபாய முன்னறிவிப்பு அமைப்பு",
      modelBadgeAudit: "தணிக்கை நிர்வாக முறை: செயலற்றது",
      modelBadgeActive: "செயலில் உள்ள மாதிரி: ",
      syntheticBadge: "செயற்கை மாதிரி (முடிவெடுக்கும் ஆதரவு மட்டுமே)",
      connectedStatus: "இணைக்கப்பட்டது",
      disconnectedStatus: "இணைப்பில்லை",
      lastSyncLabel: "கடைசி புதுப்பிப்பு:",
      refreshBtn: "புதுப்பி",
      evalAlertsBtn: "எச்சரிக்கைகளைச் சோதி",
      apiSettingsBtn: "API அமைப்பு",
      navOverview: "செயல் சுருக்கம்",
      navHerd: "மந்தை கண்காணிப்பு",
      navCowAnalysis: "மாடு & அபாய பகுப்பாய்வு",
      navTelemetry: "உணரி அளவீடுகள்",
      navAlerts: "எச்சரிக்கை மையம்",
      navGovernance: "மாதிரி நிர்வாகம்",
      heroHeadline: "AI-IoT துல்லிய முலையழற்சி அபாய முன்னறிவிப்பு",
      heroDesc: "கறவை மாடுகளுக்கான தொடர் முடிவெடுக்கும் ஆதரவு அமைப்பு. தானியங்கி உணரிகள் மற்றும் இயந்திர கற்றல் மூலம் மருத்துவ அறிகுறிகள் தோன்றுவதற்கு முன்பே 7-நாள் மற்றும் 14-நாள் முன்னறிவிப்பை வழங்குகிறது.",
      heroIndSystem: "கணினி நிலை",
      heroIndModel: "மாதிரி சேவை",
      heroIndGateway: "ESP32 நுழைவாயில்",
      heroIndSource: "தரவு மூலம்",
      kpiTotalCows: "கண்காணிக்கப்படும் மாடுகள்",
      kpiTotalSub: "பதிவுசெய்த மந்தை",
      kpiHighRisk: "அதிக அபாயம் (7/14 நாள்)",
      kpiHighRiskSub: "உடனடி கவனம் தேவை",
      kpiModerateRisk: "நடுத்தர அபாயம் (கண்காணிப்பு)",
      kpiModerateRiskSub: "உணரி விலகல் கண்டறியப்பட்டது",
      kpiHealthyCows: "ஆரோக்கியமான / குறைந்த அபாயம்",
      kpiHealthySub: "சாதாரண எல்லைக்குள்",
      herdDistTitle: "மந்தை சுகாதாரப் பரவல்",
      legendHealthy: "ஆரோக்கியமான / குறைவான",
      legendModerate: "நடுத்தர அபாயம்",
      legendHigh: "அதிக அபாயம்",
      cowAnalysisTitle: "தேர்ந்தெடுக்கப்பட்ட மாட்டின் அபாய முன்னறிவிப்பு",
      cowAnalysisSubtitle: "தனிநபர் மாட்டின் காலவரிசை போக்குகள், பல உணரி சிக்னல்கள் மற்றும் காரணிகள்",
      selectCowLabel: "மாட்டைத் தேர்ந்தெடு:",
      cowIdLabel: "மாடு எண்",
      breedLabel: "இனம்",
      ageLabel: "வயது",
      parityLabel: "ஈற்று எண்ணிக்கை",
      vaccinationLabel: "தடுப்பூசி நிலை",
      priorMastitisLabel: "முந்தைய முலையழற்சி",
      dataDaysLabel: "சேகரிக்கப்பட்ட நாட்கள்",
      forecast7dTitle: "7-நாள் முலையழற்சி அபாய முன்னறிவிப்பு",
      forecast7dRole: "முதன்மை ஆரம்ப எச்சரிக்கை அலாரம்",
      forecast7dDesc: "உடனடி மருத்துவ முடிவெடுக்கும் அலாரம் (1 முதல் 7 நாட்கள்). காம்பு பரிசோதனை, CMT சோதனை மற்றும் பராமரிப்பு ஆய்வுக்கு பரிந்துரைக்கப்படுகிறது.",
      forecast14dTitle: "14-நாள் முலையழற்சி அபாய முன்னறிவிப்பு",
      forecast14dRole: "நீண்ட கால கண்காணிப்பு சிக்னல்",
      forecast14dDesc: "நீண்ட கால கண்காணிப்பு சிக்னல் (1 முதல் 14 நாட்கள்). கறவையின் போது கவனிக்க வேண்டிய முன்கூட்டிய மாற்றங்களை உணர்த்துகிறது.",
      dataWarningTitle: "குறைந்த தரவு வரலாறு அறிவிப்பு",
      dataWarningDesc: "இந்த மாட்டின் பதிவு செய்யப்பட்ட நாட்கள் குறைவு (< 7 நாட்கள்). தினசரி தரவுகள் சேர சேர துல்லியம் அதிகரிக்கும்.",
      sccStaleTitle: "SCC தரவு பழையது / இல்லை",
      sccStaleDesc: "சமீபத்திய ஆய்வக SCC சோதனை இல்லை (> 7 நாட்கள்). செல் எண்ணிக்கை இயல்புநிலை மதிப்பில் கணக்கிடப்படுகிறது.",
      predInactiveTitle: "மாதிரி சேவை செயலிழந்துள்ளது",
      predInactiveDesc: "தணிக்கை அளவுகோல்கள் பூர்த்தியாகாததால் முன்னறிவிப்பு நிறுத்தப்பட்டுள்ளது. கீழே உள்ள உணரி போக்குகளைக் காணவும்.",
      latestTelemetryTitle: "சமீபத்திய உணரி அளவீடுகள்",
      latestTelemetrySubtitle: "கடைசி பதிவின் போது பெறப்பட்ட உடல் மற்றும் சூழல் அளவீடுகள்",
      sensorCondTitle: "பால் மின் கடத்துத்திறன்",
      sensorCondRef: "சாதாரண அளவு: 4.0 - 5.5 mS/cm",
      sensorTempTitle: "பால் வெப்பநிலை",
      sensorTempRef: "காய்ச்சல் நிலை: > 39.2 °C",
      sensorYieldTitle: "பால் கறவை அளவு",
      sensorYieldRef: "திடீர் குறைவு ஆரோக்கியக் குறைபாட்டைக் குறிக்கும்",
      sensorSccTitle: "சோமாடிக் செல் எண்ணிக்கை",
      sensorSccRef: "உட்கிளினிக்கல் வரம்பு: 200,000 செல்கள்/மி.லி",
      trendsTitle: "காலவரிசை உணரி & அபாயப் போக்குகள்",
      tabGrid: "அனைத்து உணரிகள் (கட்டம்)",
      tabRisk: "கணிக்கப்பட்ட அபாய வரலாறு",
      tabCond: "மின் கடத்துத்திறன் (mS/cm)",
      tabTemp: "பால் வெப்பநிலை (°C)",
      tabYield: "பால் அளவு (லிட்டர்)",
      tabScc: "SCC எண்ணிக்கை",
      chartRiskTitle: "7-நாள் மற்றும் 14-நாள் கணிக்கப்பட்ட அபாயப் போக்கு",
      chartCondTitle: "பால் மின் கடத்துத்திறன் வரலாறு (mS/cm)",
      chartTempTitle: "பால் வெப்பநிலை வரலாறு (°C)",
      chartYieldTitle: "தினசரி பால் கறவை வரலாறு (லிட்டர்)",
      chartSccTitle: "சோமாடிக் செல் எண்ணிக்கை வரலாறு (செல்கள்/மி.லி)",
      driversTitle: "முக்கிய அபாயக் காரணிகள் (SHAP விளக்கங்கள்)",
      driversSubtitle: "இந்த கணிப்பிற்கு அதிக பங்களித்த முக்கிய உணரி காரணிகள்",
      noDrivers: "குறிப்பிடத்தக்க அபாயக் காரணிகள் எதுவும் இல்லை.",
      recsTitle: "செயல்படுத்தக்கூடிய பரிந்துரைகள்",
      recsSubtitle: "அடையாளம் காணப்பட்ட காரணிகளின் அடிப்படையிலான மருத்துவ ஆதரவு",
      noRecs: "அனைத்து அளவீடுகளும் வழக்கமான எல்லைக்குள் உள்ளன. வழக்கமான நடைமுறையைத் தொடரவும்.",
      disclaimerText: "மாஸ்டிசென்ஸ் என்பது ஒரு முடிவெடுக்கும் ஆதரவுக் கருவி மட்டுமே; இது மருத்துவப் பரிசோதனைக்கு மாற்றாகாது.",
      herdTableTitle: "மந்தை கண்காணிப்பு அட்டவணை",
      herdTableSubtitle: "தனிநபர் மாடுகளின் நலன் மற்றும் முன்னறிவிப்பு கண்காணிப்பு அட்டவணை",
      colCowId: "மாடு எண்",
      colBreedParity: "இனம் & ஈற்று",
      col7DayRisk: "7-நாள் அபாயம்",
      col14DayRisk: "14-நாள் அபாயம்",
      colHistory: "வரலாறு",
      colDrivers: "முக்கிய காரணிகள்",
      colActions: "செயல்",
      inspectBtn: "ஆய்வு செய்",
      searchPlaceholder: "மாடு எண் அல்லது இனம் மூலம் தேடுக...",
      noCowsFound: "மாடுகள் எதுவும் பதிவு செய்யப்படவில்லை.",
      alertsTitle: "செயலில் உள்ள எச்சரிக்கைகள் & நிகழ்வு மையம்",
      alertsSubtitle: "அதிக அபாயம் அல்லது உணரி முரண்பாடுகளால் தூண்டப்பட்ட எச்சரிக்கைகள்",
      noAlerts: "செயலில் உள்ள எச்சரிக்கைகள் ஏதுமில்லை. மந்தை நலமாக உள்ளது.",
      markResolved: "தீர்க்கப்பட்டது",
      confirmResolve: "உறுதி செய்",
      cancelResolve: "ரத்து செய்",
      resolveNotePlaceholder: "மேற்கொண்ட பராமரிப்பு நடவடிக்கையை உள்ளிடவும்...",
      resolvedBadge: "தீர்க்கப்பட்டது",
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
    }
  };

  // --------------------------------------------------------------------------
  // 2. State Manager
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
    }
  };

  // --------------------------------------------------------------------------
  // 3. Internationalization (I18N) Helper
  // --------------------------------------------------------------------------
  function t(key) {
    const lang = State.currentLang;
    if (I18N[lang] && I18N[lang][key] !== undefined) return I18N[lang][key];
    if (I18N["en"] && I18N["en"][key] !== undefined) return I18N["en"][key];
    return key;
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

    const langBtnText = document.getElementById("langBtnText");
    if (langBtnText) {
      langBtnText.textContent = State.currentLang === "en" ? "தமிழ்" : "English";
    }

    // Refresh dynamic widgets with localized strings
    renderKpis();
    renderHerdDistribution();
    renderHerdTable();
    if (State.selectedCowId) {
      renderSelectedCow();
    }
    renderAlerts();
    renderAuditTable();
    renderDriftStatus();
  }

  function toggleLanguage() {
    State.currentLang = State.currentLang === "en" ? "ta" : "en";
    localStorage.setItem("mastitis_lang", State.currentLang);
    applyLanguage();
    showToast(State.currentLang === "ta" ? "மொழி: தமிழ் செயல்படுத்தப்பட்டது" : "Language: English active");
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
    }
  };

  // --------------------------------------------------------------------------
  // 5. Toast Notifications
  // --------------------------------------------------------------------------
  function showToast(message, isError = false) {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${isError ? "toast-error" : ""}`;
    toast.innerHTML = `<span>${isError ? "⚠" : "✓"}</span><span>${escapeHtml(message)}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // --------------------------------------------------------------------------
  // 6. Data Refresh & Synchronization Orchestrator
  // --------------------------------------------------------------------------
  async function refreshData(silent = false) {
    const refreshIcon = document.getElementById("refreshSpinnerIcon");
    if (refreshIcon) refreshIcon.style.animation = "spin 1s linear infinite";

    try {
      // 1. Root Handshake
      let rootData;
      try {
        rootData = await ApiClient.getRoot();
        State.isConnected = true;
      } catch (e) {
        State.isConnected = false;
        updateConnectionStatus(false, e.message);
        renderErrorState("Cannot connect to MastiSense API server at " + State.apiBase + ". Please verify backend is running.");
        return;
      }

      updateConnectionStatus(true);
      State.isModelActive = (rootData.model_status === "active" && Boolean(rootData.model_version));
      State.activeModelVersion = rootData.model_version;
      State.candidateVersions = rootData.candidate_versions || [];
      State.featurePipelineVersion = rootData.feature_pipeline_version;
      State.dataType = rootData.data_type || "synthetic";

      // 2. Fetch Core Datasets Concurrently
      const [cows, metricsRes, alerts, drift] = await Promise.all([
        ApiClient.getCows().catch(() => []),
        ApiClient.getMetrics().catch(() => ({})),
        ApiClient.getAlerts().catch(() => []),
        ApiClient.getDriftSummary().catch(() => ({}))
      ]);

      State.registeredCows = cows || [];
      State.alertsList = alerts || [];
      State.metrics = metricsRes || {};
      State.driftReport = drift || {};

      // 3. Herd Risk Predictions (if model active)
      if (State.isModelActive) {
        State.herdRiskList = await ApiClient.getHerdRisk().catch(() => []);
      } else {
        State.herdRiskList = [];
      }

      // Candidate audit summaries
      if (metricsRes.candidate_summaries) {
        State.candidateSummaries = metricsRes.candidate_summaries;
      } else if (metricsRes["7d"]) {
        State.candidateSummaries = [{
          version: State.activeModelVersion || "current",
          "7d_auc": metricsRes["7d"].auc,
          "7d_recall": metricsRes["7d"].recall,
          "14d_auc": metricsRes["14d"] ? metricsRes["14d"].auc : null,
          "14d_recall": metricsRes["14d"] ? metricsRes["14d"].recall : null,
          promotion_status: "promoted",
          promotion_reasons: ["Active production model approved for serving."]
        }];
      } else {
        State.candidateSummaries = [];
      }

      State.lastSyncTime = new Date();
      const lastSyncEl = document.getElementById("lastSyncTime");
      if (lastSyncEl) lastSyncEl.textContent = State.lastSyncTime.toLocaleTimeString();

      // 4. Update Header Badges
      updateHeaderBadges();

      // 5. Render Core Components
      renderKpis();
      renderHerdDistribution();
      populateCowDropdown();
      renderHerdTable();
      renderAlerts();
      renderAuditTable();
      renderDriftStatus();

      // 6. Select Default Cow if none selected
      if (!State.selectedCowId && State.registeredCows.length > 0) {
        await selectCow(State.registeredCows[0].cow_id, false);
      } else if (State.selectedCowId) {
        await selectCow(State.selectedCowId, false);
      }

      if (!silent) {
        showToast("Dashboard synchronized with API.");
      }

    } catch (err) {
      console.error("Dashboard refresh error:", err);
      updateConnectionStatus(false, err.message);
      showToast("Data refresh error: " + err.message, true);
    } finally {
      if (refreshIcon) refreshIcon.style.animation = "none";
    }
  }

  function updateConnectionStatus(connected, errDetail) {
    const pill = document.getElementById("connectionStatusPill");
    const text = document.getElementById("connectionStatusText");
    const dot = document.getElementById("connectionDot");

    if (connected) {
      if (pill) pill.className = "status-pill pill-connected";
      if (text) text.textContent = t("connectedStatus");
      if (dot) dot.className = "pulse-dot";
    } else {
      if (pill) pill.className = "status-pill pill-disconnected";
      if (text) text.textContent = t("disconnectedStatus");
      if (dot) dot.className = "pulse-dot offline";
    }
  }

  function updateHeaderBadges() {
    const modelBadge = document.getElementById("headerModelBadge");
    const modelText = document.getElementById("headerModelText");

    if (State.isModelActive) {
      if (modelBadge) modelBadge.className = "status-pill pill-active-model";
      if (modelText) modelText.textContent = `${t("modelBadgeActive")}${State.activeModelVersion}`;
    } else {
      if (modelBadge) modelBadge.className = "status-pill pill-audit-mode";
      if (modelText) modelText.textContent = t("modelBadgeAudit");
    }

    const heroSystemStatus = document.getElementById("heroSystemStatus");
    if (heroSystemStatus) heroSystemStatus.textContent = State.isConnected ? "Online" : "Offline";

    const heroModelStatus = document.getElementById("heroModelStatus");
    if (heroModelStatus) heroModelStatus.textContent = State.isModelActive ? `${State.activeModelVersion} (Serving)` : "Audit Mode";

    const heroIndSource = document.getElementById("heroIndSource");
    if (heroIndSource) heroIndSource.textContent = State.dataType ? (State.dataType.charAt(0).toUpperCase() + State.dataType.slice(1)) : "Synthetic";
  }

  // --------------------------------------------------------------------------
  // 7. Render Herd KPIs & Health Distribution
  // --------------------------------------------------------------------------
  function renderKpis() {
    const totalCount = State.registeredCows.length;
    let highCount = 0;
    let modCount = 0;
    let lowCount = 0;

    if (State.isModelActive && State.herdRiskList.length > 0) {
      State.herdRiskList.forEach(c => {
        const isHigh = c.risk_tier_7d === "High Risk" || c.risk_tier_14d === "High Risk";
        const isMod = !isHigh && (c.risk_tier_7d === "Moderate Risk" || c.risk_tier_14d === "Moderate Risk");

        if (isHigh) highCount++;
        else if (isMod) modCount++;
        else lowCount++;
      });
    } else {
      // Inactive model
      lowCount = totalCount;
    }

    // Set KPI Values
    setText("kpiTotalVal", totalCount);
    setText("kpiHighVal", State.isModelActive ? highCount : "0 (Audit)");
    setText("kpiModVal", State.isModelActive ? modCount : "0 (Audit)");
    setText("kpiHealthyVal", State.isModelActive ? lowCount : totalCount);

    // Dynamic subtitles
    setText("kpiHighSub", State.isModelActive && highCount > 0 ? `${highCount} cow${highCount > 1 ? "s" : ""} require review` : t("kpiHighRiskSub"));
    setText("kpiModSub", State.isModelActive && modCount > 0 ? `${modCount} cow${modCount > 1 ? "s" : ""} on watch list` : t("kpiModerateRiskSub"));
  }

  function renderHerdDistribution() {
    const total = State.registeredCows.length;
    let highCount = 0;
    let modCount = 0;
    let lowCount = 0;

    if (State.isModelActive && State.herdRiskList.length > 0) {
      State.herdRiskList.forEach(c => {
        const isHigh = c.risk_tier_7d === "High Risk" || c.risk_tier_14d === "High Risk";
        const isMod = !isHigh && (c.risk_tier_7d === "Moderate Risk" || c.risk_tier_14d === "Moderate Risk");
        if (isHigh) highCount++;
        else if (isMod) modCount++;
        else lowCount++;
      });
    } else {
      lowCount = total;
    }

    const pHealthy = total > 0 ? (lowCount / total) * 100 : 100;
    const pMod = total > 0 ? (modCount / total) * 100 : 0;
    const pHigh = total > 0 ? (highCount / total) * 100 : 0;

    const segHealthy = document.getElementById("distSegHealthy");
    const segMod = document.getElementById("distSegMod");
    const segHigh = document.getElementById("distSegHigh");

    if (segHealthy) segHealthy.style.width = `${pHealthy}%`;
    if (segMod) segMod.style.width = `${pMod}%`;
    if (segHigh) segHigh.style.width = `${pHigh}%`;

    setText("distHealthyLabel", `${t("legendHealthy")}: ${lowCount} (${pHealthy.toFixed(0)}%)`);
    setText("distModLabel", `${t("legendModerate")}: ${modCount} (${pMod.toFixed(0)}%)`);
    setText("distHighLabel", `${t("legendHigh")}: ${highCount} (${pHigh.toFixed(0)}%)`);
  }

  // --------------------------------------------------------------------------
  // 8. Cow Selection & Profile Rendering
  // --------------------------------------------------------------------------
  function populateCowDropdown() {
    const select = document.getElementById("cowSelectDropdown");
    if (!select) return;

    select.innerHTML = `<option value="">${t("selectCowLabel")}</option>` +
      State.registeredCows.map(c => `
        <option value="${escapeHtml(c.cow_id)}" ${c.cow_id === State.selectedCowId ? "selected" : ""}>
          ${escapeHtml(c.cow_id)} — ${escapeHtml(c.breed || "Crossbred Dairy")} (P${c.parity || 1})
        </option>
      `).join("");
  }

  async function selectCow(cowId, updateUrl = false) {
    if (!cowId) return;
    State.selectedCowId = cowId;

    const select = document.getElementById("cowSelectDropdown");
    if (select && select.value !== cowId) {
      select.value = cowId;
    }

    // Highlight row in herd table
    document.querySelectorAll("#herdTableBody tr").forEach(tr => {
      if (tr.getAttribute("data-cow-id") === cowId) {
        tr.classList.add("active-row");
      } else {
        tr.classList.remove("active-row");
      }
    });

    // Find cow metadata
    const profile = State.registeredCows.find(c => c.cow_id === cowId) || { cow_id: cowId };
    State.selectedCowProfile = profile;

    // Fetch individual cow datasets concurrently
    try {
      const [history, risk, riskHistory] = await Promise.all([
        ApiClient.getCowHistory(cowId).catch(() => []),
        State.isModelActive ? ApiClient.getCowRisk(cowId).catch(() => null) : Promise.resolve(null),
        State.isModelActive ? ApiClient.getCowRiskHistory(cowId).catch(() => []) : Promise.resolve([])
      ]);

      State.selectedCowHistory = history || [];
      State.selectedCowRisk = risk;
      State.selectedCowRiskHistory = riskHistory || [];

      // Render Selected Cow Components
      renderSelectedCow();

    } catch (err) {
      console.error("Failed to load cow profile", err);
      showToast("Error loading cow data: " + err.message, true);
    }
  }

  function renderSelectedCow() {
    const cow = State.selectedCowProfile || {};
    const risk = State.selectedCowRisk;
    const history = State.selectedCowHistory || [];
    const riskHistory = State.selectedCowRiskHistory || [];

    // Profile metadata
    setText("profAvatarCowId", cow.cow_id || "-");
    setText("profCowIdText", cow.cow_id || "-");
    setText("profBreedText", `${cow.breed || "Standard Dairy"} (P${cow.parity || 1})`);
    setText("profAgeVal", cow.age_years ? `${cow.age_years} yrs` : "-");
    setText("profParityVal", cow.parity ? `Lactation ${cow.parity}` : "1");
    setText("profCalvingVal", cow.calving_date || "Historical");
    setText("profVaccineVal", cow.vaccination_status ? t("yes") : t("no"));
    setText("profPriorMastitisVal", cow.prior_mastitis_flag ? t("yes") : t("no"));
    setText("profHistoryDaysVal", `${history.length} ${t("readingsUnit")}`);

    // Render Risk Gauges
    renderRiskGauges(risk, history.length);

    // Render Latest Telemetry Metric Cards
    renderLatestTelemetry(history);

    // Render Trend Charts
    renderCharts(history, riskHistory);

    // Render Drivers & Recommendations
    renderExplainability(risk);
  }

  // --------------------------------------------------------------------------
  // 9. Dual-Horizon Risk Gauges (7-Day & 14-Day)
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

    // Circumference for r=42 is 263.89
    const circumference = 263.89;

    if (!State.isModelActive || !risk) {
      // Inactive model state
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

    // Data Sufficiency Warning & Staleness Warnings
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
  // 10. Latest Sensor Telemetry Cards
  // --------------------------------------------------------------------------
  function renderLatestTelemetry(history) {
    if (!history || history.length === 0) {
      setText("sensorCondVal", "--");
      setText("sensorTempVal", "--");
      setText("sensorYieldVal", "--");
      setText("sensorSccVal", "--");
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

    // Milk Yield
    if (latest.milk_yield_l !== undefined && latest.milk_yield_l !== null) {
      setText("sensorYieldVal", Number(latest.milk_yield_l).toFixed(1));
    } else {
      setText("sensorYieldVal", "--");
    }

    // Somatic Cell Count (SCC)
    if (latest.scc_value !== undefined && latest.scc_value !== null) {
      setText("sensorSccVal", Number(latest.scc_value).toLocaleString());
      const dot = document.getElementById("sccRefDot");
      if (dot) {
        dot.className = latest.scc_value > 200000 ? "ref-status-dot elevated" : "ref-status-dot";
      }
    } else {
      setText("sensorSccVal", "Not tested");
    }
  }

  // --------------------------------------------------------------------------
  // 11. Chart.js Time-Series Trends
  // --------------------------------------------------------------------------
  function renderCharts(history, riskHistory) {
    const labels = history.map(h => {
      if (!h.timestamp) return "";
      const d = new Date(h.timestamp);
      return isNaN(d) ? h.timestamp.substring(5, 10) : `${d.getMonth() + 1}/${d.getDate()}`;
    });

    const commonScales = {
      x: {
        grid: { color: "#f1f5f9" },
        ticks: { font: { size: 10 }, color: "#64748b" }
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

    // 1. Calibrated Risk History Chart
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
              label: "7-Day Risk (%)",
              data: r7Data,
              borderColor: "#dc2626",
              backgroundColor: "rgba(220, 38, 38, 0.06)",
              fill: true,
              tension: 0.25,
              pointRadius: 3,
              pointBackgroundColor: "#dc2626"
            },
            {
              label: "14-Day Risk (%)",
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
          plugins: { ...commonPlugins, legend: { display: true, position: "top", labels: { boxWidth: 10, font: { size: 10 } } } },
          scales: {
            ...commonScales,
            y: { ...commonScales.y, min: 0, max: 100, title: { display: true, text: "Risk %", font: { size: 10 } } }
          }
        }
      });
    } else {
      if (riskCard) riskCard.style.display = "none";
      if (riskTab) riskTab.style.display = "none";
    }

    // 2. Milk Conductivity Chart
    if (State.charts.cond) State.charts.cond.destroy();
    const ctxCond = document.getElementById("chartCanvasCond").getContext("2d");
    State.charts.cond = new Chart(ctxCond, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Conductivity (mS/cm)",
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
        plugins: commonPlugins,
        scales: {
          ...commonScales,
          y: { ...commonScales.y, title: { display: true, text: "mS/cm", font: { size: 10 } } }
        }
      }
    });

    // 3. Milk Temperature Chart
    if (State.charts.temp) State.charts.temp.destroy();
    const ctxTemp = document.getElementById("chartCanvasTemp").getContext("2d");
    State.charts.temp = new Chart(ctxTemp, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Temperature (°C)",
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
        plugins: commonPlugins,
        scales: {
          ...commonScales,
          y: { ...commonScales.y, title: { display: true, text: "°C", font: { size: 10 } } }
        }
      }
    });

    // 4. Somatic Cell Count (SCC) Chart (handles nulls with spanGaps)
    if (State.charts.scc) State.charts.scc.destroy();
    const ctxScc = document.getElementById("chartCanvasScc").getContext("2d");
    State.charts.scc = new Chart(ctxScc, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "SCC (cells/mL)",
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
        plugins: commonPlugins,
        scales: {
          ...commonScales,
          y: {
            ...commonScales.y,
            title: { display: true, text: "cells/mL", font: { size: 10 } },
            suggestedMax: 400000
          }
        }
      }
    });

    // 5. Milk Yield Chart
    if (State.charts.yield) State.charts.yield.destroy();
    const ctxYield = document.getElementById("chartCanvasYield").getContext("2d");
    State.charts.yield = new Chart(ctxYield, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Yield (Litres)",
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
        plugins: commonPlugins,
        scales: {
          ...commonScales,
          y: { ...commonScales.y, title: { display: true, text: "Litres", font: { size: 10 } } }
        }
      }
    });
  }

  function switchChartTab(mode) {
    State.currentChartMode = mode;
    document.querySelectorAll(".chart-tab-btn").forEach(btn => btn.classList.remove("active"));
    const activeBtn = document.getElementById(`tabBtn${mode.charAt(0).toUpperCase() + mode.slice(1)}`);
    if (activeBtn) activeBtn.classList.add("active");

    const container = document.getElementById("chartsGridContainer");
    const cards = {
      risk: document.getElementById("cardChartRisk"),
      cond: document.getElementById("cardChartCond"),
      temp: document.getElementById("cardChartTemp"),
      yield: document.getElementById("cardChartYield"),
      scc: document.getElementById("cardChartScc")
    };

    if (mode === "grid") {
      if (container) container.className = "charts-grid-container";
      for (const k in cards) {
        if (cards[k]) {
          cards[k].style.display = (k === "risk" && (!State.isModelActive || !State.selectedCowRiskHistory.length)) ? "none" : "flex";
        }
      }
    } else {
      if (container) container.className = "charts-grid-container single-mode";
      for (const k in cards) {
        if (cards[k]) {
          cards[k].style.display = (k === mode) ? "flex" : "none";
        }
      }
    }
  }

  // --------------------------------------------------------------------------
  // 12. Model Explainability & Recommendations
  // --------------------------------------------------------------------------
  function renderExplainability(risk) {
    const driversList = document.getElementById("topDriversList");
    const recsList = document.getElementById("recommendationsList");

    if (!risk) {
      if (driversList) driversList.innerHTML = `<div class="state-container" style="padding:16px;"><span class="state-desc">${t("noDrivers")}</span></div>`;
      if (recsList) recsList.innerHTML = `<div class="state-container" style="padding:16px;"><span class="state-desc">${t("noRecs")}</span></div>`;
      return;
    }

    // Top SHAP Risk Drivers
    const drivers = risk.top_driver_features || [];
    if (driversList) {
      if (drivers.length === 0) {
        driversList.innerHTML = `<div class="state-container" style="padding:16px;"><span class="state-desc">${t("noDrivers")}</span></div>`;
      } else {
        // Calculate maximum absolute impact for relative bar scaling
        const maxImpact = Math.max(...drivers.map(d => Math.abs(d.impact || 0)), 0.0001);

        driversList.innerHTML = drivers.map(d => {
          const impact = d.impact || 0;
          const absImpact = Math.abs(impact);
          const pctWidth = Math.min(100, Math.max(12, (absImpact / maxImpact) * 100));
          const isPositive = impact >= 0;
          const signStr = isPositive ? "+" : "-";

          return `
            <div class="driver-item-row">
              <div class="driver-item-head">
                <span class="driver-feature-name">${escapeHtml(formatFeatureName(d.feature))}</span>
                <span class="driver-impact-val" style="color:${isPositive ? 'var(--risk-high-text)' : 'var(--risk-none-text)'};">
                  ${signStr}${absImpact.toFixed(3)}
                </span>
              </div>
              <div class="driver-bar-track">
                <div class="driver-bar-fill ${isPositive ? 'positive-risk' : 'mitigating'}" style="width:${pctWidth}%;"></div>
              </div>
            </div>
          `;
        }).join("");
      }
    }

    // Actionable Recommendations
    const recs = risk.recommendations || [];
    if (recsList) {
      if (recs.length === 0) {
        recsList.innerHTML = `
          <div class="rec-item">
            <span class="rec-icon">✓</span>
            <span>${t("noRecs")}</span>
          </div>
        `;
      } else {
        recsList.innerHTML = recs.map(r => `
          <div class="rec-item">
            <span class="rec-icon">→</span>
            <span>${escapeHtml(r)}</span>
          </div>
        `).join("");
      }
    }
  }

  function formatFeatureName(rawName) {
    if (!rawName) return "";
    return rawName
      .replace(/_/g, " ")
      .replace(/\b([a-z])/g, c => c.toUpperCase())
      .replace("Scc", "SCC")
      .replace("Temp C", "Temp (°C)")
      .replace("Yield L", "Yield (L)")
      .replace("Delta", "Δ");
  }

  // --------------------------------------------------------------------------
  // 13. Herd Surveillance Matrix Table
  // --------------------------------------------------------------------------
  function renderHerdTable() {
    const tbody = document.getElementById("herdTableBody");
    const query = (document.getElementById("cowSearchInput")?.value || "").toLowerCase().trim();

    if (!tbody) return;

    if (!State.registeredCows || State.registeredCows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="state-container"><span class="state-desc">${t("noCowsFound")}</span></td></tr>`;
      return;
    }

    const filtered = State.registeredCows.filter(c => {
      if (!query) return true;
      const cid = (c.cow_id || "").toLowerCase();
      const breed = (c.breed || "").toLowerCase();
      return cid.includes(query) || breed.includes(query);
    });

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="state-container"><span class="state-desc">No cows match "${escapeHtml(query)}".</span></td></tr>`;
      return;
    }

    tbody.innerHTML = filtered.map(c => {
      const cid = c.cow_id;
      const riskObj = State.herdRiskList.find(r => r.cow_id === cid);
      const isSelected = (cid === State.selectedCowId);

      let risk7Html = `<span class="status-pill pill-synthetic">${t("modelBadgeAudit")}</span>`;
      let risk14Html = `<span class="status-pill pill-synthetic">${t("modelBadgeAudit")}</span>`;
      let driversHtml = `<span style="color:var(--text-faint);">--</span>`;
      let dataDays = c.data_days || "-";

      if (State.isModelActive && riskObj) {
        const tier7Cls = `tier-${(riskObj.risk_tier_7d || "NoRisk").replace(/\s+/g, "")}`;
        const tier14Cls = `tier-${(riskObj.risk_tier_14d || "NoRisk").replace(/\s+/g, "")}`;

        risk7Html = `<span class="risk-tier-badge ${tier7Cls}">${riskObj.risk_percent_7d}% (${riskObj.risk_tier_7d})</span>`;
        risk14Html = `<span class="risk-tier-badge ${tier14Cls}">${riskObj.risk_percent_14d}% (${riskObj.risk_tier_14d})</span>`;
        dataDays = riskObj.data_days;

        if (riskObj.top_driver_features && riskObj.top_driver_features.length > 0) {
          driversHtml = riskObj.top_driver_features.slice(0, 3).map(d => `
            <span class="driver-chip">${escapeHtml(formatFeatureName(d.feature))}</span>
          `).join("");
        }
      }

      return `
        <tr data-cow-id="${escapeHtml(cid)}" onclick="window.MastiSenseApp.selectCow('${escapeHtml(cid)}', true)" class="${isSelected ? 'active-row' : ''}">
          <td><b>${escapeHtml(cid)}</b></td>
          <td>${escapeHtml(c.breed || "Crossbred Dairy")} (P${c.parity || 1})</td>
          <td>${risk7Html}</td>
          <td>${risk14Html}</td>
          <td>${dataDays} ${dataDays !== "-" ? t("daysUnit") : ""}</td>
          <td>${driversHtml}</td>
          <td>
            <button onclick="event.stopPropagation(); window.MastiSenseApp.selectCow('${escapeHtml(cid)}', true)" class="btn btn-secondary btn-sm">
              ${t("inspectBtn")}
            </button>
          </td>
        </tr>
      `;
    }).join("");
  }

  // --------------------------------------------------------------------------
  // 14. Alerts Center & Incident Management
  // --------------------------------------------------------------------------
  function renderAlerts() {
    const container = document.getElementById("alertsContainer");
    if (!container) return;

    if (!State.alertsList || State.alertsList.length === 0) {
      container.innerHTML = `<div class="state-container"><span class="state-desc">${t("noAlerts")}</span></div>`;
      return;
    }

    container.innerHTML = State.alertsList.map(a => {
      const isResolved = a.status === "resolved";
      const pct = a.risk_score ? (a.risk_score * 100).toFixed(1) + "% risk" : "";
      const timeStr = a.timestamp ? new Date(a.timestamp).toLocaleString() : "";
      const resolvedNote = isResolved
        ? `<div style="font-size:0.75rem; color:#64748b; margin-top:4px;"><b>${t("resolvedBadge")}:</b> ${escapeHtml(a.resolved_note || "Resolved")} (${a.resolved_at ? new Date(a.resolved_at).toLocaleDateString() : ""})</div>`
        : "";

      return `
        <div class="alert-card-item ${isResolved ? 'resolved' : 'open'}" id="alertCard_${a.id}">
          <div class="alert-body">
            <div class="alert-head-meta">
              <span class="alert-cow-badge">${escapeHtml(a.cow_id)}</span>
              ${pct ? `<span class="alert-score-badge">${pct}</span>` : ""}
              <span class="alert-time">${timeStr}</span>
            </div>
            <div class="alert-message-text">${escapeHtml(a.message || "Elevated mastitis warning")}</div>
            ${resolvedNote}
            <div class="alert-resolve-box" id="resolveBox_${a.id}">
              <input type="text" id="resolveInput_${a.id}" class="resolve-input" placeholder="${t("resolveNotePlaceholder")}">
              <button onclick="window.MastiSenseApp.confirmResolveAlert(${a.id})" class="btn btn-primary btn-sm">${t("confirmResolve")}</button>
              <button onclick="window.MastiSenseApp.toggleResolveBox(${a.id}, false)" class="btn btn-secondary btn-sm">${t("cancelResolve")}</button>
            </div>
          </div>
          <div>
            ${!isResolved
              ? `<button onclick="window.MastiSenseApp.toggleResolveBox(${a.id}, true)" class="btn btn-secondary btn-sm" id="btnOpenResolve_${a.id}">${t("markResolved")}</button>`
              : `<span class="risk-tier-badge tier-NoRisk" style="font-size:0.7rem; padding:2px 8px;">${t("resolvedBadge")}</span>`
            }
          </div>
        </div>
      `;
    }).join("");
  }

  function toggleResolveBox(alertId, show) {
    const box = document.getElementById(`resolveBox_${alertId}`);
    const btn = document.getElementById(`btnOpenResolve_${alertId}`);
    if (box) box.classList.toggle("active", show);
    if (btn) btn.style.display = show ? "none" : "inline-flex";
  }

  async function confirmResolveAlert(alertId) {
    const input = document.getElementById(`resolveInput_${alertId}`);
    const note = input ? input.value.trim() : "";

    try {
      const ok = await ApiClient.resolveAlert(alertId, note);
      if (ok) {
        showToast("Alert marked as resolved.");
        refreshData(true);
      } else {
        showToast("Failed to resolve alert.", true);
      }
    } catch (e) {
      showToast("Error resolving alert: " + e.message, true);
    }
  }

  async function evaluateAlertsNow() {
    const btn = document.getElementById("btnEvalAlerts");
    if (btn) btn.disabled = true;

    try {
      showToast("Evaluating herd alerts...");
      const result = await ApiClient.checkAlerts();
      if (result.status === "evaluated") {
        showToast(`Alert evaluation complete: ${result.new_alerts_created} new alerts.`);
      } else {
        showToast(result.note || "Alert check completed.");
      }
      refreshData(true);
    } catch (e) {
      showToast("Alert evaluation failed: " + e.message, true);
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  // --------------------------------------------------------------------------
  // 15. Model Governance & Sensor Drift Surveillance
  // --------------------------------------------------------------------------
  function renderAuditTable() {
    const tbody = document.getElementById("auditTableBody");
    if (!tbody) return;

    if (!State.candidateSummaries || State.candidateSummaries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="state-container"><span class="state-desc">No model candidate audit records available.</span></td></tr>`;
      return;
    }

    tbody.innerHTML = State.candidateSummaries.map(c => {
      const isPromoted = c.promotion_status === "promoted";
      const statusBadge = isPromoted
        ? `<span class="risk-tier-badge tier-NoRisk" style="font-size:0.75rem;">Promoted</span>`
        : `<span class="risk-tier-badge tier-HighRisk" style="font-size:0.75rem;">Rejected</span>`;

      const m7 = (c["7d_auc"] !== undefined && c["7d_auc"] !== null)
        ? `ROC-AUC: ${c["7d_auc"].toFixed(3)} | Recall: ${(c["7d_recall"] * 100).toFixed(1)}%`
        : "N/A";
      const m14 = (c["14d_auc"] !== undefined && c["14d_auc"] !== null)
        ? `ROC-AUC: ${c["14d_auc"].toFixed(3)} | Recall: ${(c["14d_recall"] * 100).toFixed(1)}%`
        : "N/A";
      const reasons = (c.promotion_reasons || []).map(r => `• ${escapeHtml(r)}`).join("<br>");

      return `
        <tr>
          <td><b>${escapeHtml(c.version)}</b></td>
          <td>${m7}</td>
          <td>${m14}</td>
          <td>${statusBadge}</td>
          <td style="font-size:0.75rem; color:${isPromoted ? 'var(--text-secondary)' : 'var(--risk-high-text)'};">
            ${reasons || "Passed promotion gates."}
          </td>
        </tr>
      `;
    }).join("");

    // Render Metrics Cards if available
    renderGovernanceMetrics();
  }

  function renderGovernanceMetrics() {
    const metrics7d = State.metrics["7d"];
    if (!metrics7d) return;

    if (metrics7d.auc !== undefined && metrics7d.auc !== null) {
      setText("govAucVal", Number(metrics7d.auc).toFixed(3));
      if (metrics7d.baseline_logistic_auc !== undefined) {
        const diff = metrics7d.auc - metrics7d.baseline_logistic_auc;
        setText("govAucSub", `Baseline Adv: ${diff >= 0 ? "+" : ""}${diff.toFixed(3)}`);
      }
    }

    const recall = metrics7d.sensitivity_recall !== undefined ? metrics7d.sensitivity_recall : metrics7d.recall;
    if (recall !== undefined && recall !== null) {
      setText("govRecallVal", `${(Number(recall) * 100).toFixed(1)}%`);
      const floor = metrics7d.target_recall_setting ? (metrics7d.target_recall_setting * 100).toFixed(0) : "70";
      setText("govRecallSub", `Target Floor: ≥ ${floor}.0%`);
    }

    if (metrics7d.specificity !== undefined && metrics7d.specificity !== null) {
      setText("govSpecVal", `${(Number(metrics7d.specificity) * 100).toFixed(1)}%`);
      setText("govSpecSub", "Clean herd days cleared");
    }

    if (metrics7d.brier_score !== undefined && metrics7d.baseline_logistic_brier !== undefined) {
      const imp = ((1 - metrics7d.brier_score / metrics7d.baseline_logistic_brier) * 100);
      setText("govBrierVal", `${imp.toFixed(1)}%`);
      setText("govBrierSub", `Brier: ${Number(metrics7d.brier_score).toFixed(4)} (Platt)`);
    } else if (metrics7d.brier_score !== undefined) {
      setText("govBrierVal", Number(metrics7d.brier_score).toFixed(4));
      setText("govBrierSub", "Platt Sigmoid Scaled");
    }
  }

  function renderDriftStatus() {
    const el = document.getElementById("driftStatusText");
    if (!el) return;

    const drift = State.driftReport;
    if (!drift || !drift.status) {
      el.textContent = "Sensor stability audit unavailable.";
      return;
    }

    const note = drift.note || "Sensor population distributions stable.";
    const statusCls = drift.status === "stable" ? "tier-NoRisk" : "tier-ModerateRisk";

    el.innerHTML = `
      <span class="risk-tier-badge ${statusCls}" style="font-size:0.75rem; padding:2px 8px;">${drift.status.toUpperCase()}</span>
      <span style="color:var(--text-secondary); margin-left:6px;">Window: ${drift.recent_window_days || 30} days — ${escapeHtml(note)}</span>
    `;
  }

  function renderErrorState(message) {
    const herd = document.getElementById("herdTableBody");
    if (herd) herd.innerHTML = `<tr><td colspan="7" class="state-container" style="color:var(--risk-high-text);"><span class="state-desc">${escapeHtml(message)}</span></td></tr>`;

    const alerts = document.getElementById("alertsContainer");
    if (alerts) alerts.innerHTML = `<div class="state-container" style="color:var(--risk-high-text);"><span class="state-desc">${escapeHtml(message)}</span></div>`;
  }

  // --------------------------------------------------------------------------
  // 16. Utility Helpers
  // --------------------------------------------------------------------------
  function setText(elementId, text) {
    const el = document.getElementById(elementId);
    if (el) el.textContent = text !== null && text !== undefined ? text : "-";
  }

  // API Base Configuration Modal
  function openApiModal() {
    const input = document.getElementById("modalApiInput");
    if (input) input.value = State.apiBase;
    const modal = document.getElementById("apiModalBackdrop");
    if (modal) modal.classList.add("open");
  }

  function closeApiModal() {
    const modal = document.getElementById("apiModalBackdrop");
    if (modal) modal.classList.remove("open");
  }

  function saveApiBase() {
    const input = document.getElementById("modalApiInput");
    const val = input ? input.value.trim() : "";
    if (val) {
      State.apiBase = val;
      localStorage.setItem("mastitis_api_base", val);
      closeApiModal();
      showToast("API server address updated: " + val);
      refreshData();
    }
  }

  // Sidebar navigation handling
  function setupNavigation() {
    const links = document.querySelectorAll(".sidebar-nav .nav-link");
    links.forEach(link => {
      link.addEventListener("click", e => {
        links.forEach(l => l.classList.remove("active"));
        link.classList.add("active");

        // On mobile, close sidebar after clicking
        const sidebar = document.getElementById("appSidebar");
        if (sidebar && window.innerWidth <= 768) {
          sidebar.classList.remove("mobile-open");
        }
      });
    });

    const toggleBtn = document.getElementById("sidebarToggleBtn");
    const sidebar = document.getElementById("appSidebar");
    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener("click", () => {
        sidebar.classList.toggle("mobile-open");
      });
    }
  }

  // --------------------------------------------------------------------------
  // 17. Initialization
  // --------------------------------------------------------------------------
  function init() {
    setupNavigation();
    applyLanguage();
    refreshData(true);

    // Set up search listener
    const searchInput = document.getElementById("cowSearchInput");
    if (searchInput) {
      searchInput.addEventListener("input", () => renderHerdTable());
    }

    // Auto-refresh cycle (every 30 seconds)
    setInterval(() => {
      refreshData(true);
    }, 30000);
  }

  // Expose global methods for HTML onclick bindings
  window.MastiSenseApp = {
    init,
    refreshData,
    toggleLanguage,
    selectCow,
    switchChartTab,
    toggleResolveBox,
    confirmResolveAlert,
    evaluateAlertsNow,
    openApiModal,
    closeApiModal,
    saveApiBase
  };

  // Run on DOM Ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

})();
