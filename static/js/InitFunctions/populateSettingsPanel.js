export function populateSettingsPanel(controls) {
    const div = document.getElementById('settings-controls');
    div.innerHTML = '';
    Object.keys(controls).sort((a, b) => controls[a].priority - controls[b].priority).forEach(k => {
        const s = controls[k];
        const prColor = s.priority <= 3 ? 'text-yellow-600' : 'text-gray-400';
        div.innerHTML += `<div class="bg-dark-green p-2 rounded border border-gray-200 mb-2 hover:border-yellow-600 transition-colors shadow-sm"><div class="flex justify-between mb-1"><span class="text-xs font-bold text-white truncate">${k}</span><span class="text-[10px] ${prColor} font-mono font-bold">PR:${s.priority}</span></div><div class="grid grid-cols-4 gap-2"><div><span class="text-[8px] text-white block">L %</span><input id="c-${k}-L" type="number" value="${s.Lower}" class="compact-input w-full rounded text-center"></div><div><span class="text-[8px] text-white block">H %</span><input id="c-${k}-H" type="number" value="${s.Higher}" class="compact-input w-full rounded text-center"></div><div><span class="text-[8px] text-white block">MIN</span><input id="c-${k}-Min" type="number" value="${s.Min}" class="compact-input w-full rounded text-center"></div><div><span class="text-[8px] text-white block">MAX</span><input id="c-${k}-Max" type="number" value="${s.Max}" class="compact-input w-full rounded text-center"></div></div></div>`;
    });
}
