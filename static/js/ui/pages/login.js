export function login() {
    const container = document.createElement("div");
    container.className = "login-container w-full max-w-md bg-gray-900/95 backdrop-blur-xl border border-gray-700/50 rounded-3xl shadow-2xl p-10 flex flex-col items-center space-y-8";
    container.id = "login"

    container.innerHTML = `
        <!-- Form -->
        <form class="w-full space-y-6" id="loginForm" novalidate>
         <div class="flex flex-col items-center">
                <span class="text-innoyellow text-2xl font-bold text-white tracking-tight">
                            <img src="/static/img/getsitelogo.png"">
</span>
            </div>
            <!-- Username Field -->
            <div class="fields">
                <label for="email" class="block text-sm font-semibold text-gray-300 mb-2">Email</label>
                <input 
                    type="text" 
                    id="email" 
                    name="username" 
                    class="w-full px-5 py-4 bg-gray-800/50 border border-gray-600 rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-innoyellow focus:border-transparent transition-all duration-300 text-lg shadow-inner" 
                    placeholder="Enter Email"
                    required
                >
                                <p class="error text-red-400 text-sm mt-1"></p>

            </div>

            <!-- Password Field -->
            <div class="fields">
                <label for="password" class="block text-sm font-semibold text-gray-300 mb-2">Password</label>
                <input 
                    type="password" 
                    id="password" 
                    name="password" 
                    class="w-full px-5 py-4 bg-gray-800/50 border border-gray-600 rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-innoyellow focus:border-transparent transition-all duration-300 text-lg shadow-inner" 
                    placeholder="Enter Password"
                    required
                >
                                <p class="error text-red-400 text-sm mt-1"></p>

            </div>

            <!-- Login Button -->
            <button 
                type="submit" 
                class="w-full bg-gradient-to-r from-innoyellow to-yellow-400 hover:from-yellow-400 hover:to-innoyellow text-black font-bold py-5 px-6 rounded-2xl text-lg shadow-xl hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 uppercase tracking-wide"
            >
                Login
            </button>
        </form>

`;

    return container;
}
