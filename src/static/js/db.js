// static/js/db.js
const DB_NAME = "VideoCacheDB";
const STORE_NAME = "videos";

// Open Database
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 1);
        request.onupgradeneeded = (e) => {
            e.target.result.createObjectStore(STORE_NAME);
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

// Save File
async function saveVideoToBrowser(filename, blob) {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).put(blob, "current_video"); // We only store one active video
    return new Promise((resolve) => {
        tx.oncomplete = () => resolve();
    });
}

// Load File
async function loadVideoFromBrowser() {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readonly");
    const request = tx.objectStore(STORE_NAME).get("current_video");
    return new Promise((resolve) => {
        request.onsuccess = () => resolve(request.result);
    });
}