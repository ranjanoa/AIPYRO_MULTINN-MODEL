export function SoftSensor() {
    const container = document.createElement("div");
    container.className = "soft-sensor-container hidden h-full flex-col gap-4";
    container.id = "panel-softsensor"

    container.innerHTML = `
        <div class="glass-panel fit-content p-4 flex justify-between items-center shrink-0 bg-white border-l-4 border-l-yellow-600">
            <div class="flex items-center gap-4">
                <div><h2 class="text-lg font-bold text-whiteoff">Soft Sensor Prediction (1 Hour)</h2>
                    <p class="text-xs text-whiteoff">World Model Rollout (Constant Action)</p></div>
                <div class="flex flex-col"><label class="text-[10px] font-bold text-whiteoff label-margin-bottom">TARGET
                    VARIABLE</label><select id="softsensor-select" onchange="Actions.fetchSoftSensorPrediction()"
                                            class="border border-gray-300 rounded px-2 py-1 outline-none font-bold text-sm text-select-white"></select>
                </div>
            </div>
            <button onclick="Actions.fetchSoftSensorPrediction()"
                    class="px-6 py-2 bg-yellow-900 text-sm font-bold rounded hover:bg-gray-200 transition">
                RECALCULATE
            </button>
        </div>
        <div class="flex-1 glass-panel custom-container p-4 relative min-h-0 bg-dark-green flex flex-col">
            <div id="softsensor-chart-container" class="w-full h-full">
                <div class="flex justify-center items-center h-full text-gray-400">Select a variable...</div>
            </div>
        </div>

  `;

    return container;
}
