import {state} from "../inits/state.js"
export function populateMbrlDropdowns(currentModelConfig) {
    const sel = document.getElementById('mbrl-chart-select');
    sel.innerHTML = '';
    if (currentModelConfig.control_variables) {
        Object.keys(currentModelConfig.control_variables).forEach((k, i) => {
            const opt = document.createElement('option');
            opt.value = k;
            opt.text = k;
            sel.appendChild(opt);
            if (i === 0) state.activeMbrlVar = k;
        });
    }
}