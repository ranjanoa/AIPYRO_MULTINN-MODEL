import { state } from "../../inits/state.js";

export function drawOpParallelChartCooler() {
if (!document.getElementById('op-dash-plotly-cooler')) return;
            if (document.getElementById('op-dash-chart-parallel-cooler').classList.contains('hidden')) return;

            // Use manually selected trends if available, otherwise fallback to active AI variables so the chart isn't empty
            let varsToPlot = state.opActiveTrendsCooler.length >= 2 ? state.opActiveTrendsCooler : (window.currentAIVars || []);
            if (!varsToPlot.length) return;

            const pDims = varsToPlot.slice(0, 5).map(k => {
                const liveVals = state.opHistoryDataCooler[k] || [];
                const curr = liveVals.length ? liveVals[liveVals.length - 1].val : 0;

                let goal = curr;
                if (state.opPredictionDataCooler[k] && state.opPredictionDataCooler[k].length > 0) {
                    goal = state.opPredictionDataCooler[k][state.opPredictionDataCooler[k].length - 1]; // End of prediction
                } else {
                    const goalAct = (window.latestActions || []).find(a => a.var_name === k);
                    if (goalAct) goal = parseFloat(goalAct.fingerprint_set_point || 0);
                }

                const pad = Math.abs(goal - curr) * 0.5 || Math.abs(goal) * 0.1 || 1;

                return {
                    range: [Math.min(curr, goal) - pad, Math.max(curr, goal) + pad],
                    label: k.length > 15 ? k.substring(0, 12) + '...' : k,
                    values: [curr, goal],
                    tickfont: { color: 'white', size: 10 }
                };
            });

            Plotly.react('op-dash-plotly-cooler', [{
                type: 'parcoords',
                line: { color: [0, 1], colorscale: [[0, '#3b82f6'], [1, '#10b981']], showscale: false },
                dimensions: pDims
            }], {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: 'white' },
                margin: { l: 30, r: 30, t: 30, b: 20 },
                annotations: [
                    { x: 0, y: 1.15, xref: 'paper', yref: 'paper', text: '<b>— Real (Blue)</b>', showarrow: false, font: { color: '#3b82f6', size: 10 }, xanchor: 'left' },
                    { x: 0.5, y: 1.15, xref: 'paper', yref: 'paper', text: '<b>— Goal (Green)</b>', showarrow: false, font: { color: '#10b981', size: 10 }, xanchor: 'left' }
                ]
            });
}
