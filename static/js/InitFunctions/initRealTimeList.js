import {state} from "../inits/state.js";

export function initRealTimeList() {
    const cDiv = document.getElementById('current-setpoints');
    cDiv.innerHTML = '';
    const add = (k, c) => `<div class="flex justify-between py-1 border-b border-gray-100"><span class="text-white truncate w-2/3 text-xs font-bold">${k}</span><span id="live-val-${k.replace(/[^a-zA-Z0-9-_]/g, '')}" class="${c} font-mono text-xs font-bold">---</span></div>`;
    if (state.currentModelConfig.control_variables) Object.keys(state.currentModelConfig.control_variables).sort().forEach(k => cDiv.innerHTML += add(k, 'text-yellow-600'));
    if (state.currentModelConfig.indicator_variables) {
        cDiv.innerHTML += `<div class="mt-3 mb-1 pt-1 border-t border-gray-200 text-[9px] font-bold text-yellow-600 uppercase tracking-wider">Indicators</div>`;
        Object.keys(state.currentModelConfig.indicator_variables).sort().forEach(k => cDiv.innerHTML += add(k, 'text-yellow-600'));
    }
}