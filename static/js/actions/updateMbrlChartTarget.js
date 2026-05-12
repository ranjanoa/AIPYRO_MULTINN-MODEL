import{state} from "../inits/state.js";

export function updateMbrlChartTarget(val) {
    state.activeMbrlVar = val;
    if (state.charts.mbrlTrendChart) {
        state.charts.mbrlTrendChart.data.labels = [];
        state.charts.mbrlTrendChart.data.datasets[0].data = [];
        state.charts.mbrlTrendChart.data.datasets[1].data = [];
        state.charts.mbrlTrendChart.update();
    }
}
