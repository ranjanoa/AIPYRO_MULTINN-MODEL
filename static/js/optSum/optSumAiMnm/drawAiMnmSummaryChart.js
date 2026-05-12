import { state } from "../../inits/state.js";

// Plots Curr (solid) + SP (dashed) for active trend variables. Last 10 minutes historical window for both curr and sp.
export function drawAiMnmSummaryChart() {
    if (!state.charts.aiMnmSummaryChartCanvas) return;

    const now = Date.now();
    const colors = ['#ebf552', '#3b82f6', '#10b981', '#f97316', '#a855f7', '#ec4899', '#ffffff', '#22d3ee'];
    const datasets = [];

    const varsToPlot = [...(state.aiMnmActiveTrends || [])];

    varsToPlot.slice(0, 8).forEach((tag, idx) => {
        const color = colors[idx % colors.length];

        // Historical curr line (last 10 minutes)
        let histData = [];
        if (state.aiMnmHistoryData[tag]) {
            histData = state.aiMnmHistoryData[tag].map(pt => ({
                x: -((now - pt.ts) / 60000),
                y: pt.val
            })).filter(pt => pt.x >= -10);
        }

        datasets.push({
            label: tag + ' (Curr)',
            data: histData,
            borderColor: color,
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.1
        });

        // Setpoint line: historical SP over the last 10 minutes (no forward projection — plot real CV vs SP only)
        const spHist = state.aiMnmSetpointData[tag] || [];
        const latestSp = spHist.length ? spHist[spHist.length - 1].val : null;
        if (latestSp !== null && !isNaN(latestSp)) {
            const spData = [];
            // Historical SP segment (last 10 minutes)
            spHist.forEach(pt => {
                const xMin = -((now - pt.ts) / 60000);
                if (xMin >= -10) spData.push({ x: xMin, y: pt.val });
            });
            // Anchor the latest SP point at x=0 so the line meets the curr line at "now"
            spData.push({ x: 0, y: latestSp });

            datasets.push({
                label: tag + ' (SP)',
                data: spData,
                borderColor: color,
                borderWidth: 2,
                borderDash: [4, 4],
                pointRadius: 0,
                tension: 0.1
            });
        }
    });

    state.charts.aiMnmSummaryChartCanvas.data.datasets = datasets;
    state.charts.aiMnmSummaryChartCanvas.update('none');
}
