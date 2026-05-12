import { state } from "../../inits/state.js";
import { drawOpSummaryChartKiln} from "./drawOpSummaryChartKiln.js"
import { drawOpParallelChartKiln} from "./drawOpParallelChartKiln.js"

export function toggleOpTrendKiln(tag) {
    const idx = state.opActiveTrendsKiln.indexOf(tag);
    const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
    const btns = document.querySelectorAll(`#op-trend-btn-kiln-${safeId}`);

    if (idx > -1) {
        state.opActiveTrendsKiln.splice(idx, 1);
        btns.forEach(b => b.classList.remove('trend-active', 'text-yellow-600'));
    } else {
        if (state.opActiveTrendsKiln.length >= 6) {
            return alert("Maximum 6 trends can be displayed at once.");
        }
        state.opActiveTrendsKiln.push(tag);

        if (!state.opHistoryDataKiln[tag]) {
            state.opHistoryDataKiln[tag] = [];
        }
        btns.forEach(b => b.classList.add('trend-active', 'text-yellow-600'));
    }
    drawOpSummaryChartKiln();
    drawOpParallelChartKiln();
}
