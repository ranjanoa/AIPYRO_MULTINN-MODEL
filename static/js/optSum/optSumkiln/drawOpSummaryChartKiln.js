import { state } from "../../inits/state.js";
export function drawOpSummaryChartKiln() {
    if (!state.charts.opSummarykilnChartCanvas) return;

            const now = Date.now();
            const colors = ['#ebf552', '#3b82f6', '#10b981', '#f97316', '#a855f7', '#ec4899', '#ffffff', '#22d3ee'];
            const datasets = [];

            // STRICTLY ONLY variables manually selected by the user
            const varsToPlot = [...state.opActiveTrendsKiln];
            const scales = {
                x: {
                    type: 'linear',
                    min: -15,
                    max: 15,
                    ticks: {
                        stepSize: 5,
                        color: '#aabdc4',
                        callback: function (val) { return val + 'm'; }
                    },
                    grid: { color: '#2d4a54' }
                },
                y: { display: false }
            };

            varsToPlot.slice(0, 8).forEach((tag, idx) => {
                const color = colors[idx % colors.length];
                const yAxisId = `y-${tag.replace(/[^a-zA-Z0-9]/g, '')}`;

                // Add dynamic scale for this variable
                scales[yAxisId] = {
                    display: idx === 0, // Show first axis as reference
                    position: 'left',
                    grid: { display: idx === 0, color: '#2d4a54' },
                    ticks: { color: '#aabdc4' }
                };

                let histData = [];
                if (state.opHistoryDataKiln[tag]) {
                    histData = state.opHistoryDataKiln[tag].map(pt => ({
                        x: -((now - pt.ts) / 60000),
                        y: pt.val
                    })).filter(pt => pt.x >= -15);
                }

                datasets.push({
                    label: tag + ' (Real)',
                    data: histData,
                    borderColor: color,
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.1,
                    yAxisID: yAxisId
                });

                // Guarantee a prediction line
                let predDataRaw = state.opPredictionDataKiln[tag];
                if (!predDataRaw || predDataRaw.length === 0) {
                    const curr = state.latestLiveValues[tag] !== undefined ? parseFloat(state.latestLiveValues[tag]) : (histData.length > 0 ? histData[histData.length - 1].y : 0);
                    predDataRaw = Array(16).fill(curr);
                }

                let predData = predDataRaw.map((val, minFromNow) => ({
                    x: minFromNow,
                    y: val
                })).filter(pt => pt.x <= 15);

                if (histData.length > 0) {
                    predData.unshift({ x: 0, y: histData[histData.length - 1].y });
                }

                datasets.push({
                    label: tag + ' (Pred)',
                    data: predData,
                    borderColor: color,
                    borderWidth: 2,
                    borderDash: [4, 4],
                    pointRadius: 0,
                    tension: 0.1,
                    yAxisID: yAxisId
                });
            });

            state.charts.opSummarykilnChartCanvas.options.scales = scales;
            state.charts.opSummarykilnChartCanvas.data.datasets = datasets;
            state.charts.opSummarykilnChartCanvas.update('none');

}
