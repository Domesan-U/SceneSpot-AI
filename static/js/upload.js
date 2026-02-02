document.getElementById('file-input').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    // Show Loader
    document.getElementById('drop-zone').classList.add('hidden');
    document.getElementById('loader').classList.remove('hidden');

    // 1. SAVE TO BROWSER DB (The Magic Step)
    await saveVideoToBrowser(file.name, file);

    // 2. Upload to Backend (For Indexing Only)
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.status === "success") {
            // Redirect
            window.location.href = `/player?video=${encodeURIComponent(data.filename)}`;
        }
    } catch (err) {
        alert("Upload Failed");
        location.reload();
    }
});