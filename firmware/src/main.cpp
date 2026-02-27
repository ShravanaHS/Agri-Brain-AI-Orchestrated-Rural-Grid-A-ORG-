#include <ArduinoJson.h>
#include <DHT.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>


// --- Configuration ---
const char *ssid = "Wokwi-GUEST";
const char *password = "";
const char *mqtt_server = "33712c7cb7174024b63e809028448b03.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char *mqtt_user = "agribrain";
const char *mqtt_pass = "#Shs_2838";

// --- Constants & Pins ---
const int numRegions = 4;
const int dhtPins[numRegions] = {15, 13, 25, 26};
const int valvePins[numRegions] = {2, 4, 5, 18};
const int motorPin = 19;
const int healthRedPin = 21;
const int healthGreenPin = 22;

#define DHTTYPE DHT22
DHT dhts[numRegions] = {DHT(dhtPins[0], DHTTYPE), DHT(dhtPins[1], DHTTYPE),
                        DHT(dhtPins[2], DHTTYPE), DHT(dhtPins[3], DHTTYPE)};

// Topic Prefix
const char *topic_prefix = "agribrain_shravan";

// --- Global Variables ---
WiFiClientSecure espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;
bool autoIrrigation = true; // Auto mode enabled by default
bool motorHealthOK = true;

void setup_wifi() {
  delay(10);
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  espClient.setInsecure();
}

void callback(char *topic, byte *payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++)
    message += (char)payload[i];
  String topicStr = String(topic);

  Serial.printf("Message arrived [%s]: %s\n", topic, message.c_str());

  // Auto Irrigation Toggle
  if (topicStr.endsWith("/control/auto")) {
    autoIrrigation = (message == "ON");
    Serial.printf("Auto-Irrigation: %s\n",
                  autoIrrigation ? "ENABLED" : "DISABLED");
  }
  // Motor Health Control (from Dashboard)
  else if (topicStr.endsWith("/control/motor/health")) {
    motorHealthOK = (message == "OK");
    digitalWrite(healthGreenPin, motorHealthOK ? HIGH : LOW);
    digitalWrite(healthRedPin, motorHealthOK ? LOW : HIGH);
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting HiveMQ Cloud connection...");
    String clientId = "AgriBrain-ESP32-" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      Serial.println("connected");
      String subTopic = String(topic_prefix) + "/control/#";
      client.subscribe(subTopic.c_str());
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  for (int i = 0; i < numRegions; i++) {
    pinMode(valvePins[i], OUTPUT);
    digitalWrite(valvePins[i], LOW);
    dhts[i].begin();
  }

  pinMode(motorPin, OUTPUT);
  pinMode(healthRedPin, OUTPUT);
  pinMode(healthGreenPin, OUTPUT);

  digitalWrite(motorPin, LOW);
  digitalWrite(healthGreenPin, HIGH); // Default OK
  digitalWrite(healthRedPin, LOW);

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected())
    reconnect();
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > 5000) {
    lastMsg = now;
    bool anyValveOn = false;

    for (int i = 0; i < numRegions; i++) {
      float h = dhts[i].readHumidity();
      float t = dhts[i].readTemperature();

      if (isnan(h) || isnan(t)) {
        Serial.printf("Failed to read DHT from region %d\n", i + 1);
        continue;
      }

      // Auto-Irrigation Logic
      if (autoIrrigation) {
        if (h < 50.0) {
          digitalWrite(valvePins[i], HIGH);
        } else {
          digitalWrite(valvePins[i], LOW);
        }
      }

      if (digitalRead(valvePins[i]) == HIGH)
        anyValveOn = true;

      // Publish Telemetry
      StaticJsonDocument<128> doc;
      doc["region"] = i + 1;
      doc["humidity"] = h;
      doc["temp"] = t;
      doc["valve"] = (digitalRead(valvePins[i]) == HIGH);

      char buffer[128];
      serializeJson(doc, buffer);
      String topic =
          String(topic_prefix) + "/telemetry/region/" + String(i + 1);
      client.publish(topic.c_str(), buffer);
    }

    // Motor Logic: On if any valve is on
    digitalWrite(motorPin, anyValveOn ? HIGH : LOW);

    // Motor Telemetry
    StaticJsonDocument<128> motorDoc;
    motorDoc["state"] = anyValveOn ? "ON" : "OFF";
    motorDoc["health"] = motorHealthOK ? "OK" : "FAULT";

    char motorBuffer[128];
    serializeJson(motorDoc, motorBuffer);
    String motorTopic = String(topic_prefix) + "/telemetry/motor";
    client.publish(motorTopic.c_str(), motorBuffer);

    Serial.println("Telemetry published.");
  }
}
