import { state } from "../../inits/state.js";
import { drawAiMnmSummaryChart } from "./drawAiMnmSummaryChart.js";
import { drawAiMnmParallelChart } from "./drawAiMnmParallelChart.js";

export function clearAiMnmTrends() {
    state.aiMnmActiveTrends = [];
    document.querySelectorAll('[id^="ai-mnm-trend-btn-"]').forEach(b => {
        b.classList.remove('trend-active', 'text-yellow-600');
    });
    drawAiMnmSummaryChart();
    drawAiMnmParallelChart();
}
