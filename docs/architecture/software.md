# Software Layer Architecture

This document covers the high-level applications that the end-user (the farmer or farm manager) interacts with, as well as the local Edge Gateway engine.

---

## 1. The Python Edge Gateway (`verify_mqtt.py`)

The Python gateway is the "Brain" running locally on an AMD-powered machine.

### Core Responsibilities:
1.  **State Management**: Subscribes to the MQTT broker and maintains the live state of all 4 grids in memory.
2.  **Auto-Irrigation Engine**: If the system is in Auto mode, Python evaluates the DHT moisture logic. If moisture drops to 0%, the Python script fires an MQTT packet to `control/grid/N` to open the valve.
3.  **The Local Ledger (SQLite)**: Every time a valve opens, or pressure drops, Python logs the timestamp, action, and trigger-type into `farm_ledger.db`. This provides an offline, permanent audit trail.

---

## 2. Web Development (Vanilla JS & CSS)

We built a lightweight, zero-dependency Web Dashboard.

### Tech Stack:
*   **HTML5 / CSS3**: Designed using a modern glassmorphic UI, tailored for readability on tablets and desktops.
*   **Vanilla JavaScript**: No React or Vue overhead.
*   **Paho-MQTT WebSocket**: Connects directly to HiveMQ over `wss://` on port 8884 to bypass corporate firewalls.

### Dashboard Features:
*   **Live Grid View**: 4 visual cards representing the 4 regions. The cards dynamically update their moisture percentages and color-code themselves (e.g., Red = Dry, Blue = Irrigating).
*   **Manual Override Panel**: A form allowing the user to select Grid 1-4, specify a time (in minutes), and fire a manual MQTT command to the farm.

---

## 3. Mobile Development (Flutter & Dart)

For on-the-go access, we developed a cross-platform mobile application.

### Tech Stack:
*   **Framework**: Flutter (Dart).
*   **Package**: `mqtt_client` for secure, background-capable MQTT connections directly to HiveMQ.

### App Features:
*   **Dashboard Screen (`dashboard_screen.dart`)**: A mobile-optimized replica of the Web UI, showing live DHT sensor feeds.
*   **Calendar Screen (`calendar_screen.dart`)**: A scaffolded UI for scheduling future irrigation blocks and reviewing historical ledger data.

---

## 4. Software UI Screenshots

### Web Application
*(Insert Web App Dashboard Screenshot Here)*
> **Screenshot details:** Show the modern web UI with the 4 grid cards displaying active telemetry.

### Flutter Mobile App
*(Insert Flutter App Screenshot Here)*
> **Screenshot details:** Show the mobile screen displaying the manual override toggles and the live status.

### SQLite Ledger
*(Insert SQLite DB Browser Screenshot Here)*
> **Screenshot details:** Show a table view of `farm_ledger.db` with columns like `timestamp`, `event_type`, `region`, and `details`.
