export function dashboard() {
    const container = document.createElement("div");
    container.className = "account-container hidden grid-cols-12 gap-4 h-full w-full transition-grid relative";
    container.id = "account"

    container.innerHTML = `

  <div class="glass-panel p-6 border-l-4 border-l-black shrink-0 flex justify-between items-center bg-white">
            <div> <span  class="text-sm font-medium text-white">
            LoggedIn As:
        </span> <h3 class="text-lg font-bold text-white" id="roleTextP"></h3></div>
            <button onclick="Actions.logout()"
                    class="text-yellow-600 border border-yellow px-6 py-2 rounded hover:bg-gray-100 text-sm font-bold">Logout</button>
        </div>
        <div class="flex-1 glass-panel flex flex-col min-h-0 bg-dark-green">
        </div>
  `;

    return container;
}
