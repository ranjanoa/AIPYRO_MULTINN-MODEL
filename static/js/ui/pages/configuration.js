export function Configuration() {
    const container = document.createElement("div");
    container.className = "configuration-container hidden h-full flex-col gap-4 overflow-y-auto pr-2 custom-scrollbar";
    container.id = "panel-config"

    container.innerHTML = ` <div class="glass-panel border-l-yellow-600 fit-content p-4 border-l-4 border-l-[#ebf552] shrink-0 flex justify-between items-center bg-[#1a3842]">
                <div class="flex items-center gap-4">
                    <h3 class="text-lg font-bold text-white">System Configuration</h3>
                    <div class="h-6 w-px bg-white/10"></div>
                   
                    <label class="switch">
                                            <span class="label-text text-[10px] font-bold text-gray-500 group-hover:text-blue-400 mr-2 uppercase tracking-widest transition-colors">Developer Mode</span>

  <input type="checkbox" id="config-ui-toggle" onchange="Actions.toggleConfigView()">
  <span class="slider round"></span>
</label>
                </div>
                <button onclick="Actions.syncData()" class="hoverWhite bg-yellow-900 text-[#ebf552] border-gray-200 border border-[#ebf552] px-4 py-1.5 rounded hover:bg-[#ebf552] hover:text-[#122a33] text-xs font-bold transition-all shadow-sm active:scale-95">SYNC DATA LAKE</button>
            </div>

            <div id="config-table-view" class="flex flex-col gap-6 pb-8">
                <div class="glass-panel overflow-hidden border-gray-200 border border-white/5">
                    <div class="p-3 bg-white/5 border-b border-gray-200 border-white/10 flex justify-between items-center">
                        <h4 class="text-xs font-black text-white uppercase tracking-tighter">Active Optimization Strategy</h4>
                        <button id="toggle-strategy-btn" onclick="Actions.toggleConfigSection('config-strategy-content', 'toggle-strategy-btn')" class="text-white hover:text-yellow-400 font-bold transition-colors">▼</button>
                    </div>
                    <div id="config-strategy-content" class="hidden p-4 bg-[#0e2229]/50">
                        <div class="flex items-center gap-4">
                            <div class="flex-1">
                                <label class="text-[10px] font-bold text-white uppercase block mb-1">Select Strategy</label>
                                <select id="config-active-strategy" class="w-full border border-gray-300 rounded px-3 py-1.5 outline-none w-64 font-bold text-sm text-select-white"></select>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="glass-panel overflow-hidden border-gray-200 border border-white/5">
                    <div class="p-3 bg-white/5 border-b border-gray-200 border-white/10 flex justify-between items-center">
                        <h4 class="text-xs font-black text-white uppercase tracking-tighter">Control Variables (MVs)</h4>
                        <button id="toggle-controls-btn" onclick="Actions.toggleConfigSection('config-controls-content', 'toggle-controls-btn')" class="text-white hover:text-yellow-400 font-bold transition-colors">▼</button>
                    </div>
                    <div id="config-controls-content" class="hidden overflow-x-auto">
                        <table class="w-full text-left text-[11px]">
                            <thead>
                                <tr class="bg-[#122a33] text-gray-400 uppercase font-black border-gray-200 border-b border-[#476570]">
                                    <th class="px-4 text-white py-3">Variable Name</th>
                                    <th class="px-2 text-white py-3">Unit</th>
                                    <th class="px-2 text-white py-3">Min</th>
                                    <th class="px-2 text-white py-3">Max</th>
                                    <th class="px-2 text-white py-3">Priority</th>
                                    <th class="px-2 text-white py-3">Nudge</th>
                                    <th class="px-3 text-white py-3 text-center">AI Enable</th>
                                    <th class="px-3 text-white py-3 text-center">Filtering</th>
                                </tr>
                            </thead>
                            <tbody id="config-controls-body" class="divide-y divide-white/5"></tbody>
                        </table>
                    </div>
                </div>

                <div class="glass-panel overflow-hidden border border-gray-200 border-white/5">
                    <div class="p-3 bg-white/5 border-b border-gray-200 border-white/10 flex justify-between items-center">
                        <h4 class="text-xs font-black text-white uppercase tracking-tighter">Indicator Variables (Signal Filtering)</h4>
                        <button id="toggle-indicators-btn" onclick="Actions.toggleConfigSection('config-indicators-content', 'toggle-indicators-btn')" class="text-white hover:text-yellow-400 font-bold transition-colors">▼</button>
                    </div>
                    <div id="config-indicators-content" class="hidden overflow-x-auto">
                        <table class="w-full text-left text-[11px]">
                            <thead>
                                <tr class="bg-[#122a33] text-gray-400 uppercase font-black border-b border-gray-200 border-[#476570]">
                                    <th class="px-4 text-white py-3">Variable Name</th>
                                    <th class="px-2 text-white py-3">Unit</th>
                                    <th class="px-2 text-white py-3">Min</th>
                                    <th class="px-2 text-white py-3">Max</th>
                                    <th class="px-2 text-white py-3">Priority</th>
                                    <th class="px-2 text-white py-3">Nudge</th>
                                    <th class="px-4 text-white py-3 text-center">Filtering</th>
                                </tr>
                            </thead>
                            <tbody id="config-indicators-body" class="divide-y divide-white/5"></tbody>
                        </table>
                    </div>
                </div>

                <div class="glass-panel overflow-hidden border border-gray-200 border-white/5">
                    <div class="p-3 bg-white/5 border-b border-gray-200 border-white/10 flex justify-between items-center">
                        <h4 class="text-xs font-black text-white uppercase tracking-tighter text-orange-400">Upset Scenarios (Safety Overrides)</h4>
                        <button id="toggle-upsets-btn" onclick="Actions.toggleConfigSection('config-upsets-content', 'toggle-upsets-btn')" class="text-white hover:text-yellow-400 font-bold transition-colors">▼</button>
                    </div>
                    <div id="config-upsets-content" class="hidden overflow-x-auto">
                        <table class="w-full text-left text-[11px]">
                            <thead>
                                <tr class="bg-[#122a33] text-gray-400 uppercase font-black border-b border-gray-200 border-[#476570]">
                                    <th class="px-4 text-white py-3">Scenario ID</th>
                                    <th class="px-4 text-white py-3">Description</th>
                                    <th class="px-2 text-white py-3 text-center">Group</th>
                                    <th class="px-2 text-white py-3 text-center">Priority</th>
                                    <th class="px-4 text-white py-3 text-center">Enabled</th>
                                </tr>
                            </thead>
                            <tbody id="config-upsets-body" class="divide-y divide-white/5"></tbody>
                        </table>
                    </div>
                </div>

                <!-- AI_MNM Configuration Section -->
                <div class="glass-panel overflow-hidden border border-gray-200 border-white/5">
                    <div class="p-3 bg-white/5 border-b border-gray-200 border-white/10 flex justify-between items-center">
                        <h4 class="text-xs font-black text-white uppercase tracking-tighter text-[#ebf552]">AI_MNM — CV Parameters</h4>
                        <div class="flex gap-2">
                            <button onclick="Actions.saveAiMnmConfig('cv')" class="text-[10px] font-bold px-2 py-0.5 border border-[#ebf552] text-[#ebf552] rounded hover:bg-[#ebf552] hover:text-[#122a33] transition-colors">Save CVs</button>
                            <button id="toggle-ai-mnm-cv-btn" onclick="Actions.toggleConfigSection('config-ai-mnm-cv-content', 'toggle-ai-mnm-cv-btn')" class="text-white hover:text-yellow-400 font-bold transition-colors">▼</button>
                        </div>
                    </div>
                    <div id="config-ai-mnm-cv-content" class="hidden overflow-x-auto">
                        <table class="w-full text-left text-[11px]">
                            <thead>
                                <tr class="bg-[#122a33] text-gray-400 uppercase font-black border-gray-200 border-b border-[#476570]">
                                    <th class="px-4 text-white py-3">Parameter Name</th>
                                    <th class="px-2 text-white py-3">Label</th>
                                    <th class="px-2 text-white py-3">Unit</th>
                                    <th class="px-2 text-white py-3" title="Influx field name in cimpor_data_result for current value">Curr Field</th>
                                    <th class="px-2 text-white py-3" title="Influx field name in cimpor_data_result for AI set point">SP Field</th>
                                    <th class="px-2 text-white py-3" title="control_variables key (var_name) to override in Operator/Kiln/Preheater/Cooler when AI_MNM mode is active">Target Var</th>
                                    <th class="px-2 text-white py-3">Min</th>
                                    <th class="px-2 text-white py-3">Max</th>
                                    <th class="px-2 text-white py-3">Priority</th>
                                    <th class="px-2 text-white py-3">Nudge</th>
                                    <th class="px-2 text-white py-3">Position</th>
                                </tr>
                            </thead>
                            <tbody id="config-ai-mnm-cv-body" class="divide-y divide-white/5"></tbody>
                        </table>
                        <div class="p-2 flex justify-end">
                            <button onclick="Actions.saveAiMnmConfig('add-cv')" class="text-[10px] font-bold px-2 py-0.5 bg-[#152e36] border border-white/10 text-gray-300 rounded hover:bg-white/10">+ Add CV Row</button>
                        </div>
                    </div>
                </div>

                <div class="glass-panel overflow-hidden border border-gray-200 border-white/5">
                    <div class="p-3 bg-white/5 border-b border-gray-200 border-white/10 flex justify-between items-center">
                        <h4 class="text-xs font-black text-white uppercase tracking-tighter text-[#ebf552]">AI_MNM — Indicator Parameters</h4>
                        <div class="flex gap-2">
                            <button onclick="Actions.saveAiMnmConfig('ind')" class="text-[10px] font-bold px-2 py-0.5 border border-[#ebf552] text-[#ebf552] rounded hover:bg-[#ebf552] hover:text-[#122a33] transition-colors">Save Indicators</button>
                            <button id="toggle-ai-mnm-ind-btn" onclick="Actions.toggleConfigSection('config-ai-mnm-ind-content', 'toggle-ai-mnm-ind-btn')" class="text-white hover:text-yellow-400 font-bold transition-colors">▼</button>
                        </div>
                    </div>
                    <div id="config-ai-mnm-ind-content" class="hidden overflow-x-auto">
                        <table class="w-full text-left text-[11px]">
                            <thead>
                                <tr class="bg-[#122a33] text-gray-400 uppercase font-black border-gray-200 border-b border-[#476570]">
                                    <th class="px-4 text-white py-3">Parameter Name</th>
                                    <th class="px-2 text-white py-3">Label</th>
                                    <th class="px-2 text-white py-3">Unit</th>
                                    <th class="px-2 text-white py-3" title="Influx field name in cimpor_data_result — typically prefixed feat_ or suffixed _real / _optimized">Field (cimpor_data_result)</th>
                                    <th class="px-2 text-white py-3">Min</th>
                                    <th class="px-2 text-white py-3">Max</th>
                                    <th class="px-2 text-white py-3">Position</th>
                                </tr>
                            </thead>
                            <tbody id="config-ai-mnm-ind-body" class="divide-y divide-white/5"></tbody>
                        </table>
                        <div class="p-2 flex justify-end">
                            <button onclick="Actions.saveAiMnmConfig('add-ind')" class="text-[10px] font-bold px-2 py-0.5 bg-[#152e36] border border-white/10 text-gray-300 rounded hover:bg-white/10">+ Add Indicator Row</button>
                        </div>
                    </div>
                </div>

                <div class="glass-panel overflow-hidden border border-gray-200 border-white/5">
                    <div class="p-3 bg-white/5 border-b border-gray-200 border-white/10 flex justify-between items-center">
                        <h4 class="text-xs font-black text-white uppercase tracking-tighter text-blue-400">Simulator Settings</h4>
                        <button id="toggle-simulator-btn" onclick="Actions.toggleConfigSection('config-simulator-content', 'toggle-simulator-btn')" class="text-white hover:text-yellow-400 font-bold transition-colors">▼</button>
                    </div>
                    <div id="config-simulator-content" class="hidden p-4 bg-[#0e2229]/50">
                        <div class="flex items-center gap-4">
                            <div class="flex-1">
                                <label class="text-[10px] font-bold text-white uppercase block mb-1">Default "Color By" Variable</label>
                                <select id="config-sim-default-color" class="w-full border border-gray-300 rounded px-3 py-1.5 outline-none w-80 font-bold text-sm text-select-white"></select>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="flex justify-end pt-2">
                    <button onclick="Actions.saveTableConfig()" class="hoverWhite bg-yellow-900 border-gray-200 px-4 py-1.5 bg-[#ebf552] text-[#122a33] text-xs font-black uppercase rounded shadow-lg hover:brightness-110 active:scale-95 transition-all">Apply Changes</button>
                </div>
            </div>

            <div id="config-json-view" class="custom-container hidden flex-1 glass-panel flex flex-col min-h-0 bg-[#1a3842] border-2 border-dashed border-white/10">
                <div class="p-3 bg-red-900/10 border-gray-200 border-b border-white/5 flex justify-between items-center"><span class="text-white text-[10px] font-bold text-red-400 animate-pulse">!! STANDBY: RAW JSON EDITOR !!</span><span class="text-[9px] text-gray-500">Manual edit bypasses UI validation.</span></div>
                <textarea id="config-editor" class="flex-1 bg-[#0e2229] text-gray-300 p-6 font-mono text-sm resize-none border-none outline-none"></textarea>
                <div class="p-4 bg-[#152e36] border-gray-200  border-t border-[#476570] flex justify-end shrink-0 gap-4"><button onclick="Actions.saveConfig()" class="hoverWhite border-gray-200 px-4 py-1.5 bg-red-600 text-white text-xs font-black uppercase rounded hover:bg-red-500 shadow-xl transition-all active:scale-95">Overwrite JSON</button></div>
            </div>  `;


    return container;
}
