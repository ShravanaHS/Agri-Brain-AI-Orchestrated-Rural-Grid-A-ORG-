import pyttsx3
import json
import time
import sys
import os
import pyaudio
import re
from vosk import Model, KaldiRecognizer

class StandaloneEdgeAI:
    def __init__(self):
        print("--- 🚀 Standalone Edge AI Playground ---")
        
        # 1. Initialize TTS (Voice Response)
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 160)
            print("✅ TTS Engine ready.")
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize TTS engine. {e}")
            self.engine = None

        print("🧠 Loading Offline AI Model (Vosk)...")
        try:
            # Look for model in the root (one level up from this playground)
            base_path = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(base_path, "..", "model")
            
            if not os.path.exists(model_path):
                 print(f"❌ Error: Model folder not found at {os.path.abspath(model_path)}")
                 print("Please ensure the 'model' folder exists in the project root.")
                 sys.exit(1)
            self.model = Model(model_path)
            
            # 📚 Custom Vocabulary Boost (Grammar)
            # This forces the AI to look for these specific words first, increasing accuracy 10x
            vocabulary = [
                "added", "removed", "sprayed", "purchased", "used", "applied",
                "potash", "polash", "urea", "pomegranate", "tomato", "fertilizer", "pesticide",
                "what", "how", "tell", "query", "me", "about", "kg", "liters", "bags",
                "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                "five kg", "ten kg", "amount", "of", "[unk]"
            ]
            
            self.rec = KaldiRecognizer(self.model, 16000, json.dumps(vocabulary))
            print("✅ Offline Hearing ready (with Vocabulary Boost).")
        except Exception as e:
            print(f"❌ Failed to load Vosk model: {e}")
            sys.exit(1)

        # 3. Initialize Audio Stream
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            self.stream.stop_stream()
            print("✅ Microphone ready.")
        except Exception as e:
            print(f"❌ Error: Could not open microphone. {e}")
            sys.exit(1)

        # 4. Internal "Ledger" (Simulation)
        self.local_ledger = []
        
        # 5. Local Knowledge Base (Simulation of local Gemini)
        self.kb = {
            "pomegranate": "Pomegranates need well-drained soil with a pH of 6.0 to 7.0.",
            "tomato": "Early blight is common. Use 2 liters of pesticide per grid.",
            "potash": "Potash helps in root development. Best timing is early morning.",
            "urea": "Urea provides high nitrogen. Apply only 5kg per grid to avoid root burn."
        }

    def speak(self, text):
        print(f"🤖 AI: {text}")
        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()

    def process_voice_ledger(self, text):
        """Extracts facts for the 'Voice Ledger'"""
        actions = ["added", "removed", "sprayed", "purchased", "used"]
        materials = ["potash", "polash", "urea", "npm", "water", "fertilizer", "pesticide", "seeds"]
        
        extracted_action = None
        extracted_material = None
        
        for a in actions:
            if a in text: extracted_action = a; break
        for m in materials:
            if m in text: 
                extracted_material = m.replace("polash", "potash"); 
                break
        
        qty_match = re.search(r'(\d+)', text)
        qty = qty_match.group(0) if qty_match else "N/A"

        if extracted_action and extracted_material:
            entry = f"{extracted_action.upper()} {qty}kg of {extracted_material.upper()}"
            self.local_ledger.append(entry)
            return entry
        return None

    def query_advisor(self, text):
        """Simulates logic for the 'Gemini Advisor'"""
        for key, value in self.kb.items():
            if key in text:
                return value
        return "I heard you, but I'm not sure about that specific crop yet. Try asking about tomatoes or pomegranates."

    def run(self):
        self.speak("Edge AI testing playground is active. I am listening.")
        self.stream.start_stream()
        
        print("\n--- TEST COMMANDS ---")
        print("1. 'Tell me about tomatoes' (Advisor Test)")
        print("2. 'Added 10kg of urea' (Ledger Test)")
        print("--- START TALKING NOW ---\n")

        try:
            while True:
                data = self.stream.read(4000, exception_on_overflow=False)
                if self.rec.AcceptWaveform(data):
                    res = json.loads(self.rec.Result())
                    text = res.get("text", "").strip()
                    
                    if text:
                        print(f"🗣️ You: '{text}'")
                        
                        # 1. Try to parse for Ledger
                        ledger_entry = self.process_voice_ledger(text)
                        if ledger_entry:
                            self.speak(f"Recording to Ledger: {ledger_entry}")
                            print(f"📔 [LOCAL LEDGER]: {self.local_ledger}")
                        
                        # 2. Try to answer questions (Advisor)
                        elif any(word in text for word in ["tell", "what", "how", "query"]):
                            answer = self.query_advisor(text)
                            self.speak(answer)
                        
                        else:
                            self.speak(f"I heard you say: {text}")

                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n🛑 Closing Playground...")
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()

if __name__ == "__main__":
    ai = StandaloneEdgeAI()
    ai.run()
