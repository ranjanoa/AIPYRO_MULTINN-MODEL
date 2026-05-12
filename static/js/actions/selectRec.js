import { state } from "../inits/state.js";
import { refreshBatchListUI } from "./refreshBatchListUI.js";
import { updateAutoButtonUI } from "../updateFunctions/updateAutoButtonUI.js";
import { drawOpParallelChartCooler } from "../optSum/optSumCooler/drawOpParallelChartCooler.js";
import { drawOpSummaryChartCooler } from "../optSum/optSumCooler/drawOpSummaryChartCooler.js";
import { drawOpParallelChartPreheater } from "../optSum/optSumPreheater/drawOpParallelChartPreheater.js";
import { drawOpSummaryChartPreheater } from "../optSum/optSumPreheater/drawOpSummaryChartPreheater.js";
import { drawOpParallelChartKiln } from "../optSum/optSumkiln/drawOpParallelChartKiln.js";
import { drawOpSummaryChartKiln } from "../optSum/optSumkiln/drawOpSummaryChartKiln.js";
import { drawOpSummaryChart } from "../optSum/drawOpSummaryChart.js";
import { drawOpParallelChart } from "../optSum/drawOpParallelChart.js";

export function selectRec(idx) {
    if (state.isHybridEngaged) {
        alert("Please DISENGAGE to change batch.");
        return;
    }
    // Auto-disable Auto Mode if user clicks a batch
    if (state.isAutoMode) {
        state.isAutoMode = false;
        updateAutoButtonUI();
    }
    state.selectedBatchIndex = idx;
    refreshBatchListUI();
    const rec = state.allRecommendations[idx];
    const div = document.getElementById('recommended-setpoints');
    div.innerHTML = '';
    const rawActions = rec.actions || [];
    if (rawActions.length === 0) {
        div.innerHTML = `<div class="text-center text-whiteoff mt-6 italic">No Configured Setpoints Found.</div>`;
        return;
    }
    const sortedActions = rawActions.sort((a, b) => (a.type === 'Control' ? -1 : 1));
    sortedActions.forEach(a => {
        const color = a.type === 'Control' ? 'text-yellow-600' : 'text-gray-500';
        const label = a.type === 'Control' ? a.var_name : `• ${a.var_name}`;
        div.innerHTML += `<div class="flex justify-between py-1 border-b border-gray-100"><span class="text-whiteoff text-xs font-bold truncate w-2/3" title="${a.var_name}">${label}</span><span class="${color} font-bold text-sm font-mono">${parseFloat(a.fingerprint_set_point).toFixed(2)}</span></div>`;
    });
    const colors = ['#000000', '#0099cc', '#e11d48', '#d97706', '#7c3aed'];
    const datasets = [];
    (rec.top_variables || []).forEach((key, i) => {
        const col = colors[i % 5];
        const liveVals = rec.live_history[key] || [];
        const liveData = liveVals.map((v, x) => ({ x: x - (liveVals.length - 1), y: v })).filter(pt => pt.x >= -5.5);
        datasets.push({
            label: key + " (Real)",
            data: liveData,
            borderColor: col,
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.2
        });
        const predVals = rec.fingerprint_prediction[key] || [];
        const predData = predVals.map((v, x) => ({ x: x, y: v })).filter(pt => pt.x <= 30);
        if (liveData.length) predData.unshift({ x: 0, y: liveData[liveData.length - 1].y });
        datasets.push({
            label: key + " (Pred)",
            data: predData,
            borderColor: col,
            borderWidth: 2,
            borderDash: [4, 4],
            pointRadius: 0,
            tension: 0.2
        });
    });
    if (state.charts.timeSeriesChart) {
        state.charts.timeSeriesChart.data.datasets = datasets;
        state.charts.timeSeriesChart.update();
    }
    if (document.getElementById('dash-plotly')) {
        const pDims = (rec.top_variables || []).map(k => {
            const curr = rec.live_history[k] ? rec.live_history[k].slice(-1)[0] : 0;
            const goal = parseFloat(rec.actions.find(a => a.var_name === k)?.fingerprint_set_point || 0);
            const pad = Math.abs(goal - curr) * 0.5 || goal * 0.1 || 1;
            return {
                range: [Math.min(curr, goal) - pad, Math.max(curr, goal) + pad],
                label: k,
                values: [curr, goal],
                tickfont: { color: '#334155', size: 12 },
                gridcolor: '#f1f5f9',

            };
        });
        Plotly.newPlot('dash-plotly', [{
            type: 'parcoords',
            line: { color: [0, 1], colorscale: [[0, '#6060F9'], [1, '#10b981']], showscale: false },
            dimensions: pDims
        }], {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#f1f5f9' },
            margin: { l: 50, r: 50, t: 60, b: 30 },
            annotations: [{
                x: 0,
                y: 1.15,
                xref: 'paper',
                yref: 'paper',
                text: '<b>— Real (Blue)</b>',
                showarrow: false,
                font: { color: '#6060F9', size: 14 },
                xanchor: 'left'
            }, {
                x: 0.5,
                y: 1.15,
                xref: 'paper',
                yref: 'paper',
                text: '<b>— Goal (Green)</b>',
                showarrow: false,
                font: { color: '#10b981', size: 14 },
                xanchor: 'left'
            }]
        }, { responsive: true, displayModeBar: false });
    }
    // Trigger updates on operator summary immediately
    drawOpSummaryChart();
    drawOpParallelChart();
   drawOpParallelChartKiln()
   drawOpSummaryChartKiln()
    drawOpParallelChartCooler()
    drawOpSummaryChartCooler()
    drawOpParallelChartPreheater()
    drawOpSummaryChartPreheater()
}
