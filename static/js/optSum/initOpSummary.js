import { state } from "../inits/state.js";

export function initOpSummary() {
     if (!state.currentModelConfig) return;

            // 1. Populate KPIs dynamically
            const kpiRow = document.getElementById('op-kpi-row');
            if (kpiRow && state.currentModelConfig.kpi_tags) {
                kpiRow.innerHTML = '';

                const hasKpiSummary = Object.values(state.currentModelConfig.kpi_tags).some(v => v.op_summary !== undefined);

                Object.keys(state.currentModelConfig.kpi_tags).forEach(kpiName => {
                    const tagInfo = state.currentModelConfig.kpi_tags[kpiName];

                    if (hasKpiSummary && tagInfo.op_summary !== true && tagInfo.op_summary !== "true") return;

                    kpiRow.innerHTML += `
                        <div class="flex-1 bg-[#1a3842] border border-gray-100 p-2 flex flex-col justify-between rounded min-w-[120px] max-h-[50px]">
                            <span class="text-[9px] font-bold text-white uppercase tracking-widest leading-none truncate" title="${kpiName}">${kpiName}</span>
                            <div class="flex items-baseline gap-1 mt-1">
                                <span class="text-lg font-black text-white font-mono leading-none" id="op3-kpi-${tagInfo.tag.replace(/[^a-zA-Z0-9]/g, '')}">---</span>
                                <span class="text-[10px] text-[#ebf552] text-white font-bold uppercase leading-none">${tagInfo.unit || ''}</span>
                            </div>
                        </div>
                    `;
                });
            }

            // Trend Icon helper
            const getTrendBtn = (tag) => `
                <button onclick="Actions.toggleOpTrend('${tag}')" id="op-trend-btn-${tag.replace(/[^a-zA-Z0-9]/g, '')}" class="text-white hover:text-[#ebf552] transition-colors focus:outline-none shrink-0">
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
                            <span class="truncate flex-1 min-w-0 text-[11px] font-bold text-white" title="${tag}">${alias}</span>
                        </div>
                    </td>
                    <td class="p-1.5 font-mono text-[11px] text-right text-white font-black truncate align-middle" id="op3-cur-${safeId}">---</td>
                    <td class="p-1.5 font-mono text-[11px] text-right font-black  text-white truncate align-middle" id="op3-nsp-${safeId}">---</td>
                    <td class="p-1.5 font-mono text-[11px] text-right text-white font-black pr-2 truncate align-middle" id="op3-tgt-${safeId}">---</td>
                </tr>`;
            };

            // 2. Populate Setpoints Tables dynamically or fallback
            const tKiln = document.getElementById('op-table-kiln');
            const tPh = document.getElementById('op-table-phpc');
            const tCooler = document.getElementById('op-table-cooler');

            if (tKiln) tKiln.innerHTML = '';
            if (tPh) tPh.innerHTML = '';
            if (tCooler) tCooler.innerHTML = '';

            const ctrlVars = state.currentModelConfig.control_variables || {};
            const calcVars = state.currentModelConfig.calculated_variables || {};

            const allPotentialMVs = { ...ctrlVars };
            // Inject calculated setpoints/controls
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

                        if (combined.includes('cooler') || combined.includes('grate') || combined.includes('grille') || combined.includes('filter')) {
                            if (tCooler) tCooler.innerHTML += buildRow(tag, alias);
                        } else if (combined.includes('fan') || combined.includes('calciner') || combined.includes('cyclone') || combined.includes('flap') || combined.includes('gate') || combined.includes('tert') || combined.includes('quench')) {
                            if (tPh) tPh.innerHTML += buildRow(tag, alias);
                        } else {
                            if (tKiln) tKiln.innerHTML += buildRow(tag, alias);
                        }
                    }
                });
            } else {
                // Legacy Fallback
                if (tKiln) {
                    tKiln.innerHTML =
                        buildRow("Kiln feed", "Kiln feed") +
                        buildRow("Kiln speed", "Kiln speed") +
                        buildRow("Petcoke (Kiln)", "Petcoke main") +
                        buildRow("RDF (Kiln)", "RDF main bur") +
                        buildRow("RIP (Kiln)", "RIP (liquids) n");
                }
                if (tPh) {
                    tPh.innerHTML =
                        buildRow("ID fan speed", "ID fan speed") +
                        buildRow("Petcoke (PC)", "Petcoke calciner") +
                        buildRow("RDF 1 (PC)", "RDF calciner 1") +
                        buildRow("RDF 2 (PC)", "RDF calciner 2") +
                        buildRow("Tert air damper", "Tert. air damp") +
                        buildRow("Dividing gate", "Dividing gate pos") +
                        buildRow("Quench fan gas flow", "Quench fan flow");
                }
                if (tCooler) {
                    tCooler.innerHTML =
                        buildRow("Cooler speed (central 1)", "Cooler grate C1") +
                        buildRow("Cooler speed (central 2)", "Cooler grate C2") +
                        buildRow("Cooler speed (left)", "Cooler grate L") +
                        buildRow("Cooler speed (right)", "Cooler grate R") +
                        buildRow("Cooler BF fan motor speed", "Cooler BF fan");
                }
            }

            // 3. Populate Live Sensors dynamically (Standardized IDs & All Categories)
            const liveSensorsList = document.getElementById('op-live-sensors-list');
            if (liveSensorsList) {
                liveSensorsList.innerHTML = '';
                const indVars = state.currentModelConfig.indicator_variables || {};
                const ctrlVars = state.currentModelConfig.control_variables || {};
                const calcVars = state.currentModelConfig.calculated_variables || {};

                // Unified lookup: Include all categories
                const allVars = { ...indVars, ...ctrlVars, ...calcVars };

                // Filter: Must have op_summary: true AND a defined position
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
                    const rowId = `op-live-row-${safeId}`;
                    const valId = `op-live-val-${safeId}`;

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
