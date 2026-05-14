export const MOCK_CONFIG = Object.freeze({
    // VERSION: 2026-05-15_00:09 (FORCE IP)
    API_URL: 'http://10.1.250.1:5000',

    config: {
        "model_name": "NEXUS-V4 Simulator",
        "control_variables": {"calcinerHeadTemp": {"unit": "°C"}},
        "indicator_variables": {"sinteringZoneTemp": {"unit": "C"}}
    }
});

console.log("[AI-CONFIG] Active API URL:", MOCK_CONFIG.API_URL);
