import { drawAiMnmParallelChart } from "./drawAiMnmParallelChart.js";

export function toggleAiMnmDashChart(mode) {
    const t = document.getElementById('ai-mnm-dash-chart-trend');
    const p = document.getElementById('ai-mnm-dash-chart-parallel');
    const btnT = document.getElementById('btn-ai-mnm-pred-trend');
    const btnP = document.getElementById('btn-ai-mnm-pred-parallel');

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
        drawAiMnmParallelChart();
    }
}
