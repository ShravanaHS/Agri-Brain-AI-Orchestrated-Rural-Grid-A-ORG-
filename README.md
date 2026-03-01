<div align="center">
  <img src="mobile_app/assets/images/logo.png" alt="Agri-Brain Logo" width="150" height="auto" />
  <h1>🌾 Agri-Brain: AI-Orchestrated Rural Grid (A-ORG)</h1>
  <p><em>Solving the "Kilometer Gap" with Local Edge AI</em></p>

  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
  [![Flutter](https://img.shields.io/badge/Flutter-02569B?style=for-the-badge&logo=flutter&logoColor=white)](#)
  [![C++](https://img.shields.io/badge/C++-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white)](#)
  [![MQTT](https://img.shields.io/badge/MQTT-660066?style=for-the-badge&logo=mqtt&logoColor=white)](#)
  [![ESP32](https://img.shields.io/badge/ESP32-E7352C?style=for-the-badge&logo=espressif&logoColor=white)](#)
  [![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)](#)

  <br />
  <h3>📊 <strong><a href="docs/AgriBrain_Submission_v2.pptx">Download the Official Pitch Deck Presentation</a></strong></h3>
</div>

---

## 📖 Table of Contents
- [🌟 The Vision](#-the-vision)
- [👨‍🌾 The Problem](#-the-problem)
- [🚀 The Solution: "AMD Brain" Gateway](#-the-solution-amd-brain-gateway)
- [🧠 Farm Health AI (AMD-Powered)](#-farm-health-ai-amd-powered)
- [🌊 10-Grid Irrigation Strategy](#-the-10-grid-irrigation-strategy)
- [🏗️ Technical Architecture](#️-technical-architecture)
- [🛠️ Quick Start](#️-quick-start)
- [📈 Roadmap](#-roadmap-to-production)

---

## 🌟 The Vision
Imagine a world where a farmer doesn't have to walk miles in the heat just to flip a switch. Imagine a farm that "listens" to its own motors and "watches" its own crops, making decisions in milliseconds to save water and prevent equipment damage.

**Agri-Brain** is that vision. It’s not just a "smart" tool; it’s an **autonomous nervous system** for the modern farm, powered by **AMD Ryzen™** and **Edge AI**.

---

## 👨‍🌾 The Problem
Indian farmers face three massive, interconnected challenges:

| Challenge | Impact |
| :--- | :--- |
| 🚶 **1. The "Kilometer Gap"** | Farmers walk 5-10km daily just to toggle irrigation valves manually across large fields. |
| 🔥 **2. Motor Burnouts** | If a pump runs dry, the motor burns out. This single event costs a farmer their entire month's profit. |
| ☁️ **3. The Cloud Gap** | Most "Smart Agri" edge solutions demand 4G or Cloud setups. In villages, the internet is a luxury, not a guarantee. |

---

## 🚀 The Solution: "AMD Brain" Gateway
We don't need the Cloud. We brought the processing power directly to the farm.

**Agri-Brain** uses a local **Laptop** as an **Edge Gateway**. It speaks to **ESP32 microcontrollers** in the field using lightning-fast MQTT communication.

### 🧠 How It Works
1. 💧 **Sensory Input:** Nodes in the soil send moisture/pH data to the local AMD Laptop.
2. 🎧 **Acoustic AI:** The laptop algorithmically listens to the pump motor. If it sounds "wrong" (dry run), it shuts everything down instantly to prevent burnout.
3. 👁️ **Vision AI:** Models running locally watch the plants for early disease detection.
4. 🎙️ **Voice Ledger:** The farmer just says *"Added 5kg Potash"* in Kannada/Hindi, and the laptop automatically records it into the local ledger—no typing needed.

---

## 🧠 Farm Health AI (AMD-Powered)

#### 👁️ Vision AI: Leaf Disease Detection
Using the incredible processing power of **AMD Ryzen™**, the gateway processes crop images completely offline to detect:
- Early and Late Blight in Tomatoes.
- Pest infestations (Leaf Miner, Spider Mites).
- Nutrient deficiencies mapped from leaf discoloration patterns.

#### 🌍 Soil Health Mapping
Real-time analysis of pH, macronutrients, and moisture across all 10 grids.
- **Localized Mapping:** Generates grid-specific health scores dynamically.
- **Actionable Insights:** Instant automated logic (e.g., *"Grid 4 is acidic: Add Lime"*).

#### 🗣️ Local LLM Assistant
A lightweight, offline LLM model acting as a 24/7 Agricultural Advisor, answering localized queries about crop rotation, water profiles, and local pest management entirely offline!

---

## 🌊 The 10-Grid Irrigation Strategy
Agri-Brain (A-ORG) replaces wasteful broad-field irrigation with a hyper-efficient **Sequential Grid System**.

- ⚙️ **The Hardware:** 1 Main Pump + 10 Solenoid Valves managed efficiently by an ESP32 hub.
- 💦 **Micro-Irrigation:** The system waters section-by-section (e.g., Grid 1 → Grid 2) rather than all at once, maintaining maximum water pressure at every single nozzle/drip.
- 🛡️ **Fail-Safe Integrity:** Built-in 2-hour "Hard Timeout" logic physically coded onto the ESP32 prevents accidental flooding even if the gateway disconnects entirely.

---

## 🏗️ Technical Architecture
Agri-Brain is built from the ground up on a **Local-First** philosophy perfectly tailored for rural environments.

<div align="center">

```mermaid
graph TD
    %% Node Defining
    subgraph "The Field Layer (Physical/Wokwi)"
        ESP[ESP32 Controller Hub]
        Solenoids[10x Solenoid Valves]
        Sensors[Soil Moisture + pH Sensors]
        
        ESP --- Solenoids
        Sensors --- ESP
    end

    subgraph "Communication Layer"
        Broker((MQTT Broker<br/>HiveMQ / Mosquitto))
    end

    subgraph "The Brain (AMD AI Gateway)"
        AMD{AMD Ryzen Laptop}
        Irrigation[Sequential Target Engine]
        Vision[Vision AI Node]
        Gemini[Local LLM Advisor]
        
        AMD --- Irrigation
        AMD --- Vision
        AMD --- Gemini
    end

    subgraph "User Layer"
        App📱[Flutter Dashboard]
    end

    %% Flows
    ESP <==> Broker
    Broker <==> AMD
    App📱 <==> Broker
    
    style ESP fill:#2b2b2b,stroke:#00aa00,stroke-width:2px,color:#fff
    style Broker fill:#1f0f4a,stroke:#8A2BE2,stroke-width:2px,color:#fff
    style AMD fill:#111,stroke:#dd0000,stroke-width:2px,color:#fff
    style App📱 fill:#01579B,stroke:#0288D1,stroke-width:2px,color:#fff
```

</div>

---

## 🛠️ Quick Start (Try it in 2 minutes!)

### 1. The Virtual Farm Simulation (Wokwi)
- Open `firmware/diagram.json` and `firmware/src/main.cpp`.
- Load them into [Wokwi.com](https://wokwi.com).
- Press **Play**. You now have a complete virtual farm transmitting telemetry!

### 2. The AI Brain (Gateway Engine)
Ensure you have `paho-mqtt` installed in your Python environment:
```powershell
py -m pip install paho-mqtt
```
Wake up the Brain Watcher:
```powershell
py gateway/verify_mqtt.py
```
> **Tip:** *Move the physical moisture slider in Wokwi down to 0% and watch the AI instantly trigger commands in your terminal to turn ON the localized grids!*

---

## 📈 Simulation Results (Phase 1)
<div align="center">
  <img src="assets/phase1_demo.png" alt="Phase 1 Simulation Result" width="80%">
  <p><em>Above: Wokwi ESP32 simulation reporting 0% moisture, triggering the Python AI Watcher to send AUTO-COMMANDS to turn ON all 10 grids.</em></p>
</div>

### 🌐 [Click Here to View the Wokwi Simulation Online](https://wokwi.com/projects/456861684447098881)

---

## 📈 Roadmap to Production
- ✅ **Day 1:** Phase 1 (Wokwi + Public Broker)
- ✅ **Day 2:** 10-Grid Irrigation Sequential Logic & Hardware Safety Rules
- ✅ **Day 3:** Farm Health AI models (Vision & Soil Mapping)
- ✅ **Day 4:** Premium Flutter Mobile Dashboard with Grid Mapping UI
- ✅ **Day 5:** Final Integration & Pitch Deck Finalization

---

## 📦 System Extras (Integrated Subsystems)
- 🎧 **Acoustic Motor Guard:** Pressure-based run-dry protection reacting instantly to acoustic signatures.
- 🗣️ **Local NLP Voice Ledger:** Hands-free logging of sensitive farm activity directly into a SQLite local database.

---

<div align="center">
  <h3>🤝 Project by Shravan HS</h3>
  <p><em>Built proudly for the AMD Slingshot 2026 Innovation Challenge</em></p>
</div>
