import { state } from "../../inits/state.js";
import { drawAiMnmSummaryChart } from "./drawAiMnmSummaryChart.js";
import { drawAiMnmParallelChart } from "./drawAiMnmParallelChart.js";

export function toggleAiMnmTrend(tag) {
    if (!state.aiMnmActiveTrends) state.aiMnmActiveTrends = [];
    const idx = state.aiMnmActiveTrends.indexOf(tag);
    const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
    const btns = document.querySelectorAll(`#ai-mnm-trend-btn-${safeId}`);

    if (idx > -1) {
        state.aiMnmActiveTrends.splice(idx, 1);
        btns.forEach(b => b.classList.remove('trend-active', 'text-yellow-600'));
    } else {
        if (state.aiMnmActiveTrends.length >= 6) {
            return alert("Maximum 6 trends can be displayed at once.");
        }
        state.aiMnmActiveTrends.push(tag);
        if (!state.aiMnmHistoryData[tag]) state.aiMnmHistoryData[tag] = [];
        if (!state.aiMnmSetpointData[tag]) state.aiMnmSetpointData[tag] = [];
        btns.forEach(b => b.classList.add('trend-active', 'text-yellow-600'));
    }
    drawAiMnmSummaryChart();
    drawAiMnmParallelChart();
}
