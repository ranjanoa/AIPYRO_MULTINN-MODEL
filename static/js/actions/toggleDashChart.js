export function toggleDashChart(mode) {
    const t = document.getElementById('dash-chart-trend');
    const p = document.getElementById('dash-chart-parallel');

    const tbtn = document.getElementById('trend-btn');
    const pbtn = document.getElementById('parallel-btn');

    if (mode === 'trend') {
        t.classList.remove('hidden');
        p.classList.add('hidden');

        pbtn.classList.remove('bg-gray-100','text-black');
        tbtn.classList.add('bg-gray-100','text-black');
        pbtn.classList.add('text-whiteoff');
        tbtn.classList.remove('text-whiteoff');
    } else {
        t.classList.add('hidden');
        p.classList.remove('hidden');

        tbtn.classList.remove('bg-gray-100','text-black');
        tbtn.classList.add('text-whiteoff');
        pbtn.classList.add('bg-gray-100','text-black');
        pbtn.classList.remove('text-whiteoff');
        Plotly.Plots.resize('dash-plotly');
    }
}

