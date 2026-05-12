import {MOCK_CONFIG} from "../inits/config.js";

export async function fetchSoftSensorPrediction() {
        const container = document.getElementById('softsensor-chart-container');
        container.innerHTML = '<div class="h-full flex items-center justify-center animate-pulse text-yellow-600 font-bold">Predicting...</div>';
        const sel = document.getElementById('softsensor-select');
        try {
            const response = await fetch(`${MOCK_CONFIG.API_URL}/api/softsensor/predict?tag=${sel.value}`);
            const result = await response.json();
//            console.log("result");
//             console.log(result);
            const historyData = result.history.map(d => ({x: new Date(d[0]), y: d[1]}));
            const predictionData = result.prediction.map(d => ({x: new Date(d[0]), y: d[1]}));
            const fullPredictionLine = historyData.slice(-1).concat(predictionData);
            const data = [{
                x: historyData.map(d => d.x),
                y: historyData.map(d => d.y),
                mode: 'lines',
                name: 'History',
                line: {color: '#000000', width: 2}
            }, {
                x: fullPredictionLine.map(d => d.x),
                y: fullPredictionLine.map(d => d.y),
                mode: 'lines',
                name: 'AI Prediction',
                line: {color: '#0099cc', dash: 'dash', width: 2}
            }];
            Plotly.newPlot(container, data, {
                title: `Predicted ${result.variable}`,
                margin: {t: 40, b: 30, l: 50, r: 20},
                autosize: true,
                paper_bgcolor: "#2A3B40",
                plot_bgcolor: "#2A3B40",
                font: {color: "white"},
                yaxis: {gridcolor: "#ccc"}
            });
        } catch (e) {
            container.innerHTML = "API Error";
        }
    }
