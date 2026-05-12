import { state } from "../../inits/state.js";

// Renders right-side live sensor list using indicator_parameters bounds for priority colouring.
// indicators (read from kiln1 measurement): { "<ind_label>": { curr } }
export function updateAiMnmLive(indicators) {
    const values = indicators;  // back-compat alias — internal logic still references `values`
    const list = document.getElementById('op-live-sensors-list-ai-mnm');
    if (!list || !values) return;

    const indParams = (state.currentModelConfig && state.currentModelConfig.ai_mnm && state.currentModelConfig.ai_mnm.indicator_parameters) || {};

    const getTrendBtn = (tag) => {
        const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
        const isActive = (state.aiMnmActiveTrends || []).includes(tag);
        return `
            <button onclick="Actions.toggleAiMnmTrend('${tag}')"
                id="ai-mnm-trend-btn-${safeId}"
                class="${isActive ? 'text-yellow-600 trend-active' : 'text-gray-500'} hover:text-[#ebf552] transition-colors focus:outline-none shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
            </button>`;
    };

    // Iterate every key returned by the backend (includes configured indicators
    // surfaced under their display label PLUS any extra raw fields from
    // cimpor_data_result). Configured keys keep their priority colouring; raw
    // fields default to priority 3 (info).
    const enriched = Object.keys(values).map(k => {
        const v = (values[k] && values[k].curr !== undefined) ? parseFloat(values[k].curr) : NaN;
        const cfg = indParams[k] || {};
        const min = cfg.default_min;
        const max = cfg.default_max;

        let priority = 3;
        if (!isNaN(v) && min !== undefined && max !== undefined) {
            const range = max - min;
            const buffer = range * 0.1;
            if (v < min || v > max) priority = 1;
            else if (v < (min + buffer) || v > (max - buffer)) priority = 2;
        }
        return { key: k, val: v, priority, safeId: k.replace(/[^a-zA-Z0-9]/g, '') };
    });

    enriched.sort((a, b) => {
        if (a.priority !== b.priority) return a.priority - b.priority;
        return a.key.localeCompare(b.key);
    });

    list.innerHTML = '';
    enriched.forEach(item => {
        const valId = `op-live-val-ai-mnm-${item.safeId}`;
        let colorClass = 'text-slate-800 bg-slate-100';
        if (item.priority === 1) colorClass = 'text-white bg-red-600';
        else if (item.priority === 2) colorClass = 'text-black bg-yellow-900';

        const div = document.createElement('div');
        div.className = 'flex justify-between items-center border-b border-gray-100/10 py-1.5 hover:bg-white/5 transition-colors pl-1 pr-2';
        div.innerHTML = `
            <div class="flex items-center gap-1.5 text-gray-400 flex-1 min-w-0 overflow-hidden">
                ${getTrendBtn(item.key)}
                <span class="truncate font-bold text-gray-300" title="${item.key}">${item.key}</span>
            </div>
            <div class="font-mono text-white font-black bg-[#122a33] px-1.5 py-0.5 rounded shadow-inner ml-1 shrink-0">
                <span id="${valId}" class="font-mono font-bold px-2 rounded ${colorClass}">${isNaN(item.val) ? '---' : item.val.toFixed(2)}</span>
            </div>`;
        list.appendChild(div);
    });
}
