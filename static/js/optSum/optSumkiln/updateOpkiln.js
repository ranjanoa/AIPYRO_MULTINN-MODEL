import { state } from "../../inits/state.js";
import { drawOpParallelChartKiln } from "./drawOpParallelChartKiln.js";
import { drawOpSummaryChartKiln } from "./drawOpSummaryChartKiln.js";


export function updateOpkiln(data) {
    const now = Date.now();
    // console.log("state.currentModelConfig");
    // console.log(state.currentModelConfig);
    if (state.currentModelConfig && state.currentModelConfig.kpi_tags) {
        Object.keys(state.currentModelConfig.kpi_tags).forEach(kpiName => {
            const tag = state.currentModelConfig.kpi_tags[kpiName].tag;
            if (data[tag] !== undefined) {
                const el = document.getElementById(`op3-kiln-kpi-${tag.replace(/[^a-zA-Z0-9]/g, '')}`);
                if (el) {
                    el.innerText = parseFloat(data[tag]).toFixed(1);
                }
            }
        });
    }

    Object.keys(data).forEach(tag => {
        if (tag.includes('timestamp')) return;

        const safeId = tag.replace(/[^a-zA-Z0-9]/g, '');
        const val = parseFloat(data[tag]).toFixed(2);

        const curEl = document.getElementById(`op3-kiln-cur-${safeId}`);
        if (curEl) curEl.innerText = val;

       // const liveEl = document.getElementById(`op3-kiln-live-${safeId}`);
       // if (liveEl) liveEl.innerText = val;

        if (!state.opHistoryDataKiln[tag]) {
            state.opHistoryDataKiln[tag] = [];
        }

        state.opHistoryDataKiln[tag].push({ ts: now, val: parseFloat(data[tag]) });
        state.opHistoryDataKiln[tag] = state.opHistoryDataKiln[tag].filter(pt => (now - pt.ts) <= 16 * 60000); // 16 min buffer
    });

    drawOpSummaryChartKiln();
    drawOpParallelChartKiln();
}
