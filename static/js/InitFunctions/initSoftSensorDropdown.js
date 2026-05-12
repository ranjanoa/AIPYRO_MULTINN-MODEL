import {fetchSoftSensorPrediction} from "./fetchSoftSensor.js"
import {state} from "../inits/state.js";

export function initSoftSensorDropdown() {
        const sel = document.getElementById('softsensor-select');
        if (!sel) return;
        sel.innerHTML = '';
        const allVars = {...state.currentModelConfig.control_variables, ...state.currentModelConfig.indicator_variables};
        Object.keys(allVars).sort().forEach(k => {
            const opt = document.createElement('option');
            opt.value = k;
            opt.text = k;
            if (k === 'sinteringZoneTemp') opt.selected = true;
            sel.appendChild(opt);
        });
        if (sel.options.length > 0) setTimeout(fetchSoftSensorPrediction, 500);
    }
