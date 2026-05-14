export const MOCK_CONFIG = Object.freeze({
    // VERSION: 2026-05-14_23:54
    API_URL: window.location.origin,

    config: {
        "model_name": "NEXUS-V4 Simulator",
        "control_variables": {"calcinerHeadTemp": {"unit": "°C"}},
        "indicator_variables": {"sinteringZoneTemp": {"unit": "C"}}
    }
});

console.log("[AI-CONFIG] Active API URL:", MOCK_CONFIG.API_URL);
