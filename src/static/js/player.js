// static/js/player.js

// 1. Get Filename from URL
const urlParams = new URLSearchParams(window.location.search);
const filename = urlParams.get('video');

if (!filename) {
    alert("No video selected!");
    window.location.href = "/";
}

// 2. Load Video from Browser Database
const player = document.getElementById('main-player');

async function initPlayer() {
    try {
        const videoBlob = await loadVideoFromBrowser();

        if (videoBlob) {
            console.log("✅ Video loaded from Browser Cache");
            const blobUrl = URL.createObjectURL(videoBlob);
            player.src = blobUrl;
        } else {
            alert("Video cache expired or not found. Please upload again.");
            window.location.href = "/";
        }
    } catch (e) {
        console.error("Error loading video:", e);
        alert("Could not load video from browser storage.");
    }
}

// Start Initialization
initPlayer();

// 3. Ask Logic
const askBtn = document.getElementById('ask-btn');
const input = document.getElementById('query');
const historyList = document.getElementById('history-list');

askBtn.addEventListener('click', handleQuestion);
// Allow "Enter" key to submit
input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleQuestion();
});

async function handleQuestion() {
    const query = input.value.trim();
    if (!query) return;

    // UI Feedback
    askBtn.innerText = "...";
    askBtn.disabled = true;

    const formData = new FormData();
    formData.append('query', query);
    formData.append('filename', filename);

    try {
        const res = await fetch('/api/ask', { method: 'POST', body: formData });
        const data = await res.json();

        // Add to Sidebar
        addHistoryItem(query, data);

        // If answer found, play the segment
        if (data.found) {
            playSegment(data.start);
        }
    } catch (e) {
        console.error(e);
        alert("Error getting answer from AI.");
    } finally {
        input.value = "";
        askBtn.innerText = "Ask AI";
        askBtn.disabled = false;
    }
}

// 4. The Simplified Play Logic (Seek & Play Only)
async function playSegment(start) {
    // A. Parse Number securely
    const startTime = parseFloat(start);

    console.log(`🎬 Seeking to: ${startTime}s (Continuous Play)`);

    // B. Seek
    player.currentTime = startTime;

    // C. Play
    try {
        await player.play();
    } catch (e) {
        console.warn("Autoplay blocked. User interaction needed.");
    }
}

// 5. UI Helpers
function addHistoryItem(question, data) {
    const item = document.createElement('div');
    item.className = 'history-item';

    if (data.found) {
        item.classList.add('found');
        item.innerHTML = `
            <div class="time-badge">
                <i class="fas fa-clock"></i> ${formatTime(data.start)}
            </div>
            <div class="q-text">${question}</div>
            <div class="a-text">${data.answer}</div>
            <div class="replay-hint"><i class="fas fa-play"></i> Click to jump</div>
        `;
        item.onclick = () => playSegment(data.start);
    } else {
        item.classList.add('error');
        item.innerHTML = `
            <div class="q-text">${question}</div>
            <div class="a-text">❌ No matching scene found.</div>
        `;
    }
    // Add to top of list
    historyList.prepend(item);
}

function formatTime(s) {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec < 10 ? '0' : ''}${sec}`;
}