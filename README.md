# 🌾 Agri-Brain: AI-Orchestrated Rural Grid (A-ORG)
### *Solving the "Kilometer Gap" with Edge AI*

📊 **[Download the Pitch Deck Presentation](docs/AgriBrain_Submission_v2.pptx)**

---

## 🌟 The Vision
Imagine a world where a farmer doesn't have to walk miles in the heat just to flip a switch. Imagine a farm that "listens" to its own motors and "watches" its own crops, making decisions in milliseconds to save water and prevent equipment damage.

**Agri-Brain** is that vision. It’s not just a "smart" tool; it’s an autonomous nervous system for the modern farm, powered by **AMD Ryzen™** and **Edge AI**.

---

## 👨‍🌾 The Problem: Why this matters
Indian farmers face three massive challenges:
1.  **The "Kilometer Gap":** Farmers walk 5-10km daily just to toggle irrigation valves.
2.  **Motor Burnouts:** If a pump runs dry, the motor burns out. This costs a farmer their entire month's profit.
3.  **The Cloud Gap:** Most "Smart Agri" apps need 4G/Cloud. In our villages, the internet is a luxury, not a guarantee.

---

## 🚀 The Solution: "AMD Brain" Gateway
We don't need the Cloud. We brought the processing power to the farm.
Agri-Brain uses a local ** Laptop** as an **Edge Gateway**. It talks to **ESP32 controllers** in the field using MQTT.

### 🧠 How it works (Simple Version):
1.  **Sensors** in the soil send moisture/pH data to the AMD Laptop.
2.  **Acoustic AI** (on laptop) listens to the pump motor. If it sounds "wrong," the laptop tells the pump to shut down instantly.
3.  **Vision AI** (on laptop) watches the plants for disease.
4.  **Voice Ledger:** The farmer just says *"Added 5kg Potash"* in Kannada/Hindi, and the laptop records it—no typing needed.

---

## 🏗️ Technical Architecture
Agri-Brain is built on a **Local-First** philosophy.

-   **Field Layer:** ESP32 Microcontrollers managing 10 irrigation grids.
-   **Nervous System:** MQTT Protocol for hyper-fast, low-latency communication.
-   **Intelligence Layer (The Brain):** AMD Ryzen processing Multi-Modal AI (Audio + Video + NLP).
-   **User UI:** A Flutter Mobile App for manual control and digital mapping.

```mermaid
graph TD
    subgraph "The Field (Simulated/Physical)"
        ESP[ESP32 Controller]
        Valves[10-Grid Valves/LEDs]
        Sensors[Moisture/pH/Rain]
        ESP --> Valves
        Sensors --> ESP
    end

    subgraph "The Communication Hub"
        Broker[HiveMQ / Mosquitto]
    end

    subgraph "AI Gateway (The Brain)"
        PC[Laptop]
        Acoustic[Acoustic AI Model]
        Vision[Vision AI Model]
        PC --> Acoustic
        PC --> Vision
    end

    %% Flow
    ESP <== "MQTT Telemetry" ==> Broker
    Broker <== "AI Commands" ==> PC
```

---

## ✅ Phase 1: The "Success" Milestone
We have successfully built a **Zero-Budget Prototype** using:
-   **Wokwi:** To simulate a 10-grid ESP32 hardware system.
-   **HiveMQ:** As a global public bridge.
-   **Python:** As our first-stage "Decision Engine."

**Current Status:** Moving the virtual moisture slider in Wokwi successfully triggers the Python AI Brain to turn on/off the 10 virtual irrigation valves!

---

##  Simulation Results (Phase 1)
![Phase 1 Simulation Result](assets/phase1_demo.png)
*Above: Wokwi ESP32 simulation reporting 0% moisture, triggering the Python AI Watcher to send AUTO-COMMANDS to turn ON all 10 grids.*
## [Wokwi Simulatation](https://wokwi.com/projects/456861684447098881)

---

## �🛠️ Quick Start (Try it in 2 minutes!)

### 1. The Virtual Farm (Wokwi)
- Open `firmware/diagram.json` and `firmware/src/main.cpp`.
- Load them into [Wokwi](https://wokwi.com).
- Press **Play**.

### 2. The AI Brain (Python)
Ensure you have `paho-mqtt` installed:
```powershell
py -m pip install paho-mqtt
```
Run the watcher:
```powershell
py gateway/verify_mqtt.py
```
*Move the slider in Wokwi and watch the "AI" trigger commands in your terminal!*

---

## 🌊 The 10-Grid Irrigation Strategy
Agri-Brain (A-ORG) replaces wasteful broad-field irrigation with a hyper-efficient **Sequential Grid System**.
- **The Hardware**: 1 Main Pump + 10 Solenoid Valves managed by an ESP32.
- **Micro-Irrigation**: The system waters section-by-section (e.g., Grid 1, then Grid 2), maintaining maximum water pressure at each point.
- **ESP32 Safety**: Built-in 2-hour "Hard Timeout" logic prevents accidental flooding if the gateway disconnects.

## 🧠 Farm Health AI (AMD-Powered)

### 1. Vision AI: Leaf Disease Detection
Using the processing power of **AMD Ryzen™**, the gateway processes crop images locally to detect:
- Early/Late Blight in Tomatoes.
- Pest infestations (Leaf Miner/Mites).
- Nutrient deficiencies showing in leaf color.

### 2. Soil Health Mapping
Real-time analysis of pH and moisture across all 10 grids.
- **Localized Mapping**: Grid-specific health scores.
- **Actionable Insights**: Instant advice on soil amendments (e.g., "Add Lime" for acidity).

### 3. Gemini AI Assistant
A local LLM bridge that acts as a 24/7 Agricultural Advisor, answering queries about crop rotation, water profiles, and pest management entirely offline.

---

## 🏗️ Technical Architecture
```mermaid
graph TD
    subgraph "The Field"
        ESP[ESP32 Controller]
        Solenoids[10x Solenoid Valves]
        Sensors[Moisture + pH Sensors]
        ESP --> Solenoids
        Sensors --> ESP
    end

    subgraph "Communication"
        Broker[HiveMQ / Mosquitto]
    end

    subgraph "AMD AI Gateway (The Brain)"
        AMD[AMD Ryzen Laptop]
        Irrigation[Sequential Grid Engine]
        Vision[Vision AI Node]
        Gemini[Local AI Advisor]
        AMD --> Irrigation
        AMD --> Vision
        AMD --> Gemini
    end

    subgraph "User UI"
        App[Flutter Dashboard]
    end

    %% Flow
    ESP <==> Broker
    Broker <==> AMD
    App <==> Broker
```

---

## 📈 Roadmap to Production
- [x] **Day 1:** Phase 1 (Wokwi + Public Broker) - **DONE**
- [x] **Day 2:** 10-Grid Irrigation Logic & Safety - **DONE**
- [x] **Day 3:** Farm Health AI (Vision & Soil) - **DONE**
- [x] **Day 4:** Premium Dashboard with Grid Mapping - **DONE**
- [x] **Day 5:** Final Integration & Pitch Prep - **DONE**

---

## 📦 Extras (Integrated Features)
- **Acoustic Motor Guard**: Pressure-based run-dry protection.
- **Local NLP Voice Ledger**: Hands-free logging of farm activities.

---

## 🤝 Project by Shravan HS
*Built for AMD Slingshot 2026 Innovation Challenge*
