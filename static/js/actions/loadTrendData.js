import {MOCK_CONFIG} from "../inits/config.js";
import {state} from "../inits/state.js";

export async function loadTrendData(tag) {
    state.activeTrendVariable = tag;
    if (state.charts.trendChart) {
        state.charts.trendChart.data = {
            labels: [],
            datasets: [{
                label: tag,
                data: [],
                borderColor: '#fff',
                backgroundColor: 'rgba(0,0,0,0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 0
            }]
        };
       state.charts.trendChart.update();
    }
    try {
        const res = await fetch(`${MOCK_CONFIG.API_URL}/api/trend/history?tag=${tag}&minutes=60&t=${Date.now()}`);
        const json = await res.json();
        if (json.labels && json.labels.length > 0 && state.charts.trendChart) {
            state.charts.trendChart.data.labels = json.labels.map(l => new Date(l));
            state.charts.trendChart.data.datasets[0].data = json.data;
            state.charts.trendChart.update();
        }
    } catch (e) {
    }
}

