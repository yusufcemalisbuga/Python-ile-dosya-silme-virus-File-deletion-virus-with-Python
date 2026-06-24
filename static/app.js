/**
 * Real-Time AI Camera Analytics - Frontend Application
 * Handles WebSocket communication, video display, and analytics visualization
 */

let ws = null;
let pingInterval = null;
let isStreaming = false;
let frameCount = 0;
let lastFpsUpdate = Date.now();
let fpsFrames = 0;

// DOM Elements
const videoFeed = document.getElementById('videoFeed');
const placeholder = document.getElementById('placeholder');
const statusIndicator = document.getElementById('statusIndicator');
const fpsCounter = document.getElementById('fpsCounter');
const streamSelect = document.getElementById('streamSelect');
const customUrl = document.getElementById('customUrl');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const detectionLog = document.getElementById('detectionLog');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupStreamSelector();
    connectWebSocket();
});

function setupStreamSelector() {
    streamSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        const type = selectedOption.dataset.type;
        if (type === 'custom') {
            customUrl.classList.remove('hidden');
        } else {
            customUrl.classList.add('hidden');
        }
    });
}

function connectWebSocket() {
    if (pingInterval) {
        clearInterval(pingInterval);
        pingInterval = null;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        updateStatus('connected', 'Connected');
        addLog('WebSocket connected', 'info');
        pingInterval = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send('ping');
            }
        }, 30000);
    };

    ws.onmessage = (event) => {
        if (event.data === 'pong') return;

        try {
            const data = JSON.parse(event.data);
            if (data.type === 'frame') {
                handleFrame(data);
            }
        } catch (e) {
            console.error('Error parsing WebSocket message:', e);
        }
    };

    ws.onclose = () => {
        updateStatus('disconnected', 'Disconnected');
        addLog('WebSocket disconnected. Reconnecting...', 'warning');
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        addLog('Connection error', 'warning');
    };
}

function handleFrame(data) {
    // Update video feed
    if (data.frame) {
        videoFeed.src = `data:image/jpeg;base64,${data.frame}`;
        videoFeed.classList.remove('hidden');
        placeholder.style.display = 'none';
    }

    // Update FPS counter
    fpsFrames++;
    const now = Date.now();
    if (now - lastFpsUpdate >= 1000) {
        const fps = Math.round(fpsFrames * 1000 / (now - lastFpsUpdate));
        fpsCounter.textContent = `${fps} FPS`;
        fpsFrames = 0;
        lastFpsUpdate = now;
    }

    // Update detection counts
    updateDetectionCounts(data.frame_counts || {});

    // Update analytics
    if (data.analytics) {
        updateAnalytics(data.analytics);
    }

    // Update stream FPS
    if (data.stream_fps !== undefined) {
        document.getElementById('streamFps').textContent = data.stream_fps;
    }

    frameCount++;
}

function updateDetectionCounts(counts) {
    const mapping = {
        'person': 'countPerson',
        'car': 'countCar',
        'bus': 'countBus',
        'bicycle': 'countBicycle',
        'motorcycle': 'countMotorcycle',
        'truck': 'countTruck',
    };

    // Reset all to 0
    Object.values(mapping).forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '0';
    });

    // Update with current counts
    Object.entries(counts).forEach(([cls, count]) => {
        const elementId = mapping[cls];
        if (elementId) {
            const el = document.getElementById(elementId);
            if (el) {
                el.textContent = count;
                // Flash animation
                el.style.transform = 'scale(1.2)';
                setTimeout(() => { el.style.transform = 'scale(1)'; }, 200);
            }
        }
    });
}

function updateAnalytics(analytics) {
    const fields = {
        'totalDetections': analytics.total_detections || 0,
        'avgPerFrame': analytics.avg_per_frame || 0,
        'framesAnalyzed': analytics.frames_analyzed || 0,
        'activeTracks': analytics.active_tracks || 0,
    };

    Object.entries(fields).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    });
}

async function startStream() {
    const selectedOption = streamSelect.options[streamSelect.selectedIndex];
    const type = selectedOption.dataset.type;
    let url = selectedOption.value;

    if (type === 'custom') {
        url = customUrl.value.trim();
        if (!url) {
            addLog('Please enter a stream URL', 'warning');
            return;
        }
    }

    if (!url) {
        addLog('No stream URL selected', 'warning');
        return;
    }

    startBtn.disabled = true;
    addLog(`Connecting to stream...`, 'info');

    try {
        const response = await fetch('/api/stream/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, type }),
        });

        const result = await response.json();

        if (result.error) {
            addLog(`Error: ${result.error}`, 'warning');
            startBtn.disabled = false;
        } else {
            isStreaming = true;
            startBtn.disabled = true;
            stopBtn.disabled = false;
            addLog(`Stream started: ${selectedOption.text}`, 'detection');
            updateStatus('connected', 'Streaming');
        }
    } catch (e) {
        addLog(`Connection failed: ${e.message}`, 'warning');
        startBtn.disabled = false;
    }
}

async function stopStream() {
    try {
        await fetch('/api/stream/stop', { method: 'POST' });
    } catch (e) {
        console.error('Error stopping stream:', e);
    }

    isStreaming = false;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    videoFeed.classList.add('hidden');
    placeholder.style.display = 'flex';
    updateStatus('connected', 'Connected');
    addLog('Stream stopped', 'info');
}

function updateStatus(state, text) {
    statusIndicator.textContent = `● ${text}`;
    statusIndicator.className = `status-indicator ${state}`;
}

function updateConfidence(value) {
    document.getElementById('confidenceValue').textContent = `${value}%`;
    fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confidence: value / 100 }),
    }).catch(e => console.error('Failed to update confidence:', e));
}

function addLog(message, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry log-${type}`;
    const time = new Date().toLocaleTimeString();
    entry.textContent = `[${time}] ${message}`;

    detectionLog.insertBefore(entry, detectionLog.firstChild);

    // Keep only last 50 entries
    while (detectionLog.children.length > 50) {
        detectionLog.removeChild(detectionLog.lastChild);
    }
}
