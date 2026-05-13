import {state} from "../inits/state.js";
import {MOCK_CONFIG} from "../inits/config.js";
import {refreshBatchListUI} from "./refreshBatchListUI.js";
import {updateAutoButtonUI} from "../updateFunctions/updateAutoButtonUI.js";
import {updateOpSummaryActions} from "../optSum/updateOpSummaryActions.js";
import {updateOpSummaryActionsKiln} from "../optSum/optSumkiln/updateOpSummaryActionsKiln.js";
import {updateOpSummaryActionsPreheater} from "../optSum/optSumPreheater/updateOpSummaryActionsPreheater.js";
import {updateOpSummaryActionsCooler} from "../optSum/optSumCooler/updateOpSummaryActionsCooler.js";
export async function toggleHybridSystem(forceState = null) {
    const btn = document.getElementById('btn-hybrid-engage');
    const statusEl = document.getElementById('hybrid-status-text');
    const indicator = document.getElementById('fp-active-indicator');
    
    // NEW: Get strategy from selected card
    const selectedBtn = document.querySelector('.mode-card.selected');
    const strategy = selectedBtn ? selectedBtn.dataset.mode : 'FINGERPRINT';
    
    const isTest = document.getElementById('test-mode-toggle').checked;

    if (forceState !== null) {
        state.isHybridEngaged = forceState;
    } else {
        state.isHybridEngaged = !state.isHybridEngaged;
    }

    if (state.isHybridEngaged) {
        btn.innerText = "DISENGAGE SYSTEM";
        selectedBtn.classList.add('engaged');
        
        if (isTest) {
            btn.className = "w-full py-4 rounded-lg font-black text-sm tracking-wider uppercase shadow-lg transform transition-all bg-yellow-500 text-[#08191F] border border-yellow-600 hover:bg-yellow-400";
            statusEl.innerText = `TEST MODE: ${strategy}`;
            statusEl.className = "text-center text-[10px] font-mono text-yellow-600 mt-2 font-bold animate-pulse";
        } else {
            btn.className = "w-full py-4 rounded-lg font-black text-sm tracking-wider uppercase shadow-lg transform transition-all bg-ai-cyan text-[#08191F] border border-cyan-400 hover:brightness-110";
            statusEl.innerText = `RUNNING: ${strategy}`;
            statusEl.className = "text-center text-[10px] font-mono text-ai-cyan mt-2 font-bold";
        }

        // Toggle Score Displays
        if (strategy === 'HYBRID') {
            document.getElementById('single-score-container').classList.add('hidden');
            document.getElementById('dual-score-container').classList.remove('hidden');
            document.getElementById('hybrid-score-mini').classList.remove('hidden');
        } else {
            document.getElementById('single-score-container').classList.remove('hidden');
            document.getElementById('dual-score-container').classList.add('hidden');
        }

        if (strategy === 'FINGERPRINT') {
            indicator.innerText = state.isAutoMode ? "LOCKED: AUTO-SCAN" : `LOCKED: BATCH #${state.selectedBatchIndex + 1}`;
            indicator.classList.remove('hidden');
        }
       
        if (document.getElementById('find-fingerprint-btn')) document.getElementById('find-fingerprint-btn').disabled = true;
        if (document.getElementById('btn-scan')) document.getElementById('btn-scan').disabled = true;
        if (document.getElementById('btn-auto-toggle')) document.getElementById('btn-auto-toggle').classList.add('opacity-50', 'cursor-not-allowed');
        refreshBatchListUI();

    } else {
        btn.innerText = "ENGAGE SYSTEM";
        document.querySelectorAll('.mode-card').forEach(c => c.classList.remove('engaged'));
        
        btn.className = "w-full py-4 rounded-lg font-black text-sm tracking-wider uppercase shadow-lg transform transition-all bg-slate-700 text-white border border-slate-500 hover:bg-slate-600";
        statusEl.innerText = "SYSTEM STANDBY";
        statusEl.className = "text-center text-[11px] font-mono text-gray-300 mt-2 font-black tracking-widest";
        document.getElementById('action-table-body').innerHTML = `<tr><td colspan="4" class="text-center py-12 text-gray-500 italic font-mono text-[10px]">SYSTEM MONITORING...<br>No Control Commands Active.</td></tr>`;
       
        indicator.classList.add('hidden');
        document.getElementById('hybrid-score-mini').classList.add('hidden');
        document.getElementById('single-score-container').classList.remove('hidden');
        document.getElementById('dual-score-container').classList.add('hidden');
       
        if (document.getElementById('find-fingerprint-btn')) document.getElementById('find-fingerprint-btn').disabled = false;
        if (document.getElementById('btn-scan')) document.getElementById('btn-scan').disabled = false;
        if (document.getElementById('btn-auto-toggle')) document.getElementById('btn-auto-toggle').classList.remove('opacity-50', 'cursor-not-allowed');
       
        // CRITICAL: Reset Auto Mode on Disengage if needed
        // but keep it as-is for the UI
        
        refreshBatchListUI();
        updateOpSummaryActions({ actions: [] });
        updateOpSummaryActionsKiln({ actions: [] });
        updateOpSummaryActionsPreheater({ actions: [] });
        updateOpSummaryActionsCooler({ actions: [] });
    }

    let payload = {enabled: state.isHybridEngaged, strategy: strategy, test_mode: isTest};
    
    // NEW: If AI_MNM is selected, also send the chosen base strategy
    if (strategy === 'AI_MNM') {
        const baseModeEl = document.getElementById('ai-mnm-base-mode');
        if (baseModeEl) {
            payload.base_strategy = baseModeEl.value;
        }
    }

    if (state.isHybridEngaged && strategy === 'FINGERPRINT') {
        if (state.isAutoMode) {
            payload.target_batch = null; // Auto Mode Trigger
        } else if (state.allRecommendations && state.allRecommendations.length > 0 && state.selectedBatchIndex >= 0) {
            payload.target_batch = state.allRecommendations[state.selectedBatchIndex]; // Manual Mode
        }
    }

    try {
        await fetch(`${MOCK_CONFIG.API_URL}/api/autoloop`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
    } catch (e) {
        console.error("API Error", e);
        if (!state.dataFlow.isStalled) state.isHybridEngaged = !state.isHybridEngaged;
    }
}

