import {state} from "../inits/state.js";

export function initTrendDropdown() {
    const sel = document.getElementById('trend-variable-select');
    sel.innerHTML = '<option value="" disabled selected>Select...</option>';
    [...Object.keys(state.currentModelConfig.control_variables || {}), ...Object.keys(state.currentModelConfig.indicator_variables || {})].sort().forEach(v => sel.innerHTML += `<option value="${v}">${v}</option>`);
}