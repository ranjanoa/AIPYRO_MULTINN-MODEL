import {state} from "../inits/state.js";

export   function refreshBatchListUI() {
        const list = document.getElementById('recommendations-list');
        Array.from(list.children).forEach((c, i) => {
            c.classList.remove('batch-active', 'batch-disabled');
            if (i === state.selectedBatchIndex) c.classList.add('batch-active');
            if (state.isHybridEngaged) c.classList.add('batch-disabled');
        });
    }
