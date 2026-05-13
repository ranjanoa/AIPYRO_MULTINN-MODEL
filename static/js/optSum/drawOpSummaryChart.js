import { state } from "../inits/state.js";
export function drawOpSummaryChart() {
    if (!state.charts.opSummaryChartCanvas) return;

            const now = Date.now();
            const colors = ['#ebf552', '#3b82f6', '#10b981', '#f97316', '#a855f7', '#ec4899', '#ffffff', '#22d3ee'];
            const datasets = [];

            const varsToPlot = [...state.opActiveTrends];
            
            // Reconstruct the full scales object explicitly to avoid internal Chart.js config loss
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
                    ticks: { color: '#aabdc4' },
                    afterDataLimits: (scale) => {
                        const range = scale.max - scale.min;
                        const minRange = Math.max(Math.abs(scale.max) * 0.05, 1); // Minimum 5% span or 1 unit
                        if (range < minRange) {
                            const center = (scale.max + scale.min) / 2;
                            scale.max = center + minRange / 2;
                            scale.min = center - minRange / 2;
                        }
                    }
                };

                let histData = [];
                if (state.opHistoryData[tag]) {
                    histData = state.opHistoryData[tag].map(pt => ({
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

                // Only draw prediction if we actually have data for it
                let predDataRaw = state.opPredictionData[tag];
                if (!predDataRaw || predDataRaw.length === 0) return;

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

            state.charts.opSummaryChartCanvas.options.scales = scales;
            state.charts.opSummaryChartCanvas.data.datasets = datasets;
            state.charts.opSummaryChartCanvas.update('none');

}
