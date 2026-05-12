import {MOCK_CONFIG} from "../inits/config.js";

export async function saveConfig() {
    await fetch(`${MOCK_CONFIG.API_URL}/api/config`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: document.getElementById('config-editor').value
    });
    location.reload();
    
}

