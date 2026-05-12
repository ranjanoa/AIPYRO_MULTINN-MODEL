import { drawOpParallelChartCooler} from "./drawOpParallelChartCooler.js"
export function toggleOpDashChartCooler(mode) {
     const t = document.getElementById('op-dash-chart-trend-cooler');
            const p = document.getElementById('op-dash-chart-parallel-cooler');
            const btnT = document.getElementById('btn-op-pred-trend-cooler');
            const btnP = document.getElementById('btn-op-pred-parallel-cooler');

            if (mode === 'trend') {
                t.classList.remove('hidden');
                p.classList.add('hidden');
                btnT.className = "text-[8px] font-bold px-2 py-0.5 bg-[#ebf552] text-whiteoff rounded hover:brightness-110 transition-colors";
                btnP.className = "text-[8px] font-bold px-2 py-0.5 border border-gray-500 text-gray-400 rounded hover:bg-white/5 transition-colors";
            } else {
                t.classList.add('hidden');
                p.classList.remove('hidden');
                btnT.className = "text-[8px] font-bold px-2 py-0.5 border border-gray-500 text-gray-400 rounded hover:bg-white/5 transition-colors";
                btnP.className = "text-[8px] font-bold px-2 py-0.5 bg-[#ebf552] text-whiteoff rounded hover:brightness-110 transition-colors";
                drawOpParallelChartCooler();
            }
}
