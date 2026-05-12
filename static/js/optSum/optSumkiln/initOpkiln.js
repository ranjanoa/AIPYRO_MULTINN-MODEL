import { state } from "../../inits/state.js";

export function initOpkiln() {
     if (!state.currentModelConfig) return;

            // 1. Populate KPIs dynamically
            const kpiRow = document.getElementById('op-kpi-row-kiln');
            if (kpiRow && state.currentModelConfig.kpi_tags) {
                kpiRow.innerHTML = '';

                const hasKpiSummary = Object.values(state.currentModelConfig.kpi_tags).some(v => v.op_summary !== undefined);

                Object.keys(state.currentModelConfig.kpi_tags).forEach(kpiName => {
                    const tagInfo = state.currentModelConfig.kpi_tags[kpiName];

                    if (hasKpiSummary && tagInfo.op_summary !== true && tagInfo.op_summary !== "true") return;

                    kpiRow.innerHTML += `
                        <div class="flex-1 bg-[#1a3842] border border-gray-100 p-2 flex flex-col justify-between rounded min-w-[120px] max-h-[50px]">
                            <span class="text-[9px] font-bold text-gray-400 uppercase tracking-widest leading-none truncate" title="${kpiName}">${kpiName}</span>
                            <div class="flex items-baseline gap-1 mt-1">
                                <span class="text-lg font-black text-white font-mono leading-none" id="op3-kiln-kpi-${tagInfo.tag.replace(/[^a-zA-Z0-9]/g, '')}">---</span>
                                <span class="text-[8px] text-[#ebf552] font-bold uppercase leading-none">${tagInfo.unit || ''}</span>
                            </div>
                        </div>
                    `;
                });
            }

            // Trend Icon helper
            const getTrendBtn = (tag) => `
                <button onclick="Actions.toggleOpTrendKiln('${tag}')" id="op-trend-btn-kiln-${tag.replace(/[^a-zA-Z0-9]/g, '')}" class="text-gray-500 hover:text-[#ebf552] transition-colors focus:outline-none shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
                </button>
            `;

            // Row builder
            const buildRow = (tag, alias) => {
                const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
                return `
                <tr class="hover:bg-white/5 transition-colors">
                    <td class="p-1.5 text-gray-300 overflow-hidden align-middle">
                        <div class="flex items-center gap-1.5 w-full">
                            ${getTrendBtn(tag)}
                            <span class="truncate flex-1 min-w-0  font-bold text-white" title="${tag}">${alias}</span>
                        </div>
                    </td>
                    <td class="p-1.5 font-mono  font-bold text-right text-gray-300 font-black truncate align-middle" id="op3-kiln-cur-${safeId}">---</td>
                    <td class="p-1.5 font-mono  font-bold text-right text-gray-300 font-black truncate align-middle" id="op3-kiln-nsp-${safeId}">---</td>
                    <td class="p-1.5 font-mono  font-bold text-right text-gray-300  font-black pr-2 truncate align-middle" id="op3-kiln-tgt-${safeId}">---</td>
                </tr>`;
            };

            // 2. Populate Setpoints Tables dynamically or fallback
            const tKiln = document.getElementById('op-table-kilnsec');
            if (tKiln) tKiln.innerHTML = '';

            const ctrlVars = state.currentModelConfig.control_variables || {};
            const calcVars = state.currentModelConfig.calculated_variables || {};

            const allPotentialMVs = { ...ctrlVars };
            Object.keys(calcVars).forEach(k => {
                if (calcVars[k].is_control || calcVars[k].is_setpoint) {
                    allPotentialMVs[k] = { ...calcVars[k] };
                }
            });

            const hasCtrlSummary = Object.values(allPotentialMVs).some(v => v.op_summary !== undefined);

            if (hasCtrlSummary) {
                Object.keys(allPotentialMVs).forEach(tag => {
                    const v = allPotentialMVs[tag];
                    if (v.op_summary === true || v.op_summary === "true") {
                        const combined = (tag + " " + (v.description || "")).toLowerCase();
                        const alias = v.description || tag;

                        // Exclude Cooler/Preheater items if they leaked into config somehow
                        if (combined.includes('cooler') || combined.includes('grate') || combined.includes('grille') || combined.includes('filter')) return;
                        if (combined.includes('fan') || combined.includes('calciner') || combined.includes('cyclone') || combined.includes('flap') || combined.includes('gate') || combined.includes('tert') || combined.includes('quench')) return;

                        if (tKiln) tKiln.innerHTML += buildRow(tag, alias);
                    }
                });
            } else {
                // Legacy Fallback
                if (tKiln) {
                    tKiln.innerHTML =
                        buildRow("Kiln feed", "Kiln feed") +
                        buildRow("Kiln speed", "Kiln speed") +
                        buildRow("Petcoke (Kiln)", "Petcoke main burner") +
                        buildRow("RDF (Kiln)", "RDF main burner") +
                        buildRow("RIP (Kiln)", "RIP main burner");
                }
            }

            // 3. Populate Live Sensors dynamically (Standardized IDs & Position Sorting)
            const liveSensorsList = document.getElementById('op-live-sensors-list-kiln');
            if (liveSensorsList) {
                liveSensorsList.innerHTML = '';
                const indVars = state.currentModelConfig.indicator_variables || {};
                const ctrlVars = state.currentModelConfig.control_variables || {};
                const calcVars = state.currentModelConfig.calculated_variables || {};

                // Unified lookup
                const allVars = { ...indVars, ...ctrlVars, ...calcVars };

                // Filter: op_summary must be true AND position must exist
                const filtered = Object.keys(allVars).filter(tag => {
                    const v = allVars[tag];
                    return (v.op_summary === true || v.op_summary === "true") && (v.position !== undefined && v.position !== null);
                });

                // Sort: By numerical position
                filtered.sort((a, b) => {
                    const posA = parseInt(allVars[a].position) || 999;
                    const posB = parseInt(allVars[b].position) || 999;
                    return posA - posB;
                });

                filtered.forEach(tag => {
                    const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
                    const rowId = `op-live-row-kiln-${safeId}`;
                    const valId = `op-live-val-kiln-${safeId}`;

                    liveSensorsList.innerHTML += `
                        <div id="${rowId}" class="flex justify-between items-center border-b border-gray-100/10 py-1.5 hover:bg-white/5 transition-colors pl-1 pr-2">
                            <div class="flex items-center gap-1.5 text-gray-400 flex-1 min-w-0 overflow-hidden">
                                ${getTrendBtn(tag)}
                                <span class="truncate text-[11px] font-bold text-gray-300" title="${tag}">${tag}</span>
                            </div>
                            <div class="font-mono text-[11px] text-white font-black bg-[#122a33] px-1.5 py-0.5 rounded shadow-inner ml-1 shrink-0">
                                <span id="${valId}" class="font-mono font-bold px-2 rounded">---</span>
                            </div>
                        </div>
                    `;
                });
            }
}
