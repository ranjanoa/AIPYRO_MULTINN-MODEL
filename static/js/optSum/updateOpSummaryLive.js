import { state} from "../inits/state.js";

// Cache: track which sensor rows have already been created in the DOM
const _renderedRows = new Set();

export function updateOpSummaryLive(data) {
    const list = document.getElementById('op-live-sensors-list');
    if (!list) return;

    // Removed console.log (FIX 3 - was firing every 1500ms)

    const getTrendBtn = (tag) => {
        const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
        const isActive = state.opActiveTrends.includes(tag);
        return `
        <button onclick="Actions.toggleOpTrend('${tag}')"
            id="op-trend-btn-${safeId}"
            class="${isActive ? 'text-yellow-600 trend-active' : 'text-gray-500'}
                hover:text-[#ebf552] transition-colors focus:outline-none shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14"
                viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 3v18h18"/>
                <path d="m19 9-5 5-4-4-3 3"/>
            </svg>
        </button>`;
    };

    const indVars = state.currentModelConfig.indicator_variables || {};
    const ctrlVars = state.currentModelConfig.control_variables || {};
    const calcVars = state.currentModelConfig.calculated_variables || {};

    // Get all summary-enabled variables from configuration
    const allVars = { ...indVars, ...ctrlVars, ...calcVars };
    const summaryVars = Object.keys(allVars)
        .filter(k => {
            const v = allVars[k];
            return (v.op_summary === true || v.op_summary === "true") && v.position !== undefined && v.position !== null;
        })
        .map(k => ({ key: k, ...allVars[k] }));

    // Sort by configured position
    summaryVars.sort((a, b) => (parseInt(a.position) || 999) - (parseInt(b.position) || 999));

    summaryVars.forEach(item => {
        const k = item.key;
        const safeId = k.replace(/[^a-zA-Z0-9]/g, '');
        const valId = `op-live-val-${safeId}`;
        const rowId = `op-live-row-${safeId}`;

        // Value Lookup: Check key or tag_name
        let rawVal = data[k];
        if (rawVal === undefined && item.tag_name) rawVal = data[item.tag_name];
        const val = parseFloat(rawVal);

        let colorClass = 'text-slate-800 bg-slate-100';
        if (!isNaN(val) && item.default_min !== undefined && item.default_max !== undefined) {
            const min = item.default_min;
            const max = item.default_max;
            const range = max - min;
            const buffer = range * 0.1;
            if (val < min || val > max) colorClass = 'text-white bg-red-600';
            else if (val < (min + buffer) || val > (max - buffer)) colorClass = 'text-black bg-yellow-900';
        }

        const existingRow = document.getElementById(rowId);
        if (!existingRow) {
            // Row missing -> Append once
            const div = document.createElement('div');
            div.id = rowId;
            div.className = 'flex justify-between items-center border-b border-gray-100/10 py-1.5 hover:bg-white/5 transition-colors pl-1 pr-2';
            div.innerHTML = `
                <div class="flex items-center gap-1.5 text-gray-400 flex-1 min-w-0 overflow-hidden">
                    ${getTrendBtn(k)}
                    <span class="truncate text-[11px] font-bold text-gray-300" title="${k}">${k}</span>
                </div>
                <div class="font-mono text-[11px] text-white font-black bg-[#122a33] px-1.5 py-0.5 rounded shadow-inner ml-1 shrink-0">
                    <span id="${valId}" class="font-mono font-bold px-2 rounded ${colorClass}">
                        ${isNaN(val) ? '---' : val.toFixed(2)}
                    </span>
                </div>`;
            list.appendChild(div);
        } else {
            // Row exists -> Update in-place
            const valEl = document.getElementById(valId);
            if (valEl) {
                valEl.className = `font-mono font-bold px-2 rounded ${colorClass}`;
                valEl.innerText = isNaN(val) ? '---' : val.toFixed(2);
            }
            // Update trend button
            const btnEl = document.getElementById(`op-trend-btn-${safeId}`);
            if (btnEl) {
                const isActive = state.opActiveTrends.includes(k);
                btnEl.className = `${isActive ? 'text-yellow-600 trend-active' : 'text-gray-500'} hover:text-[#ebf552] transition-colors focus:outline-none shrink-0`;
            }
        }
    });

    // Cleanup: Remove rows that are no longer in the configuration summary
    const currentConfigIds = new Set(summaryVars.map(v => `op-live-row-${v.key.replace(/[^a-zA-Z0-9]/g, '')}`));
    Array.from(list.children).forEach(child => {
        if (child.id && !currentConfigIds.has(child.id)) {
            list.removeChild(child);
        }
    });
}