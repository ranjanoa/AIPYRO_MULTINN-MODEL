import { state } from "../inits/state.js";
import { MOCK_CONFIG } from "../inits/config.js";

// export async function runSoftSensorSim() {
//     const container = document.getElementById('sim-chart-container');
//     container.innerHTML = '<div class="h-full flex items-center justify-center animate-pulse text-yellow-600 font-bold">Simulating...</div>';
//     const controls = {};

//             // Re-fetch using data-tag to correctly bypass IDs with spaces replaced
//             document.querySelectorAll('#sim-input-container input[type="range"]').forEach(input => {
//                 controls[input.getAttribute('data-tag')] = parseFloat(input.value);
//             });

//     try {
//         const res = await fetch(`${MOCK_CONFIG.API_URL}/api/softsensor/simulate`, {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({
//                 controls: controls,
//                 target_variable: document.getElementById('sim-output-select').value
//             })
//         });
//         const result = await res.json();
//         console.log("result");
//         console.log(result);
//         Plotly.newPlot(container, [{
//             x: result.timestamps,
//             y: result.baseline,
//             mode: 'lines',
//             name: 'Baseline'
//         }, { x: result.timestamps, y: result.simulated, mode: 'lines', name: 'Simulated' }], {
//             margin: {
//                 t: 40,
//                 b: 60,
//                 l: 50,
//                 r: 20
//             }, autosize: true,
//             paper_bgcolor: "#2A3B40",
//             plot_bgcolor: "#2A3B40",
//             font: { color: "white" },
//             // xaxis: {gridcolor: "white" },
//             yaxis: { gridcolor: "#ccc" }
//         });
//     } catch (e) {
//         container.innerHTML = "Simulation Failed";
//     }
// }



export async function runSoftSensorSim() {
    const container = document.getElementById('sim-chart-container');
    container.innerHTML = '<div class="h-full flex items-center justify-center animate-pulse text-blue-400 font-bold">Simulating...</div>';
    const controls = {};
    document.querySelectorAll('#sim-input-container input[type="range"]').forEach(input => { controls[input.getAttribute('data-tag')] = parseFloat(input.value); });
    try {
        const res = await fetch(`${MOCK_CONFIG.API_URL}/api/softsensor/simulate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ controls: controls, target_variable: document.getElementById('sim-output-select').value }) });
        const result = await res.json();
        Plotly.newPlot(container, [
            { x: result.timestamps, y: result.baseline, mode: 'lines', name: 'Current Baseline', line: { color: '#476570', dash: 'dash' } },
            { x: result.timestamps, y: result.simulated, mode: 'lines', name: 'Simulated Adjustment', line: { color: '#ebf552', width: 3 } }
        ], { paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: { color: 'white' }, margin: { t: 40, b: 30, l: 50, r: 20 }, autosize: true, legend: { orientation: 'h', y: 1.1 } });
    } catch (e) { container.innerHTML = "Simulation Failed. Ensure backend is running."; }
}
