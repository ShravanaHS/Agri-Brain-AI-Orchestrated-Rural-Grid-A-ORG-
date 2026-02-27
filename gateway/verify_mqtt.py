import sys
import io
# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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

# --- Configuration ---
MQTT_BROKER = "33712c7cb7174024b63e809028448b03.s1.eu.hivemq.cloud" 
MQTT_PORT = 8883
MQTT_USER = "agribrain"
MQTT_PASS = "#Shs_2838"
TOPIC_PREFIX = "agribrain_shravan"

# --- AI Engines ---
motor_brain = AcousticBrain()
nlp_brain = NLPBrain()
ledger = LedgerManager()
vision_brain = VisionBrain()
soil_brain = SoilBrain()
gemini_bridge = AgriGeminiBridge()

# --- Irrigation State ---
irrigation_queue = []
active_grid = None
last_irrigation_start = 0
MAX_VALVE_TIME = 10 * 60 # 10 minutes per grid in auto-mode

def check_weather_prediction():
    """
    Simulates checking a Weather API (e.g., OpenWeatherMap).
    In a real scenario, this would cache the forecast for offline use.
    """
    # 20% chance of "Rain Predicted"
    rain_imminent = random.random() < 0.2 
    return rain_imminent

# --- Callbacks ---
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected successfully to HiveMQ Cloud.")
        # Subscribe to EVERYTHING under our prefix to debug missing messages
        client.subscribe(f"{TOPIC_PREFIX}/#")
        print(f"Subscribed to wildcard: {TOPIC_PREFIX}/#")
    else:
        print(f"Connection FAILED with code {rc}.")

def process_sequential_irrigation(client):
    global active_grid, last_irrigation_start
    now = time.time()
    
    # 1. Stop active if finished
    if active_grid:
        # Check if we have a custom duration for this grid
        duration = MAX_VALVE_TIME
        if isinstance(active_grid, dict):
            grid_id = active_grid['id']
            duration = active_grid['duration'] * 60 # convert to seconds
        else:
            grid_id = active_grid

        if now - last_irrigation_start > duration:
            print(f"DEBUG: [AUTO] Grid {grid_id} completed. Shutting off...")
            client.publish(f"{TOPIC_PREFIX}/control/grid/{grid_id}", "OFF")
            active_grid = None

    # 2. Start next in queue
    if active_grid is None and irrigation_queue:
        next_job = irrigation_queue.pop(0)
        active_grid = next_job
        last_irrigation_start = now
        
        grid_id = next_job['id'] if isinstance(next_job, dict) else next_job
        print(f"DEBUG: [AUTO] Starting Grid {grid_id} Sequential Irrigation...")
        client.publish(f"{TOPIC_PREFIX}/control/grid/{grid_id}", "ON")

def on_message(client, userdata, msg):
    global active_grid
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        print(f"DEBUG: Message received on {topic}: {payload}")
        
        if "telemetry/grid" in topic:
            data = json.loads(payload)
            grid_id = data['grid']
            moisture = data['moisture']
            ph = data.get('ph', 7.0)
            
            # 1. Soil Health Mapping
            soil_result = soil_brain.analyze_soil(grid_id, ph, moisture)
            if soil_result['status'] != "OPTIMAL":
                msg_text = soil_result['insights'][0] if soil_result['insights'] else "Soil needs attention."
                print(f"[Soil AI] Grid {grid_id} Alert: {msg_text}")
                client.publish(f"{TOPIC_PREFIX}/ai/soil/alert", json.dumps(soil_result))
            
            # 2. Sequential Irrigation Logic
            if moisture < 35.0:
                is_in_queue = any((j['id'] if isinstance(j, dict) else j) == grid_id for j in irrigation_queue)
                active_id = (active_grid['id'] if isinstance(active_grid, dict) else active_grid) if active_grid else None
                
                if not is_in_queue and active_id != grid_id:
                    print(f"[QUEUE] Low moisture in Grid {grid_id} ({moisture}%). Adding to sequence.")
                    irrigation_queue.append(grid_id)
            
            process_sequential_irrigation(client)
        
        elif "voice_command" in topic:
            payload_lower = payload.lower()
            print(f"[Command Received]: {payload}")
            
            # 1. Process NLP
            try:
                parsed = nlp_brain.process_text(payload)
            except Exception as e:
                print(f"NLP Error: {e}")
                parsed = {"action": "GENERAL", "material": "UNKNOWN", "quantity": "N/A", "grid": None, "duration": None}

            # 2. Log to ledger (Optional - Don't crash if DB fails)
            try:
                ledger.add_entry(payload, parsed['action'], parsed['material'], parsed['quantity'])
                client.publish(f"{TOPIC_PREFIX}/ledger/update", json.dumps(parsed))
                print(f"[Ledger] Stored: {parsed['action']}")
            except Exception as e:
                print(f"Ledger Warning: {e}")

            # 3. Check for Irrigation Commands
            if parsed['action'] in ["IRRIGATE", "WATER"] and parsed['grid']:
                grid_id = parsed['grid']
                duration = parsed['duration'] or 10
                print(f"[MANUAL] Queuing Grid {grid_id} for {duration} mins.")
                irrigation_queue.append({"id": grid_id, "duration": duration})
                client.publish(f"{TOPIC_PREFIX}/voice_feedback", json.dumps({"message": f"Queued Grid {grid_id} for {duration} minutes."}))
                process_sequential_irrigation(client)
            
            # 4. Handle as AI Query in thread to avoid blocking loop
            else:
                client.publish(f"{TOPIC_PREFIX}/voice_feedback", json.dumps({"message": "Consulting Agri-Gemini..."}))
                
                def ai_thread():
                    try:
                        advice = gemini_bridge.ask_advisor(payload)
                        client.publish(f"{TOPIC_PREFIX}/ai/gemini/response", json.dumps(advice))
                        print("[AI] Response sent.")
                    except Exception as ai_err:
                        print(f"AI Error: {ai_err}")
                        client.publish(f"{TOPIC_PREFIX}/voice_feedback", json.dumps({"message": "I'm having trouble thinking right now. Please try again."}))
                
                threading.Thread(target=ai_thread, daemon=True).start()
        
        elif "telemetry/motor" in topic:
            data = json.loads(payload)
            result = motor_brain.analyze_frequencies(
                data.get("peak_freq", 60), 0.5, 1.0, 
                pressure=data.get("pressure", 45.0)
            )
            if motor_brain.should_shutdown(result):
                print(f"[EMERGENCY] Motor Risk! Shutting down all valves.")
                irrigation_queue.clear()
                active_grid = None
                for i in range(1, 5): client.publish(f"{TOPIC_PREFIX}/control/grid/{i}", "OFF")
             
    except Exception as e:
        print(f"Error processing message: {e}")

# --- Main ---
try:
    from paho.mqtt import enums
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
except:
    client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message
client.tls_set()
client.username_pw_set(MQTT_USER, MQTT_PASS)

print(f"Connecting to HiveMQ Cloud: {MQTT_BROKER}...")
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
except Exception as e:
    print(f"CRITICAL: Connection Failed: {e}")
    exit(1)

def heartbeat_loop():
    while True:
        try:
            client.publish(f"{TOPIC_PREFIX}/system/heartbeat", json.dumps({"status": "ONLINE", "ts": time.time()}))
            time.sleep(5)
        except: pass

import threading
threading.Thread(target=heartbeat_loop, daemon=True).start()

client.loop_forever()
