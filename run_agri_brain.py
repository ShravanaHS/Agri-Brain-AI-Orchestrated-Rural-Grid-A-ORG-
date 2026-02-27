import subprocess
import time
import sys
import os
import io

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def launch_agribrain():
    print("Initializing Agri-Brain: AI-Orchestrated Rural Grid...")
    print("-------------------------------------------------------")
    
    # 1. Start the HiveMQ/MQTT Watcher (The Brain)
    print("Starting AI Watcher (Acoustic + NLP)...")
    try:
        # Using sys.executable to ensure we use the same python environment
        # Setting PYTHONUNBUFFERED=1 to ensure we see logs in real-time
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        watcher = subprocess.Popen([sys.executable, "gateway/verify_mqtt.py"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.STDOUT, 
                                   text=True,
                                   env=env)
        
        print("Brain is Online.")
        print("-------------------------------------------------------")
        print("Monitoring Topics:")
        print(" - agribrain_shravan/telemetry/grid/+")
        print(" - agribrain_shravan/telemetry/motor")
        print(" - agribrain_shravan/voice_command")
        print("-------------------------------------------------------")

        # Stream output
        for line in watcher.stdout:
            print(f"[EDGE BRAIN] {line.strip()}")
            
    except KeyboardInterrupt:
        print("\nShutting down Agri-Brain...")
        watcher.terminate()
    except Exception as e:
        print(f"Failed to launch: {e}")

if __name__ == "__main__":
    launch_agribrain()
