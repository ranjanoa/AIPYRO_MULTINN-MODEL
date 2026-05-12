export function Fingerprint() {
  const container = document.createElement("div");
   container.className = "fingerprint-container hidden grid-cols-12 gap-4 h-full w-full transition-grid relative";
  container.id = "panel-fingerprint"

  container.innerHTML = `
        <div id="dash-left-col"
             class="col-span-3 glass-panel flex flex-col overflow-hidden transition-all duration-300">
            <div class="p-3 border-b border-gray-200 bg-yellow-900 flex justify-between items-center shrink-0">
                <h2 class="text-sm font-bold text-black">SEARCH PARAMETERS</h2>
                <button onclick="Actions.initializeApp()" class="text-xs text-dark-blue font-bold hover:underline">RESET</button>
            </div>
            <div class="flex-1 overflow-y-auto p-3 space-y-3 bg-dark-green" id="settings-controls">
                <div class="text-center text-sm text-gray-400 mt-4">Loading Config...</div>
            </div>
            <div class="p-3 border-t border-gray-200 bg-dark-green shrink-0">
                <button onclick="Actions.findFingerprint()" id="find-fingerprint-btn"
                        class="w-full py-3 bg-yellow-900 font-mono text-sm font-bold rounded shadow hover:bg-gray-200 transition-colors">
                    SCAN HISTORY
                </button>
            </div>
        </div>
        <div id="dash-mid-col"
             class="col-span-7 flex flex-col gap-4 h-full overflow-hidden transition-all duration-300">
            <div class="grid grid-cols-2 gap-4 h-[45%] shrink-0">
                <div class="glass-panel flex flex-col overflow-hidden">
                    <div class="p-3  border-gray-200 text-whiteoff flex justify-between items-center shrink-0"><h3
                            class="text-sm font-bold ">Real-Time Status</h3>
                        <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                    </div>
                    <div id="current-setpoints"
                         class="flex-1 overflow-y-auto p-3 space-y-1 font-mono text-sm bg-dark-green"></div>
                </div>
                <div class="glass-panel flex flex-col overflow-hidden">
                    <div class="p-3  border-gray-200 text-whiteoff shrink-0"><h3
                            class="text-sm font-bold ">Optimized Target</h3></div>
                    <div id="recommended-setpoints"
                         class="flex-1 overflow-y-auto p-3 space-y-1 font-mono text-sm bg-dark-green">
                        <div class="text-center text-whiteoff mt-6">Waiting for Scan...</div>
                    </div>
                </div>
            </div>
            <div class="glass-panel flex-1 p-3 relative flex flex-col min-h-0 bg-yellow-900">
                <div class="flex justify-between items-center mb-2"><h3 class="text-sm font-bold text-white">
                    Prediction</h3>
                    <div class="flex space-x-2">
                        <button onclick="Actions.toggleDashChart('trend')"
                                class="text-xs font-bold text-black border border-gray-300 px-3 py-1 rounded bg-gray-100 hover:bg-gray-800 hover:text-whiteoff" id="trend-btn">
                            Trend
                        </button>
                        <button onclick="Actions.toggleDashChart('parallel')"
                                class="text-xs font-bold  border border-gray-200 px-3 py-1 rounded hover:bg-gray-800 hover:text-whiteoff" id="parallel-btn">
                            Parallel
                        </button>
                    </div>
                </div>
                <div id="dash-chart-trend" class="relative w-full flex-1 min-h-0">
                    <canvas id="time-series-chart"></canvas>
                </div>
                <div id="dash-chart-parallel" class="hidden relative w-full flex-1 min-h-0">
                    <div id="dash-plotly" class="w-full h-full"></div>
                </div>
            </div>
        </div>

        <div class="col-span-2 glass-panel flex flex-col overflow-hidden" id="matches">
            <div class="p-3  border-gray-200 text-whiteoff shrink-0 flex justify-between items-center"><h2
                    class="text-sm font-bold ">Matches</h2>
                <button onclick="Actions.findFingerprint()" id="btn-scan"
                        class="text-[10px]  hover:bg-gray-200  bg-yellow-900 px-2 py-1 rounded border border-gray-300 font-bold transition-colors text-black">
                    SCAN
                </button>
            </div>
            <div id="recommendations-list" class="flex-1 overflow-y-auto p-3 space-y-3 bg-dark-green">
                <div class="text-center text-white mt-10 text-xs">Click SCAN to find batches.</div>
            </div>
        </div>

  `;

  return container;
}
