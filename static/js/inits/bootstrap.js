import { initCharts } from "../shared/chart.js";
import { initSocket } from "../shared/socket.js";
import { initializeApp } from "../modules/app-init.js";
import { restoreState } from "../InitFunctions/restore.js"
import { initOpSummary } from "../optSum/initOpSummary.js"
import { initOpkiln } from "../optSum/optSumkiln/initOpkiln.js"
import { initOpPreheater } from "../optSum/optSumPreheater/initOppreheater.js";
import { initOpCooler } from "../optSum/optSumCooler/initOpCooler.js"
export function bootstrap() {
    initCharts();
    initializeApp().then(() => {
        initOpSummary();
        initOpkiln();
        initOpPreheater();
        initOpCooler();
        // Note: do NOT auto-start AI_MNM polling on boot — it kicks in only when the user lands on the tab.
        // This avoids needless requests when other tabs are active.
    });
    initSocket();
    restoreState();
}