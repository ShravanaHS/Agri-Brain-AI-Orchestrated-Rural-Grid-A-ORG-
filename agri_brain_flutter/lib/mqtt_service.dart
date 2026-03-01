import 'dart:convert';
import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';

class AgriBrainMqttService {
  late MqttServerClient client;
  final String server = '33712c7cb7174024b63e809028448b03.s1.eu.hivemq.cloud';
  final String topicPrefix = 'agribrain_shravan';
  final int port = 8883;
  final String username = 'agribrain';
  final String password = '#Shs_2838';

  AgriBrainMqttService() {
    String clientId = 'AgriBrainApp_${DateTime.now().millisecondsSinceEpoch}';
    client = MqttServerClient(server, clientId);
    client.port = port;
    client.secure = true; // Enable TLS
    client.logging(on: false);
    client.keepAlivePeriod = 20;
    client.onDisconnected = onDisconnected;
    client.onConnected = onConnected;
    client.onSubscribed = onSubscribed;
  }

  Future<bool> connect() async {
    try {
      await client.connect(username, password);
      return true;
    } catch (e) {
      print('MQTT Exception: $e');
      client.disconnect();
      return false;
    }
  }

  void onConnected() {
    print('Connected to HiveMQ Public Broker');
    // Subscribe to all telemetry
    client.subscribe('$topicPrefix/telemetry/grid/#', MqttQos.atMostOnce);
  }

  void onDisconnected() {
    print('Disconnected from Broker');
  }

  void onSubscribed(String topic) {
    print('Subscribed to: $topic');
  }

  void toggleGrid(int gridId, bool status) {
    final builder = MqttClientPayloadBuilder();
    builder.addString(status ? 'ON' : 'OFF');
    
    String topic = '$topicPrefix/control/grid/$gridId';
    client.publishMessage(topic, MqttQos.atMostOnce, builder.payload!);
    print('Published: $topic -> ${status ? 'ON' : 'OFF'}');
  }

  Stream<List<MqttReceivedMessage<MqttMessage>>>? get messagesStream => client.updates;

  // Helper to parse sensor data
  Map<String, dynamic> parseTelemetry(String payload) {
    return jsonDecode(payload);
  }
}
