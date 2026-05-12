import { state } from "../inits/state.js";

export function updateLiveUI(data) {
    if (!data) return;

    try {
        // --- Single Value Updates ---
        Object.keys(data).forEach(k => {
            const sanitizedId = k.replace(/[^a-zA-Z0-9-_]/g, '');
            const el = document.getElementById(`live-val-${sanitizedId}`);
            if (el) {
                const val = parseFloat(data[k]);
                if (!isNaN(val)) {
                    el.innerText = val.toFixed(2);
                    el.classList.add('val-flash');
                    setTimeout(() => el.classList.remove('val-flash'), 300);
                }
            }
        });

        // --- Chart Data Injection ---
        if (state.charts.timeSeriesChart && data['1_timestamp']) {
            state.charts.timeSeriesChart.data.datasets.forEach(ds => {
                const labelBase = ds.label ? ds.label.split(' (')[0] : null;
                if (labelBase && ds.label.includes('(Real)') && data[labelBase] !== undefined) {
                    const newVal = parseFloat(data[labelBase]);
                    if (!isNaN(newVal)) {
                        ds.data.push({ x: 0, y: newVal });
                        ds.data.forEach((pt, i) => {
                            pt.x = i - (ds.data.length - 1);
                        });
                        while (ds.data.length > 0 && ds.data[0].x < -10) ds.data.shift();
                    }
                }
            });
            state.charts.timeSeriesChart.update('none');
        }
    } catch (e) {
        console.error("LiveUI update failure suppressed:", e.message);
    }
}
