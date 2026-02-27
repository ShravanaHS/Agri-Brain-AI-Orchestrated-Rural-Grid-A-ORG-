import paho.mqtt.client as mqtt
import pyttsx3
import json
import time
import sys
import os
import io

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import pyaudio
from vosk import Model, KaldiRecognizer

# --- Configuration (Sync with verify_mqtt.py) ---
MQTT_BROKER = "33712c7cb7174024b63e809028448b03.s1.eu.hivemq.cloud" 
MQTT_PORT = 8883
MQTT_USER = "agribrain"
MQTT_PASS = "#Shs_2838"
TOPIC_PREFIX = "agribrain_shravan"

class VoiceBrain:
    def __init__(self):
        print("Initializing Voice Brain (Direct Vosk Edition)...")
        
        # 🔊 Text to Speech
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 160)
            print("TTS Engine ready.")
        except Exception as e:
            print(f"Warning: Could not initialize TTS engine. {e}")
            self.engine = None

        # 🧠 Offline AI Model (Vosk)
        print("Loading Offline AI Model...")
        try:
            # Look for model in root (one level up from /gateway) or current
            base_path = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(base_path, "..", "model")
            
            if not os.path.exists(model_path):
                 print(f"Error: Model folder not found at {os.path.abspath(model_path)}")
                 sys.exit(1)
            self.model = Model(model_path)
            self.rec = KaldiRecognizer(self.model, 16000)
            print("Offline AI Model loaded.")
        except Exception as e:
            print(f"Failed to load Vosk model: {e}")
            sys.exit(1)

        # 🎙️ PyAudio for Direct Mic Streaming
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            self.stream.stop_stream()
            print("Microphone stream ready.")
        except Exception as e:
            print(f"Error: Could not open microphone. {e}")
            sys.exit(1)
        
        # 📡 MQTT Setup
        # Paho MQTT v2.0+ Compatibility
        try:
            from paho.mqtt import enums
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except (ImportError, AttributeError):
            self.client = mqtt.Client()

        self.client.tls_set()
        self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("Voice Brain Online. Connected to HiveMQ Cluster.")
            self.client.subscribe(f"{TOPIC_PREFIX}/ai/gemini/response")
            self.client.subscribe(f"{TOPIC_PREFIX}/voice_feedback")
            print("Voice Brain subscribed to feedback topics.")
        else:
            print(f"MQTT Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            if "ai/gemini/response" in msg.topic:
                response_text = data.get("response", "")
                print(f"\n[Gemini]: {response_text}")
                self.speak(response_text)
            elif "voice_feedback" in msg.topic:
                feedback = data.get("message", "")
                print(f"[System Feedback]: {feedback}")
                self.speak(feedback)
        except Exception as e:
            # Silently ignore if not JSON (legacy support)
            try:
                text = msg.payload.decode()
                self.speak(text)
            except:
                pass

    def speak(self, text):
        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()

    def listen_loop(self):
        print("\nListening for commands...")
        self.stream.start_stream()
        
        try:
            while True:
                data = self.stream.read(4000, exception_on_overflow=False)
                if len(data) == 0:
                    break
                
                if self.rec.AcceptWaveform(data):
                    res = json.loads(self.rec.Result())
                    text = res.get("text", "").strip()
                    if text:
                        print(f"I heard: '{text}'")
                        self.speak(f"Processing: {text}")
                        self.client.publish(f"{TOPIC_PREFIX}/voice_command", text)
                else:
                    # Partial result (optional: could be used for live display)
                    pass
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()

    def start(self):
        print("Connecting to MQTT...")
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"MQTT Error: {e}")
            return

        self.speak("Agri-Brain voice interface is active.")
        self.listen_loop()
        self.client.loop_stop()

if __name__ == "__main__":
    vb = VoiceBrain()
    vb.start()
