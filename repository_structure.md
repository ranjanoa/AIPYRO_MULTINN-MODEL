# Deployed Repository Structure

This is the exact file schema representing the active tracked files successfully deployed to `https://github.com/ranjanoa/aipyro2004todeploy.git`.

```text
CimporDeployment-main10032026/
├── .github/
│   └── workflows/
│       └── build.yml
├── .gitignore
├── CimporApp.spec
├── Interactive_plot_duna.py
├── api.py
├── authentication.py
├── benchmark_nn.py
├── calculated_variables_export_guide.md
├── config.py
├── control_service.py
├── database.py
├── debug_ai.py
├── fingerprint_engine.py
├── logo.ico
├── main.py
├── previousInfo.py
├── process_model.py
├── readme.md
├── requirements.txt
├── files/
│   ├── json/
│   │   ├── model_config.json
│   │   └── search_failure_debug.txt
│   └── models/
│       ├── ensemble_wm_member_0.pth
│       ├── ensemble_wm_member_1.pth
│       ├── ensemble_wm_member_2.pth
│       ├── ensemble_wm_member_3.pth
│       ├── ensemble_wm_member_4.pth
│       └── sac_agent.pth
├── modules/
│   ├── upset_manager.py
│   └── ai_core/
│       ├── __init__.py
│       ├── mbrl_manager.py
│       ├── model_based_env.py
│       ├── sac_components.py
│       ├── safety_guardian.py
│       ├── train_offline.py
│       └── world_model.py
├── static/
│   ├── img/
│   │   └── getsitelogo.png
│   ├── lib/
│   │   ├── chart-adapter.js
│   │   ├── chart.js
│   │   ├── plotly.js
│   │   ├── socket.io.js
│   │   └── socket.io.js.old
│   ├── styles/
│   │   ├── fallback.css
│   │   └── style.css
│   └── js/
│       ├── actions.js
│       ├── addUi.js
│       ├── auth.js
│       ├── main.js
│       ├── InitFunctions/
│       │   ├── fetchSoftSensor.js
│       │   ├── initRealTimeList.js
│       │   ├── initSimulatorControls.js
│       │   ├── initSoftSensorDropdown.js
│       │   ├── initSoftSensorSim.js
│       │   ├── initTrendDropdown.js
│       │   ├── populateConfigUI.js
│       │   ├── populateMbrlDropdowns.js
│       │   ├── populateSettingsPanel.js
│       │   └── restore.js
│       ├── actions/
│       │   ├── displayRecs.js
│       │   ├── findFingerprint.js
│       │   ├── loadTrendData.js
│       │   ├── refreshBatchListUI.js
│       │   ├── runSimulation.js
│       │   ├── runSoftSensorSim.js
│       │   ├── saveConfig.js
│       │   ├── saveTableConfig.js
│       │   ├── selectRec.js
│       │   ├── switchTab.js
│       │   ├── syncData.js
│       │   ├── toggleAutoMode.js
│       │   ├── toggleConfigView.js
│       │   ├── toggleDashChart.js
│       │   ├── toggleHybridSystem.js
│       │   ├── toggleSimSidebar.js
│       │   └── updateMbrlChartTarget.js
│       ├── inits/
│       │   ├── bootstrap.js
│       │   ├── config.js
│       │   └── state.js
│       ├── modules/
│       │   └── app-init.js
│       ├── optSum/
│       │   ├── clearOpTrends.js
│       │   ├── drawOpParallelChart.js
│       │   ├── drawOpSummaryChart.js
│       │   ├── initOpSummary.js
│       │   ├── toggleOpDashChart.js
│       │   ├── toggleOpTrend.js
│       │   ├── updateOpSummary.js
│       │   ├── updateOpSummaryActions.js
│       │   ├── updateOpSummaryLive.js
│       │   ├── optSumCooler/
│       │   │   ├── clearOpTrendsCooler.js
│       │   │   ├── drawOpParallelChartCooler.js
│       │   │   ├── drawOpSummaryChartCooler.js
│       │   │   ├── initOpCooler.js
│       │   │   ├── toggleOpDashChartCooler.js
│       │   │   ├── toggleOpTrendCooler.js
│       │   │   ├── updateOpCooler.js
│       │   │   ├── updateOpCoolerLive.js
│       │   │   └── updateOpSummaryActionsCooler.js
│       │   ├── optSumPreheater/
│       │   │   ├── clearOpTrendsPreheater.js
│       │   │   ├── drawOpParallelChartPreheater.js
│       │   │   ├── drawOpSummaryChartPreheater.js
│       │   │   ├── initOppreheater.js
│       │   │   ├── toggleOpDashChartPreheater.js
│       │   │   ├── toggleOpTrendPreheater.js
│       │   │   ├── updateOpPreheaterLive.js
│       │   │   ├── updateOpSummaryActionsPreheater.js
│       │   │   └── updateOppreheater.js
│       │   └── optSumkiln/
│       │       ├── clearOpTrendsKiln.js
│       │       ├── drawOpParallelChartKiln.js
│       │       ├── drawOpSummaryChartKiln.js
│       │       ├── initOpkiln.js
│       │       ├── toggleOpDashChartKiln.js
│       │       ├── toggleOpTrendKiln.js
│       │       ├── updateOpKilnLive.js
│       │       ├── updateOpSummaryActionsKiln.js
│       │       └── updateOpkiln.js
│       ├── shared/
│       │   ├── api.js
│       │   ├── chart.js
│       │   └── socket.js
│       ├── ui/
│       │   ├── components/
│       │   │   ├── header.js
│       │   │   └── navbar.js
│       │   └── pages/
│       │       ├── configuration.js
│       │       ├── dashboard.js
│       │       ├── digital-simulator.js
│       │       ├── fingerprint.js
│       │       ├── hybrid-control.js
│       │       ├── login.js
│       │       ├── nural-network.js
│       │       ├── operator-cooler.js
│       │       ├── operator-kiln.js
│       │       ├── operator-preheater.js
│       │       ├── operator-summary.js
│       │       ├── soft-sensor-simulator.js
│       │       ├── soft-sensor.js
│       │       └── trend-analysis.js
│       └── updateFunctions/
│           ├── updateAutoButtonUI.js
│           ├── updateHybridDashboard.js
│           ├── updateHybridLive.js
│           ├── updateLiveUI.js
│           ├── updateMbrlLive.js
│           └── updateMbrlUI.js
└── templates/
    └── index.html
```
