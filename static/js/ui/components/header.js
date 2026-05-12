export function Header() {
    const container = document.createElement("header");
    container.className = "glass-panel border-b-0 px-6 h-[60px] flex items-center justify-between z-20 shrink-0 shadow-md";
    container.id = "header"

    container.innerHTML = `

    <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
            <img src="/static/img/getsitelogo.png" style="height:40px; width:auto;">

        </div>
        <h1 id="app-title" class="text-lg font-bold text-whiteoff tracking-tight">Innomotics - AIPYRO</h1>
    </div>
    
    <div class="flex items-center gap-4 ml-auto">
   

  
</div>

    <div class="flex items-center space-x-6">
    
     
        <div id="original-header-controls" class="flex items-center space-x-4">
            <div class="flex items-center space-x-2 bg-custom/50 px-3 py-1.5 rounded-full border border-black/10">
                <div id="socket-status-dot" class="w-2 h-2 rounded-full bg-gray-400"></div>
                <span id="socket-status" class="text-xs font-mono font-bold text-whiteoff">CONNECTING...</span>
            </div>
        </div>
        <div id="safety-banner"
             class="hidden bg-red-600 text-white px-4 py-1 rounded shadow flex items-center gap-2 animate-pulse">
            <span class="font-bold font-mono text-xs">&#9888;&#65039; GUARDIAN INTERVENTION</span>
        </div>
        <div id="upset-banner"
             class="hidden bg-orange-500 text-white px-4 py-1 rounded shadow flex items-center gap-2 animate-pulse">
            <span class="font-bold font-mono text-xs">&#9888;&#65039; UPSET OVERRIDE</span>
            <span id="upset-banner-text" class="font-mono text-[10px] truncate max-w-[300px]"></span>
        </div>
        
       <!-- User badge -->
    <button class="flex items-center space-x-2 bg-custom/50 px-2 py-0 rounded-full border border-black/10" onclick="Actions.logout()"
>  
<!-- <span class="text-sm font-medium text-white flex">-->
<!--            Logout -->
<!--        </span>-->
        <span id="roleText" class="text-sm font-medium text-white">
            
        </span>
        <span class="text-sm font-medium text-white flex">
             <svg xmlns="http://www.w3.org" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 text-white">
  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
</svg>
        </span>
    </button
    </div>
   
  `;

    return container;
}
