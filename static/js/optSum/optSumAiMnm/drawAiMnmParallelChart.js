import { state } from "../../inits/state.js";

// Parallel coordinates: Curr vs Set Point per active variable.
export function drawAiMnmParallelChart() {
    if (!document.getElementById('ai-mnm-dash-plotly')) return;
    if (document.getElementById('ai-mnm-dash-chart-parallel').classList.contains('hidden')) return;
    if (typeof Plotly === 'undefined') return;

    const varsToPlot = (state.aiMnmActiveTrends && state.aiMnmActiveTrends.length >= 2)
        ? state.aiMnmActiveTrends
        : Object.keys(state.aiMnmLatestValues || {}).slice(0, 5);

    if (!varsToPlot.length) return;

    const pDims = varsToPlot.slice(0, 5).map(k => {
        const v = (state.aiMnmLatestValues || {})[k] || {};
        const curr = parseFloat(v.curr);
        const goal = parseFloat(v.sp);
        const c = isNaN(curr) ? 0 : curr;
        const g = isNaN(goal) ? c : goal;
        const pad = Math.abs(g - c) * 0.5 || Math.abs(g) * 0.1 || 1;

        return {
            range: [Math.min(c, g) - pad, Math.max(c, g) + pad],
            label: k.length > 15 ? k.substring(0, 12) + '...' : k,
            values: [c, g],
            tickfont: { color: 'white', size: 10 }
        };
    });

    Plotly.react('ai-mnm-dash-plotly', [{
        type: 'parcoords',
        line: { color: [0, 1], colorscale: [[0, '#3b82f6'], [1, '#10b981']], showscale: false },
        dimensions: pDims
    }], {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: 'white' },
        margin: { l: 30, r: 30, t: 30, b: 20 },
        annotations: [
            { x: 0, y: 1.15, xref: 'paper', yref: 'paper', text: '<b>— Curr (Blue)</b>', showarrow: false, font: { color: '#3b82f6', size: 10 }, xanchor: 'left' },
            { x: 0.5, y: 1.15, xref: 'paper', yref: 'paper', text: '<b>— SP (Green)</b>', showarrow: false, font: { color: '#10b981', size: 10 }, xanchor: 'left' }
        ]
    });
}
