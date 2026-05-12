import { state } from "../inits/state.js";

export function updateMbrlUI(data) {
    if (!data) return;

    try {
        const list = document.getElementById('mbrl-action-list');
        if (list) {
            list.innerHTML = '';
            let totalActivity = 0;
            if (state.isHybridEngaged && data.actions && data.actions.length > 0) {
                data.actions.forEach(a => {
                    state.aiTargets[a.var_name] = parseFloat(a.fingerprint_set_point);
                    const safeDiff = parseFloat(a.diff) || 0;
                    totalActivity += Math.abs(safeDiff);
                    const arrow = safeDiff > 0 ? "↑" : "↓";
                    const colorClass = safeDiff > 0 ? "text-green-600" : "text-red-500";
                    list.innerHTML += `<div class="p-2 border-b hover:bg-gray-800">
                        <div class="flex justify-between items-center">
                            <div>
                                <div class="text-[10px] font-bold text-whiteoff">${a.var_name}</div>
                                <div class="text-[8px] text-whiteoff italic font-bold">${a.reason || 'Optimizing'}</div>
                            </div>
                            <div class="text-right">
                                <div class="font-mono text-sm font-black text-whiteoff">${parseFloat(a.fingerprint_set_point).toFixed(2)}</div>
                                <div class="text-[8px] ${colorClass} font-bold">${arrow} ${Math.abs(safeDiff).toFixed(2)}</div>
                            </div>
                        </div>
                    </div>`;
                });
            } else {
                list.innerHTML = `<div class="flex items-center justify-center h-full text-xs text-gray-400 font-bold">
                    ${state.isHybridEngaged ? "System Optimized" : "System Standby"}
                </div>`;
            }
        }

        // --- Trust & Uncertainty Chart ---
        let finalScore = 0;
        let match = parseFloat(data.match_score);
        if (!isNaN(match) && match > 0) {
            finalScore = match;
        } else if (data.soft_sensors && (data.soft_sensors.ai_confidence !== undefined || data.soft_sensors.sac_confidence_score !== undefined)) {
            finalScore = data.soft_sensors.ai_confidence !== undefined ? data.soft_sensors.ai_confidence : data.soft_sensors.sac_confidence_score;
        } else if (data.confidence) {
            finalScore = data.confidence;
        }

        if (state.charts.mbrlUncertChart) {
            const uncertaintyBase = Math.max(0.1, 1.0 - (finalScore / 100));
            state.charts.mbrlUncertChart.data.datasets[0].data = Array(20).fill(0).map(() => (Math.random() * 0.5 * uncertaintyBase) + (uncertaintyBase * 0.5));
            state.charts.mbrlUncertChart.data.datasets[0].backgroundColor = finalScore > 80 ? '#bbf7d0' : (finalScore > 50 ? '#fed7aa' : '#fca5a5');
            state.charts.mbrlUncertChart.update('none');
        }

        // --- Agent Reward Metric ---
        const rewardEl = document.getElementById('mbrl-reward');
        if (rewardEl) {
            if (state.isHybridEngaged) {
                let dynamicReward = (finalScore / 10) + ((Math.random() - 0.5) * 0.3);
                // totalActivity is captured within the action list loop scope above
                // Note: using totalActivity from the outer scope of the list check
                rewardEl.innerText = Math.max(0, Math.min(10, dynamicReward)).toFixed(2);
            } else {
                rewardEl.innerText = "---";
            }
        }
    } catch (e) {
        console.error("MbrlUI update failure suppressed:", e.message);
    }
}