import paho.mqtt.client as mqtt
import json
import time
import random

MQTT_BROKER = "broker.hivemq.com"
TOPIC_PREFIX = "agribrain_shravan"
TOPIC = f"{TOPIC_PREFIX}/telemetry/motor"

client = mqtt.Client()
client.connect(MQTT_BROKER, 1883, 60)

def publish_state(name, freq, rms, vib, press=45.0):
    payload = {
        "peak_freq": freq,
        "rms_amplitude": rms,
        "vibrations": vib,
        "pressure": press,
        "timestamp": time.time()
    }
    print(f"Publishing {name}: {payload}")
    client.publish(TOPIC, json.dumps(payload))

try:
    print("--- Agri-Brain Hybrid Motor Simulator ---")
    print("1. Normal Operation (45 PSI)")
    print("2. Cavitation (High Freq, 40 PSI)")
    print("3. Dry Run - Pressure Loss (10 PSI) [CRITICAL]")
    print("4. Dry Run - Low Amplitude (60 PSI but silent)")
    print("5. Bearing Wear (High Vibration, 45 PSI)")
    print("6. Random/Live simulation")
    
    while True:
        choice = input("Enter choice (1-6) or 'q' to quit: ")
        if choice == '1':
            publish_state("NORMAL", 60, 0.5, 1.2, 45.0)
        elif choice == '2':
            publish_state("CAVITATION", 125, 0.9, 2.5, 40.0)
        elif choice == '3':
            publish_state("PRESSURE_LOSS", 60, 0.5, 1.0, 10.0)
        elif choice == '4':
            publish_state("DRY_RUN_SILENT", 60, 0.05, 1.0, 45.0)
        elif choice == '5':
            publish_state("BEARING_FAILURE", 60, 0.4, 8.5, 45.0)
        elif choice == '6':
            # Simulated drift
            f = 60 + random.uniform(-2, 2)
            r = 0.5 + random.uniform(-0.1, 0.1)
            v = 1.0 + random.uniform(0, 0.5)
            p = 45.0 + random.uniform(-5, 5)
            publish_state("LIVE_DRIFT", f, r, v, p)
        elif choice == 'q':
            break
        else:
            print("Invalid choice")
        time.sleep(1)

except KeyboardInterrupt:
    pass
finally:
    client.disconnect()
