
export async function toggleConfigView() {
    const isDev = document.getElementById('config-ui-toggle').checked;
    document.getElementById('config-table-view').classList.toggle('hidden', isDev);
    document.getElementById('config-json-view').classList.toggle('hidden', !isDev);
}

