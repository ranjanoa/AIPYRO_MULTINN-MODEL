import {state} from "../inits/state.js";
import {MOCK_CONFIG} from "../inits/config.js";
import {displayRecs} from "./displayRecs.js";
import {selectRec} from "./selectRec.js";

export async function findFingerprint() {
    const btn = document.getElementById('find-fingerprint-btn');
    const btn2 = document.getElementById('btn-scan');
    const old = btn.innerText;
    btn.innerHTML = '...';
    btn.disabled = true;
    if (btn2) {
        btn2.innerHTML = '...';
        btn2.disabled = true;
    }
    const payload = {previous_Time: 30, future_Time: 30, deviation: {}};
    for (const k in state.controlDefaults) {
        payload.deviation[k] = {
            Lower: parseFloat(document.getElementById(`c-${k}-L`)?.value || 98),
            Higher: parseFloat(document.getElementById(`c-${k}-H`)?.value || 102),
            Min: parseFloat(document.getElementById(`c-${k}-Min`)?.value || -9999),
            Max: parseFloat(document.getElementById(`c-${k}-Max`)?.value || 9999),
            priority: state.controlDefaults[k].priority
        };
    }
    try {
        const res = await fetch(`${MOCK_CONFIG.API_URL}/api/fingerprint`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.data && json.data.length && json.data[0].fingerprint_Found !== "False") {
            state.allRecommendations = json.data;
            displayRecs(json.data);
            selectRec(0);
        } else {
            document.getElementById('recommendations-list').innerHTML = `<div class="flex flex-col items-center justify-center h-full space-y-2"><span class=\"text-sm text-whiteoff text-center\">No Matches</span><button onclick=\"findFingerprint()\" class=\"px-3 py-1 bg-blue-50 text-yellow-600 text-xs font-bold rounded hover:bg-blue-100\">Retry</button></div>`;
        }
    } catch (e) {
        alert("Error");
    }
    btn.innerHTML = old;
    btn.disabled = false;
    if (btn2) {
        btn2.innerHTML = 'SCAN';
        btn2.disabled = false;
    }
}

