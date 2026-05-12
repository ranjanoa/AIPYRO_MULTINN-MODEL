import {state} from "../inits/state.js";

export function initSimulatorControls() {
    const c = document.getElementById('sim-controls-list'), i = document.getElementById('sim-indicators-list'),
        clr = document.getElementById('sim-color-var');
    c.innerHTML = '';
    i.innerHTML = '';
    clr.innerHTML = '';
    const add = (k, p) => {
        p.innerHTML += `<label class="flex items-center space-x-2 cursor-pointer  p-1.5 rounded transition-colors"><input type="checkbox" name="sim_${k}" id="chk_${k}" class="sim-check w-4 h-4 rounded border-gray-400 text-black focus:ring-0" value="${k}"><span class="text-xs text-whiteoff truncate select-none font-medium">${k}</span></label>`;
        clr.innerHTML += `<option value="${k}">${k}</option>`;
    };
    if (state.currentModelConfig.control_variables) Object.keys(state.currentModelConfig.control_variables).sort().forEach(k => add(k, c));
    if (state.currentModelConfig.indicator_variables) Object.keys(state.currentModelConfig.indicator_variables).sort().forEach(k => add(k, i));

    // Apply default color-by variable from config
    const defaultColorBy = state.currentModelConfig.simulator_settings?.default_color_by;
    if (defaultColorBy && Array.from(clr.options).some(opt => opt.value === defaultColorBy)) {
        clr.value = defaultColorBy;
    }
}
