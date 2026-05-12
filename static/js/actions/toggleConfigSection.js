
export function toggleConfigSection(sectionId, btnId) {
    const content = document.getElementById(sectionId);
    const btn = document.getElementById(btnId);
    
    if (!content || !btn) return;

    const isHidden = content.classList.contains('hidden');
    
    if (isHidden) {
        content.classList.remove('hidden');
        btn.innerHTML = '▲'; // Up arrow when visible
    } else {
        content.classList.add('hidden');
        btn.innerHTML = '▼'; // Down arrow when hidden
    }
}
