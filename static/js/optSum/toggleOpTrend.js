import { state } from "../inits/state.js";
import { drawOpSummaryChart} from "./drawOpSummaryChart.js"
import { drawOpParallelChart} from "./drawOpParallelChart.js"

export function toggleOpTrend(tag) {
    const idx = state.opActiveTrends.indexOf(tag);
    const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
    const btns = document.querySelectorAll(`#op-trend-btn-${safeId}`);

    if (idx > -1) {
        state.opActiveTrends.splice(idx, 1);
        btns.forEach(b => b.classList.remove('trend-active', 'text-yellow-600'));
    } else {
        if (state.opActiveTrends.length >= 6) {
            return alert("Maximum 6 trends can be displayed at once.");
        }
        state.opActiveTrends.push(tag);

        if (!state.opHistoryData[tag]) {
            state.opHistoryData[tag] = [];
        }
        btns.forEach(b => b.classList.add('trend-active', 'text-yellow-600'));
    }
    drawOpSummaryChart();
    drawOpParallelChart();
}
