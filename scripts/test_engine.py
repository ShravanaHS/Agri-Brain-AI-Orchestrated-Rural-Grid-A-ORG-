import paho.mqtt.client as mqtt
import json
import time
import random
import threading

# --- Configuration ---
MQTT_BROKER = "33712c7cb7174024b63e809028448b03.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "agribrain"
MQTT_PASS = "#Shs_2838"
TOPIC_PREFIX = "agribrain_shravan"

class AgriBrainTestEngine:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.tls_set()
        self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        
        self.running = True
        self.auto_telemetry = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to HiveMQ Cloud!")
            # Subscribe to control topics to see "Brain" reactions
            self.client.subscribe(f"{TOPIC_PREFIX}/control/#")
        else:
            print(f"❌ Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        print(f"\n📥 [REACTION] Topic: {msg.topic} | Payload: {msg.payload.decode()}")

    def publish_soil_data(self, grid_id, moisture, ph=6.5):
        topic = f"{TOPIC_PREFIX}/telemetry/grid/{grid_id}"
        payload = {
            "grid": grid_id,
            "moisture": moisture,
            "ph": ph,
            "rain": moisture > 90.0
        }
        self.client.publish(topic, json.dumps(payload))
        print(f"📤 [SOIL] Grid {grid_id}: {moisture}% Moisture, {ph} pH")

    def publish_motor_data(self, state="NORMAL"):
        topic = f"{TOPIC_PREFIX}/telemetry/motor"
        if state == "EMERGENCY":
            payload = {
                "peak_freq": 120,
                "rms_amplitude": 2.5,
                "vibrations": 5.0,
                "pressure": 15.0
            }
        else:
            payload = {
                "peak_freq": 60,
                "rms_amplitude": 0.5,
                "vibrations": 0.8,
                "pressure": 45.0
            }
        self.client.publish(topic, json.dumps(payload))
        print(f"📤 [MOTOR] State: {state}")

    def publish_voice_command(self, command):
        topic = f"{TOPIC_PREFIX}/voice_command"
        self.client.publish(topic, command)
        print(f"📤 [VOICE] Command sent: '{command}'")

    def publish_vision_request(self, diagnosis="Healthy"):
        topic = f"{TOPIC_PREFIX}/ai/vision/request"
        payload = {
            "image_id": f"IMG_{int(time.time())}",
            "mock_diagnosis": diagnosis
        }
        self.client.publish(topic, json.dumps(payload))
        print(f"📤 [VISION] Request sent for: {diagnosis}")

    def telemetry_loop(self):
        while self.running:
            if self.auto_telemetry:
                # Simulate natural fluctuations for all 10 grids
                for i in range(1, 11):
                    moisture = random.uniform(30.0, 80.0)
                    ph = random.uniform(6.0, 7.5)
                    self.publish_soil_data(i, round(moisture, 1), round(ph, 1))
                self.publish_motor_data("NORMAL")
                time.sleep(10) # Send updates every 10 seconds
            else:
                time.sleep(1)

    def start(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            # Start background telemetry thread
            threading.Thread(target=self.telemetry_loop, daemon=True).start()
            
            self.show_menu()
        except Exception as e:
            print(f"Error: {e}")

    def show_menu(self):
        while self.running:
            print("\n--- 🌾 Agri-Brain Test Engine ---")
            print("1. [SOIL] Send Low Moisture (Grid 1 - Trigger Irrigation)")
            print("2. [SOIL] Send High Moisture (Grid 1 - Saturate)")
            print("3. [MOTOR] Send Emergency State (Trigger Shutdown)")
            print("4. [VOICE] Send Command ('Add 5kg Potash')")
            print("5. [VOICE] Send Question ('What is the best crop for March?')")
            print("6. [VISION] Trigger Mock Vision Request")
            print("7. [AUTO] Toggle Auto-Telemetry fluctuations")
            print("0. Exit")
            
            choice = input("\nSelect an option: ")
            
            if choice == '1':
                self.publish_soil_data(1, 25.0)
            elif choice == '2':
                self.publish_soil_data(1, 95.0)
            elif choice == '3':
                self.publish_motor_data("EMERGENCY")
            elif choice == '4':
                self.publish_voice_command("Added 5kg Potash to Grid 1")
            elif choice == '5':
                self.publish_voice_command("What is the best crop for March?")
            elif choice == '6':
                self.publish_vision_request("Tomato Late Blight")
            elif choice == '7':
                self.auto_telemetry = not self.auto_telemetry
                print(f"Auto-Telemetry is now {'ON' if self.auto_telemetry else 'OFF'}")
            elif choice == '0':
                self.running = False
                self.client.loop_stop()
                print("👋 Test Engine Stopped.")
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    engine = AgriBrainTestEngine()
    engine.start()
