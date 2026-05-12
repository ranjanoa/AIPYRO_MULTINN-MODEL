import { state } from "../inits/state.js";

export function updateHybridLive(data) {
    if (!data) return;

    try {
        const list = document.getElementById('hybrid-sensor-list');
        if (!list) return;

        // Clear and rebuild every time (for live sorting)
        list.innerHTML = '';

        const keys = Object.keys(data).filter(k => !k.includes('timestamp'));

        const enriched = keys.map(k => {
            const val = parseFloat(data[k]);
            let min = null, max = null;
            let priority = 3; // default: white

            const config = state.currentModelConfig || {};
            if (config.control_variables) {
                const varConf =
                    config.control_variables[k] ||
                    (config.indicator_variables ? config.indicator_variables[k] : null);

                if (varConf) {
                    min = varConf.default_min;
                    max = varConf.default_max;

                    if (min !== undefined && max !== undefined && !isNaN(val)) {
                        const range = max - min;
                        const buffer = range * 0.1;

                        if (val < min || val > max) priority = 1; // 🔴 RED
                        else if (val < (min + buffer) || val > (max - buffer)) priority = 2; // 🟠 ORANGE
                        else priority = 3; // ⚪ WHITE
                    }
                }
            }

            return { key: k, val, priority, min, max };
        });

        // ✅ SAFE SORT by priority then name
        enriched.sort((a, b) => {
            if (a.priority !== b.priority) return a.priority - b.priority;
            return a.key.localeCompare(b.key);
        });

        // ✅ Render in sorted order
        let html = "";
        enriched.forEach(item => {
            const k = item.key;
            const val = item.val;
            
            let colorClass = 'text-slate-800 bg-slate-100'; // Normal: White Capsule
            if (item.priority === 1) colorClass = 'text-white bg-red-600'; // Critical: Red
            else if (item.priority === 2) colorClass = 'text-black bg-yellow-900'; // Warning: Neon Yellow

            const displayVal = isNaN(val) ? "---" : val.toFixed(2);

            html += `
            <div class="flex justify-between items-center py-2 border-b border-gray-100/10 hover:bg-white/5 transition-colors">
                <span class="text-whiteoff font-bold truncate w-2/3" title="${k}">
                    ${k}
                </span>
                <div class="font-mono text-white font-black bg-[#122a33] px-1.5 py-0.5 rounded shadow-inner ml-1 shrink-0">
                    <span class="font-mono font-bold px-2 rounded ${colorClass}">
                        ${displayVal}
                    </span>
                </div>
            </div>`;
        });
        list.innerHTML = html;
    } catch (e) {
        console.error("HybridLive update failure suppressed:", e.message);
    }
}