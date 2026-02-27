let client = null;
const TOPIC_PREFIX = "agribrain_shravan";
let gridData = {};
let autoDriftInterval = null;

// DOM Elements
const loginOverlay = document.getElementById('login-overlay');
const mainContent = document.getElementById('main-content');
const mqttUrlInput = document.getElementById('mqtt-url');
const mqttUserInput = document.getElementById('mqtt-user');
const mqttPassInput = document.getElementById('mqtt-pass');
const connectBtn = document.getElementById('connect-btn');
const gridContainer = document.querySelector('.overview-grid');
const logContainer = document.getElementById('mqtt-log');
const voiceInput = document.getElementById('voice-input');
const sendVoiceBtn = document.getElementById('send-voice-btn');
const toggleAutoBtn = document.getElementById('toggle-auto');
const motorFailureBtn = document.getElementById('motor-failure-btn');

// Initialize 4 Grids
function initGrids() {
    gridContainer.innerHTML = '';
    for (let i = 1; i <= 4; i++) {
        gridData[i] = { moisture: 50, ph: 6.5, valve: false };
        const card = document.createElement('div');
        card.className = 'glass-card grid-card';
        card.id = `grid-${i}`;
        card.innerHTML = `
            <div class="grid-header">
                <h3>Grid ${i}</h3>
                <div class="valve-status" id="valve-${i}"></div>
            </div>
            <div class="stat-row">
                <div class="stat-label">
                    <span>Moisture</span>
                    <span class="moisture-val" id="moist-val-${i}">50%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="moist-fill-${i}" style="width: 50%"></div>
                </div>
                <input type="range" class="slider-input" min="0" max="100" value="50" oninput="updateGrid(${i}, this.value)">
            </div>
        `;
        gridContainer.appendChild(card);
    }
}

function updatePressure(val) {
    if (!client) return;
    const topic = `${TOPIC_PREFIX}/telemetry/motor`;
    const payload = {
        peak_freq: 60,
        rms_amplitude: 0.5,
        vibrations: 1.2,
        pressure: parseFloat(val)
    };
    client.publish(topic, JSON.stringify(payload));
    addLog('motor', `Pressure: ${val} PSI`);
}

function updateGrid(id, moisture) {
    gridData[id].moisture = parseFloat(moisture);
    const valEl = document.getElementById(`moist-val-${id}`);
    const fillEl = document.getElementById(`moist-fill-${id}`);
    if (valEl) valEl.innerText = `${moisture}%`;
    if (fillEl) fillEl.style.width = `${moisture}%`;

    if (client) {
        const topic = `${TOPIC_PREFIX}/telemetry/grid/${id}`;
        const payload = {
            grid: id,
            moisture: parseFloat(moisture),
            ph: gridData[id].ph
        };
        client.publish(topic, JSON.stringify(payload));
        addLog(topic, JSON.stringify(payload));
    }
}

function addLog(topic, msg) {
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `<span class="log-topic">${topic.split('/').pop()}</span>: <span class="log-msg">${msg}</span>`;
    logContainer.prepend(entry);
    if (logContainer.childNodes.length > 50) logContainer.removeChild(logContainer.lastChild);
}

connectBtn.onclick = () => {
    const host = mqttUrlInput.value;
    const username = mqttUserInput.value || "agribrain";
    const password = mqttPassInput.value || "#Shs_2838";

    connectBtn.innerText = "Connecting...";

    const options = {
        protocol: 'wss',
        username: username,
        password: password,
        clientId: 'AgriWebSim_' + Math.random().toString(16).substr(2, 8)
    };

    client = mqtt.connect(`wss://${host}:8884/mqtt`, options);

    client.on('connect', () => {
        loginOverlay.classList.add('hidden');
        mainContent.classList.remove('hidden');
        client.subscribe(`${TOPIC_PREFIX}/control/#`);
        client.subscribe(`${TOPIC_PREFIX}/ledger/update`);
        client.subscribe(`${TOPIC_PREFIX}/ai/gemini/response`);
        console.log("Connected to HiveMQ Cloud");
    });

    client.on('message', (topic, message) => {
        const msg = message.toString();
        addLog(topic, msg);

        if (topic.includes('control/grid/')) {
            const gridId = topic.split('/').pop();
            const status = msg === "ON";
            if (gridId === "all") {
                for (let i = 1; i <= 4; i++) setValve(i, status);
            } else {
                setValve(parseInt(gridId), status);
            }
        }
    });

    client.on('error', (err) => {
        alert("MQTT Error: " + err.message);
        connectBtn.innerText = "Initialize Brain";
    });
};

function setValve(id, status) {
    if (gridData[id]) {
        gridData[id].valve = status;
        const led = document.getElementById(`valve-${id}`);
        if (led) {
            if (status) led.classList.add('on');
            else led.classList.remove('on');
        }
    }
}

sendVoiceBtn.onclick = () => {
    const cmd = voiceInput.value;
    if (cmd && client) {
        client.publish(`${TOPIC_PREFIX}/voice_command`, cmd);
        addLog('voice_command', cmd);
        voiceInput.value = '';
    }
};

toggleAutoBtn.onclick = () => {
    if (autoDriftInterval) {
        clearInterval(autoDriftInterval);
        autoDriftInterval = null;
        toggleAutoBtn.innerText = "Toggle Auto-Drift";
    } else {
        autoDriftInterval = setInterval(() => {
            for (let i = 1; i <= 4; i++) {
                let current = gridData[i].moisture;
                let delta = (Math.random() - 0.5) * 5;
                let newVal = Math.min(100, Math.max(0, current + delta));
                updateGrid(i, newVal.toFixed(1));
            }
        }, 5000);
        toggleAutoBtn.innerText = "Auto-Drift ON";
    }
};

initGrids();
