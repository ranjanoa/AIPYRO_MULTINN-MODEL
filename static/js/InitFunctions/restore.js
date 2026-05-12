import { MOCK_CONFIG } from "../inits/config.js"
 import { state } from "../inits/state.js";
import {updateAutoButtonUI} from "../updateFunctions/updateAutoButtonUI.js"
export async function restoreState() {
        try {
            const response = await fetch(`${MOCK_CONFIG.API_URL}/api/status`);
            const data = await response.json();

            if (data.test_mode === true) {
                const toggle = document.getElementById('test-mode-toggle');
                if (toggle) {
                    toggle.checked = true;
                }
            }
 
            if (data.strategy) {
                // Update modern UI mode cards
                const modeCard = document.querySelector(`.mode-card[data-mode="${data.strategy}"]`);
                if (modeCard) {
                    document.querySelectorAll('.mode-card').forEach(c => c.classList.remove('selected'));
                    modeCard.classList.add('selected');
                    
                    const sub = modeCard.querySelector(".fp-sub-options");
                    if (sub) sub.classList.remove("opacity-60", "pointer-events-none");

                    if (data.enabled) {
                        modeCard.classList.add('engaged');
                    }
                }
                
                // Legacy radio sync
                const strategyRadio = document.querySelector(`input[name="strategy_select"][value="${data.strategy}"]`);
                if (strategyRadio) strategyRadio.checked = true;
            }

            // --- RESTORE PREFERRED MODE (Even if not engaged) ---
            if (data.fingerprint_type === 'AUTO') {
                state.isAutoMode = true;
                updateAutoButtonUI();
            } else if (data.fingerprint_type === 'MANUAL') {
                state.isAutoMode = false;
                updateAutoButtonUI();
            }

            if (data.enabled) {
                state.isHybridEngaged = true;
                const btn = document.getElementById('btn-hybrid-engage');
                const statusEl = document.getElementById('hybrid-status-text');

                if (btn) btn.innerText = "DISENGAGE SYSTEM";

                if (data.test_mode) {
                    if (btn) btn.className = "w-full py-4 rounded-lg font-black text-sm tracking-wider uppercase shadow-lg transform transition-all bg-yellow-500 text-black border border-yellow-600 hover:bg-yellow-400";
                    if (statusEl) {
                        statusEl.innerText = `TEST MODE ACTIVE: ${data.strategy}`;
                        statusEl.className = "text-center text-[10px] font-mono text-yellow-600 mt-2 font-bold animate-pulse";
                    }
                } else {
                    if (btn) btn.className = "w-full py-4 rounded-lg font-black text-sm tracking-wider uppercase shadow-lg transform transition-all bg-ai-cyan text-blackOff border border-cyan-400 hover:brightness-110";
                    if (statusEl) {
                        statusEl.innerText = `SYSTEM ACTIVE: ${data.strategy}`;
                        statusEl.className = "text-center text-[10px] font-mono text-ai-cyan mt-2 font-bold";
                    }
                }

                    if (data.fingerprint_type === 'MANUAL' && data.active_target) {
                        const indicator = document.getElementById('fp-active-indicator');
                        if (indicator) {
                            indicator.innerText = `ACTIVE: ${data.active_target.fingerprint_timestamp || 'Manual Selection'}`;
                            indicator.classList.remove('hidden');
                        }
                        const lockMsg = document.getElementById('batch-lock-msg');
                        if (lockMsg) lockMsg.classList.remove('hidden');
                    } else if (data.fingerprint_type === 'AUTO') {
                        const indicator = document.getElementById('fp-active-indicator');
                        if (indicator) {
                            indicator.innerText = "ACTIVE: AUTO-SEARCH";
                            indicator.classList.remove('hidden');
                        }
                    }

                    // Lock controls if engaged
                    const findBtn = document.getElementById('find-fingerprint-btn');
                    if (findBtn) findBtn.disabled = true;
                    
                    const scanBtn = document.getElementById('btn-scan');
                    if (scanBtn) scanBtn.disabled = true;
                    
                    const autoTog = document.getElementById('btn-auto-toggle');
                    if (autoTog) autoTog.classList.add('opacity-50', 'cursor-not-allowed');
            }
        } catch (error) {
            console.error("State Restore Failed:", error);
        }
    }
