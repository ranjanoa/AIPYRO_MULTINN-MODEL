export function OperatorSummary() {
    const container = document.createElement("div");
    container.className = "op-summary-container hidden h-full grid-cols-12 gap-4 transition-grid overflow-hidden relative";
    container.id = "panel-op-summary"

    container.innerHTML = `
            <div class="col-span-10 flex flex-col gap-3 h-full overflow-hidden">
                <div id="op-kpi-row" class="flex gap-2 shrink-0 overflow-x-auto custom-scrollbar pb-1"></div>

                <div
                    class="glass-panel shrink-0 px-3 py-1.5 bg-[#1a3842] border border-[#2d4a54] flex flex-row items-center h-[34px] overflow-hidden gap-3">
                    <div
                        class="text-white text-[#ebf552] font-black uppercase tracking-widest flex items-center gap-1 shrink-0">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                            class="mr-1.5">
                            <circle cx="12" cy="12" r="10" />
                            <line x1="12" y1="16" x2="12" y2="12" />
                            <line x1="12" y1="8" x2="12.01" y2="8" />
                        </svg>
                        PROCESS INSIGHTS
                    </div>
                    <div id="op-summary-insights"
                        class="font-mono text-xs text-white leading-none whitespace-nowrap overflow-hidden text-ellipsis flex-1">
                        <span class="text-gray-500 italic">Awaiting cycle data...</span>
                    </div>
                </div>

                <div class="flex gap-2 shrink-0 w-full">
                    <div class="p-1 flex-1 min-w-0 glass-panel border border-[#2d4a54] bg-[#1a3842] flex flex-row">
                        <div
                            class="bg-[#152e36] text-white text-[10px] font-black tracking-widest uppercase border-r border-[#2d4a54] flex items-center justify-center shrink-0 w-8">
                            <span style="writing-mode: vertical-rl; transform: rotate(180deg);">Kiln Process</span>
                        </div>
                        <div class="flex-1 min-w-0">
                            <table class="w-full text-[11px] text-left table-fixed">
                                <thead class="text-gray-500 border-b border-[#2d4a54] bg-[#1a3842]">
                                    <tr>
                                        <th class="p-1.5 font-bold w-[45%] pl-2 truncate">Variable</th>
                                        <th class="p-1.5 font-bold text-right w-[15%] truncate">Curr</th>
                                        <th class="p-1.5 font-bold text-right w-[20%] truncate">Nudge</th>
                                        <th class="p-1.5 font-bold text-right w-[20%] pr-2 truncate">Target</th>
                                    </tr>
                                </thead>
                                <tbody id="op-table-kiln" class="divide-y divide-[#2d4a54]"></tbody>
                            </table>
                        </div>
                    </div>

                    <div class="p-1 flex-1 min-w-0 glass-panel border border-[#2d4a54] bg-[#1a3842] flex flex-row">
                        <div
                            class="bg-[#152e36] text-white text-[10px] font-black tracking-widest uppercase border-r border-[#2d4a54] flex items-center justify-center shrink-0 w-8">
                            <span style="writing-mode: vertical-rl; transform: rotate(180deg);">Preheater /
                                Precalciner</span>
                        </div>
                        <div class="flex-1 min-w-0">
                            <table class="w-full text-[11px] text-left table-fixed">
                                <thead class="text-gray-500 border-b border-[#2d4a54] bg-[#1a3842]">
                                    <tr>
                                        <th class="p-1.5 font-bold w-[45%] pl-2 truncate">Variable</th>
                                        <th class="p-1.5 font-bold text-right w-[15%] truncate">Curr</th>
                                        <th class="p-1.5 font-bold text-right w-[20%] truncate">Nudge</th>
                                        <th class="p-1.5 font-bold text-right w-[20%] pr-2 truncate">Target</th>
                                    </tr>
                                </thead>
                                <tbody id="op-table-phpc" class="divide-y divide-[#2d4a54]"></tbody>
                            </table>
                        </div>
                    </div>

                    <div class="p-1 flex-1 min-w-0 glass-panel border border-[#2d4a54] bg-[#1a3842] flex flex-row">
                        <div
                            class="bg-[#152e36] text-white text-[10px] font-black tracking-widest uppercase border-r border-[#2d4a54] flex items-center justify-center shrink-0 w-8">
                            <span style="writing-mode: vertical-rl; transform: rotate(180deg);">Cooler Section</span>
                        </div>
                        <div class="flex-1 min-w-0">
                            <table class="w-full text-[11px] text-left table-fixed">
                                <thead class="text-gray-500 border-b border-[#2d4a54] bg-[#1a3842]">
                                    <tr>
                                        <th class="p-1.5 font-bold w-[45%] pl-2 truncate">Variable</th>
                                        <th class="p-1.5 font-bold text-right w-[15%] truncate">Curr</th>
                                        <th class="p-1.5 font-bold text-right w-[20%] truncate">Nudge</th>
                                        <th class="p-1.5 font-bold text-right w-[20%] pr-2 truncate">Target</th>
                                    </tr>
                                </thead>
                                <tbody id="op-table-cooler" class="divide-y divide-[#2d4a54]"></tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div class="flex-1 flex min-h-0 shrink-0 w-full mt-2">
                    <div class="glass-panel flex-1 flex flex-col min-h-0 border border-[#2d4a54] bg-[#1a3842] min-w-0">
                        <div
                            class="p-1.5 bg-[#152e36] border-b border-gray-100 flex justify-between items-center shrink-0">
                            <span class="text-[10px] font-bold text-white uppercase tracking-wider">Real-Time Trends &
                                AI Predictions</span>
                            <div class="flex gap-2">
                                <button onclick="Actions.clearOpTrends()"
                                    class="text-[8px] font-bold px-2 py-0.5 border border-red-500 text-red-500 rounded hover:bg-red-500 hover:text-white transition-colors">CLEAR
                                    MANUAL TRENDS</button>
                                <div class="w-px h-3 bg-gray-600 mx-1"></div>
                                <button onclick="Actions.toggleOpDashChart('trend')" id="btn-op-pred-trend"
                                    class="text-[8px] font-bold px-2 py-0.5 bg-[#ebf552] text-white rounded hover:brightness-110 transition-colors">TREND
                                    VIEW</button>
                                <button onclick="Actions.toggleOpDashChart('parallel')" id="btn-op-pred-parallel"
                                    class="text-[8px] font-bold px-2 py-0.5 border border-gray-100 text-white rounded hover:bg-white/5 transition-colors">PARALLEL
                                    VIEW</button>
                            </div>
                        </div>
                        <div id="op-dash-chart-trend" class="flex-1 relative w-full min-h-0 p-1"><canvas
                                id="op-summary-chart-canvas"></canvas></div>
                        <div id="op-dash-chart-parallel" class="hidden relative w-full flex-1 min-h-0 p-1">
                            <div id="op-dash-plotly" class="w-full h-full"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div
                class="col-span-2 glass-panel flex flex-col h-full border border-[#2d4a54] bg-[#1a3842] overflow-hidden">
                <div
                    class="bg-yellow-900 text-[#122a33] text-[10px] font-black uppercase p-3 flex justify-between items-center shrink-0 shadow-md">
                    LIVE SENSORS <span
                        class="text-[8px] px-2 py-0.5 font-bold opacity-70 border  border-black  px-1 rounded">FIXED VIEW</span>
                </div>
                <div id="op-live-sensors-list" class="flex-1 overflow-hidden p-1 flex flex-col gap-0.5 overflow-y-auto"></div>
            </div>
  `;

    return container;
}
