/* ═══════════════════════════════════════════════════════════
   AGRI-BRAIN  app.js  — Farming Theme Edition
   All bugs fixed + farming UI: crop icons, clock, stars,
   rain particles, soil bars, water estimate, per-region data
   ═══════════════════════════════════════════════════════════ */

// ── CROP CONFIG per region ────────────────────────────────
const CROPS = {
    1: { svgId: 'icon-wheat', name: 'Wheat', color: 'var(--gold)', growSpeed: '3.8s' },
    2: { svgId: 'icon-corn', name: 'Corn', color: 'var(--amber)', growSpeed: '4.2s' },
    3: { svgId: 'icon-tomato', name: 'Tomato', color: 'var(--tomato)', growSpeed: '3.5s' },
    4: { svgId: 'icon-sunflower', name: 'Sunflower', color: 'var(--gold)', growSpeed: '4.6s' },
};

function cropSVG(regionId, w, h) {
    const c = CROPS[regionId];
    return `<svg viewBox="0 0 70 90" width="${w}" height="${h}" style="overflow:visible"><use href="#${c.svgId}" style="color:${c.color}"/></svg>`;
}

// ── CONFIG ────────────────────────────────────────────────
const CONFIG = {
    BROKER: 'wss://33712c7cb7174024b63e809028448b03.s1.eu.hivemq.cloud:8884/mqtt',
    TOPIC_PREFIX: 'agribrain_shravan',
    USER: 'agribrain',
    PASS: '#Shs_2838'
};

// ── MQTT ──────────────────────────────────────────────────
const client = mqtt.connect(CONFIG.BROKER, {
    username: CONFIG.USER,
    password: CONFIG.PASS,
    clientId: 'AgriBrain_Farm_' + Math.random().toString(16).slice(2, 8),
    reconnectPeriod: 4000,
    keepalive: 30
});

// ── STATE ─────────────────────────────────────────────────
let selectedRegion = null;
let regionData = {};
let irrigatingTimers = {};
let ledgerCount = 0;
let isListening = false;
let rainDrops = [];

// ── DOM SHORTCUTS ─────────────────────────────────────────
const $ = id => document.getElementById(id);

// ── GENERATE STARFIELD ────────────────────────────────────
function buildStars() {
    const layer = $('stars-layer');
    if (!layer) return;
    const count = 120;
    for (let i = 0; i < count; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        const size = Math.random() * 2.5 + 0.5;
        const dur = (Math.random() * 4 + 2).toFixed(1) + 's';
        const delay = (Math.random() * 5).toFixed(1) + 's';
        const op = (Math.random() * 0.5 + 0.2).toFixed(2);
        star.style.cssText = `
            width:${size}px; height:${size}px;
            left:${Math.random() * 100}%;
            top:${Math.random() * 55}%;
            --dur:${dur}; --op:${op};
            animation-delay:${delay};
        `;
        layer.appendChild(star);
    }
}

// ── BUILD HERO CROP ROW (SVG plants) ──────────────────────────────
function buildHeroCrops() {
    const row = $('hero-crops-row');
    if (!row) return;
    [1, 2, 1, 3, 1, 4, 1, 2, 1, 3, 1, 4].forEach((rid, i) => {
        const span = document.createElement('span');
        span.className = `hc hc${i + 1}`;
        span.innerHTML = cropSVG(rid, 28, 36);
        row.appendChild(span);
    });
}

// ── RAIN PARTICLES ────────────────────────────────────────
function buildRain() {
    const container = $('particles');
    if (!container) return;
    for (let i = 0; i < 50; i++) {
        const drop = document.createElement('div');
        drop.className = 'rain-drop';
        const speed = (Math.random() * 0.6 + 0.5).toFixed(2) + 's';
        const delay = (Math.random() * 1.5).toFixed(2) + 's';
        drop.style.cssText = `
            left: ${Math.random() * 100}%;
            --speed: ${speed};
            animation-delay: ${delay};
            height: ${Math.random() * 14 + 8}px;
        `;
        container.appendChild(drop);
        rainDrops.push(drop);
    }
}

function setRain(on) {
    rainDrops.forEach(d => d.classList.toggle('active', on));
}

// ── LIVE CLOCK ────────────────────────────────────────────
function updateClock() {
    const now = new Date();
    const timeEl = $('clock-time');
    const dateEl = $('clock-date');
    if (timeEl) timeEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    if (dateEl) dateEl.textContent = now.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' }).toUpperCase();
}

// ── BUILD REGION CARDS ────────────────────────────────────
function buildRegionCards() {
    const container = $('grid-container');
    if (!container) return;
    for (let i = 1; i <= 4; i++) {
        const crop = CROPS[i];
        const card = document.createElement('div');
        card.className = 'grid-item';
        card.id = `region-${i}`;
        card.innerHTML = `
            <div class="water-ripple"><div class="water-wave"></div></div>
            <div class="region-timer" id="timer-${i}">00:00</div>
            <div class="grid-header">
                <span class="region-num">ZONE ${i}</span>
                <span class="region-status-badge" id="badge-${i}">IDLE</span>
            </div>
            <div class="crop-icon-hero">
                <span class="ci-name" style="color:${crop.color}">${crop.name}</span>
                <span class="ci-svg" style="--sg:${crop.growSpeed}" id="crop-${i}">${cropSVG(i, 40, 50)}</span>
            </div>
            <div class="region-soil-bar">
                <div class="region-soil-fill" id="soil-fill-${i}" style="width:0%"></div>
            </div>
            <div class="region-stats-row">
                <div class="rstat">
                    <span class="rstat-label">HUMIDITY</span>
                    <span class="rstat-val humid-val" id="reg-${i}-h">--%</span>
                </div>
                <div class="rstat">
                    <span class="rstat-label">TEMP</span>
                    <span class="rstat-val temp-val" id="reg-${i}-t">--°C</span>
                </div>
                <div class="rstat">
                    <span class="rstat-label">CROP</span>
                    <span class="rstat-val" style="font-size:.72rem;color:var(--text-dim)">${crop.name}</span>
                </div>
            </div>
            <div class="irrigate-cta">💧 TAP TO IRRIGATE</div>
        `;
        card.addEventListener('click', () => openIrrigationModal(i));
        container.appendChild(card);
    }
}

// ── AUTO TOGGLE ───────────────────────────────────────────
const autoToggle = $('auto-irrigation-toggle');
autoToggle.checked = false;
syncModeUI(false);

autoToggle.addEventListener('change', () => {
    const on = autoToggle.checked;
    publishAutoMode(on);
    syncModeUI(on);
    addChatMsg(on ? '🔁 Switched to AUTO irrigation mode.' : '🖐 Switched to MANUAL mode. Click a field zone to irrigate.', 'sys');
});

function publishAutoMode(on) {
    client.publish(`${CONFIG.TOPIC_PREFIX}/control/auto`, on ? 'ON' : 'OFF', { retain: true, qos: 1 });
}

function syncModeUI(auto) {
    const mi = $('mode-indicator');
    const off = $('toggle-label-off');
    const on = $('toggle-label-on');
    if (mi) mi.textContent = auto ? 'AUTO' : 'MANUAL';
    if (off) off.classList.toggle('active', !auto);
    if (on) on.classList.toggle('active', auto);
}

// ── MODAL ─────────────────────────────────────────────────
function openIrrigationModal(id) {
    if (autoToggle.checked) {
        addChatMsg('⚠️ Switch to MANUAL mode first to irrigate a specific field zone.', 'sys');
        return;
    }
    selectedRegion = id;
    const crop = CROPS[id];
    const modalIcon = $('modal-crop-icon');
    const modalBadge = $('modal-region-badge');
    const modalTitle = $('modal-grid-title');
    if (modalIcon) modalIcon.textContent = crop.icon;
    if (modalBadge) modalBadge.textContent = `R${id}`;
    if (modalTitle) modalTitle.textContent = `IRRIGATE REGION ${id} — ${crop.name.toUpperCase()}`;

    const timeInput = $('irrigation-time');
    if (timeInput) { timeInput.value = 10; updateWaterEstimate(10); }

    document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('selected'));
    $('irrigation-modal').classList.add('active');
}

$('modal-cancel').addEventListener('click', () => $('irrigation-modal').classList.remove('active'));

$('irrigation-time').addEventListener('input', e => updateWaterEstimate(parseInt(e.target.value) || 1));

function updateWaterEstimate(mins) {
    const el = $('water-estimate');
    if (el) el.textContent = `~${(mins * 5).toFixed(0)}L estimated`;    // 5L/min rough estimate
}

document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const val = parseInt(btn.dataset.val);
        $('irrigation-time').value = val;
        updateWaterEstimate(val);
        document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
    });
});

$('modal-start').addEventListener('click', () => {
    const duration = parseInt($('irrigation-time').value) || 1;
    const region = selectedRegion;
    $('irrigation-modal').classList.remove('active');

    addChatMsg(`💧 Irrigating Zone ${region} (${CROPS[region].name}) for ${duration} min.`, 'user');
    client.publish(`${CONFIG.TOPIC_PREFIX}/control/manual`,
        JSON.stringify({ region, duration }), { qos: 1 });

    startCountdown(region, duration);
});

// ── COUNTDOWN TIMER ───────────────────────────────────────
function startCountdown(regionId, durationMin) {
    if (irrigatingTimers[regionId]) clearInterval(irrigatingTimers[regionId].id);

    const endMs = Date.now() + durationMin * 60000;
    const card = $(`region-${regionId}`);
    const timerEl = $(`timer-${regionId}`);
    const badgeEl = $(`badge-${regionId}`);
    const soilEl = $(`soil-fill-${regionId}`);

    if (card) card.classList.add('irrigating');
    if (badgeEl) badgeEl.textContent = 'IRRIGATING';

    setRain(true);
    updateActiveBar();

    const id = setInterval(() => {
        const rem = endMs - Date.now();
        if (rem <= 0) {
            clearInterval(id);
            delete irrigatingTimers[regionId];

            if (card) { card.classList.remove('irrigating'); card.classList.remove('active'); }
            if (timerEl) timerEl.textContent = '00:00';
            if (badgeEl) badgeEl.textContent = 'IDLE';

            const anyLeft = Object.keys(irrigatingTimers).length > 0;
            setRain(anyLeft);
            updateActiveBar();
            addChatMsg(`✅ Zone ${regionId} (${CROPS[regionId].name}) irrigation complete.`, 'sys');
            return;
        }
        const m = Math.floor(rem / 60000);
        const s = Math.floor((rem % 60000) / 1000);
        if (timerEl) timerEl.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

        // Animate soil bar filling up
        if (soilEl) {
            const pct = Math.min(100, 100 - (rem / (durationMin * 60000)) * 100);
            soilEl.style.width = `${Math.round(40 + pct * 0.6)}%`;  // goes from 40% → 100% while irrigating
        }
        updateActiveBar();
    }, 1000);

    irrigatingTimers[regionId] = { id, endMs };
}

function updateActiveBar() {
    const bar = $('active-bar');
    const barText = $('active-bar-text');
    const active = Object.keys(irrigatingTimers);
    if (!bar) return;

    if (active.length === 0) { bar.style.display = 'none'; return; }
    bar.style.display = 'flex';

    const parts = active.map(rid => {
        const rem = irrigatingTimers[rid].endMs - Date.now();
        if (rem <= 0) return null;
        const m = Math.floor(rem / 60000), s = Math.floor((rem % 60000) / 1000);
        return `Zone ${rid} (${CROPS[rid].name}): ${m}m ${String(s).padStart(2, '0')}s`;
    }).filter(Boolean);

    if (barText) barText.textContent = parts.join('   |   ');
}

// ── MQTT ──────────────────────────────────────────────────
client.on('connect', () => {
    setPill($('mqtt-pill'), $('mqtt-status'), 'CONNECTED', true);
    const p = CONFIG.TOPIC_PREFIX;
    client.subscribe(`${p}/telemetry/region/+`);
    client.subscribe(`${p}/telemetry/motor`);
    client.subscribe(`${p}/ai/gemini/response`);
    client.subscribe(`${p}/voice_feedback`);
    client.subscribe(`${p}/ledger/update`);
    client.subscribe(`${p}/system/heartbeat`);
    publishAutoMode(false);   // start in MANUAL
});
client.on('reconnect', () => setPill($('mqtt-pill'), $('mqtt-status'), 'CONNECTING…', false));
client.on('offline', () => setPill($('mqtt-pill'), $('mqtt-status'), 'OFFLINE', false));

client.on('message', (topic, payload) => {
    const pt = payload.toString().trim();
    try {
        if (topic.includes('telemetry/region/')) {
            const d = JSON.parse(pt);
            const id = d.region;
            regionData[id] = d;

            const h = isNaN(d.humidity) ? null : Math.round(d.humidity);
            const t = isNaN(d.temp) ? null : Math.round(d.temp);

            const hEl = $(`reg-${id}-h`);
            const tEl = $(`reg-${id}-t`);
            if (hEl) hEl.textContent = h !== null ? `${h}%` : '--%';
            if (tEl) tEl.textContent = t !== null ? `${t}°C` : '--°C';

            // Soil fill bar (only if not actively irrigating)
            if (!irrigatingTimers[id]) {
                const sfEl = $(`soil-fill-${id}`);
                if (sfEl && h !== null) {
                    sfEl.style.width = `${Math.min(h, 100)}%`;
                    sfEl.classList.toggle('dry', h < 30);
                }
            }

            const card = $(`region-${id}`);
            const badge = $(`badge-${id}`);
            if (card && !irrigatingTimers[id]) {
                card.classList.toggle('active', !!d.valve);
                if (badge) badge.textContent = d.valve ? 'VALVE OPEN' : 'IDLE';
            }
            updateGlobalStats();
        }

        else if (topic.includes('telemetry/motor')) {
            const d = JSON.parse(pt);
            const motorEl = $('motor-state');
            if (motorEl) motorEl.textContent = d.state || '--';

            const psi = d.pressure_psi !== undefined ? d.pressure_psi : null;
            const stage = d.stage || 'UNKNOWN';
            const hvEl = $('health-val');
            const hdot = $('health-status-dot');

            if (psi !== null && hvEl) {
                hvEl.textContent = `${psi} PSI`;
                const fault = psi <= 20;
                if (hdot) hdot.classList.toggle('fault', fault);
                hvEl.style.color = fault ? 'var(--danger)' : 'var(--green-neon)';
            }
            const mi = $('motor-info');
            if (mi) mi.textContent = `STAGE: ${stage}`;
        }
        else if (topic.includes('voice_feedback') || topic.includes('ai/gemini/response')) {
            removeTyping();

            let ptStr = pt.trim();
            // Handle plain string fallback
            if (ptStr.startsWith('"') && ptStr.endsWith('"')) {
                ptStr = ptStr.substring(1, ptStr.length - 1);
            }

            try {
                const d = JSON.parse(ptStr);
                const msg = d.response || d.message || d.text || ptStr;
                addChatMsg(msg, 'ai');
            } catch (e) {
                // If JSON.parse fails, it might just be a raw string
                addChatMsg(ptStr, 'ai');
            }
        }

        else if (topic.includes('ledger/update')) {
            addLedgerEntry(JSON.parse(pt));
        }

        else if (topic.includes('system/heartbeat')) {
            setPill($('gateway-pill'), $('gateway-status'), 'ONLINE', true);
            clearTimeout(window._hbTimer);
            window._hbTimer = setTimeout(() => setPill($('gateway-pill'), $('gateway-status'), 'OFFLINE', false), 10000);
            // Update weather badge randomly based on heartbeat
            const weathers = [
                ['☀️', 'Clear Sky'], ['⛅', 'Partly Cloudy'], ['🌤️', 'Mostly Clear'],
                ['💨', 'Windy'], ['🌙', 'Clear Night'], ['⭐', 'Starlit Sky']
            ];
            const w = weathers[Math.floor(Math.random() * weathers.length)];
            const wb = $('weather-badge');
            const wt = $('weather-text');
            if (wb) wb.firstElementChild.textContent = w[0];
            if (wt) wt.textContent = w[1];
        }

    } catch (e) {
        console.warn('MQTT parse error:', topic, e.message);
    }
});

// ── GLOBAL STATS ──────────────────────────────────────────
function updateGlobalStats() {
    const vals = Object.values(regionData);
    if (!vals.length) return;

    const hs = vals.map(d => d.humidity).filter(v => !isNaN(v));
    if (hs.length) {
        const avg = hs.reduce((a, b) => a + b, 0) / hs.length;
        const ahEl = $('avg-humidity'), hpEl = $('humidity-progress');
        if (ahEl) ahEl.textContent = Math.round(avg);
        if (hpEl) hpEl.style.width = `${Math.min(avg, 100)}%`;
    }

    const ts = vals.map(d => d.temp).filter(v => !isNaN(v));
    if (ts.length) {
        const avg = ts.reduce((a, b) => a + b, 0) / ts.length;
        const atEl = $('avg-temp'), tpEl = $('temp-progress');
        if (atEl) atEl.textContent = Math.round(avg);
        if (tpEl) tpEl.style.width = `${Math.min((avg / 50) * 100, 100)}%`;
    }
}

// ── CHAT ──────────────────────────────────────────────────
function addChatMsg(text, sender) {
    const box = $('chat-box');
    if (!box) return;

    const wrap = document.createElement('div');
    wrap.className = `msg ${sender}`;

    if (sender === 'ai') {
        wrap.innerHTML = `<div class="ai-avatar">🌿</div><div class="msg-bubble">${text}</div>`;
    } else {
        const bubble = document.createElement('div');
        bubble.className = 'msg-bubble';
        bubble.textContent = text;
        wrap.appendChild(bubble);
    }

    box.appendChild(wrap);
    box.scrollTop = box.scrollHeight;
}

function showTyping() {
    const box = $('chat-box');
    if (!box) return;
    const wrap = document.createElement('div');
    wrap.className = 'msg ai typing-indicator';
    wrap.id = 'typing-ind';
    wrap.innerHTML = `<div class="ai-avatar">${AI_AVATAR_SVG}</div><div class="msg-bubble"><span class="tdot"></span><span class="tdot"></span><span class="tdot"></span></div>`;
    box.appendChild(wrap);
    box.scrollTop = box.scrollHeight;
}

function removeTyping() {
    const el = $('typing-ind');
    if (el) el.remove();
}

// ── SEND TO BRAIN ─────────────────────────────────────────
function sendChat() {
    const input = $('chat-input');
    const text = input?.value.trim();
    if (!text) return;
    addChatMsg(text, 'user');
    input.value = '';
    showTyping();
    client.publish(`${CONFIG.TOPIC_PREFIX}/voice_command`, text, { qos: 1 });
}

$('send-btn').addEventListener('click', sendChat);
$('chat-input').addEventListener('keypress', e => { if (e.key === 'Enter') sendChat(); });

// ── MIC (Web Speech API) ──────────────────────────────────
const Recog = window.SpeechRecognition || window.webkitSpeechRecognition;
const micBtn = $('mic-btn');
const micIcon = $('mic-icon');

if (Recog) {
    const recognition = new Recog();
    recognition.lang = 'en-IN';
    recognition.interimResults = false;

    recognition.onresult = e => {
        $('chat-input').value = e.results[0][0].transcript;
        sendChat();
    };
    recognition.onstart = () => { isListening = true; micBtn.classList.add('listening'); micIcon.textContent = '🔴'; };
    recognition.onend = () => { isListening = false; micBtn.classList.remove('listening'); micIcon.textContent = '🎤'; };
    recognition.onerror = () => recognition.onend();

    micBtn.addEventListener('click', () => isListening ? recognition.stop() : recognition.start());
} else {
    micBtn.style.opacity = '0.5';
    micBtn.addEventListener('click', () => addChatMsg('⚠️ Voice input needs Chrome or Edge browser.', 'sys'));
}

// ── LEDGER ────────────────────────────────────────────────
function addLedgerEntry(data) {
    const list = $('ledger-list');
    if (!list) return;
    const placeholder = list.querySelector('.ledger-empty');
    if (placeholder) placeholder.remove();

    const item = document.createElement('div');
    item.className = 'ledger-item';
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const action = (data.action || 'LOG').toUpperCase();
    const raw = data.raw || data.material || 'Command logged';

    item.innerHTML = `
        <span class="ledger-action">${action}</span>
        <span class="ledger-text">${raw}</span>
        <span class="ledger-time">${now}</span>
    `;
    list.insertBefore(item, list.firstChild);
    ledgerCount++;
    const countEl = $('ledger-count');
    if (countEl) countEl.textContent = `${ledgerCount} entr${ledgerCount === 1 ? 'y' : 'ies'}`;
}

// ── STATUS PILL HELPER ────────────────────────────────────
function setPill(pillEl, valEl, text, online) {
    if (valEl) valEl.textContent = text;
    if (pillEl) {
        pillEl.classList.toggle('connected', online);
        pillEl.classList.toggle('offline', !online);
    }
}

// ── MODAL RAIN DROPS ──────────────────────────────────────
function buildModalRain() {
    const rainEl = document.querySelector('.modal-rain');
    if (!rainEl) return;
    // Pure CSS rain via background-position animation (already in CSS)
}

// ── INIT ─────────────────────────────────────────────────
buildStars();
buildRain();
buildRegionCards();
buildModalRain();
updateClock();
setInterval(updateClock, 1000);
