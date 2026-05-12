export function SoftSensorSimulator() {
    const container = document.createElement("div");
    container.className = "soft-sensor-simulator-container hidden h-full grid-cols-12 gap-4";
    container.id = "panel-softsensor-sim"



    container.innerHTML = `
<div class="col-span-4 glass-panel flex flex-col bg-[#1a3842] overflow-hidden">
                <div class="p-4 border-b border-[#476570] brand-header-bg bg-yellow-900 flex justify-between items-center">
                    <div>
                        <h2 class="text-lg font-bold ">Manual Inputs</h2>
                        <p class="text-xs ">Adjust setpoints to simulate impact.</p>
                    </div>
                    <button onclick="Actions.initSoftSensorSim()"
                        class="bg-yellow-900 px-3 py-1.5 rounded text-[10px] border-black font-black hover:brightness-125 shadow transition-all uppercase tracking-wider hoverWhite">SYNC
                        LIVE</button>
                </div>
                <div id="sim-input-container" class="flex-1 overflow-y-auto p-5 space-y-6 custom-scrollbar"></div>
                <div class="p-4 border-t border-[#476570] bg-[#152e36]">
                    <button onclick="Actions.runSoftSensorSim()"
                        class="w-full py-3 bg-yellow-900 hover:bg-blue-500 font-bold rounded shadow transition-all">RUN
                        SIMULATION (60 min)</button>
                </div>
            </div>
            <div class="col-span-8 glass-panel flex flex-col bg-[#1a3842] p-4">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-lg font-bold text-white">Projected Response</h2>
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-bold text-whiteoff">VIEW:</span>
                        <select id="sim-output-select" onchange="Actions.runSoftSensorSim()"
                            class="border border-gray-300 rounded px-3 py-1.5 outline-none w-64 font-bold text-sm text-select-white"></select>
                    </div>
                </div>
                <div id="sim-chart-container" class="flex-1 relative w-full min-h-0">
                    <div class="flex h-full items-center justify-center text-gray-500">Run simulation to view data</div>
                </div>
            </div>`;
//     container.innerHTML = `

// <div class="col-span-4 glass-panel flex flex-col bg-[#1a3842] overflow-hidden">
//                 <div class="p-4 border-b border-[#476570] brand-header-bg flex justify-between items-center">
//                     <div><h2 class="text-lg font-bold text-[#122a33]">Manual Inputs</h2><p class="text-xs text-[#122a33]/70">Adjust setpoints to simulate impact.</p></div>
//                     <button onclick="Actions.initSoftSensorSim()" class="bg-[#122a33] text-[#ebf552] px-3 py-1.5 rounded text-[10px] font-black hover:brightness-125 shadow transition-all uppercase tracking-wider">SYNC LIVE</button>
//                 </div>
//                 <div id="sim-input-container" class="flex-1 overflow-y-auto p-5 space-y-6 custom-scrollbar"></div>
//                 <div class="p-4 border-t border-[#476570] bg-[#152e36]">
//                     <button onclick="Actions.runSoftSensorSim()" class="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded shadow transition-all">RUN SIMULATION (60 min)</button>
//                 </div>
//             </div>
//             <div class="col-span-8 glass-panel flex flex-col bg-[#1a3842] p-4">
//                 <div class="flex justify-between items-center mb-4">
//                     <h2 class="text-lg font-bold text-white">Projected Response</h2>
//                     <div class="flex items-center gap-2"><span class="text-xs font-bold text-[#ebf552]">VIEW:</span><select id="sim-output-select" onchange="Actions.runSoftSensorSim()" class="border border-gray-600 rounded px-2 py-1 text-xs font-bold bg-[#122a33] text-white outline-none"></select></div>
//                 </div>
//                 <div id="sim-chart-container" class="flex-1 relative w-full min-h-0">
//                     <div class="flex h-full items-center justify-center text-gray-500">Run simulation to view data</div>
//                 </div>
//             </div>            </div>`;


    return container;
}
