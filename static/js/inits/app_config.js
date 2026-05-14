export const MOCK_CONFIG = Object.freeze({
    // SMART CONNECTION: Automatically detects if it's local or network access
    API_URL: (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? '' : window.location.origin,

    config: {
        "model_name": "NEXUS-V4 Simulator",
        "control_variables": {"calcinerHeadTemp": {"unit": "°C"}},
        "indicator_variables": {"sinteringZoneTemp": {"unit": "C"}}
    }
});

console.log("[AI-CONFIG] Active API URL:", MOCK_CONFIG.API_URL);
