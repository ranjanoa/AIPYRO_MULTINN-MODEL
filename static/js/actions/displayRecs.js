import {selectRec} from "./selectRec.js"
export function displayRecs(list) {
    const div = document.getElementById('recommendations-list');
    div.innerHTML = '';
    list.forEach((r, i) => {
        const score = r.match_score || 0;
        const color = score > 90 ? 'text-green-600' : (score > 70 ? 'text-amber-500' : 'text-red-500');
        div.innerHTML += `<div onclick="Actions.selectRec(${i})" class="select-batch p-3 rounded bg-dark-green border border-gray-200 hover:border-yellow-600 cursor-pointer transition-all shadow-sm group mb-2"><div class="flex justify-between items-center"><span class="text-white group-hover:text-blue-800 text-sm font-bold">BATCH #${i + 1}</span><span class="${color} text-xs font-mono font-bold">${score}% MATCH</span></div><div class="text-[10px] text-whiteoff mt-1">${(r.fingerprint_timestamp || "").split(' ')[1]}</div></div>`;
    });
}

