import { state } from "../../inits/state.js";
import { drawOpSummaryChartCooler} from "./drawOpSummaryChartCooler.js"
import { drawOpParallelChartCooler} from "./drawOpParallelChartCooler.js"

export function toggleOpTrendCooler(tag) {
    const idx = state.opActiveTrendsCooler.indexOf(tag);
    const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
    const btns = document.querySelectorAll(`#op-trend-btn-cooler-${safeId}`);

    if (idx > -1) {
        state.opActiveTrendsCooler.splice(idx, 1);
        btns.forEach(b => b.classList.remove('trend-active', 'text-yellow-600'));
    } else {
        if (state.opActiveTrendsCooler.length >= 6) {
            return alert("Maximum 6 trends can be displayed at once.");
        }
        state.opActiveTrendsCooler.push(tag);

        if (!state.opHistoryDataCooler[tag]) {
            state.opHistoryDataCooler[tag] = [];
        }
        btns.forEach(b => b.classList.add('trend-active', 'text-yellow-600'));
    }
    drawOpSummaryChartCooler();
    drawOpParallelChartCooler();
}
