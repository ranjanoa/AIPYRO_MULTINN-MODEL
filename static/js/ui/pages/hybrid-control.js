import { state } from "../../inits/state.js";
export function HybridControl() {
    const container = document.createElement("div");
    container.className = "hybrid-control-container grid grid-cols-12 gap-4 h-full w-full transition-grid";
    container.id = "panel-hybrid"

    container.innerHTML = `
        <div class="col-span-3 glass-panel flex flex-col overflow-hidden transition-all duration-300" id="system-control">
            <div class="p-4 border-b border-yellow-200 bg-yellow-900  text-blackOff flex justify-between items-center shrink-0">
                <h2 class="text-sm font-bold tracking-wider">SYSTEM CONTROL</h2>
                <div id="hybrid-connection-dot" class="w-2 h-2 rounded-full bg-red-500"></div>
            </div>
            <div class="p-5 bg-dark-green flex-1 overflow-y-auto flex flex-col gap-4">
                <div>
                    <label class="text-xs font-bold text-whiteoff uppercase tracking-wider mb-3 block">Strategy Selection</label>
                    <div class="space-y-3" id="mode-selector">
                        <!-- FINGERPRINT CARD -->
                        <div class="mode-card p-3 rounded-lg cursor-pointer border border-[#476570] group relative" data-mode="FINGERPRINT">
                            <div class="flex justify-between items-start mb-2">
                                <div>
                                    <div class="font-bold text-white text-sm">Fingerprint Match</div>
                                    <div class="text-[10px] text-gray-400">Historical Best-Fit Search</div>
                                </div>
                                <div class="mode-status-icon w-3 h-3 rounded-full border border-gray-600 mt-1"></div>
                            </div>
                            <div class="fp-sub-options flex items-center gap-2 mt-2 pt-2 border-t border-white/5 opacity-60 pointer-events-none transition-all duration-300">
                                <button onclick="Actions.toggleAutoMode(event)" id="btn-auto-toggle" class="text-[9px] font-bold px-2 py-1 rounded bg-[#122a33] border border-gray-600 text-gray-400 hover:text-white transition-all">
                                    MANUAL
                                </button>
                                <span class="text-[9px] text-gray-500 italic">Continuous scan off</span>
                            </div>
                        </div>

                        <!-- NEURAL NETWORK CARD -->
                        <div class="mode-card p-3 rounded-lg cursor-pointer border border-[#476570] group" data-mode="AI">
                            <div class="flex justify-between items-start">
                                <div>
                                    <div class="font-bold text-white text-sm">Neural Network (SAC)</div>
                                    <div class="text-[10px] text-gray-400">Deep Learning Optimizer</div>
                                </div>
                                <div class="mode-status-icon w-3 h-3 rounded-full border border-gray-600 mt-1"></div>
                            </div>
                        </div>

                        <!-- HYBRID CARD -->
                        <div class="mode-card p-3 rounded-lg cursor-pointer border border-[#476570] group" data-mode="HYBRID">
                            <div class="flex justify-between items-start">
                                <div>
                                    <div class="font-bold text-white text-sm">Hybrid Auto-Arb.</div>
                                    <div class="text-[10px] text-gray-400">Dynamic Multi-Agent Logic</div>
                                </div>
                                <div class="mode-status-icon w-3 h-3 rounded-full border border-gray-600 mt-1"></div>
                            </div>
                            <div id="hybrid-score-mini" class="mt-2 pt-2 border-t border-white/5 hidden">
                                <div class="flex justify-between text-[9px] font-mono text-gray-400">
                                    <span>FP: <span id="mini-fp-score">0</span>%</span>
                                    <span>NN: <span id="mini-nn-score">0</span>%</span>
                                </div>
                            </div>
                        </div>

                        <!-- AI_MNM CARD -->
                        <div class="mode-card p-3 rounded-lg cursor-pointer border border-[#476570] group" data-mode="AI_MNM">
                            <div class="flex justify-between items-start">
                                <div>
                                    <div class="font-bold text-white text-sm">AI_MNM</div>
                                    <div class="text-[10px] text-gray-400">Override 6 CV SPs from cimpor_data_result · base mode supplies the rest</div>
                                </div>
                                <div class="mode-status-icon w-3 h-3 rounded-full border border-gray-600 mt-1"></div>
                            </div>
                            <div class="mt-2 pt-2 border-t border-white/5">
                                <label class="flex items-center justify-between gap-2">
                                    <span class="text-[9px] text-gray-400 uppercase tracking-wider">Base mode</span>
                                    <select id="ai-mnm-base-mode" onclick="event.stopPropagation()"
                                            style="background-color:#122a33;color:#fff;"
                                            class="text-[10px] border border-gray-600 rounded px-1 py-0.5">
                                        <option value="FINGERPRINT" style="background-color:#122a33;color:#fff;">Fingerprint</option>
                                        <option value="AI"          style="background-color:#122a33;color:#fff;">Neural Network</option>
                                        <option value="HYBRID"      style="background-color:#122a33;color:#fff;">Hybrid</option>
                                    </select>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="border-t border-[#476570] pt-4">
                    <label class="flex items-center justify-between cursor-pointer group">
                        <div>
                            <span class="font-bold text-sm text-whiteoff group-hover:text-white">Test Mode</span>
                            <div class="text-[10px] text-gray-400 italic">Bypass standard safety interlocks</div>
                        </div>
                        <div class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" id="test-mode-toggle" class="sr-only peer">
                            <div class="w-10 h-5 bg-gray-700 rounded-full peer peer-focus:ring-1 peer-focus:ring-blue-300 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-yellow-500"></div>
                        </div>
                    </label>
                </div>
                
                <div class="border-t border-[#476570] pt-4">
                    <label class="text-xs font-bold text-whiteoff uppercase tracking-wider mb-2 block">Process Insight Log</label>
                    <div id="hybrid-insight-log"
                        class="bg-black/40 border border-[#2a3b40] rounded p-2 overflow-y-auto font-mono text-[9px] text-gray-400 space-y-2 custom-scrollbar"
                        style="max-height: 150px;">
                        <div class="text-blue-400 italic">Initializing insight monitor...</div>
                    </div>
                </div>

                <div class="mt-auto pt-4 border-t border-[#476570]">
                    <button id="btn-hybrid-engage" onclick="Actions.toggleHybridSystem()"
                            class="w-full py-4 rounded-lg font-black text-sm tracking-wider uppercase shadow-lg transform transition-all active:scale-95 bg-slate-700 text-white border border-slate-500 hover:bg-slate-600">
                        ENGAGE SYSTEM
                    </button>
                    <div id="hybrid-status-text" class="text-center text-[10px] font-mono text-gray-500 mt-2 font-bold uppercase">
                        SYSTEM STANDBY
                    </div>
                </div>
            </div>
        </div>

        <div class="col-span-6 flex flex-col gap-4 h-full overflow-hidden">
            <div id="score-block" class="glass-panel p-5 bg-white shrink-0">
                <div class="flex justify-between items-end mb-3">
                    <div id="active-driver-container" class="flex items-center">
                        <h3 class="text-xs font-bold text-whiteoff mr-2">Active Adjustments</h3>
                    </div>
                    <div id="conf-badge" class="px-2 py-1 bg-gray-100 text-[9px] font-black rounded uppercase tracking-tighter shadow-sm border border-gray-200">STANDBY</div>
                </div>
                
                <!-- SINGLE SCORE BAR (FINGERPRINT / NN) -->
                <div id="single-score-container" class="space-y-1">
                    <div class="flex items-center gap-2">
                        <div class="flex items-baseline gap-1">
                             <span id="conf-val" class="text-3xl font-black text-whiteoff tracking-tighter">0</span>
                             <span class="text-[10px] text-whiteoff opacity-50 font-bold">%</span>
                        </div>
                        <div class="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden relative">
                            <div id="conf-bar" class="h-full bg-gray-300 transition-all duration-500 rounded-full" style="width: 0%"></div>
                        </div>
                    </div>
                </div>

                <!-- DUAL SCORE BAR (HYBRID) -->
                 <div id="dual-score-container" class="hidden grid grid-cols-2 gap-6 pt-1">
                    <div class="space-y-1">
                        <div class="flex justify-between items-center text-[11px] font-black text-gray-400 uppercase tracking-widest">
                            <span>Fingerprint</span>
                            <span id="fp-confidence-text" class="text-white text-sm font-black">0%</span>
                        </div>
                        <div class="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div id="fp-conf-bar" class="h-full bg-blue-500 transition-all duration-500" style="width: 0%"></div>
                        </div>
                    </div>
                    <div class="space-y-1">
                        <div class="flex justify-between items-center text-[11px] font-black text-gray-400 uppercase tracking-widest">
                            <span>Neural Network</span>
                            <span id="nn-confidence-text" class="text-white text-sm font-black">0%</span>
                        </div>
                        <div class="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div id="nn-conf-bar" class="h-full bg-cyan-500 transition-all duration-500" style="width: 0%"></div>
                        </div>
                    </div>
                </div>

                 <div id="fp-active-indicator" class="mt-3 text-[10px] font-mono font-bold text-white bg-blue-600 px-3 py-1.5 rounded border border-blue-400 shadow-lg hidden animate-pulse">
                    LOCKED: None
                </div>
            </div>

            <div class="glass-panel flex flex-col overflow-hidden flex-1 bg-white relative">
                <div id="data-stall-overlay"
                     class="absolute inset-0 bg-dark-green/95 backdrop-blur-sm z-50 flex flex-col items-center justify-center hidden">
                    <div class="text-red-500 font-black text-2xl animate-pulse tracking-tighter mb-1">⚠️ DATA STALLED</div>
                    <div class="text-gray-400 font-bold text-[10px] uppercase tracking-widest">Communication Failure / No Updates</div>
                </div>

                <div class="p-3 border-b border-gray-200/10 bg-dark-green flex justify-between items-center shrink-0">
                    <div class="flex items-center gap-2">
                        <div class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
                        <span class="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Live Optimization Engine</span>
                    </div>
                    <span class="text-[10px] text-white font-mono bg-black/30 px-2 py-0.5 rounded border border-white/10 shadow-inner" id="last-update-time">WAITING...</span>
                </div>
                <div class="flex-1 overflow-y-auto p-2">
                    <table class="action-table">
                        <thead>
                                <tr>
                                    <th class="pl-3">Variable</th>
                                    <th>Current</th>
                                    <th>Nudge</th>
                                    <th>Target</th>
                                </tr>
                            </thead>
                        <tbody id="action-table-body">
                        <tr>
                            <td colspan="4" class="text-center py-12 text-gray-500 italic font-mono text-[10px]">
                                SYSTEM MONITORING...<br>No Control Commands Active.
                            </td>
                        </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="col-span-3 glass-panel flex flex-col overflow-hidden bg-white">
            <div class="bg-yellow-900 text-[#122a33] text-[10px] font-black uppercase p-3 flex justify-between items-center shrink-0 shadow-md">
                LIVE SENSORS <span class="text-[8px] px-2 py-0.5 font-bold opacity-70 border border-black rounded">SITE-WIDE VIEW</span>
            </div>
            <div id="hybrid-sensor-list" class="flex-1 overflow-y-auto p-4 space-y-1.5 bg-dark-green/30 font-mono text-xs custom-scrollbar"></div>
    `;

    // --- SELECTION LOGIC ---
    setTimeout(() => {
        const cards = container.querySelectorAll(".mode-card");
        const modeSelector = (selectedMode) => {
            cards.forEach((c) => {
                c.classList.remove("selected");
                const sub = c.querySelector(".fp-sub-options");
                if (sub) {
                    sub.classList.add("opacity-60", "pointer-events-none");
                }
            });

            const active = container.querySelector(`.mode-card[data-mode="${selectedMode}"]`);
            if (active) {
                active.classList.add("selected");
                const sub = active.querySelector(".fp-sub-options");
                if (sub) {
                    sub.classList.remove("opacity-60", "pointer-events-none");
                }
            }
        };

        cards.forEach((card) => {
            card.addEventListener("click", () => {
                modeSelector(card.dataset.mode);
                // If already engaged, trigger the update immediately to backend
                if (state.isHybridEngaged) {
                    Actions.toggleHybridSystem(true);
                }
            });
        });

        const baseModeSelector = container.querySelector("#ai-mnm-base-mode");
        if (baseModeSelector) {
            baseModeSelector.addEventListener("change", () => {
                if (state.isHybridEngaged) {
                    Actions.toggleHybridSystem(true);
                }
            });
        }

        // Apply default selection ONLY if none was restored by the system state
        setTimeout(() => {
            if (!container.querySelector('.mode-card.selected')) {
                modeSelector("FINGERPRINT");
            }
        }, 50);
    }, 0);

    return container;
}
