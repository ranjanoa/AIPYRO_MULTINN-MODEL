import { state } from "../../inits/state.js";
import { drawOpSummaryChartPreheater} from "./drawOpSummaryChartPreheater.js"
import { drawOpParallelChartPreheater} from "./drawOpParallelChartPreheater.js"

export function toggleOpTrendPreheater(tag) {
    const idx = state.opActiveTrendsPreheater.indexOf(tag);
    const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
    const btns = document.querySelectorAll(`#op-trend-btn-preheater-${safeId}`);

    if (idx > -1) {
        state.opActiveTrendsPreheater.splice(idx, 1);
        btns.forEach(b => b.classList.remove('trend-active', 'text-yellow-600'));
    } else {
        if (state.opActiveTrendsPreheater.length >= 6) {
            return alert("Maximum 6 trends can be displayed at once.");
        }
        state.opActiveTrendsPreheater.push(tag);

        if (!state.opHistoryDataPreheater[tag]) {
            state.opHistoryDataPreheater[tag] = [];
        }
        btns.forEach(b => b.classList.add('trend-active', 'text-yellow-600'));
    }
    drawOpSummaryChartPreheater();
    drawOpParallelChartPreheater();
}
