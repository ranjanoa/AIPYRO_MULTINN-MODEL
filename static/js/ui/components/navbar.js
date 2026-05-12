

export function Navbar() {
    const container = document.createElement("navbar");
    container.className = "glass-panel px-6 h-[45px] flex space-x-6 z-10 shrink-0 items-end overflow-x-auto";
    container.id = "navbar"

    container.innerHTML = `
<nav class="glass-panel px-6 h-[45px] flex space-x-6 z-10 shrink-0 items-end overflow-x-auto">
    <button onclick="Actions.switchTab('hybrid')" id="nav-hybrid"
            class="py-2.5 px-2 text-sm font-bold text-ai-cyan border-b-4 border-ai-cyan whitespace-nowrap">Hybrid
        Control
    </button>
    <button onclick="Actions.switchTab('fingerprint')" id="nav-fingerprint"
            class="py-2.5 px-2 text-sm  text-gray-500 hover:text-yellow-50 border-b-4 border-transparent whitespace-nowrap">
        Fingerprint Engine
    </button>
    <button onclick="Actions.switchTab('mbrl')" id="nav-mbrl"
            class="py-2.5 px-2 text-sm  text-gray-500 hover:text-yellow-50 border-b-4 border-transparent whitespace-nowrap">
        AI Neural Network
    </button>
    <button onclick="Actions.switchTab('simulator')" id="nav-simulator"
            class="py-2.5 px-2 text-sm  text-gray-500 hover:text-yellow-50 border-b-4 border-transparent whitespace-nowrap">
        Digital Simulator
    </button>
    <button onclick="Actions.switchTab('softsensor')" id="nav-softsensor"
            class="py-2.5 px-2 text-sm  text-gray-500 hover:text-yellow-50 border-b-4 border-transparent whitespace-nowrap">
        Soft Sensor (1hr)
    </button>
    <button onclick="Actions.switchTab('softsensor-sim')" id="nav-softsensor-sim"
            class="py-2.5 px-2 text-sm  text-gray-500 hover:text-yellow-50 border-b-4 border-transparent whitespace-nowrap">
        Soft Sensor Simulator
    </button>
    <button onclick="Actions.switchTab('trends')" id="nav-trends"
            class="py-2.5 px-2 text-sm  text-gray-500 hover:text-yellow-50 border-b-4 border-transparent whitespace-nowrap">
        Trend Analysis
    </button>
    <button onclick="Actions.switchTab('op-summary')" id="nav-op-summary"
            class="py-2.5 px-2 text-sm  text-gray-500 hover:text-yellow-50 border-b-4 border-transparent whitespace-nowrap">Operator
            Summary</button>
             <button onclick="Actions.switchTab('op-kiln')" id="nav-op-kiln"
            class="py-2.5 px-2 text-sm  text-gray-500 hover:text-yellow-50 border-b-4 border-transparent whitespace-nowrap">Kiln</button> 
    <button onclick="Actions.switchTab('op-preheater')" id="nav-op-preheater"
            class="py-2.5 px-2 text-sm  text-gray-500 hover:text-yellow-50 border-b-4 border-transparent whitespace-nowrap">Preheater</button>
            <button onclick="Actions.switchTab('op-cooler')" id="nav-op-cooler"
            class="py-2.5 px-2 text-sm  text-gray-500 hover:text-yellow-50 border-b-4 border-transparent whitespace-nowrap">Cooler</button>   
    <button onclick="Actions.switchTab('ai-mnm')" id="nav-ai-mnm"
            class="py-2.5 px-2 text-sm  text-gray-500 hover:text-yellow-50 border-b-4 border-transparent whitespace-nowrap">AI_MNM</button>
    <button onclick="Actions.switchTab('config')" id="nav-config"
            class="py-2.5 px-2 text-sm text-gray-500 hover:text-yellow-50 border-b-4 border-transparent whitespace-nowrap">
        Configuration
    </button>
    <!--     <button onclick="Actions.switchTab('account')" id="nav-account"-->
<!--            class="py-2.5 px-2 text-sm text-gray-500 hover:text-yellow-50 border-b-4 border-transparent whitespace-nowrap">-->
<!--        Account-->
<!--    </button>-->
</nav>
  `;



    // container.querySelectorAll(".tab-btn")
    //     .forEach(btn => {
    //         btn.addEventListener("click", () => {
    //             switchTab(btn.dataset.tab);
    //         });
    //     });

    return container;
}
