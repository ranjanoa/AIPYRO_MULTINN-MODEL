import { state } from "../../inits/state.js";
import { drawOpSummaryChartCooler} from "./drawOpSummaryChartCooler.js"
import { drawOpParallelChartCooler} from "./drawOpParallelChartCooler.js"

export function clearOpTrendsCooler() {
    state.opActiveTrendsCooler = [];
    document.querySelectorAll('.trend-active').forEach(b => {
        b.classList.remove('trend-active', 'text-yellow-600')
    });
    drawOpSummaryChartCooler();
    drawOpParallelChartCooler();
}
