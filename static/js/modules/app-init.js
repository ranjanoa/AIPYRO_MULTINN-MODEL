import { MOCK_CONFIG } from "../inits/config.js"
import { initRealTimeList } from "../InitFunctions/initRealTimeList.js"
import { initTrendDropdown } from "../InitFunctions/initTrendDropdown.js"
import { initSimulatorControls } from "../InitFunctions/initSimulatorControls.js"
import { populateMbrlDropdowns } from "../InitFunctions/populateMbrlDropdowns.js"
import { initSoftSensorDropdown } from "../InitFunctions/initSoftSensorDropdown.js"
import { initSoftSensorSim } from "../InitFunctions/initSoftSensorSim.js"
import { populateSettingsPanel } from "../InitFunctions/populateSettingsPanel.js"
import { state } from "../inits/state.js";
import { populateConfigUI} from "../InitFunctions/populateConfigUI.js"

export async function initializeApp() {
    try {
        const confRes = await fetch(`${MOCK_CONFIG.API_URL}/api/config`);
        if (!confRes.ok) throw new Error("Offline");
        state.currentModelConfig = await confRes.json();
    } catch (e) {
        state.currentModelConfig = {};
        document.getElementById('socket-status').innerText = 'DEMO';
    }
    document.getElementById('config-editor').value = JSON.stringify(state.currentModelConfig, null, 2);
    populateConfigUI(state.currentModelConfig);

    initRealTimeList();
    initTrendDropdown();
    initSimulatorControls();
    populateMbrlDropdowns(state.currentModelConfig);
    initSoftSensorDropdown();
    initSoftSensorSim();
    const combined = {};
    const cvs = state.currentModelConfig.control_variables || {};
    Object.keys(cvs).forEach(k => {
        combined[k] = {
            Lower: 98,
            Higher: 102,
            // FIX: Check explicitly if undefined, allowing 0 to pass through
            Min: cvs[k].default_min !== undefined ? cvs[k].default_min : -9999,
            Max: cvs[k].default_max !== undefined ? cvs[k].default_max : 9999,
            priority: cvs[k].priority || 5
        };
    });
    state.controlDefaults = combined;
    populateSettingsPanel(state.controlDefaults);
}
