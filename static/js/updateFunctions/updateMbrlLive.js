import { state } from "../inits/state.js"
export function updateMbrlLive(data) {
    const list = document.getElementById('mbrl-live-list');
    if (!list) return;

    if (list.children.length === 0) {
        Object.keys(data).sort().forEach(k => {
            if (k.includes('timestamp')) return;
            list.innerHTML += `<div class="flex justify-between border-b border-gray-100 pb-1"><span class="text-whiteoff truncate w-20" title="${k}">${k}</span><span id="mbrl-val-${k}" class="text-whiteoff font-bold">---</span></div>`;
        });
    }

    Object.keys(data).forEach(k => {
        const el = document.getElementById(`mbrl-val-${k}`);
        if (el) {
            const val = parseFloat(data[k]);
            el.innerText = isNaN(val) ? "---" : val.toFixed(2);
        }
    });

    if (state.activeMbrlVar && data[state.activeMbrlVar] && state.charts.mbrlTrendChart) {
        const now = new Date();
        state.charts.mbrlTrendChart.data.labels.push(now);
        state.charts.mbrlTrendChart.data.datasets[0].data.push(data[state.activeMbrlVar]);
        const target = state.aiTargets[state.activeMbrlVar] !== undefined ? state.aiTargets[state.activeMbrlVar] : null;
        state.charts.mbrlTrendChart.data.datasets[1].data.push(target);
        if (state.charts.mbrlTrendChart.data.labels.length > 60) {
            state.charts.mbrlTrendChart.data.labels.shift();
            state.charts.mbrlTrendChart.data.datasets[0].data.shift();
            state.charts.mbrlTrendChart.data.datasets[1].data.shift();
        }
        state.charts.mbrlTrendChart.update('none');
    }
}
