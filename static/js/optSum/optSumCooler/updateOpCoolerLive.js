import { state} from "../../inits/state.js";

export function updateOpCoolerLive(data) {
    const list = document.getElementById('op-live-sensors-list-cooler');
    const getTrendBtn = (tag) => {
        const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
        const isActive = state.opActiveTrendsCooler.includes(tag);
        return `
            <button onclick="Actions.toggleOpTrendCooler('${tag}')"
                id="op-trend-btn-cooler-${safeId}"
                class="${isActive ? 'text-yellow-600 trend-active' : 'text-gray-500'} hover:text-[#ebf552] transition-colors focus:outline-none shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
            </button>`;
    };

    if (!list) return;

    list.innerHTML = '';
    const indVars = state.currentModelConfig.indicator_variables || {};
    const ctrlVars = state.currentModelConfig.control_variables || {};
    const calcVars = state.currentModelConfig.calculated_variables || {};
    const allVars = { ...indVars, ...ctrlVars, ...calcVars };

    const keys = Object.keys(data).filter(k => !k.includes('timestamp'));
    const enriched = keys.map(k => {
        const val = parseFloat(data[k]);
        const item = allVars[k];
        
        let priority = 3; 
        let min = null;
        let max = null;

        if (item) {
            min = item.default_min;
            max = item.default_max;

            if (!isNaN(val) && min !== undefined && max !== undefined) {
                const range = max - min;
                const buffer = range * 0.1;
                if (val < min || val > max) priority = 1;
                else if (val < (min + buffer) || val > (max - buffer)) priority = 2;
            }
        }

        return { key: k, val, priority, min, max, safeId: k.replace(/[^a-zA-Z0-9]/g, '') };
    });

    // Sort: Alert Priority first, then name
    enriched.sort((a, b) => {
        if (!a || !b) return 0;
        if (a.priority !== b.priority) return a.priority - b.priority;
        return a.key.localeCompare(b.key);
    });

    enriched.forEach(item => {
        const k = item.key;
        const val = item.val;
        const valId = `op-live-val-cooler-${item.safeId}`;

        let colorClass = 'text-slate-800 bg-slate-100'; // Normal: White Capsule
        if (item.priority === 1) colorClass = 'text-white bg-red-600'; // Critical: Red
        else if (item.priority === 2) colorClass = 'text-black bg-yellow-900'; // Warning: Neon Yellow

        const div = document.createElement('div');
        div.className = 'flex justify-between items-center border-b border-gray-100/10 py-1.5 hover:bg-white/5 transition-colors pl-1 pr-2';
        div.innerHTML = `
            <div class="flex items-center gap-1.5 text-gray-400 flex-1 min-w-0 overflow-hidden">
                ${getTrendBtn(k)}
                <span class="truncate font-bold text-gray-300" title="${k}">${k}</span>
            </div>
            <div class="font-mono text-white font-black bg-[#122a33] px-1.5 py-0.5 rounded shadow-inner ml-1 shrink-0">
                <span id="${valId}" class="font-mono font-bold px-2 rounded ${colorClass}">${isNaN(val) ? '---' : val.toFixed(2)}</span>
            </div>`;
        list.appendChild(div);
    });
}