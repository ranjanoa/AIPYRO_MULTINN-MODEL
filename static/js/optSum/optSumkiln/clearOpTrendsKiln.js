import { state } from "../../inits/state.js";
import { drawOpSummaryChartKiln} from "./drawOpSummaryChartKiln.js"
import { drawOpParallelChartKiln} from "./drawOpParallelChartKiln.js"

export function clearOpTrendsKiln() {
    state.opActiveTrendsKiln = [];
    document.querySelectorAll('.trend-active').forEach(b => {
        b.classList.remove('trend-active', 'text-yellow-600')
    });
    drawOpSummaryChartKiln();
    drawOpParallelChartKiln();
}
