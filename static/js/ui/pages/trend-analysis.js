export function TrendAnalysis() {
    const container = document.createElement("div");
    container.className = "trend-analysis-container hidden h-full flex-col gap-4";
    container.id = "panel-trends"

    container.innerHTML = `
        <div class="glass-panel border-l-yellow-600 p-4 flex items-center space-x-4 shrink-0 border-l-4 border-l-black bg-white"><span
                class="text-sm font-bold text-white">TAG:</span><select id="trend-variable-select"
                                                                        onchange="Actions.loadTrendData(this.value)"
                                                                        class="border border-gray-300 rounded px-3 py-1.5 outline-none w-64 font-bold text-sm text-select-white"></select>
        </div>
        <div class="glass-panel flex-1 p-4 relative min-h-0 bg-dark-green">
            <canvas id="trend-chart"></canvas>
        </div>

  `;

    return container;
}
