import { state } from "../../inits/state.js";
import { drawOpSummaryChartPreheater} from "./drawOpSummaryChartPreheater.js"
import { drawOpParallelChartPreheater} from "./drawOpParallelChartPreheater.js"

export function clearOpTrendsPreheater() {
    state.opActiveTrendsPreheater = [];
    document.querySelectorAll('.trend-active').forEach(b => {
        b.classList.remove('trend-active', 'text-yellow-600')
    });
    drawOpSummaryChartPreheater();
    drawOpParallelChartPreheater();
}
