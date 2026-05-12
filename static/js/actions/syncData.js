import {MOCK_CONFIG} from "../inits/config.js";

export async function syncData() {
    fetch(`${MOCK_CONFIG.API_URL}/api/history/sync`, {method: 'POST'});
    alert("Sync Started");

    
}