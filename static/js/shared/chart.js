import { state } from "../inits/state.js"
const nowLinePlugin = {
    id: 'nowLine',
    beforeDraw: chart => {
        const ctx = chart.ctx;
        const xAxis = chart.scales.x;
        // Fallback to the first available Y-axis if 'y' is missing (for multi-axis charts)
        const yAxis = chart.scales.y || Object.values(chart.scales).find(s => s.id.startsWith('y-'));

        if (xAxis && yAxis && xAxis.min <= 0 && xAxis.max >= 0) {
            const x = xAxis.getPixelForValue(0);
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(x, yAxis.top);
            ctx.lineTo(x, yAxis.bottom);
            ctx.lineWidth = 1;
            ctx.strokeStyle = '#ebf552';
            ctx.setLineDash([5, 5]);
            ctx.stroke();
            ctx.restore();

            ctx.fillStyle = '#ebf552';
            ctx.font = 'bold 10px monospace';
            ctx.fillText('NOW', x - 12, yAxis.bottom - 5);
        }
    }

}
export function initCharts() {
    if (typeof Chart === 'undefined') return;

            Chart.register(nowLinePlugin);
            const darkGrid = '#2d4a54';
            const darkText = '#aabdc4';

            const dashOpts = {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                scales: {
                    x: { 
                        type: 'linear', 
                        min: -5, 
                        max: 30, 
                        ticks: { stepSize: 5, color: darkText }, 
                        grid: { color: darkGrid }, 
                        title: { display: true, text: 'Minutes from Now', color: darkText } 
                    },
                    y: { 
                        grid: { color: darkGrid }, 
                        ticks: { color: darkText },
                        display: true,
                        afterDataLimits: (scale) => {
                            const range = scale.max - scale.min;
                            const minRange = Math.max(Math.abs(scale.max) * 0.05, 1);
                            if (range < minRange) {
                                const center = (scale.max + scale.min) / 2;
                                scale.max = center + minRange / 2;
                                scale.min = center - minRange / 2;
                            }
                        }
                    }
                },
                plugins: {
                    legend: { labels: { boxWidth: 12, color: darkText } }
                }
            };

            const timeOpts = {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                scales: {
                    x: { type: 'time', time: { unit: 'minute' }, grid: { display: false }, ticks: { color: darkText } },
                    y: { 
                        grid: { color: darkGrid }, 
                        ticks: { color: darkText },
                        afterDataLimits: (scale) => {
                            const range = scale.max - scale.min;
                            const minRange = Math.max(Math.abs(scale.max) * 0.05, 1);
                            if (range < minRange) {
                                const center = (scale.max + scale.min) / 2;
                                scale.max = center + minRange / 2;
                                scale.min = center - minRange / 2;
                            }
                        }
                    }
                },
                elements: { point: { radius: 0 } },
                plugins: {
                    legend: { labels: { color: darkText } }
                }
            };

            const multiAxisOpts = {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: { mode: 'index', intersect: false },
                scales: {
                    x: { 
                        type: 'linear', 
                        min: -15, 
                        max: 15, 
                        ticks: { 
                            stepSize: 5, 
                            color: darkText, 
                            callback: function (val) { return val + 'm'; } 
                        }, 
                        grid: { color: darkGrid } 
                    },
                    y: { display: false } // Base axis hidden, dynamic ones will be added
                },
                plugins: {
                    legend: { 
                        labels: { 
                            boxWidth: 10, 
                            color: darkText, 
                            usePointStyle: true, 
                            pointStyle: 'line',
                            font: { size: 10, weight: 'bold' }
                        } 
                    },
                    tooltip: { 
                        backgroundColor: 'rgba(18, 42, 51, 0.95)', 
                        titleColor: '#ebf552',
                        borderColor: '#2d4a54',
                        borderWidth: 1,
                        padding: 10,
                        bodyFont: { size: 11 },
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) label += ': ';
                                if (context.parsed.y !== null) label += context.parsed.y.toFixed(2);
                                return label;
                            }
                        }
                    }
                }
            };

            if (document.getElementById('time-series-chart')) {
                state.charts.timeSeriesChart = new Chart(document.getElementById('time-series-chart'), { type: 'line', data: { datasets: [] }, options: dashOpts });
            }
            if (document.getElementById('trend-chart')) {
                state.charts.trendChart = new Chart(document.getElementById('trend-chart'), { type: 'line', data: { labels: [], datasets: [] }, options: timeOpts });
            }
            if (document.getElementById('mbrl-trend-chart')) {
                state.charts.mbrlTrendChart = new Chart(document.getElementById('mbrl-trend-chart'), { type: 'line', data: { labels: [], datasets: [{ label: 'Real', borderColor: '#FFFFFF', borderWidth: 2, data: [] }, { label: 'Target', borderColor: '#ebf552', borderDash: [5, 5], borderWidth: 2, data: [] }] }, options: timeOpts });
            }
            if (document.getElementById('mbrl-uncertainty-chart')) {
                state.charts.mbrlUncertChart = new Chart(document.getElementById('mbrl-uncertainty-chart'), { type: 'bar', data: { labels: Array(20).fill(''), datasets: [{ label: 'Conf', data: Array(20).fill(0.1), backgroundColor: '#476570' }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false, max: 1.0 } } } });
            }
            
            // Shared multi-axis initialization for all optimization summary charts
            if (document.getElementById('op-summary-chart-canvas')) {
                state.charts.opSummaryChartCanvas = new Chart(document.getElementById('op-summary-chart-canvas'), {
                    type: 'line', data: { datasets: [] }, options: JSON.parse(JSON.stringify(multiAxisOpts))
                });
            }
            if (document.getElementById('op-summary-chart-canvas-kiln')) {
                state.charts.opSummarykilnChartCanvas = new Chart(document.getElementById('op-summary-chart-canvas-kiln'), {
                    type: 'line', data: { datasets: [] }, options: JSON.parse(JSON.stringify(multiAxisOpts))
                });
            }
            if (document.getElementById('op-summary-chart-canvas-preheater')) {
                state.charts.opSummaryPreheaterChartCanvas = new Chart(document.getElementById('op-summary-chart-canvas-preheater'), {
                    type: 'line', data: { datasets: [] }, options: JSON.parse(JSON.stringify(multiAxisOpts))
                });
            }
             if (document.getElementById('ai-mnm-summary-chart-canvas')) {
                state.charts.aiMnmSummaryChartCanvas = new Chart(document.getElementById('ai-mnm-summary-chart-canvas'), {
                    type: 'line',
                    data: { datasets: [] },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: false,
                        interaction: { mode: 'index', intersect: false },
                        scales: {
                            x: { type: 'linear', min: -10, max: 0, ticks: { stepSize: 2, color: darkText, callback: function (val) { return val + 'm'; } }, grid: { color: darkGrid } },
                            y: { grid: { color: darkGrid }, ticks: { color: darkText } }
                        },
                        plugins: {
                            legend: { labels: { boxWidth: 10, color: darkText, usePointStyle: true, pointStyle: 'line' } },
                            tooltip: { backgroundColor: '#122a33', titleColor: '#ebf552' }
                        }
                    }
                });
            }

            if (document.getElementById('op-summary-chart-canvas-cooler')) {
                state.charts.opSummaryCoolerChartCanvas = new Chart(document.getElementById('op-summary-chart-canvas-cooler'), {
                    type: 'line', data: { datasets: [] }, options: JSON.parse(JSON.stringify(multiAxisOpts))
                });
            }
}

