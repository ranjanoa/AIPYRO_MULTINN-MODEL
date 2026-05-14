
export function populateConfigUI(cfg) {
     // Populate Active Strategy Selector
            const strategySel = document.getElementById('config-active-strategy');
            strategySel.innerHTML = '';
            if (cfg.strategies) {
                Object.keys(cfg.strategies).sort().forEach(sKey => {
                    const opt = document.createElement('option');
                    opt.value = sKey;
                    opt.text = sKey;
                    if (sKey === cfg.active_strategy) opt.selected = true;
                    strategySel.appendChild(opt);
                });
            }

            const ctrlBody = document.getElementById('config-controls-body');
            const indBody = document.getElementById('config-indicators-body');
            ctrlBody.innerHTML = '';
            indBody.innerHTML = '';

            const renderRow = (key, c, isMV) => {
                const isFilteringEnabled = (c.filtering && c.filtering.enabled) ? 'checked' : '';
                const isAIPC = c.aipc ? 'checked' : '';
                
                return `
                    <tr class="hover:bg-white/5 transition-colors group">
                        <td class="text-white border-gray-200 px-4 py-2 font-bold text-gray-300">${key}</td>
                        <td class="text-white border-gray-200 px-2 py-2 text-gray-500 font-mono">${c.unit || ''}</td>
                        <td class="text-white border-gray-200 px-2 py-2"><input type="number" data-tag="${key}" data-field="default_min" value="${c.default_min ?? 0}" class="w-16 bg-black/30 border border-white/10 rounded px-1 py-1 text-center text-blue-300"></td>
                        <td class="text-white border-gray-200 px-2 py-2"><input type="number" data-tag="${key}" data-field="default_max" value="${c.default_max ?? 0}" class="w-16 bg-black/30 border border-white/10 rounded px-1 py-1 text-center text-blue-300"></td>
                        <td class="text-white border-gray-200 px-2 py-2"><input type="number" data-tag="${key}" data-field="priority" value="${c.priority ?? 5}" class="w-12 bg-black/30 border border-white/10 rounded px-1 py-1 text-center text-yellow-500 font-bold"></td>
                        <td class="text-white border-gray-200 px-2 py-2"><input type="number" step="0.01" data-tag="${key}" data-field="nudge_speed" value="${c.nudge_speed ?? 0.05}" class="text-white border-gray-200 w-14 bg-black/30 border border-white/10 rounded px-1 py-1 text-center text-gray-400"></td>
                        ${isMV ? `<td class="text-white border-gray-200 px-3 py-2 text-center"><input type="checkbox" data-tag="${key}" data-field="aipc" ${isAIPC} class="w-4 h-4 accent-[#ebf552]"></td>` : ''}
                        <td class="text-white border-gray-200px-3 py-2 text-center"><input type="checkbox" data-tag="${key}" data-field="filtering_enabled" ${isFilteringEnabled} class="w-4 h-4 accent-[#ebf552]"></td>
                    </tr>`;
            };

            if (cfg.control_variables) {
                Object.keys(cfg.control_variables).sort().forEach(key => {
                    ctrlBody.innerHTML += renderRow(key, cfg.control_variables[key], true);
                });
            }
            if (cfg.indicator_variables) {
                Object.keys(cfg.indicator_variables).sort().forEach(key => {
                    indBody.innerHTML += renderRow(key, cfg.indicator_variables[key], false);
                });
            }

            // Populate Simulator Settings
            const simColorSel = document.getElementById('config-sim-default-color');
            if (simColorSel) {
                simColorSel.innerHTML = '';
                const allVars = [...Object.keys(cfg.control_variables || {}), ...Object.keys(cfg.indicator_variables || {})].sort();
                allVars.forEach(v => {
                    const opt = document.createElement('option');
                    opt.value = v;
                    opt.text = v;
                    if (cfg.simulator_settings && v === cfg.simulator_settings.default_color_by) opt.selected = true;
                    simColorSel.appendChild(opt);
                });
            }

            // -----------------------------------------------------------------
            // AI_MNM CV + Indicator parameter tables
            // -----------------------------------------------------------------
            const aiMnmCfg = cfg.ai_mnm || {};
            const cvParams = aiMnmCfg.cv_parameters || {};
            const indParams = aiMnmCfg.indicator_parameters || {};

            const escAttr = (s) => String(s ?? '').replace(/"/g, '&quot;');

            // Inline styles — the project ships a pre-built Tailwind CSS that does NOT
            // include w-12/w-14/w-16/w-32/w-36/w-44/w-56/text-cyan-300 etc., so utility-class
            // sizing fails silently and inputs collapse to invisibility. Inline style attrs
            // bypass the missing-class problem entirely.
            const baseInputStyle = "background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.1);border-radius:4px;padding:4px 6px;color:#fff;";
            const numStyle  = baseInputStyle + "width:70px;text-align:center;color:#93c5fd;";
            const prioStyle = baseInputStyle + "width:54px;text-align:center;color:#eab308;font-weight:700;";
            const nudgeStyle= baseInputStyle + "width:60px;text-align:center;color:#d1d5db;";
            const posStyle  = baseInputStyle + "width:54px;text-align:center;color:#d1d5db;";
            const unitStyle = baseInputStyle + "width:60px;text-align:center;color:#d1d5db;";
            const nameStyle = baseInputStyle + "width:170px;";
            const labelStyle= baseInputStyle + "width:180px;";
            const monoStyle = baseInputStyle + "width:230px;color:#67e8f9;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;";
            const indMonoStyle = baseInputStyle + "width:200px;color:#67e8f9;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;";

            const renderAiMnmCvRow = (key, c) => {
                return `
                <tr class="hover:bg-white/5 transition-colors group" data-row-type="cv">
                    <td class="px-3 py-2"><input type="text"   data-ai-mnm-row="cv" data-field="name"        value="${escAttr(key)}"                                  style="${nameStyle}"></td>
                    <td class="px-2 py-2"><input type="text"   data-ai-mnm-row="cv" data-field="label"       value="${escAttr(c.label ?? c.description ?? key)}"        style="${labelStyle}"></td>
                    <td class="px-2 py-2"><input type="text"   data-ai-mnm-row="cv" data-field="unit"        value="${escAttr(c.unit ?? '')}"                           style="${unitStyle}"></td>
                    <td class="px-2 py-2"><input type="text"   data-ai-mnm-row="cv" data-field="curr_field"  value="${escAttr(c.curr_field ?? '')}"                     style="${monoStyle}" placeholder="<param>_real"></td>
                    <td class="px-2 py-2"><input type="text"   data-ai-mnm-row="cv" data-field="sp_field"    value="${escAttr(c.sp_field ?? '')}"                       style="${monoStyle}" placeholder="<param>_AI_optimised"></td>
                    <td class="px-2 py-2"><input type="text"   data-ai-mnm-row="cv" data-field="target_var"  value="${escAttr(c.target_var ?? '')}"                     style="${monoStyle}" placeholder="control_variables key"></td>
                    <td class="px-2 py-2"><input type="number" data-ai-mnm-row="cv" data-field="default_min" value="${c.default_min ?? 0}"                              style="${numStyle}"></td>
                    <td class="px-2 py-2"><input type="number" data-ai-mnm-row="cv" data-field="default_max" value="${c.default_max ?? 0}"                              style="${numStyle}"></td>
                    <td class="px-2 py-2"><input type="number" data-ai-mnm-row="cv" data-field="priority"    value="${c.priority ?? 5}"                                 style="${prioStyle}"></td>
                    <td class="px-2 py-2"><input type="number" step="0.01" data-ai-mnm-row="cv" data-field="nudge_speed" value="${c.nudge_speed ?? 0.05}"                style="${nudgeStyle}"></td>
                    <td class="px-2 py-2"><input type="number" data-ai-mnm-row="cv" data-field="position"    value="${c.position ?? 1}"                                 style="${posStyle}"></td>
                </tr>`;
            };

            const renderAiMnmIndRow = (key, c) => {
                return `
                <tr class="hover:bg-white/5 transition-colors group" data-row-type="ind">
                    <td class="px-3 py-2"><input type="text"   data-ai-mnm-row="ind" data-field="name"        value="${escAttr(key)}"                                  style="${nameStyle}"></td>
                    <td class="px-2 py-2"><input type="text"   data-ai-mnm-row="ind" data-field="label"       value="${escAttr(c.label ?? c.description ?? key)}"        style="${labelStyle}"></td>
                    <td class="px-2 py-2"><input type="text"   data-ai-mnm-row="ind" data-field="unit"        value="${escAttr(c.unit ?? '')}"                           style="${unitStyle}"></td>
                    <td class="px-2 py-2"><input type="text"   data-ai-mnm-row="ind" data-field="field"       value="${escAttr(c.field ?? key)}"                         style="${indMonoStyle}" placeholder="kiln1 field name"></td>
                    <td class="px-2 py-2"><input type="number" data-ai-mnm-row="ind" data-field="default_min" value="${c.default_min ?? 0}"                              style="${numStyle}"></td>
                    <td class="px-2 py-2"><input type="number" data-ai-mnm-row="ind" data-field="default_max" value="${c.default_max ?? 0}"                              style="${numStyle}"></td>
                    <td class="px-2 py-2"><input type="number" data-ai-mnm-row="ind" data-field="position"    value="${c.position ?? 1}"                                 style="${posStyle}"></td>
                </tr>`;
            };

            const aiMnmCvBody = document.getElementById('config-ai-mnm-cv-body');
            if (aiMnmCvBody) {
                aiMnmCvBody.innerHTML = '';
                Object.keys(cvParams)
                    .sort((a, b) => (parseInt(cvParams[a].position) || 999) - (parseInt(cvParams[b].position) || 999) || a.localeCompare(b))
                    .forEach(key => {
                        aiMnmCvBody.innerHTML += renderAiMnmCvRow(key, cvParams[key]);
                    });
            }
            const aiMnmIndBody = document.getElementById('config-ai-mnm-ind-body');
            if (aiMnmIndBody) {
                aiMnmIndBody.innerHTML = '';
                Object.keys(indParams)
                    .sort((a, b) => (parseInt(indParams[a].position) || 999) - (parseInt(indParams[b].position) || 999) || a.localeCompare(b))
                    .forEach(key => {
                        aiMnmIndBody.innerHTML += renderAiMnmIndRow(key, indParams[key]);
                    });
            }

            // Expose row-templates so saveAiMnmConfig can append blank rows
            window.__aiMnmCvRowTemplate = renderAiMnmCvRow;
            window.__aiMnmIndRowTemplate = renderAiMnmIndRow;

            // Populate Upset Scenarios
            const upsetBody = document.getElementById('config-upsets-body');
            if (upsetBody && cfg.upset_conditions) {
                upsetBody.innerHTML = '';
                Object.keys(cfg.upset_conditions).sort().forEach(key => {
                    const u = cfg.upset_conditions[key];
                    const isEnabled = u.enabled ? 'checked' : '';
                    upsetBody.innerHTML += `
                        <tr class="hover:bg-white/5 transition-colors group">
                            <td class="text-gray-400 border-gray-200 px-4 py-2 font-mono text-[10px]">${key}</td>
                            <td class="text-white border-gray-200 px-4 py-2 font-bold">${u.description || 'No description'}</td>
                            <td class="text-gray-500 border-gray-200 px-2 py-2 text-center uppercase text-[10px]">${u.group || 'N/A'}</td>
                            <td class="text-white border-gray-200 px-2 py-2 text-center">
                                <input type="number" data-tag="${key}" data-field="priority" value="${u.priority ?? 5}" 
                                    class="w-12 bg-black/30 border border-white/10 rounded px-1 py-1 text-center text-orange-400 font-bold">
                            </td>
                            <td class="text-white border-gray-200 px-4 py-2 text-center">
                                <input type="checkbox" data-tag="${key}" data-field="enabled" ${isEnabled} 
                                    class="w-4 h-4 accent-[#ebf552]">
                            </td>
                        </tr>`;
                });
            }
}
