import sys
import io
# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import paho.mqtt.client as mqtt
import json
import time
import random
import threading
from acoustic_brain import AcousticBrain
from nlp_brain import NLPBrain
from ledger_manager import LedgerManager
from vision_brain import VisionBrain
from soil_brain import SoilBrain
from gemini_bridge import AgriGeminiBridge

# ── Configuration ──────────────────────────────────────────
MQTT_BROKER  = "33712c7cb7174024b63e809028448b03.s1.eu.hivemq.cloud"
MQTT_PORT    = 8883
MQTT_USER    = "agribrain"
MQTT_PASS    = "#Shs_2838"
TOPIC_PREFIX = "agribrain_shravan"

# ── AI Engines ─────────────────────────────────────────────
motor_brain    = AcousticBrain()
nlp_brain      = NLPBrain()
ledger         = LedgerManager()
vision_brain   = VisionBrain()
soil_brain     = SoilBrain()
gemini_bridge  = AgriGeminiBridge()

# ── Irrigation State ───────────────────────────────────────
irrigation_queue    = []   # Each item is ALWAYS a dict: {"id": int, "duration": float(min)}
active_grid         = None # Same dict format as above
last_irrigation_start = 0
MAX_VALVE_TIME      = 10   # minutes, used when no explicit duration given

# ── Irrigation Queue Lock (thread safety) ──────────────────
q_lock = threading.Lock()

# ──────────────────────────────────────────────────────────
def make_job(grid_id, duration_min=None):
    """Always create jobs as a dict with consistent keys."""
    return {"id": int(grid_id), "duration": float(duration_min or MAX_VALVE_TIME)}

def job_id(job):
    return job["id"] if isinstance(job, dict) else int(job)

def job_dur(job):
    return job.get("duration", MAX_VALVE_TIME) if isinstance(job, dict) else MAX_VALVE_TIME

# ──────────────────────────────────────────────────────────
def check_weather_prediction():
    """Simulates checking a Weather API (20% rain chance)."""
    return random.random() < 0.2

# ── MQTT Callbacks ─────────────────────────────────────────
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[BRAIN] Connected to HiveMQ Cloud.")
        client.subscribe(f"{TOPIC_PREFIX}/#")
        print(f"[BRAIN] Subscribed: {TOPIC_PREFIX}/#")
    else:
        print(f"[BRAIN] Connection FAILED rc={rc}")

# ──────────────────────────────────────────────────────────
def process_sequential_irrigation(client):
    """Drive the irrigation queue: stop finished jobs, start next."""
    global active_grid, last_irrigation_start
    now = time.time()

    with q_lock:
        # 1. Check if active job is done
        if active_grid is not None:
            duration_sec = job_dur(active_grid) * 60
            if now - last_irrigation_start >= duration_sec:
                gid = job_id(active_grid)
                print(f"[QUEUE] Grid {gid} done — closing valve.")
                client.publish(f"{TOPIC_PREFIX}/control/grid/{gid}", "OFF", qos=1)
                active_grid = None

        # 2. Start next job if idle
        if active_grid is None and irrigation_queue:
            next_job             = irrigation_queue.pop(0)
            active_grid          = next_job
            last_irrigation_start = now
            gid                  = job_id(next_job)
            dur                  = job_dur(next_job)
            print(f"[QUEUE] Starting Grid {gid} for {dur} min.")
            client.publish(f"{TOPIC_PREFIX}/control/grid/{gid}", "ON", qos=1)

# ──────────────────────────────────────────────────────────
def on_message(client, userdata, msg):
    global active_grid

    try:
        topic   = msg.topic
        payload = msg.payload.decode("utf-8", errors="replace").strip()
        print(f"[MSG] {topic}: {payload[:120]}")

        # ── Region Telemetry (FIX: was checking 'telemetry/grid' not 'telemetry/region') ──
        if "telemetry/region/" in topic:
            data     = json.loads(payload)
            grid_id  = int(data.get("region", 0))
            moisture = float(data.get("humidity", 100))   # DHT sends 'humidity' not 'moisture'
            ph       = float(data.get("ph", 7.0))

            # Soil analysis
            try:
                soil_result = soil_brain.analyze_soil(grid_id, ph, moisture)
                if soil_result.get("status") != "OPTIMAL":
                    alert_msg = soil_result["insights"][0] if soil_result.get("insights") else "Soil needs attention."
                    print(f"[SOIL] Grid {grid_id}: {alert_msg}")
                    client.publish(f"{TOPIC_PREFIX}/ai/soil/alert", json.dumps(soil_result))
            except Exception as soil_err:
                print(f"[SOIL] Analysis error: {soil_err}")

            # FIX: always use make_job() - never append plain int
            if moisture < 50.0 and active_grid is None:
                with q_lock:
                    already_queued = any(job_id(j) == grid_id for j in irrigation_queue)
                if not already_queued:
                    print(f"[AUTO] Low humidity {moisture:.0f}% – queuing Grid {grid_id}.")
                    with q_lock:
                        irrigation_queue.append(make_job(grid_id))

            process_sequential_irrigation(client)

        # ── Voice / Text Command ───────────────────────────────
        elif "voice_command" in topic:
            print(f"[CMD] '{payload}'")

            # 1. NLP parse
            try:
                parsed = nlp_brain.process_text(payload)
            except Exception as e:
                print(f"[NLP] Error: {e}")
                parsed = {"action": "GENERAL", "material": "UNKNOWN", "quantity": "N/A",
                          "grid": None, "duration": None, "grids": []}

            # 2. Ledger (non-blocking)
            try:
                ledger.add_entry(payload, parsed["action"], parsed["material"], parsed["quantity"])
                ledger_payload = {
                    "action":   parsed["action"],
                    "material": parsed["material"],
                    "quantity": parsed["quantity"],
                    "raw":      payload,
                    "ts":       time.time()
                }
                client.publish(f"{TOPIC_PREFIX}/ledger/update", json.dumps(ledger_payload))
            except Exception as le:
                print(f"[LEDGER] Warning: {le}")

            # 3. Irrigation command?
            if parsed["action"] in ("IRRIGATE", "WATER") and (parsed.get("grid") or parsed.get("grids")):
                grids_to_do = parsed.get("grids") or []
                if not grids_to_do and parsed.get("grid"):
                    grids_to_do = [{"grid": parsed["grid"], "duration": parsed.get("duration")}]

                labels = []
                for g in grids_to_do:
                    gid  = int(g["grid"])
                    dur  = float(g.get("duration") or 10)
                    print(f"[MANUAL] Queuing Grid {gid} for {dur} min.")
                    with q_lock:
                        irrigation_queue.append(make_job(gid, dur))
                    labels.append(f"Region {gid} for {dur:.0f} min")

                reply = "Queued " + " and ".join(labels) + "."
                client.publish(f"{TOPIC_PREFIX}/voice_feedback", json.dumps({"message": reply}))
                process_sequential_irrigation(client)

            # 4. AI advisory (non-blocking thread)
            else:
                client.publish(f"{TOPIC_PREFIX}/voice_feedback",
                               json.dumps({"message": "Consulting Agri-Gemini… please wait."}))

                def ai_thread():
                    try:
                        advice = gemini_bridge.ask_advisor(payload)
                        client.publish(f"{TOPIC_PREFIX}/ai/gemini/response", json.dumps(advice))
                        print("[AI] Gemini response sent.")
                    except Exception as ai_err:
                        print(f"[AI] Error: {ai_err}")
                        client.publish(f"{TOPIC_PREFIX}/voice_feedback",
                                       json.dumps({"message": "I couldn't get a response right now. Please try again."}))

                threading.Thread(target=ai_thread, daemon=True).start()

        # ── Web-App Manual Override ────────────────────────────
        elif "control/manual" in topic:
            data      = json.loads(payload)
            region_id = int(data["region"])
            duration  = float(data.get("duration", 1))
            print(f"[MANUAL] Web override: Region {region_id} for {duration} min.")
            with q_lock:
                irrigation_queue.append(make_job(region_id, duration))
            process_sequential_irrigation(client)
            client.publish(f"{TOPIC_PREFIX}/voice_feedback",
                           json.dumps({"message": f"Manual irrigation queued: Region {region_id} for {duration:.0f} min."}))

        # ── Motor Telemetry → Acoustic AI ──────────────────────
        elif "telemetry/motor" in topic:
            data = json.loads(payload)
            # FIX: firmware sends 'pressure_psi', not 'pressure' or 'peak_freq'
            pressure_psi = float(data.get("pressure_psi", 45.0))
            result = motor_brain.analyze_frequencies(
                60,              # nominal frequency
                0.5, 1.0,
                pressure=pressure_psi
            )
            if motor_brain.should_shutdown(result):
                print("[EMERGENCY] Motor risk detected! Shutting all valves.")
                with q_lock:
                    irrigation_queue.clear()
                active_grid = None
                for i in range(1, 5):
                    client.publish(f"{TOPIC_PREFIX}/control/grid/{i}", "OFF", qos=1)
                client.publish(f"{TOPIC_PREFIX}/voice_feedback",
                               json.dumps({"message": "⚠️ Emergency shutdown: motor risk detected. All valves closed."}))

    except Exception as e:
        import traceback
        print(f"[ERROR] {e}")
        traceback.print_exc()

# ── Heartbeat Thread ───────────────────────────────────────
def heartbeat_loop(client):
    while True:
        try:
            client.publish(f"{TOPIC_PREFIX}/system/heartbeat",
                           json.dumps({"status": "ONLINE", "ts": time.time()}), qos=0)
        except Exception:
            pass
        time.sleep(5)

# ── Main ───────────────────────────────────────────────────
try:
    from paho.mqtt import enums
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
except Exception:
    mqttc = mqtt.Client()

mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.tls_set()
mqttc.username_pw_set(MQTT_USER, MQTT_PASS)

print(f"[BRAIN] Connecting to {MQTT_BROKER}…")
try:
    mqttc.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
except Exception as ce:
    print(f"[BRAIN] CRITICAL: Connection failed: {ce}")
    sys.exit(1)

threading.Thread(target=heartbeat_loop, args=(mqttc,), daemon=True).start()

mqttc.loop_forever()
