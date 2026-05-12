export function NuralNetwork() {
  const container = document.createElement("div");
  container.className = "nural-network-container hidden grid-cols-12 gap-4 h-full w-full grid ";
  container.id = "panel-mbrl"

  container.innerHTML = `
        <div class="col-span-2 glass-panel flex flex-col rounded overflow-hidden">
            <div class="bg-yellow-900 p-2  flex justify-between items-center"><h2
                    class="text-[10px] font-bold tracking-wider">LIVE SENSORS</h2></div>
            <div id="mbrl-live-list" class="flex-1 overflow-y-auto p-2 space-y-1 font-mono text-[10px] bg-dark-green"></div>
        </div>
        <div class="col-span-7 flex flex-col gap-4 overflow-y-auto">
            <div class="h-1/3 glass-panel rounded p-3 flex flex-col relative bg-yellow-900"><h2
                    class="text-[10px] font-bold text-whiteoff uppercase">Ensemble Uncertainty (System Confidence)</h2>
                <div class="flex-1 relative overflow-hidden">
                    <canvas id="mbrl-uncertainty-chart"></canvas>
                </div>
                <div class="absolute top-2 right-2 text-right">
                    <div class="text-2xl font-black text-whiteoff" id="mbrl-reward">---</div>
                    <div class="text-[9px] text-whiteoff font-bold uppercase">Estimated Reward</div>
                </div>
            </div>
            <div class="h-2/3 glass-panel rounded p-3 flex flex-col bg-yellow-900">
                <div class="flex justify-between items-center mb-2"><h2
                        class="text-[10px] font-bold text-whiteoff uppercase">Control Trajectory</h2><select
                        id="mbrl-chart-select" onchange="Actions.updateMbrlChartTarget(this.value)"
                        class="text-[10px] border rounded text-select-white font-bold"></select></div>
                <div class="flex-1 relative overflow-hidden">
                    <canvas id="mbrl-trend-chart"></canvas>
                </div>
            </div>
        </div>
        <div class="col-span-3 flex flex-col gap-4 overflow-y-auto">
            <div class="flex-1 glass-panel rounded flex flex-col overflow-hidden bg-dark-green">
                <div class=" header-border-bottom p-2 border-b flex justify-between items-center"><h2
                        class="text-[10px] font-bold text-whiteoff uppercase">Current Action</h2></div>
                <div id="mbrl-action-list" class="flex-1 overflow-y-auto bg-dark-green p-0"></div>
            </div>
            <div class="h-1/3 glass-panel rounded flex flex-col overflow-hidden border-t-2 header-border-bottom">
                <div class=" p-2 border-b border-red-100 header-border-bottom"><h2 class="text-[10px] font-bold text-red-200">
                    GUARDIAN LOGS</h2></div>
                <div id="mbrl-guardian-log"
                     class="flex-1 overflow-y-auto p-2 font-mono text-[9px] bg-gray-900 text-gray-300"></div>
            </div>
        </div>
  `;

  return container;
}
