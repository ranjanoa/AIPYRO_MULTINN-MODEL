import {state} from "../inits/state.js";
import {updateAutoButtonUI} from "../updateFunctions/updateAutoButtonUI.js"
import {MOCK_CONFIG} from "../inits/config.js";

export async function toggleAutoMode(e) {
    if (state.isHybridEngaged) return; // Locked while active

    state.isAutoMode = !state.isAutoMode;
    const mode = state.isAutoMode ? 'AUTO' : 'MANUAL';
    
    updateAutoButtonUI();

    try {
        await fetch(`${MOCK_CONFIG.API_URL}/api/fingerprint/mode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: mode })
        });
    } catch (err) {
        console.error("Failed to persist fingerprint mode:", err);
    }
}