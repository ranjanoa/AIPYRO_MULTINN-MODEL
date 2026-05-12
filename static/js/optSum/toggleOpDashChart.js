import { drawOpParallelChart} from "./drawOpParallelChart.js"
export function toggleOpDashChart(mode) {
     const t = document.getElementById('op-dash-chart-trend');
            const p = document.getElementById('op-dash-chart-parallel');
            const btnT = document.getElementById('btn-op-pred-trend');
            const btnP = document.getElementById('btn-op-pred-parallel');

            if (mode === 'trend') {
                t.classList.remove('hidden');
                p.classList.add('hidden');
                btnT.className = "text-[8px] font-bold px-2 py-0.5 bg-[#ebf552] bg-yellow-900 text-[#122a33] rounded hover:brightness-110 transition-colors";
                btnP.className = "text-[8px] font-bold px-2 py-0.5 border border-gray-100 text-white rounded hover:bg-white/5 transition-colors";
            } else {
                t.classList.add('hidden');
                p.classList.remove('hidden');
                btnT.className = "text-[8px] font-bold px-2 py-0.5 border border-gray-100 text-white rounded hover:bg-white/5 transition-colors";
                btnP.className = "text-[8px] font-bold px-2 py-0.5 bg-yellow-900 text-[#122a33] rounded hover:brightness-110 transition-colors";
                drawOpParallelChart();
            }
}
