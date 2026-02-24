# Mosquitto MQTT Setup Guide (Windows)

To set up the communication backbone for Agri-Brain on your AMD Laptop, follow these steps:

1. **Download Mosquitto:**
   - Go to [mosquitto.org/download](https://mosquitto.org/download/) and download the Windows 64-bit installer.
2. **Install:**
   - Run the installer. Default path is `C:\Program Files\mosquitto`.
3. **Configure for Local Network:**
   - Open `C:\Program Files\mosquitto\mosquitto.conf` with Notepad (as Administrator).
   - Add these lines to allow connections from your ESP32 and Mobile App:
     ```conf
     listener 1883
     allow_anonymous true
     ```
4. **Start the Service:**
   - Open Command Prompt (Admin) and run:
     ```cmd
     net start mosquitto
     ```
   - *Alternative (Manual Run):*
     ```cmd
     cd "C:\Program Files\mosquitto"
     mosquitto -v -c mosquitto.conf
     ```
5. **Find your Laptop's IP:**
   - In Command Prompt, type `ipconfig`. Look for "IPv4 Address" (e.g., `192.168.1.5`). This is what the ESP32 and Flutter app will use as the MQTT Broker address.
