import { state } from "../../inits/state.js";
import { MOCK_CONFIG } from "../../inits/config.js";
import { updateAiMnm } from "./updateAiMnm.js";
import { updateAiMnmLive } from "./updateAiMnmLive.js";

// Trend Icon helper (reused by table + live list)
const getTrendBtn = (tag) => {
    const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
    const isActive = (state.aiMnmActiveTrends || []).includes(tag);
    return `
        <button onclick="Actions.toggleAiMnmTrend('${tag}')" id="ai-mnm-trend-btn-${safeId}"
            class="${isActive ? 'text-yellow-600 trend-active' : 'text-gray-500'} hover:text-[#ebf552] transition-colors focus:outline-none shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
        </button>`;
};

// Build a row for the AI_MNM CV table
function buildRow(tag, alias, unit) {
    const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
    return `
        <tr class="hover:bg-white/5 transition-colors cursor-pointer" onclick="Actions.toggleAiMnmTrend('${tag}')">
            <td class="p-1.5 text-gray-300 overflow-hidden align-middle">
                <div class="flex items-center gap-1.5 w-full">
                    ${getTrendBtn(tag)}
                    <span class="truncate flex-1 min-w-0 font-bold text-white" title="${tag}">${alias}</span>
                </div>
            </td>
            <td class="p-1.5 font-mono font-bold text-right text-gray-400 truncate align-middle">${unit || ''}</td>
            <td class="p-1.5 font-mono font-bold text-right text-gray-300 font-black truncate align-middle" id="op3-ai-mnm-cur-${safeId}">---</td>
            <td class="p-1.5 font-mono font-bold text-right text-gray-300 font-black pr-2 truncate align-middle" id="op3-ai-mnm-tgt-${safeId}">---</td>
        </tr>`;
}

// One-shot fetch of latest AI_MNM Curr/SP from cimpor_data_result
async function fetchAiMnmValues() {
    try {
        const res = await fetch(`${MOCK_CONFIG.API_URL}/api/aimnm/values`);
        if (!res.ok) return;
        const payload = await res.json();
        // payload: {
        //   values:     { "<cv_param>":  { curr, sp } },   // CVs from cimpor_data_result
        //   indicators: { "<ind_label>": { curr } },        // indicators from kiln1
        //   timestamp:  "..."
        // }
        if (!payload) return;
        const values = payload.values || {};
        const indicators = payload.indicators || {};

        // Cache for charts (CV trend buffer keyed by CV param)
        state.aiMnmLatestValues = values;
        state.aiMnmLatestIndicators = indicators;

        // Update UI
        updateAiMnm(values);
        updateAiMnmLive(indicators);

        // Refresh indicator
        const ind = document.getElementById('ai-mnm-refresh-indicator');
        if (ind) {
            const ts = new Date();
            ind.textContent = `Updated ${ts.toLocaleTimeString()} · 10s`;
        }
    } catch (e) {
        console.warn("AI_MNM fetch failed", e);
    }
}

export function initAiMnm() {
    if (!state.currentModelConfig) return;

    const aiMnmCfg = state.currentModelConfig.ai_mnm || {};
    const cvParams = aiMnmCfg.cv_parameters || {};
    const indParams = aiMnmCfg.indicator_parameters || {};

    // 1. Populate CV Table (Label / Unit / Curr / SP)
    const tBody = document.getElementById('op-table-ai-mnm');
    if (tBody) {
        tBody.innerHTML = '';
        const sortedKeys = Object.keys(cvParams).sort((a, b) => {
            const pa = parseInt(cvParams[a].position) || 999;
            const pb = parseInt(cvParams[b].position) || 999;
            return pa - pb || a.localeCompare(b);
        });
        sortedKeys.forEach(tag => {
            const v = cvParams[tag] || {};
            const alias = v.description || v.label || tag;
            tBody.innerHTML += buildRow(tag, alias, v.unit);
        });
    }

    // 2. Populate Live Sensor list (Indicator parameters, position-sorted)
    const liveList = document.getElementById('op-live-sensors-list-ai-mnm');
    if (liveList) {
        liveList.innerHTML = '';
        const filtered = Object.keys(indParams).filter(k => indParams[k].position !== undefined && indParams[k].position !== null);
        filtered.sort((a, b) => (parseInt(indParams[a].position) || 999) - (parseInt(indParams[b].position) || 999));

        // Fallback: if no position set, just show all
        const finalKeys = filtered.length ? filtered : Object.keys(indParams);

        finalKeys.forEach(tag => {
            const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
            const rowId = `op-live-row-ai-mnm-${safeId}`;
            const valId = `op-live-val-ai-mnm-${safeId}`;
            liveList.innerHTML += `
                <div id="${rowId}" class="flex justify-between items-center border-b border-gray-100/10 py-1.5 hover:bg-white/5 transition-colors pl-1 pr-2">
                    <div class="flex items-center gap-1.5 text-gray-400 flex-1 min-w-0 overflow-hidden">
                        ${getTrendBtn(tag)}
                        <span class="truncate text-[11px] font-bold text-gray-300" title="${tag}">${tag}</span>
                    </div>
                    <div class="font-mono text-[11px] text-white font-black bg-[#122a33] px-1.5 py-0.5 rounded shadow-inner ml-1 shrink-0">
                        <span id="${valId}" class="font-mono font-bold px-2 rounded">---</span>
                    </div>
                </div>
            `;
        });
    }

    // 3. Start polling at 10s. Clear any prior interval first to avoid duplicates.
    if (state.aiMnmInterval) {
        clearInterval(state.aiMnmInterval);
        state.aiMnmInterval = null;
    }
    fetchAiMnmValues(); // Immediate first fetch
    state.aiMnmInterval = setInterval(fetchAiMnmValues, 10000);
}

export { fetchAiMnmValues };
