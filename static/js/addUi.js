// addUi.js

import { login } from "./ui/pages/login.js";
import { attachLoginHandler } from "./auth.js";

import { Header } from "./ui/components/header.js";
import { Navbar } from "./ui/components/navbar.js";

import { dashboard } from "./ui/pages/dashboard.js";
import { HybridControl } from "./ui/pages/hybrid-control.js";
import { Fingerprint } from "./ui/pages/fingerprint.js";
import { NuralNetwork } from "./ui/pages/nural-network.js";
import { DigitalSimulator } from "./ui/pages/digital-simulator.js";
import { SoftSensor } from "./ui/pages/soft-sensor.js";
import { SoftSensorSimulator } from "./ui/pages/soft-sensor-simulator.js";
import { TrendAnalysis } from "./ui/pages/trend-analysis.js";
import { Configuration } from "./ui/pages/configuration.js";
import { OperatorSummary } from "./ui/pages/operator-summary.js";
import { OperatorKiln } from "./ui/pages/operator-kiln.js";
import { OperatorPreheater } from "./ui/pages/operator-preheater.js";
import { OperatorCooler } from "./ui/pages/operator-cooler.js";
import { OperatorAiMnm } from "./ui/pages/ai-mnm.js";


import { initActions } from "./actions.js";
import { bootstrap } from "./inits/bootstrap.js";
import { applyRoleAccess } from "./auth.js"
/* ===============================
   ROOT
================================ */
const app = document.getElementById("app");

/* ===============================
   CLEANUP (IMPORTANT)
================================ */
function cleanup() {
   // remove global listeners if any
   window.onresize = null;
   document.onkeydown = null;
}

/* ===============================
   RENDER APP (🔥 CORE FUNCTION)
================================ */
export function renderApp() {
   cleanup();

   const auth = JSON.parse(localStorage.getItem("auth"));

   // clear everything
   app.innerHTML = "";

   /* ===============================
      NOT AUTHENTICATED → LOGIN
   ================================ */
   if (!auth?.isAuth) {
      app.appendChild(login());
      attachLoginHandler();
      return;
   }

   /* ===============================
      AUTHENTICATED → APP UI
   ================================ */
   // Header & Navbar
   app.appendChild(Header());
   app.appendChild(Navbar());

   // CREATE tabs-panel BEFORE APPENDING PAGES
   const main = document.createElement("main");
   main.id = "tabs-panel";
   main.className = "flex-1 min-h-0 p-4 overflow-hidden relative";

   app.appendChild(main);

   // Pages (ORDER IS IMPORTANT)
   main.appendChild(dashboard());
   main.appendChild(HybridControl());
   main.appendChild(Fingerprint());
   main.appendChild(NuralNetwork());
   main.appendChild(DigitalSimulator());
   main.appendChild(SoftSensor());
   main.appendChild(SoftSensorSimulator());
   main.appendChild(TrendAnalysis());
   main.appendChild(OperatorSummary());
   main.appendChild(OperatorKiln());
   main.appendChild(OperatorCooler());
   main.appendChild(OperatorPreheater());
   main.appendChild(OperatorAiMnm());
   main.appendChild(Configuration());

   initActions()
   bootstrap()
   applyRoleAccess();


}

/* ===============================
   INITIAL RENDER
================================ */
renderApp();

/* ===============================
   AUTH EVENTS (NO RELOAD)
================================ */
document.addEventListener("auth:login", renderApp);
document.addEventListener("auth:logout", renderApp);
