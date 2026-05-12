import {state} from "../inits/state.js";

export function updateAutoButtonUI() {
            const btn = document.getElementById('btn-auto-toggle');
            if (!btn) return;
            if (state.isAutoMode) {
                btn.innerText = "AUTO ENABLED";
                btn.className = "text-[10px] font-bold px-3 py-1 rounded border border-green-600 bg-green-500 text-white shadow-md transform scale-105 transition-all uppercase";

                // Visual Reset of Selection
                const list = document.getElementById('recommendations-list');
                if(list) Array.from(list.children).forEach(c => c.classList.remove('batch-active'));
                state.selectedBatchIndex = -1;
            } else {
                btn.innerText = "MANUAL";
                btn.className = "text-[10px] font-bold px-3 py-1 rounded border border-[#476570] bg-[#122a33] text-gray-400 hover:text-white hover:border-gray-400 shadow-sm transition-all uppercase";
            }
        }