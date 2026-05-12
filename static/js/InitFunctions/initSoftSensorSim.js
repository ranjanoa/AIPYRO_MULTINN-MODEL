import { state } from "../inits/state.js";

export function initSoftSensorSim() {
    const container = document.getElementById('sim-input-container');
    const outSel = document.getElementById('sim-output-select');
    if (!container) return;

    // Save current selection to restore if re-syncing
    const currentSel = outSel.value;

    container.innerHTML = '';
    outSel.innerHTML = '';
//    console.log("sim:",)
    Object.keys(state.currentModelConfig.control_variables).sort().forEach(key => {
        const conf = state.currentModelConfig.control_variables[key];
        const safeId = key.replace(/[^a-zA-Z0-9]/g, '');
//        console.log("sim:", conf)
//        console.log("latestLiveValues:", state.latestLiveValues)

        // Prioritize LIVE value over center midpoint
        let val = ((conf.default_min + conf.default_max) * 0.5);
        if (state.latestLiveValues[key] !== undefined) {
            val = parseFloat(state.latestLiveValues[key]);
        }

        // Clamp within config boundaries to prevent UI breakage
        val = Math.max(conf.default_min, Math.min(conf.default_max, val));
        const displayVal = val.toFixed(2);

        container.innerHTML += `
                    <div class="mb-4">
                        <div class="flex justify-between mb-1">
                            <label class="text-xs font-bold text-gray-300 truncate" title="${key}">${key}</label>
                            <span id="disp-${safeId}" class="text-xs font-mono font-bold text-whiteoff">${displayVal} ${conf.unit || ''}</span>
                        </div>
                        <div class="flex items-center gap-3">
                            <span class="text-[9px] text-gray-500 font-mono">${conf.default_min}</span>
                            <input type="range" id="input-${safeId}" data-tag="${key}" min="${conf.default_min}" max="${conf.default_max}" step="0.1" value="${val}" oninput="document.getElementById('disp-${safeId}').innerText = parseFloat(this.value).toFixed(2) + ' ${conf.unit || ''}'" class="w-full h-2 bg-[#122a33] border border-[#476570] rounded-lg appearance-none cursor-pointer">
                            <span class="text-[9px] text-whiteoff font-mono">${conf.default_max}</span>
                        </div>
                    </div>`;
    });

    const allVars = { ...state.currentModelConfig.indicator_variables, ...state.currentModelConfig.control_variables };
    Object.keys(allVars).forEach(k => {
        const opt = document.createElement('option');
        opt.value = k;
        opt.text = k;
        outSel.appendChild(opt);
    });

    // Restore previous selection or pick defaults
    if (currentSel && allVars[currentSel]) {
        outSel.value = currentSel;
    } else if (allVars['Kiln motor 1 Amps']) {
        outSel.value = 'Kiln motor 1 Amps';
    } else if (allVars['Kiln BZT1']) {
        outSel.value = 'Kiln BZT1';
    }
}
