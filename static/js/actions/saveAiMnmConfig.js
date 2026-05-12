import { state } from "../inits/state.js";
import { MOCK_CONFIG } from "../inits/config.js";

// Harvest one of the AI_MNM tables into a JS object keyed by parameter name.
function harvest(rowType) {
    const tbodyId = rowType === 'cv' ? 'config-ai-mnm-cv-body' : 'config-ai-mnm-ind-body';
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return {};

    const out = {};
    tbody.querySelectorAll('tr').forEach(tr => {
        const inputs = tr.querySelectorAll(`input[data-ai-mnm-row="${rowType}"]`);
        const obj = {};
        let name = null;
        inputs.forEach(inp => {
            const field = inp.getAttribute('data-field');
            if (field === 'name') {
                name = (inp.value || '').trim();
            } else if (inp.type === 'number') {
                const v = parseFloat(inp.value);
                obj[field] = isNaN(v) ? 0 : v;
            } else {
                obj[field] = inp.value;
            }
        });
        if (name) out[name] = obj;
    });
    return out;
}

function appendBlankRow(rowType) {
    const tbodyId = rowType === 'cv' ? 'config-ai-mnm-cv-body' : 'config-ai-mnm-ind-body';
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    const tpl = rowType === 'cv' ? window.__aiMnmCvRowTemplate : window.__aiMnmIndRowTemplate;
    if (!tpl) return;
    const placeholder = `new_param_${Date.now().toString().slice(-5)}`;
    tbody.insertAdjacentHTML('beforeend', tpl(placeholder, {}));
}

/**
 * Save AI_MNM config OR append a blank row.
 *
 * Per spec (08 May 2026): config (CV + indicator min/max/nudge/priority/labels)
 * is persisted ONLY to model_config.json. kiln2 stores ONLY the live CV setpoint
 * values written by the backend on every poll (mirror_aimnm_cv_to_kiln2).
 * Indicator values are read live from cimpor_data_result and are NOT persisted
 * to kiln2.
 *
 * Modes:
 *   'cv'      -> harvest CV table, persist to model_config.json
 *   'ind'     -> harvest indicator table, persist to model_config.json
 *   'add-cv'  -> append a blank CV row (no save)
 *   'add-ind' -> append a blank indicator row (no save)
 */
export async function saveAiMnmConfig(mode) {
    if (mode === 'add-cv') return appendBlankRow('cv');
    if (mode === 'add-ind') return appendBlankRow('ind');

    if (mode !== 'cv' && mode !== 'ind') {
        console.warn(`Unknown saveAiMnmConfig mode: ${mode}`);
        return;
    }

    const cfg = JSON.parse(JSON.stringify(state.currentModelConfig || {}));
    if (!cfg.ai_mnm) cfg.ai_mnm = { cv_parameters: {}, indicator_parameters: {} };

    if (mode === 'cv') {
        cfg.ai_mnm.cv_parameters = harvest('cv');
    } else {
        cfg.ai_mnm.indicator_parameters = harvest('ind');
    }

    try {
        // 1. Persist updated config (model_config.json)
        const cfgRes = await fetch(`${MOCK_CONFIG.API_URL}/api/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cfg)
        });
        if (!cfgRes.ok) {
            alert("Failed to save AI_MNM configuration to model_config.json.");
            return;
        }

        // Config-only flow: model_config.json holds everything. kiln2 stores ONLY the
        // live CV setpoints written every poll by the backend. Indicator values are
        // read live from cimpor_data_result and never persisted to kiln2.
        state.currentModelConfig = cfg;
        alert(`AI_MNM ${mode === 'cv' ? 'CV' : 'Indicator'} parameters saved.`);
    } catch (e) {
        alert("Error saving AI_MNM configuration: " + e.message);
    }
}
