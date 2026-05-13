import { state } from "../inits/state.js";

export function updateOpSummaryActions(data) {
    if (!data) return;
    const insightsBox = document.getElementById('op-summary-insights');

    if (insightsBox) {
        const timeStr = new Date().toLocaleTimeString([], { hour12: false });
        let msg = "";

        if (data.match_score === "SAFETY-CLAMP") {
            msg = `<span class="text-red-500 font-bold">[${timeStr}] GUARDIAN: Safety limit breached. Clamping output.</span>`;
        } else if (data.upset_active) {
            msg = `<span class="text-orange-400 font-bold">[${timeStr}] UPSET OVERRIDE: Process disturbance detected — AI suppressed.</span>`;
            if (data.upset_summary && data.upset_summary.length > 0) {
                msg += ` <span class="text-gray-600">|</span> <span class="text-orange-300 text-[10px]">${data.upset_summary.join(' | ')}</span>`;
            }
        } else if (data.active_strategy === "AI") {
            const conf = data.soft_sensors?.ai_confidence || data.soft_sensors?.sac_confidence_score || data.confidence || 0;
            msg = `<span class="text-ai-cyan">[${timeStr}] AI: Optimization active (Conf: ${Math.round(conf)}%)</span>`;
            if (data.actions && data.actions.length > 0) {
                msg += ` <span class="text-gray-600">|</span> <span class="text-[10px] text-gray-300">Targeting: ${data.actions[0].var_name} &rarr; ${parseFloat(data.actions[0].fingerprint_set_point).toFixed(2)}</span>`;
            }
        } else if (data.match_score) {
            msg = `<span class="text-green-400">[${timeStr}] FINGERPRINT: Match Found (${data.match_score}%)</span>`;
            if (data.target_timestamp) {
                msg += ` <span class="text-gray-600">|</span> <span class="text-gray-400 text-[10px]">Ref: ${data.target_timestamp}</span>`;
            }
            if (data.match_meta) {
                const m = data.match_meta;
                let details = [];
                if (m.tsr_at_match !== undefined) details.push(`TSR: ${m.tsr_at_match}%`);
                if (m.shc_at_match !== undefined) details.push(`SHC: ${m.shc_at_match}`);
                if (m.primary_value_at_match !== undefined) details.push(`Target: ${m.primary_value_at_match}`);
                if (details.length > 0) msg += ` <span class="text-gray-600">|</span> <span class="text-[#ebf552] font-bold text-[10px]">Metrics: ${details.join(', ')}</span>`;
            }
        } else {
            msg = `<span class="text-white">[${timeStr}] SYSTEM: Calculating next cycle...</span>`;
        }

        if (data.soft_sensors) {
            const s = data.soft_sensors;
            let kpis = [];
            if (s.bzt_pred) kpis.push(`BZT:${Math.round(s.bzt_pred)}`);
            if (s.o2_pred) kpis.push(`O2:${parseFloat(s.o2_pred).toFixed(1)}`);
            if (kpis.length > 0) msg += ` <span class="text-gray-600">|</span> <span class="text-yellow-500/80 font-bold text-[10px]">KPIs: ${kpis.join(', ')}</span>`;
        }

        insightsBox.innerHTML = msg;
    }

    // 1. Prediction Persistence Logic
    // Only clear if switching modes or if explicitly provided
    const isFpMode = data.active_strategy === 'FINGERPRINT' || (state.isHybridEngaged && document.querySelector('input[name="strategy_select"]:checked')?.value === 'FINGERPRINT');
    
    if (isFpMode && state.allRecommendations.length > 0 && state.selectedBatchIndex >= 0) {
        const rec = state.allRecommendations[state.selectedBatchIndex];
        if (rec && rec.fingerprint_prediction) {
            Object.keys(rec.fingerprint_prediction).forEach(k => {
                state.opPredictionData[k] = rec.fingerprint_prediction[k];
            });
        }
    }

    if (data.fingerprint_prediction) {
        Object.keys(data.fingerprint_prediction).forEach(k => {
            state.opPredictionData[k] = data.fingerprint_prediction[k];
        });
    }

    // 2. Action Display & Nudging
    if (data.actions && data.actions.length > 0) {
        window.currentAIVars = data.actions.map(a => a.var_name);
        window.latestActions = data.actions;

        data.actions.forEach(act => {
            const safeId = act.var_name.replace(/[^a-zA-Z0-9]/g, '');
            const nspEl = document.getElementById(`op3-nsp-${safeId}`);
            const tgtEl = document.getElementById(`op3-tgt-${safeId}`);

            const liveCurr = state.latestLiveValues[act.var_name] !== undefined ?
                parseFloat(state.latestLiveValues[act.var_name]) :
                parseFloat(act.current_setpoint || 0);

            const finalTarget = parseFloat(act.fingerprint_set_point || 0);
            const backendNudge = act.nudge_target !== undefined ? parseFloat(act.nudge_target) : null;

            const varConf = state.currentModelConfig.control_variables[act.var_name];
            const gain = varConf ? (Math.abs(parseFloat(varConf.nudge_speed)) || 0.15) : 1.0;
            const defMax = varConf ? parseFloat(varConf.default_max || 9999) : 9999;
            const defMin = varConf ? parseFloat(varConf.default_min || -9999) : -9999;
            const span = Math.abs(defMax - defMin);
            const minPush = span < 10000 ? (span * 0.05) : 0.1;
            
            const gap = finalTarget - liveCurr;
            let nudgedTarget = backendNudge !== null ? backendNudge : finalTarget;
            
            // Fallback calculation only if backend didn't provide a nudge
            if (backendNudge === null && Math.abs(gap) > 0.001) {
                const moveRequest = Math.max(Math.abs(gap * gain), minPush);
                nudgedTarget = liveCurr + Math.sign(gap) * Math.min(moveRequest, Math.abs(gap));
            }

            const nudgeDiff = nudgedTarget - liveCurr;

            if (nspEl) {
                if (Math.abs(nudgeDiff) > 0.001) {
                    if (nudgeDiff > 0) {
                        nspEl.innerHTML = `<span class="text-blue-400 font-bold">▲ ${nudgedTarget.toFixed(2)}</span>`;
                    } else {
                        nspEl.innerHTML = `<span class="text-gray-400 font-bold">▼ ${nudgedTarget.toFixed(2)}</span>`;
                    }
                } else {
                    nspEl.innerHTML = `<span class="text-white">-</span>`;
                }
            }
            if (tgtEl) tgtEl.innerText = finalTarget.toFixed(2);
        });
    } else {
        window.currentAIVars = [];
        window.latestActions = [];
        document.querySelectorAll('[id^="op3-nsp-"]').forEach(el => el.innerHTML = `<span class="text-white">-</span>`);
        document.querySelectorAll('[id^="op3-tgt-"]').forEach(el => el.innerHTML = `<span class="text-white">---</span>`);
    }
}
