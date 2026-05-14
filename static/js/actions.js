
import { syncData } from "./actions/syncData.js";
import { saveConfig } from "./actions/saveConfig.js";
import { switchTab } from "./actions/switchTab.js";
import { runSoftSensorSim } from "./actions/runSoftSensorSim.js";
import { toggleSimSidebar } from "./actions/toggleSimSidebar.js";
import { runSimulation } from "./actions/runSimulation.js";
import { updateMbrlChartTarget } from "./actions/updateMbrlChartTarget.js";
import { toggleHybridSystem } from "./actions/toggleHybridSystem.js";
import { toggleDashChart } from "./actions/toggleDashChart.js";
import { findFingerprint } from "./actions/findFingerprint.js";
import { fetchSoftSensorPrediction } from "./InitFunctions/fetchSoftSensor.js";
import { loadTrendData } from "./actions/loadTrendData.js";
import { initializeApp } from "./modules/app-init.js";
import { toggleAutoMode } from "./actions/toggleAutoMode.js";
import { protectPage } from "./auth.js";
import { logout } from "./auth.js"
import { selectRec } from "./actions/selectRec.js";
import { clearOpTrends } from "./optSum/clearOpTrends.js";
import { toggleOpDashChart } from "./optSum/toggleOpDashChart.js";
import { toggleOpTrend} from "./optSum/toggleOpTrend.js"
import {toggleConfigView} from "./actions/toggleConfigView.js"
import {initSoftSensorSim} from "./InitFunctions/initSoftSensorSim.js"
import { saveTableConfig} from "./actions/saveTableConfig.js"
import { toggleConfigSection } from "./actions/toggleConfigSection.js";

import { clearOpTrendsKiln} from "./optSum/optSumkiln/clearOpTrendsKiln.js"
import { toggleOpDashChartKiln} from "./optSum/optSumkiln/toggleOpDashChartKiln.js"
import { toggleOpTrendKiln} from "./optSum/optSumkiln/toggleOpTrendKiln.js"

import { clearOpTrendsPreheater} from "./optSum/optSumPreheater/clearOpTrendsPreheater.js"
import { toggleOpDashChartPreheater} from "./optSum/optSumPreheater/toggleOpDashChartPreheater.js"
import { toggleOpTrendPreheater} from "./optSum/optSumPreheater/toggleOpTrendPreheater.js"

import { clearOpTrendsCooler} from "./optSum/optSumCooler/clearOpTrendsCooler.js"
import { toggleOpDashChartCooler} from "./optSum/optSumCooler/toggleOpDashChartCooler.js"
import { toggleOpTrendCooler} from "./optSum/optSumCooler/toggleOpTrendCooler.js"


import { clearAiMnmTrends } from "./optSum/optSumAiMnm/clearAiMnmTrends.js"
import { toggleAiMnmDashChart } from "./optSum/optSumAiMnm/toggleAiMnmDashChart.js"
import { toggleAiMnmTrend } from "./optSum/optSumAiMnm/toggleAiMnmTrend.js"
import { saveAiMnmConfig } from "./actions/saveAiMnmConfig.js"


window.Actions = {
    switchTab,
    toggleHybridSystem,
    toggleDashChart,
    findFingerprint,
    runSimulation,
    toggleSimSidebar,
    updateMbrlChartTarget,
    loadTrendData,
    runSoftSensorSim,
    saveConfig,
    syncData,
    fetchSoftSensorPrediction,
    initializeApp,
    toggleAutoMode,
    logout,
    selectRec,
    toggleOpDashChart,
    clearOpTrends,
    toggleOpTrend,
    toggleConfigView,
    initSoftSensorSim,
    saveTableConfig,
    toggleConfigSection,


      clearOpTrendsKiln,
    toggleOpDashChartKiln,
    toggleOpTrendKiln,

    clearOpTrendsPreheater,
    toggleOpDashChartPreheater,
    toggleOpTrendPreheater,

     clearOpTrendsCooler,
    toggleOpDashChartCooler,
    toggleOpTrendCooler,

    clearAiMnmTrends,
    toggleAiMnmDashChart,
    toggleAiMnmTrend,
    saveAiMnmConfig
};


export function initActions() {
//    console.log("✅ initActions");

    protectPage();

    // Default state AFTER UI exists
    switchTab("hybrid");

    toggleDashChart("trend");

    updateMbrlChartTarget("");
    toggleSimSidebar();
    // toggleAutoMode(); -- Removed as it flips state incorrectly on refresh

    runSoftSensorSim()
    loadTrendData();
 

}
