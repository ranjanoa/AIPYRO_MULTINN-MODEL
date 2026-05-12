import {state} from "../inits/state.js";

export function toggleSimSidebar() {
    const sb = document.getElementById('sim-sidebar');
    const pa = document.getElementById('sim-plot-area');
    const btn = document.getElementById('sim-toggle-btn');
    if (state.ui.isSidebarOpen) {
        sb.classList.remove('hidden');
        sb.classList.add('col-span-3');
        pa.classList.replace('col-span-12', 'col-span-9');
       // btn.innerText = "◀";
        btn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="black">
            <path d="M15 18l-6-6 6-6"/>
        </svg>`;
    } else {
        sb.classList.add('hidden');
        sb.classList.remove('col-span-3');
        pa.classList.replace('col-span-9', 'col-span-12');
        btn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="black">
            <path d="M9 6l6 6-6 6"/>
        </svg>`;
       // btn.innerText = "▶";
    }
    state.ui.isSidebarOpen = !state.ui.isSidebarOpen;
    setTimeout(() => Plotly.Plots.resize('plotly-container'), 50);
}
