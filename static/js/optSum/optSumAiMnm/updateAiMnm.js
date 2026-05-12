import { state } from "../../inits/state.js";
import { drawAiMnmSummaryChart } from "./drawAiMnmSummaryChart.js";

// values: { "<param>": { curr: <num>, sp: <num> }, ... }
export function updateAiMnm(values) {
    if (!values) return;
    const now = Date.now();

    Object.keys(values).forEach(tag => {
        const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
        const v = values[tag] || {};
        const curr = (v.curr !== undefined && v.curr !== null) ? parseFloat(v.curr) : NaN;
        const sp = (v.sp !== undefined && v.sp !== null) ? parseFloat(v.sp) : NaN;

        const curEl = document.getElementById(`op3-ai-mnm-cur-${safeId}`);
        if (curEl) curEl.innerText = isNaN(curr) ? '---' : curr.toFixed(2);

        const tgtEl = document.getElementById(`op3-ai-mnm-tgt-${safeId}`);
        if (tgtEl) tgtEl.innerText = isNaN(sp) ? '---' : sp.toFixed(2);

        // Maintain history buffer (16 min) for chart
        if (!state.aiMnmHistoryData[tag]) state.aiMnmHistoryData[tag] = [];
        if (!isNaN(curr)) {
            state.aiMnmHistoryData[tag].push({ ts: now, val: curr });
            state.aiMnmHistoryData[tag] = state.aiMnmHistoryData[tag].filter(pt => (now - pt.ts) <= 16 * 60000);
        }

        // Setpoint history (used to draw target line in chart)
        if (!state.aiMnmSetpointData[tag]) state.aiMnmSetpointData[tag] = [];
        if (!isNaN(sp)) {
            state.aiMnmSetpointData[tag].push({ ts: now, val: sp });
            state.aiMnmSetpointData[tag] = state.aiMnmSetpointData[tag].filter(pt => (now - pt.ts) <= 16 * 60000);
        }
    });

    drawAiMnmSummaryChart();
}
