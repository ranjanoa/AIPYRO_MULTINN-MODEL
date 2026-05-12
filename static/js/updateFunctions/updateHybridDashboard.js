import { state } from "../inits/state.js";

export function updateHybridDashboard(data) {
    if (!data) return;

    try {
        // --- 1. CONNECTION STATUS ---
        const connectionDot = document.getElementById('hybrid-connection-dot');
        if (connectionDot) {
            connectionDot.className = "w-2 h-2 rounded-full bg-green-500 animate-pulse";
        }
        const lastUpdate = document.getElementById('last-update-time');
        if (lastUpdate) {
            lastUpdate.innerText = new Date().toLocaleTimeString();
        }

        // --- 2. LOGICAL DRIVER RESOLUTION ---
        // Determine mode and driver for synchronized UI updates
        if (data.active_strategy) state.activeStrategy = data.active_strategy;
        const strategy = state.activeStrategy || data.active_strategy;
        let currentDriver = data.driver;

        // Auto-fix labels if driver is missing or generic
        if (strategy === 'FINGERPRINT') currentDriver = 'HISTORY';
        else if (strategy === 'NEURAL' || strategy === 'AI') currentDriver = 'AI';
        
        const isHistory = String(currentDriver || '').includes('HISTORY');
        const driverLabel = isHistory ? 'HISTORICAL' : 'AI-NN';
        const driverClass = isHistory ? 'bg-blue-600' : 'bg-cyan-600';

        // Update Header Badge
        const tableHeader = document.querySelector("#active-driver-container h3");
        if (tableHeader) {
            const badgeHtml = `<span class="active-driver-badge text-[9px] ml-2 px-2 py-0.5 rounded ${driverClass} text-white font-black uppercase tracking-wider border border-white/20 shadow-sm">DRIVER: ${driverLabel}</span>`;
            tableHeader.innerHTML = `Active Adjustments ${badgeHtml}`;
        }

        // --- 3. DUAL-SCORE MAPPING (FP/NN MINI-INDICATORS) ---
        // Priority: data.fp_score/ai_score (new) -> fallback to older paths
        const fpScore = Math.round(data.fp_score !== undefined ? data.fp_score : (data.match_meta?.similarity_score || data.match_score || 0));
        const nnScore = Math.round(data.ai_score !== undefined ? data.ai_score : (data.soft_sensors?.ai_confidence || data.soft_sensors?.sac_confidence_score || data.confidence || 0));

        // Update Mini indicators (always visible in Hybrid card)
        const miniFp = document.getElementById('mini-fp-score');
        const miniNn = document.getElementById('mini-nn-score');
        if (miniFp) miniFp.innerText = fpScore;
        if (miniNn) miniNn.innerText = nnScore;

        // Update Dual Bars (Hybrid Detail View)
        const fpBar = document.getElementById('fp-conf-bar');
        const fpText = document.getElementById('fp-confidence-text');
        if (fpBar) fpBar.style.width = `${fpScore}%`;
        if (fpText) fpText.innerText = `${fpScore}%`;
        
        const nnBar = document.getElementById('nn-conf-bar');
        const nnText = document.getElementById('nn-confidence-text');
        if (nnBar) nnBar.style.width = `${nnScore}%`;
        if (nnText) nnText.innerText = `${nnScore}%`;

        // --- 4. HERO SCORE RESOLVER (MAIN GAUGE) ---
        const isHybrid = strategy === 'HYBRID';
        const singleScoreContainer = document.getElementById('single-score-container');
        const dualScoreContainer = document.getElementById('dual-score-container');

        // RESOLVE HERO SCORE: Which one is currently driving?
        // Explicitly check strategy name for more robust mapping
        let heroScore = nnScore; 
        if (strategy === 'FINGERPRINT' || strategy === 'HISTORY' || isHistory) {
            heroScore = fpScore;
        }

        if (isHybrid && dualScoreContainer) {
            if (singleScoreContainer) singleScoreContainer.classList.add('hidden');
            dualScoreContainer.classList.remove('hidden');
        } else if (singleScoreContainer) {
            if (dualScoreContainer) dualScoreContainer.classList.add('hidden');
            singleScoreContainer.classList.remove('hidden');
            
            const confVal = document.getElementById('conf-val');
            const confBar = document.getElementById('conf-bar');
            if (confVal) confVal.innerText = heroScore;
            if (confBar) confBar.style.width = `${heroScore}%`;
        }

        // Update Main Badge (High/Moderate Trust)
        const badge = document.getElementById('conf-badge');
        if (badge) {
            if (data.system_trust === 0 || data.match_score === "SYSTEM-PAUSED") {
                badge.innerText = "LOCKED";
                badge.className = "px-2 py-1 bg-red-900 text-red-200 text-[9px] font-black rounded uppercase border border-red-700";
            } else if (heroScore > 80) {
                badge.innerText = "HIGH TRUST";
                badge.className = "px-2 py-1 bg-green-900 text-green-200 text-[9px] font-black rounded uppercase border border-green-700";
            } else if (heroScore > 50) {
                badge.innerText = "MODERATE";
                badge.className = "px-2 py-1 bg-blue-900 text-blue-200 text-[9px] font-black rounded uppercase border border-blue-700";
            } else {
                badge.innerText = "LOW TRUST";
                badge.className = "px-2 py-1 bg-slate-800 text-slate-400 text-[9px] font-black rounded uppercase border border-slate-700";
            }
        }

        // --- 5. ACTIONS TABLE ---
        const tbody = document.getElementById('action-table-body');
        if (tbody) {
            tbody.innerHTML = '';
            if (data.actions && data.actions.length > 0) {
                data.actions.forEach(act => {
                    const varConf = state.currentModelConfig.control_variables ? state.currentModelConfig.control_variables[act.var_name] : null;
                    const tag = varConf ? varConf.tag : act.var_name;

                    const liveCurr = (state.latestLiveValues[tag] !== undefined)
                        ? parseFloat(state.latestLiveValues[tag])
                        : (state.latestLiveValues[act.var_name] !== undefined)
                            ? parseFloat(state.latestLiveValues[act.var_name])
                            : parseFloat(act.current_setpoint || 0);
                    
                    const finalTarget = parseFloat(act.fingerprint_set_point || 0);
                    const gain = varConf ? (Math.abs(parseFloat(varConf.nudge_speed)) || 0.15) : 1.0;
                    const defMax = varConf ? parseFloat(varConf.default_max || 9999) : 9999;
                    const defMin = varConf ? parseFloat(varConf.default_min || -9999) : -9999;
                    const span = Math.abs(defMax - defMin);
                    const minPush = span < 10000 ? (span * 0.05) : 0.1;
                    
                    const gap = finalTarget - liveCurr;
                    let nudgeTarget = finalTarget;
                    
                    if (Math.abs(gap) > 0.001) {
                        const moveRequest = Math.max(Math.abs(gap * gain), minPush);
                        nudgeTarget = liveCurr + Math.sign(gap) * Math.min(moveRequest, Math.abs(gap));
                    }

                    const diff = finalTarget - liveCurr;

                    let nudgeHtml = `<span class="text-gray-500">-</span>`;
                    if (Math.abs(diff) > 0.001) {
                        const color = diff > 0 ? "text-green-400" : "text-yellow-400";
                        const arrow = diff > 0 ? "▲" : "▼";
                        nudgeHtml = `<span class="${color} font-black drop-shadow-sm">${arrow} <span class="text-white">${nudgeTarget.toFixed(2)}</span></span>`;
                    }

                    tbody.innerHTML += `
                        <tr class="border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors">
                            <td class="pl-3 py-3">
                                <div class="font-bold text-white text-xs">${act.var_name}</div>
                                <span class="text-[9px] font-bold text-gray-400 uppercase tracking-tighter">${act.reason || 'Optimizing'}</span>
                            </td>
                            <td class="font-mono text-xs text-white font-bold">${liveCurr.toFixed(2)}</td>
                            <td class="font-mono text-xs">${nudgeHtml}</td>
                            <td class="font-mono text-sm font-black text-white drop-shadow-sm">${finalTarget.toFixed(2)}</td>
                        </tr>`;
                });
            } else {
                tbody.innerHTML = `<tr><td colspan="4" class="text-center py-12 text-gray-500 italic font-mono text-[10px]">
                    ${state.activeStrategy ? "SYSTEM ACTIVE - STABILIZING" : "SYSTEM STANDBY<br>No Control Commands Active."}</td></tr>`;
            }
        }

        // --- 6. INSIGHT LOG ---
        const log = document.getElementById('hybrid-insight-log');
        if (log && data.insights && data.insights.length > 0) {
            const now = new Date().toLocaleTimeString([], { hour12: false });
            if (log.innerHTML.includes("Initializing insight monitor...")) log.innerHTML = "";

            const entry = document.createElement('div');
            entry.className = "pb-4 mb-2 border-b border-white/5 last:border-0";
            let entryHtml = `<div class="text-[8px] text-gray-500 mb-1 font-mono">[${now}] CYCLE UPDATE</div>`;
            
            data.insights.forEach(insight => {
                let colorClass = "text-gray-400";
                if (insight.type === 'strategy') colorClass = "text-blue-300 italic";
                else if (insight.type === 'goal') colorClass = "text-white font-bold";
                else if (insight.type === 'logic') colorClass = "text-ai-cyan";
                else if (insight.type === 'safety') colorClass = "text-red-500 font-black animate-pulse";
                else if (insight.type === 'hcf') colorClass = "text-yellow-500";
                entryHtml += `<div class="${colorClass} leading-tight mb-0.5">${insight.text}</div>`;
            });
            
            entry.innerHTML = entryHtml;
            log.insertBefore(entry, log.firstChild);
            while (log.children.length > 15) { log.removeChild(log.lastChild); }
        }

    } catch (e) {
        console.error("Critical Hybrid Dashboard Update Failure:", e);
    }
}
