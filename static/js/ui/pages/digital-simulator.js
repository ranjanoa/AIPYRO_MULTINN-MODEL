export function DigitalSimulator() {
    const container = document.createElement("div");
    container.className = "digital-simulator-container hidden h-full grid-cols-12 gap-4 transition-grid";
    container.id = "panel-simulator"

    container.innerHTML = `
<!--        <button onclick="Actions.toggleSimSidebar()" id="sim-toggle-btn" class="sidebar-toggle">◀</button>-->
        <button onclick="Actions.toggleSimSidebar()" id="sim-toggle-btn" class="sidebar-toggle"  >
  
</button>
        <div id="sim-sidebar" class="col-span-3 glass-panel flex flex-col overflow-hidden transition-all duration-300">
            <div class="p-3 border-b border-gray-200 bg-yellow-900 flex justify-between items-center"><h2
                    class="text-sm font-bold text-black">Selection</h2></div>
            <div class="flex-1 overflow-y-auto p-3 space-y-4 ml-4 bg-dark-green">
                <div><h3
                        class="text-xs font-bold text-gray-500 mb-2 uppercase tracking-wider border-b border-gray-100 pb-1">
                    Controls</h3>
                    <div id="sim-controls-list" class="space-y-1"></div>
                </div>
                <div><h3
                        class="text-xs font-bold text-gray-500 mb-2 uppercase tracking-wider border-b border-gray-100 pb-1">
                    Indicators</h3>
                    <div id="sim-indicators-list" class="space-y-1"></div>
                </div>
            </div>
            <div class="p-3 bg-dark-green flex flex-col gap-3 shrink-0 border-t border-gray-200">
                <div><span class="text-xs text-gray-500 block mb-1">Color By:</span><select id="sim-color-var"
                                                                                            class="w-full outline-none font-bold rounded p-1 text-xs text-select-white"></select>
                </div>
                <div><span class="text-xs text-gray-500 block mb-1">Window:</span><select id="sim-time-window"
                                                                                          class="w-full outline-none font-bold rounded p-1 text-xs text-select-white">
                    <option value="1440">Last 24 Hours</option>
                    <option value="0">Full Dataset</option>
                </select></div>
                <button onclick="Actions.runSimulation()"
                        class="w-full py-2 bg-black text-white text-xs font-bold uppercase rounded hover:bg-gray-800 shadow-sm">
                    GENERATE PLOT
                </button>
            </div>
        </div>
        <div id="sim-plot-area"
             class="col-span-9 glass-panel p-3 flex flex-col relative transition-all duration-300 bg-dark-green h-full">
            <div id="plotly-container" class="flex-1 w-full min-h-0 relative overflow-x-auto">
                <div class="h-full flex items-center justify-center text-yellow-600 text-sm flex-col"><span>Select variables...</span>
                </div>
            </div>
        </div>

  `;

    return container;
}
