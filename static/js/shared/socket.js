import { MOCK_CONFIG } from "../inits/app_config.js"
import { updateLiveUI } from "../updateFunctions/updateLiveUI.js";
import { updateHybridLive } from "../updateFunctions/updateHybridLive.js";
import { updateMbrlLive } from "../updateFunctions/updateMbrlLive.js";
import { updateHybridDashboard } from "../updateFunctions/updateHybridDashboard.js";
import { updateMbrlUI } from "../updateFunctions/updateMbrlUI.js";
import { state } from "../inits/state.js"
import { updateOpSummary } from "../optSum/updateOpSummary.js"
import { updateOpSummaryLive } from "../optSum/updateOpSummaryLive.js"
import { updateOpSummaryActions } from "../optSum/updateOpSummaryActions.js"
import { updateOpSummaryActionsKiln } from "../optSum/optSumkiln/updateOpSummaryActionsKiln.js";
import { updateOpSummaryActionsPreheater } from "../optSum/optSumPreheater/updateOpSummaryActionsPreheater.js";
import { updateOpSummaryActionsCooler } from "../optSum/optSumCooler/updateOpSummaryActionsCooler.js";
import { updateOpPreheater } from "../optSum/optSumPreheater/updateOppreheater.js";
import { updateOpPreheaterLive } from "../optSum/optSumPreheater/updateOpPreheaterLive.js";
import { updateOpkiln } from "../optSum/optSumkiln/updateOpkiln.js";
import { updateOpKilnLive } from "../optSum/optSumkiln/updateOpKilnLive.js";
import { updateCooler } from "../optSum/optSumCooler/updateOpCooler.js";
import { updateOpCoolerLive } from "../optSum/optSumCooler/updateOpCoolerLive.js";

let socket = null;
let stallInterval = null;
let uiUpdateInterval = null;

// BUFFER DATA
let latestLiveData = null;
let latestAutopilotData = null;

// ROBUSTNESS REGISTRY: Tracks unique errors to prevent console spam
const errorRegistry = new Set();

/**
 * Executes an update function safely within a try-catch block.
 * Isolated execution ensures one component crash doesn't halt the entire loop.
 */
function safeExecute(fn, data, label) {
    if (typeof fn !== 'function') return;
    try {
        fn(data);
        // Clear from registry if it succeeded this time
        if (errorRegistry.has(label)) {
            console.info(`[RECOVERY] ${label} has resumed normal operation.`);
            errorRegistry.delete(label);
        }
    } catch (e) {
        if (!errorRegistry.has(label)) {
            console.error(`[CRITICAL] UI Update Failed in ${label}:`, e.message);
            errorRegistry.add(label);
        }
    }
}

function setStatus(text, className) {
    const status = document.getElementById('socket-status');
    const dot = document.getElementById('socket-status-dot');

    if (status) status.innerText = text;
    if (dot) dot.className = className;
}

function showOverlay(show) {
    const overlay = document.getElementById('data-stall-overlay');
    if (!overlay) return;

    if (show) overlay.classList.remove('hidden');
    else overlay.classList.add('hidden');
}

export function initSocket() {
    if (socket) {
        console.log("Socket already initialized");
        return socket;
    }

    try {
        socket = io(MOCK_CONFIG.API_URL, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: Infinity,
            reconnectionDelay: 2000,
            timeout: 20000
        });

        // CONNECT
        socket.on('connect', () => {
            console.log("Socket Connected");
            setStatus('LIVE', 'w-2 h-2 rounded-full bg-green-500');
        });

        // DISCONNECT
        socket.on('disconnect', () => {
            console.log("Socket Disconnected");
            setStatus('DISCONNECTED', 'w-2 h-2 rounded-full bg-gray-500');
        });

        // STORE DATA ONLY (NO UI UPDATE HERE)
        socket.on('live_values', (data) => {
            // DIAGNOSTIC: Print raw data to console for machine-to-machine comparison
            if (Math.random() > 0.95) { // Log every ~10 seconds to avoid flooding
                console.log("[DIAGNOSTIC] Raw Telemetry from Server:", data);
            }
            state.dataFlow.lastDataTime = Date.now();
            state.latestLiveValues = { ...state.latestLiveValues, ...data };
            latestLiveData = data;

            if (state.dataFlow.isStalled) {
                state.dataFlow.isStalled = false;
                setStatus('LIVE', 'w-2 h-2 rounded-full bg-green-500');
                showOverlay(false);
            }
        });

        socket.on('autopilot_update', (data) => {
            latestAutopilotData = data;
        });

        // UI UPDATE LOOP (Every 1.5 sec)
        if (!uiUpdateInterval) {
            uiUpdateInterval = setInterval(() => {

                if (latestLiveData) {
                    safeExecute(updateLiveUI, latestLiveData, 'LiveUI');
                    safeExecute(updateHybridLive, latestLiveData, 'HybridLive');
                    safeExecute(updateMbrlLive, latestLiveData, 'MbrlLive');
                    safeExecute(updateOpSummary, latestLiveData, 'OpSummary');
                    safeExecute(updateOpPreheater, latestLiveData, 'OpPreheater');
                    safeExecute(updateOpkiln, latestLiveData, 'OpKiln');
                    safeExecute(updateCooler, latestLiveData, 'Cooler');
                    safeExecute(updateOpSummaryLive, latestLiveData, 'OpSummaryLive');
                    safeExecute(updateOpKilnLive, latestLiveData, 'OpKilnLive');
                    safeExecute(updateOpPreheaterLive, latestLiveData, 'OpPreheaterLive');
                    safeExecute(updateOpCoolerLive, latestLiveData, 'OpCoolerLive');
                }

                if (latestAutopilotData) {
                    safeExecute(updateHybridDashboard, latestAutopilotData, 'HybridDashboard');
                    safeExecute(updateMbrlUI, latestAutopilotData, 'MbrlUI');
                    safeExecute(updateOpSummaryActions, latestAutopilotData, 'OpSummaryActions');
                    safeExecute(updateOpSummaryActionsKiln, latestAutopilotData, 'OpSummaryActionsKiln');
                    safeExecute(updateOpSummaryActionsCooler, latestAutopilotData, 'OpSummaryActionsCooler');
                    safeExecute(updateOpSummaryActionsPreheater, latestAutopilotData, 'OpSummaryActionsPreheater');
                }

            }, 1500);
        }

        // DATA STALL CHECK
        if (!stallInterval) {
            stallInterval = setInterval(() => {
                if (!state.dataFlow.lastDataTime) return;

                if (Date.now() - state.dataFlow.lastDataTime > 100000 && !state.dataFlow.isStalled) {
                    state.dataFlow.isStalled = true;
                    setStatus('DATA STALLED', 'w-2 h-2 rounded-full bg-red-600 animate-pulse');
                    showOverlay(true);
                }
            }, 1000);
        }

        return socket;

    } catch (e) {
        console.warn("Socket Error", e);
    }
}
