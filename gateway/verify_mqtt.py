import paho.mqtt.client as mqtt
import json
import time

# --- Configuration ---
MQTT_BROKER = "broker.hivemq.com" 
MQTT_PORT = 1883
TOPIC_PREFIX = "agribrain_shravan"

# --- Callbacks ---
def on_connect(client, userdata, flags, rc):
    print(f"Connected to Public Broker with result code {rc}")
    # Subscribe to telemetry from Wokwi simulation
    client.subscribe(f"{TOPIC_PREFIX}/telemetry/grid/+")

def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic}")
    try:
        data = json.loads(msg.payload)
        grid_id = data['grid']
        moisture = data['moisture']
        
        print(f"Grid {grid_id} | Moisture: {moisture}% | Rain: {data.get('rain', False)}")
        
        # Phase 1 Auto-Irrigation Logic
        if moisture < 35.0:
            print(f"!!! [AUTO-COMMAND] Turning ON Grid {grid_id} (Dry) !!!")
            client.publish(f"{TOPIC_PREFIX}/control/grid/{grid_id}", "ON")
        elif moisture > 85.0:
            print(f"!!! [AUTO-COMMAND] Turning OFF Grid {grid_id} (Saturated) !!!")
            client.publish(f"{TOPIC_PREFIX}/control/grid/{grid_id}", "OFF")
             
    except Exception as e:
        print(f"Error parsing JSON or Logic: {e}")

# --- Main ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to {MQTT_BROKER}...")
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
except Exception as e:
    print(f"Connection Failed: {e}")
    exit(1)

print("Starting Phase 1 AI Watcher. Press Ctrl+C to stop.")
client.loop_forever()
