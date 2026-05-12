export function OperatorCooler() {
    const container = document.createElement("div");
    container.className = "op-cooler-container hidden h-full grid-cols-12 gap-4 transition-grid overflow-hidden relative";
    container.id = "panel-op-cooler"

    container.innerHTML = `
            <div class="col-span-10 flex flex-col gap-3 h-full overflow-hidden">
                

                <div class="flex gap-2 shrink-0 w-full">
                  
                    <div class="p-1 flex-1 min-w-0 glass-panel border border-[#2d4a54] bg-[#1a3842] flex flex-row">
                        <div
                            class="bg-[#152e36] text-white text-[10px] font-black tracking-widest uppercase border-r border-[#2d4a54] flex items-center justify-center shrink-0 w-8">
                            <span style="writing-mode: vertical-rl; transform: rotate(180deg);">Cooler Section</span>
                        </div>
                        <div class="flex-1 min-w-0">
                            <table class="w-full text-[11px] text-left table-fixed">
                                <thead class="text-gray-500 border-b border-[#2d4a54] bg-[#1a3842]">
                                    <tr>
                                        <th class="p-1.5  font-bold w-[45%] pl-2 truncate">Variable</th>
                                        <th class="p-1.5  font-bold text-right w-[15%] truncate">Curr</th>
                                        <th class="p-1.5  font-bold text-right w-[20%] truncate">Nudge</th>
                                        <th class="p-1.5  font-bold text-right w-[20%] pr-2 truncate">Target</th>
                                    </tr>
                                </thead>
                                <tbody id="op-table-coolersec" class="divide-y divide-[#2d4a54]"></tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div class="flex-1 flex min-h-0 shrink-0 w-full mt-2">
                    <div class="glass-panel flex-1 flex flex-col min-h-0 border border-[#2d4a54] bg-[#1a3842] min-w-0">
                        <div
                            class="p-1.5 bg-[#152e36] border-b border-[#2d4a54] flex justify-between items-center shrink-0">
                            <span class="text-[10px] font-bold text-white uppercase tracking-wider">Real-Time Trends &
                                AI Predictions</span>
                            <div class="flex gap-2">
                                <button onclick="Actions.clearOpTrendsCooler()"
                                    class="text-[8px] font-bold px-2 py-0.5 border border-red-500 text-red-500 rounded hover:bg-red-500 hover:text-white transition-colors">CLEAR
                                    MANUAL TRENDS</button>
                                <div class="w-px h-3 bg-gray-600 mx-1"></div>
                                <button onclick="Actions.toggleOpDashChartCooler('trend')" id="btn-op-pred-trend-cooler"
                                    class="text-[8px] font-bold px-2 py-0.5 bg-[#ebf552] text-whiteoff rounded hover:brightness-110 transition-colors">TREND
                                    VIEW</button>
                                <button onclick="Actions.toggleOpDashChartCooler('parallel')" id="btn-op-pred-parallel-cooler"
                                    class="text-[8px] font-bold px-2 py-0.5 border border-gray-500 text-gray-400 rounded hover:bg-white/5 transition-colors">PARALLEL
                                    VIEW</button>
                            </div>
                        </div>
                        <div id="op-dash-chart-trend-cooler" class="flex-1 relative w-full min-h-0 p-1"><canvas
                                id="op-summary-chart-canvas-cooler"></canvas></div>
                        <div id="op-dash-chart-parallel-cooler" class="hidden relative w-full flex-1 min-h-0 p-1">
                            <div id="op-dash-plotly-cooler" class="w-full h-full"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div
                class="col-span-2 glass-panel flex flex-col h-full border border-[#2d4a54] bg-[#1a3842] overflow-hidden">
                <div
                    class="bg-yellow-900 text-[#122a33] text-[10px] font-black uppercase p-3 flex justify-between items-center shrink-0 shadow-md">
                    LIVE SENSORS
                    <span class="text-[9px] bg-yellow-900/40 text-[#122a33] px-1.5 py-0.5 rounded border border-[#ebf552]/40 font-black">SITE-WIDE VIEW</span>
                </div>
                <div id="op-live-sensors-list-cooler" class="flex-1 overflow-y-auto p-1 flex flex-col gap-0.5"></div>
            </div>
  `;

    return container;
}
