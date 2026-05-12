import { state } from "../inits/state.js";
import { drawOpSummaryChart} from "./drawOpSummaryChart.js"
import { drawOpParallelChart} from "./drawOpParallelChart.js"

export function clearOpTrends() {
    state.opActiveTrends = [];
    document.querySelectorAll('.trend-active').forEach(b => {
        b.classList.remove('trend-active', 'text-yellow-600')
    });
    drawOpSummaryChart();
    drawOpParallelChart();
}
