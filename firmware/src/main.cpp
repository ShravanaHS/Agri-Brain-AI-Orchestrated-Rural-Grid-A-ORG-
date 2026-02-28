#include <ArduinoJson.h>
#include <DHT.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>

// ================= CONFIG =================
#define DHTTYPE DHT22
#define NUM_REGIONS 4
#define TELEMETRY_INTERVAL 5000 // ms between telemetry publishes

// Pressure logic
#define PRESSURE_MAX_PSI 100
#define PRESSURE_DRY_THRESHOLD_PCT 20

// WiFi
const char *ssid = "Wokwi-GUEST";
const char *password = "";

// MQTT
const char *mqtt_server = "33712c7cb7174024b63e809028448b03.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char *mqtt_user = "agribrain";
const char *mqtt_pass = "#Shs_2838";

const char *topic_prefix = "agribrain_shravan";

// ================= PINS =================
const uint8_t dhtPins[NUM_REGIONS] = {32, 13, 25, 26};
const uint8_t valvePins[NUM_REGIONS] = {2, 4, 5, 18};

const uint8_t pressurePin = 34;
const uint8_t motorPin = 19;
const uint8_t pumpRedPin = 21;
const uint8_t pumpGreenPin = 22;

// ================= OBJECTS =================
DHT dhts[NUM_REGIONS] = {DHT(dhtPins[0], DHTTYPE), DHT(dhtPins[1], DHTTYPE),
                         DHT(dhtPins[2], DHTTYPE), DHT(dhtPins[3], DHTTYPE)};

WiFiClientSecure espClient;
PubSubClient client(espClient);

// ================= GLOBALS =================
unsigned long lastMsg = 0;
unsigned long lastReconnectAttempt = 0;
bool autoIrrigation = false; // Boot in MANUAL mode

// FIX: Manual valve timer — track when each valve should auto-close
// 0 = not scheduled. Non-zero = millis() deadline.
unsigned long manualValveEndMs[NUM_REGIONS] = {0, 0, 0, 0};

// =====================================================
// READ PRESSURE (0–100 PSI)
// =====================================================
float readPressurePSI() {
  int raw = analogRead(pressurePin); // 0–4095
  return (raw / 4095.0f) * PRESSURE_MAX_PSI;
}

// =====================================================
// PUMP SAFETY LOGIC
// =====================================================
bool applyPumpLogic(float psi) {
  float threshold = (PRESSURE_DRY_THRESHOLD_PCT / 100.0f) * PRESSURE_MAX_PSI;
  bool good = (psi > threshold);
  digitalWrite(motorPin, good ? HIGH : LOW);
  digitalWrite(pumpRedPin, good ? LOW : HIGH);
  digitalWrite(pumpGreenPin, good ? HIGH : LOW);
  return good;
}

// =====================================================
// WIFI
// =====================================================
void setup_wifi() {
  Serial.print("Connecting to WiFi…");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" Connected!");
  espClient.setInsecure(); // For HiveMQ Cloud (no CA pinning needed in Wokwi)
}

// =====================================================
// MQTT CALLBACK
// =====================================================
void callback(char *topic, byte *payload, unsigned int length) {

  // FIX: safe null-termination (guard against length == buffer size)
  char msgBuf[256];
  unsigned int safeLen =
      (length < sizeof(msgBuf) - 1) ? length : sizeof(msgBuf) - 1;
  memcpy(msgBuf, payload, safeLen);
  msgBuf[safeLen] = '\0';
  const char *msg = msgBuf;

  Serial.printf("MQTT [%s]: %s\n", topic, msg);

  // ── Auto mode toggle ──────────────────────────────────
  if (strstr(topic, "/control/auto")) {
    autoIrrigation = (strcmp(msg, "ON") == 0);
    Serial.printf("Auto irrigation: %s\n", autoIrrigation ? "ON" : "OFF");
    return;
  }

  // ── Brain controlled valve: /control/grid/N  ON|OFF ──
  if (strstr(topic, "/control/grid/")) {
    // Extract region number from topic tail
    const char *numPtr = topic + strlen(topic) - 1;
    while (numPtr > topic && *(numPtr - 1) != '/')
      numPtr--;
    int regionNum = atoi(numPtr); // 1-based
    if (regionNum >= 1 && regionNum <= NUM_REGIONS) {
      bool on = (strcmp(msg, "ON") == 0);
      int idx = regionNum - 1;
      digitalWrite(valvePins[idx], on ? HIGH : LOW);
      // Clear any manual timer since brain took over
      if (!on)
        manualValveEndMs[idx] = 0;
      Serial.printf("[VALVE] Region %d -> %s\n", regionNum,
                    on ? "OPEN" : "CLOSED");
    }
    return;
  }

  // ── Web-app direct manual: /control/manual ────────────
  // Brain normally handles this, but ESP acts as fallback if brain offline.
  // FIX: now honors the duration and schedules a timed close.
  if (strstr(topic, "/control/manual")) {
    StaticJsonDocument<128> doc;
    if (deserializeJson(doc, msg) == DeserializationError::Ok) {
      int regionNum = doc["region"] | 0;
      int duration = doc["duration"] | 1; // minutes
      if (regionNum >= 1 && regionNum <= NUM_REGIONS) {
        int idx = regionNum - 1;
        digitalWrite(valvePins[idx], HIGH);
        // FIX: schedule an auto-close after 'duration' minutes
        manualValveEndMs[idx] =
            millis() + (unsigned long)duration * 60UL * 1000UL;
        Serial.printf(
            "[MANUAL] Region %d OPEN for %d min (auto-close scheduled)\n",
            regionNum, duration);
      }
    }
    return;
  }
}

// =====================================================
// MQTT RECONNECT (Non-blocking)
// =====================================================
void reconnect() {
  if (client.connected())
    return;

  unsigned long now = millis();
  if (now - lastReconnectAttempt < 5000)
    return;
  lastReconnectAttempt = now;

  Serial.print("Connecting to MQTT…");
  if (client.connect("AgriBrainESP32", mqtt_user, mqtt_pass)) {
    Serial.println(" OK");

    char subTopic[64];
    snprintf(subTopic, sizeof(subTopic), "%s/control/#", topic_prefix);
    client.subscribe(subTopic);
    lastReconnectAttempt = 0;

  } else {
    Serial.printf(" Failed rc=%d\n", client.state());
  }
}

// =====================================================
// SETUP
// =====================================================
void setup() {
  Serial.begin(115200);

  // Valve & DHT init
  for (int i = 0; i < NUM_REGIONS; i++) {
    pinMode(valvePins[i], OUTPUT);
    digitalWrite(valvePins[i], LOW);
    dhts[i].begin();
  }

  // Pump LEDs
  pinMode(motorPin, OUTPUT);
  pinMode(pumpRedPin, OUTPUT);
  pinMode(pumpGreenPin, OUTPUT);
  digitalWrite(motorPin, LOW);
  digitalWrite(pumpRedPin, HIGH); // Red = off initially
  digitalWrite(pumpGreenPin, LOW);

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

// =====================================================
// LOOP
// =====================================================
void loop() {
  // MQTT maintenance
  if (!client.connected())
    reconnect();
  client.loop();

  // FIX: Check and execute manual valve auto-close timers
  unsigned long nowMs = millis();
  for (int i = 0; i < NUM_REGIONS; i++) {
    if (manualValveEndMs[i] != 0 && nowMs >= manualValveEndMs[i]) {
      digitalWrite(valvePins[i], LOW);
      manualValveEndMs[i] = 0;
      Serial.printf("[MANUAL] Region %d valve AUTO-CLOSED after timer\n",
                    i + 1);
    }
  }

  // Telemetry throttle
  unsigned long now = millis();
  if (now - lastMsg < TELEMETRY_INTERVAL)
    return;
  lastMsg = now;

  bool anyValveOn = false;

  // ── Region telemetry ──────────────────────────────────
  for (int i = 0; i < NUM_REGIONS; i++) {
    float h = dhts[i].readHumidity();
    float t = dhts[i].readTemperature();

    if (isnan(h) || isnan(t))
      continue;

    bool valveState = false;

    if (autoIrrigation) {
      // Auto: open if humidity < 50%
      valveState = (h < 50.0f);
      // Don't override if there's still a manual timer running
      if (manualValveEndMs[i] == 0) {
        digitalWrite(valvePins[i], valveState ? HIGH : LOW);
      }
    } else {
      // Manual: read actual pin state
      valveState = (digitalRead(valvePins[i]) == HIGH);
    }

    if (valveState)
      anyValveOn = true;

    // Publish region telemetry
    StaticJsonDocument<128> doc;
    doc["region"] = i + 1;
    doc["humidity"] = h;
    doc["temp"] = t;
    doc["valve"] = valveState;

    char regionTopic[64], regionPayload[128];
    snprintf(regionTopic, sizeof(regionTopic), "%s/telemetry/region/%d",
             topic_prefix, i + 1);
    serializeJson(doc, regionPayload);
    client.publish(regionTopic, regionPayload);
  }

  // ── Pump/pressure telemetry ───────────────────────────
  float psi = readPressurePSI();
  bool pumpRunning = false;

  if (anyValveOn) {
    pumpRunning = applyPumpLogic(psi);
  } else {
    digitalWrite(motorPin, LOW);
    applyPumpLogic(psi); // update LEDs only
  }

  const char *stage =
      (psi <= (PRESSURE_DRY_THRESHOLD_PCT / 100.0f * PRESSURE_MAX_PSI)) ? "DRY"
                                                                        : "OK";

  StaticJsonDocument<128> pumpDoc;
  pumpDoc["state"] = pumpRunning ? "ON" : "OFF";
  pumpDoc["stage"] = stage;
  pumpDoc["pressure_psi"] = (int)psi;

  char motorTopic[64], motorPayload[128];
  snprintf(motorTopic, sizeof(motorTopic), "%s/telemetry/motor", topic_prefix);
  serializeJson(pumpDoc, motorPayload);
  client.publish(motorTopic, motorPayload);

  Serial.printf("Pressure: %.1f PSI | Pump: %s | Stage: %s\n", psi,
                pumpRunning ? "ON" : "OFF", stage);
  Serial.println("--- Telemetry Published ---");
}