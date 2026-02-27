// --- Configuration ---
const CONFIG = {
    BROKER: 'wss://33712c7cb7174024b63e809028448b03.s1.eu.hivemq.cloud:8884/mqtt',
    TOPIC_PREFIX: 'agribrain_shravan',
    USER: 'agribrain',
    PASS: '#Shs_2838'
};

const client = mqtt.connect(CONFIG.BROKER, {
    username: CONFIG.USER,
    password: CONFIG.PASS,
    clientId: 'AgriBrain_Dashboard_' + Math.random().toString(16).substring(2, 8)
});

console.log("Connecting to Agri-Brain HiveMQ...");

// --- DOM Elements ---
const gridContainer = document.getElementById('grid-container');
const mqttStatus = document.getElementById('mqtt-status');
const avgHumidityVal = document.getElementById('avg-humidity');
const humidityProgress = document.getElementById('humidity-progress');
const motorStateVal = document.getElementById('motor-state');
const healthStatusDot = document.getElementById('health-status-dot');
const healthVal = document.getElementById('health-val');
const gatewayStatus = document.getElementById('gateway-status');
const ledgerList = document.getElementById('ledger-list');
const micBtn = document.getElementById('mic-btn');
const autoToggle = document.getElementById('auto-irrigation-toggle');

// Gemini UI Elements
const chatBox = document.getElementById('chat-box');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

// Irrigation Modal Elements
const irrigationModal = document.getElementById('irrigation-modal');
const modalTitle = document.getElementById('modal-grid-title');
const timerInput = document.getElementById('irrigation-time');
const modalCancel = document.getElementById('modal-cancel');
const modalStart = document.getElementById('modal-start');

let selectedRegion = null;
let regionData = {};

// --- Initialization ---
// Create 4 Regions
for (let i = 1; i <= 4; i++) {
    const div = document.createElement('div');
    div.className = 'grid-item';
    div.id = `region-${i}`;
    div.innerHTML = `
        <span class="grid-number">${i}</span>
        <span class="grid-label">REGION ${i}</span>
        <div class="region-stats" style="font-size: 0.7rem; margin-top: 10px; opacity: 0.8;">
            H: <span id="reg-${i}-h">--</span>% | T: <span id="reg-${i}-t">--</span>°C
        </div>
    `;
    div.onclick = () => openIrrigationModal(i);
    gridContainer.appendChild(div);
}

// --- Control Logic ---
autoToggle.onchange = () => {
    const state = autoToggle.checked ? "ON" : "OFF";
    client.publish(`${CONFIG.TOPIC_PREFIX}/control/auto`, state);
    console.log(`Auto-Irrigation set to ${state}`);
};

function openIrrigationModal(id) {
    if (autoToggle.checked) {
        addChatMessage("Switch to MANUAL mode to override specific regions.", "ai");
        return;
    }
    selectedRegion = id;
    modalTitle.innerText = `IRRIGATE REGION ${id}`;
    irrigationModal.classList.add('active');
}

modalCancel.onclick = () => irrigationModal.classList.remove('active');

modalStart.onclick = () => {
    const time = timerInput.value;
    addChatMessage(`Irrigating Region ${selectedRegion} for ${time} minutes manually.`, 'user');
    client.publish(`${CONFIG.TOPIC_PREFIX}/control/region/${selectedRegion}`, "ON");
    irrigationModal.classList.remove('active');
};

// --- MQTT Handlers ---
client.on('connect', () => {
    mqttStatus.innerText = 'CONNECTED';
    mqttStatus.style.color = '#00ff88';

    // Subscribe to topics
    client.subscribe(`${CONFIG.TOPIC_PREFIX}/telemetry/region/+`);
    client.subscribe(`${CONFIG.TOPIC_PREFIX}/telemetry/motor`);
    client.subscribe(`${CONFIG.TOPIC_PREFIX}/ai/gemini/response`);
    client.subscribe(`${CONFIG.TOPIC_PREFIX}/system/heartbeat`);
});

client.on('message', (topic, payload) => {
    const pt = payload.toString().trim();
    try {
        if (topic.includes('telemetry/region/')) {
            const data = JSON.parse(pt);
            const id = data.region;
            regionData[id] = data;

            document.getElementById(`reg-${id}-h`).innerText = Math.round(data.humidity);
            document.getElementById(`reg-${id}-t`).innerText = Math.round(data.temp);

            const regionEl = document.getElementById(`region-${id}`);
            if (data.valve) regionEl.classList.add('active');
            else regionEl.classList.remove('active');

            // Update Average Humidity
            updateGlobalStats();
        }
        else if (topic.includes('telemetry/motor')) {
            const data = JSON.parse(pt);
            motorStateVal.innerText = data.state;
            healthVal.innerText = data.health;

            if (data.health === "OK") {
                healthStatusDot.classList.remove('fault');
                healthVal.style.color = "#00ff88";
            } else {
                healthStatusDot.classList.add('fault');
                healthVal.style.color = "#ff4444";
            }
        }
        else if (topic.includes('system/heartbeat')) {
            gatewayStatus.innerText = 'BRAIN ONLINE';
            gatewayStatus.style.color = '#00ff88';
        }
    } catch (e) { console.error("MQTT Error:", e); }
});

function updateGlobalStats() {
    const humidities = Object.values(regionData).map(d => d.humidity);
    if (humidities.length > 0) {
        const avg = humidities.reduce((a, b) => a + b, 0) / humidities.length;
        avgHumidityVal.innerText = Math.round(avg);
        humidityProgress.style.width = `${avg}%`;
    }
}

// --- Chat Interface ---
function addChatMessage(text, sender) {
    const msg = document.createElement('div');
    msg.className = `message ${sender}`;
    msg.innerText = text;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

sendBtn.onclick = () => {
    const text = chatInput.value.trim();
    if (text) {
        addChatMessage(text, 'user');
        client.publish(`${CONFIG.TOPIC_PREFIX}/voice_command`, text);
        chatInput.value = '';
    }
};

chatInput.onkeypress = (e) => { if (e.key === 'Enter') sendBtn.click(); };
