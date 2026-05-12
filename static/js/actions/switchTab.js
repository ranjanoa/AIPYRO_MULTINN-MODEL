import { fetchSoftSensorPrediction } from "../InitFunctions/fetchSoftSensor.js"
import { runSoftSensorSim } from "./runSoftSensorSim.js"
import { initSoftSensorSim } from "../InitFunctions/initSoftSensorSim.js"
import { drawOpSummaryChart } from "../optSum/drawOpSummaryChart.js"
import { drawOpParallelChart } from "../optSum/drawOpParallelChart.js"
import { drawOpSummaryChartKiln } from "../optSum/optSumkiln/drawOpSummaryChartKiln.js"
import { drawOpParallelChartKiln} from "../optSum/optSumkiln/drawOpParallelChartKiln.js"
import { drawOpSummaryChartPreheater } from "../optSum/optSumPreheater/drawOpSummaryChartPreheater.js"
import { drawOpParallelChartPreheater} from "../optSum/optSumPreheater/drawOpParallelChartPreheater.js"
import { drawOpSummaryChartCooler } from "../optSum/optSumCooler/drawOpSummaryChartCooler.js"
import { drawOpParallelChartCooler} from "../optSum/optSumCooler/drawOpParallelChartCooler.js"
import { initOpkiln } from "../optSum/optSumkiln/initOpkiln.js"
import { initOpPreheater } from "../optSum/optSumPreheater/initOpPreheater.js"
import { initOpCooler } from "../optSum/optSumCooler/initOpCooler.js"
import { initAiMnm } from "../optSum/optSumAiMnm/initAiMnm.js"
import { drawAiMnmSummaryChart } from "../optSum/optSumAiMnm/drawAiMnmSummaryChart.js"
import { drawAiMnmParallelChart } from "../optSum/optSumAiMnm/drawAiMnmParallelChart.js"
import { state } from "../inits/state.js"
export function switchTab(t) {
    const tabs = ['hybrid', 'fingerprint', 'mbrl', 'simulator', 'trends', 'config', 'softsensor', 'softsensor-sim', 'op-summary','op-kiln','op-preheater','op-cooler','ai-mnm'];

    // Stop AI_MNM polling when leaving the tab (started inside initAiMnm on entry)
    if (t !== 'ai-mnm' && state.aiMnmInterval) {
        clearInterval(state.aiMnmInterval);
        state.aiMnmInterval = null;
    }

    tabs.forEach(x => {
        const p = document.getElementById(`panel-${x}`);
        const b = document.getElementById(`nav-${x}`);

        if (p) {
            p.classList.add('hidden');
            p.classList.remove('grid', 'flex');
            if (x === t) {
                p.classList.remove('hidden');
                p.classList.add(x === 'softsensor-sim' || x === 'mbrl' || x === 'hybrid' || x === 'fingerprint' || x === 'simulator' || x === 'op-summary' ? 'grid' : 'flex' || x === 'op-kiln' ? 'grid' : 'flex'|| x === 'op-preheater' ? 'grid' : 'flex'|| x === 'op-cooler' ? 'grid' : 'flex'|| x === 'ai-mnm' ? 'grid' : 'flex');
            }
        }

        if (b) {
            // b.classList.remove('nav-btn-active');
            // b.classList.add('nav-btn-inactive');
            b.classList.remove('text-black', 'border-black', 'text-ai-cyan', 'border-ai-cyan', 'font-bold');
            b.classList.add('text-gray-500', 'border-transparent');
            if (x === t) {
                // b.classList.add('nav-btn-active');
                // b.classList.remove('nav-btn-inactive');
                if (x === 'hybrid') {
                    b.classList.add('text-ai-cyan', 'border-ai-cyan', 'font-bold');
                } else {
                    // b.classList.add('text-black', 'border-black');
                    b.classList.add('text-ai-cyan', 'border-ai-cyan', 'font-bold');
                }
                b.classList.remove('text-gray-500', 'border-transparent');
                setTimeout(() => {
                    window.dispatchEvent(new Event('resize'));
                    if (t === 'softsensor') fetchSoftSensorPrediction();
                    if (t === 'softsensor-sim') runSoftSensorSim();
                    if (t === 'op-summary' ) {
                        drawOpSummaryChart();
                        drawOpParallelChart();
                    }
                    if (t === 'op-kiln' ) {
                        initOpkiln();
                        drawOpSummaryChartKiln();
                        drawOpParallelChartKiln();
                    }
                    if (t === 'op-preheater' ) {
                        initOpPreheater();
                        drawOpSummaryChartPreheater();
                        drawOpParallelChartPreheater();
                    }
                    if (t === 'op-cooler' ) {
                        initOpCooler();
                        drawOpSummaryChartCooler();
                        drawOpParallelChartCooler();
                    }
                    if (t === 'ai-mnm' ) {
                        initAiMnm();
                        drawAiMnmSummaryChart();
                        drawAiMnmParallelChart();
                    }
                }, 100);
            }
        }
    });

    if (t === 'softsensor-sim') {
        initSoftSensorSim();
    }
}

// =========================================================================
// CHARTS & SOCKETS
// =========================================================================

