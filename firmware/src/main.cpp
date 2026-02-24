#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>


// --- Configuration ---
const char *ssid = "Wokwi-GUEST";
const char *password = "";
const char *mqtt_server = "broker.hivemq.com";

// --- Constants & Pins ---
const int numGrids = 10;
// Pins matched to diagram.json (TX=1, RX=3, Dxx=xx)
const int relayPins[numGrids] = {1, 3, 2, 4, 5, 18, 19, 21, 22, 23};
const int potPin = 34; // Slide Potentiometer (Moisture)
const int dhtPin = 15; // DHT22 (Rain simulation)

// Topic Prefix (Unique to avoid interference)
const char *topic_prefix = "agribrain_shravan";

// --- Global Objects ---
WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to Wokwi WiFi...");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
}

void callback(char *topic, byte *payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  String topicStr = String(topic);
  Serial.printf("Message arrived [%s]: %s\n", topic, message.c_str());

  // Control Logic: agribrain_shravan/control/grid/{id}
  String controlPrefix = String(topic_prefix) + "/control/grid/";
  if (topicStr.startsWith(controlPrefix)) {
    String gridIdStr = topicStr.substring(controlPrefix.length());

    if (gridIdStr == "all") {
      for (int i = 0; i < numGrids; i++) {
        digitalWrite(relayPins[i], (message == "ON") ? HIGH : LOW);
      }
    } else {
      int gridId = gridIdStr.toInt();
      if (gridId >= 1 && gridId <= numGrids) {
        digitalWrite(relayPins[gridId - 1], (message == "ON") ? HIGH : LOW);
      }
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "AgriBrainClient-" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      String subTopic = String(topic_prefix) + "/control/grid/#";
      client.subscribe(subTopic.c_str());
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  for (int i = 0; i < numGrids; i++) {
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], LOW);
  }

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > 5000) {
    lastMsg = now;

    // Read simulated sensors
    int potValue = analogRead(potPin);
    float moisture = map(potValue, 0, 4095, 0, 1000) / 10.0;

    for (int i = 1; i <= numGrids; i++) {
      StaticJsonDocument<128> doc;
      doc["grid"] = i;
      doc["moisture"] = moisture;
      doc["ph"] = 6.5 + (random(-5, 5) / 10.0);
      doc["rain"] = (moisture > 90.0) ? true : false; // Dummy rain logic

      char buffer[128];
      serializeJson(doc, buffer);

      String topic = String(topic_prefix) + "/telemetry/grid/" + String(i);
      client.publish(topic.c_str(), buffer);
    }
    Serial.println("Telemetry published to HiveMQ.");
  }
}
