import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../mqtt_service.dart';
import 'dart:convert';

class DashboardScreen extends StatefulWidget {
  @override
  _DashboardScreenState createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final AgriBrainMqttService mqttService = AgriBrainMqttService();
  
  double moisture = 0.0;
  double pressure = 0.0;
  double health = 100.0;
  List<bool> gridStatus = List.generate(10, (index) => false);
  List<int> irrigationQueue = [];
  int? activeGridId;
  
  Map<String, dynamic>? visionResult;
  String? geminiResponse;
  List<String> logs = [];

  @override
  void initState() {
    super.initState();
    _setupMqtt();
  }

  void _setupMqtt() async {
    bool connected = await mqttService.connect();
    if (connected) {
      mqttService.client.subscribe('${mqttService.topicPrefix}/telemetry/grid/+', MqttQos.atMostOnce);
      mqttService.client.subscribe('${mqttService.topicPrefix}/telemetry/motor', MqttQos.atMostOnce);
      mqttService.client.subscribe('${mqttService.topicPrefix}/ai/vision/result', MqttQos.atMostOnce);
      mqttService.client.subscribe('${mqttService.topicPrefix}/ai/gemini/response', MqttQos.atMostOnce);
      mqttService.client.subscribe('${mqttService.topicPrefix}/ledger/update', MqttQos.atMostOnce);
      mqttService.client.subscribe('${mqttService.topicPrefix}/control/grid/+', MqttQos.atMostOnce);

      mqttService.messagesStream?.listen((List<MqttReceivedMessage<MqttMessage>> c) {
        final recMess = c[0].payload as MqttPublishMessage;
        final String topic = c[0].topic;
        final String pt = MqttPublishPayload.bytesToStringAsString(recMess.payload.message);
        
        setState(() {
          if (topic.contains('telemetry/motor')) {
            final data = jsonDecode(pt);
            pressure = (data['pressure'] ?? 0.0).toDouble();
          } else if (topic.contains('telemetry/grid')) {
            final data = jsonDecode(pt);
            moisture = (data['moisture'] ?? 0.0).toDouble();
          } else if (topic.contains('control/grid')) {
             // Track real-time status from commands
             int id = int.parse(topic.split('/').last);
             gridStatus[id-1] = (pt == "ON");
             if (pt == "ON") activeGridId = id;
             else if (activeGridId == id) activeGridId = null;
          } else if (topic.contains('ai/vision/result')) {
            visionResult = jsonDecode(pt);
          } else if (topic.contains('ai/gemini/response')) {
            geminiResponse = jsonDecode(pt)['response'];
          } else if (topic.contains('ledger/update')) {
            final data = jsonDecode(pt);
            logs.insert(0, "${data['action']} ${data['quantity']} ${data['material']}");
          }
        });
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF0A0E0A),
      body: SafeArea(
        child: CustomScrollView(
          slivers: [
            _buildAppBar(),
            SliverToBoxAdapter(child: _buildHealthGrid()),
            SliverToBoxAdapter(child: _build10GridMap()),
            SliverToBoxAdapter(child: _buildAIAdvisorSection()),
            SliverToBoxAdapter(child: _buildSensorHighlights()),
            SliverToBoxAdapter(child: _buildVoiceLedger()),
            SliverPadding(padding: EdgeInsets.only(bottom: 40)),
          ],
        ),
      ),
    );
  }

  Widget _buildAppBar() {
    return SliverAppBar(
      backgroundColor: Colors.transparent,
      title: Text("AGRI-BRAIN", style: GoogleFonts.outfit(fontWeight: FontWeight.bold, color: Colors.greenAccent)),
      actions: [
        IconButton(icon: Icon(Icons.camera_alt_outlined, color: Colors.greenAccent), 
          onPressed: () {
            // Mock Vision Trigger
            final builder = MqttClientPayloadBuilder();
            builder.addString(jsonEncode({"camera_id": "Field_01", "crop": "Tomato"}));
            mqttService.client.publishMessage('${mqttService.topicPrefix}/ai/vision/request', MqttQos.atMostOnce, builder.payload!);
          }),
        CircleAvatar(backgroundColor: Colors.green.withOpacity(0.2), child: Icon(Icons.person, color: Colors.greenAccent)),
        SizedBox(width: 20),
      ],
    );
  }

  Widget _build10GridMap() {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(30),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("FIELD GRID MAP", style: GoogleFonts.outfit(color: Colors.white54, letterSpacing: 2, fontSize: 12)),
              if (activeGridId != null) 
                Text("WATERING GRID $activeGridId", style: GoogleFonts.outfit(color: Colors.blueAccent, fontSize: 10, fontWeight: FontWeight.bold)),
            ],
          ),
          SizedBox(height: 15),
          GridView.builder(
            shrinkWrap: true,
            physics: NeverScrollableScrollPhysics(),
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 5,
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
            ),
            itemCount: 10,
            itemBuilder: (context, index) {
              bool isActive = gridStatus[index];
              return AnimatedContainer(
                duration: Duration(milliseconds: 500),
                decoration: BoxDecoration(
                  color: isActive ? Colors.blueAccent.withOpacity(0.4) : Colors.green.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: isActive ? Colors.blueAccent : Colors.white10),
                  boxShadow: isActive ? [BoxShadow(color: Colors.blueAccent.withOpacity(0.2), blurRadius: 10)] : [],
                ),
                child: Center(
                  child: Text("${index + 1}", 
                    style: GoogleFonts.outfit(color: isActive ? Colors.white : Colors.white24, fontWeight: FontWeight.bold)),
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildAIAdvisorSection() {
    return Container(
      margin: EdgeInsets.all(20),
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [Colors.green.withOpacity(0.1), Colors.blue.withOpacity(0.1)]),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.auto_awesome, color: Colors.yellowAccent, size: 18),
              SizedBox(width: 10),
              Text("GEMINI AGRI-ADVISOR", style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.bold)),
            ],
          ),
          SizedBox(height: 15),
          if (visionResult != null) ...[
             Text("Leaf Analysis: ${visionResult!['diagnosis']}", style: GoogleFonts.outfit(color: Colors.greenAccent, fontSize: 14)),
             Text(visionResult!['recommendation'], style: GoogleFonts.outfit(color: Colors.white70, fontSize: 12)),
             SizedBox(height: 15),
          ],
          Text(geminiResponse ?? "Ask me anything about your farm health...", 
            style: GoogleFonts.outfit(color: Colors.white54, fontSize: 13, fontStyle: FontStyle.italic)),
        ],
      ),
    );
  }

  Widget _buildHealthGrid() {
    return Container(
      margin: EdgeInsets.all(20),
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("System Health", style: GoogleFonts.outfit(color: Colors.white, fontSize: 18)),
              Text("${health.toInt()}%", style: GoogleFonts.outfit(color: Colors.greenAccent, fontSize: 24, fontWeight: FontWeight.bold)),
            ],
          ),
          SizedBox(height: 10),
          LinearProgressIndicator(
            value: health / 100,
            backgroundColor: Colors.white12,
            color: health > 70 ? Colors.greenAccent : (health > 40 ? Colors.orange : Colors.red),
            minHeight: 8,
            borderRadius: BorderRadius.circular(5),
          ),
        ],
      ),
    );
  }

  Widget _buildSensorHighlights() {
    return Row(
      children: [
        _sensorCard("Moisture", "$moisture%", Icons.water_drop, Colors.blueAccent),
        _sensorCard("Pressure", "$pressure PSI", Icons.speed, Colors.purpleAccent),
      ],
    );
  }

  Widget _sensorCard(String label, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        margin: EdgeInsets.symmetric(horizontal: 10, vertical: 10),
        padding: EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(25),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color),
            SizedBox(height: 15),
            Text(label, style: GoogleFonts.outfit(color: Colors.white70)),
            Text(value, style: GoogleFonts.outfit(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  Widget _buildValveGrid() {
    return SliverPadding(
      padding: EdgeInsets.symmetric(horizontal: 20),
      sliver: SliverGrid(
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 5,
          mainAxisSpacing: 10,
          crossAxisSpacing: 10,
        ),
        delegate: SliverChildBuilderDelegate(
          (context, index) {
            return GestureDetector(
              onTap: () {
                setState(() => gridStatus[index] = !gridStatus[index]);
                mqttService.toggleGrid(index + 1, gridStatus[index]);
              },
              child: AnimatedContainer(
                duration: Duration(milliseconds: 300),
                decoration: BoxDecoration(
                  color: gridStatus[index] ? Colors.green.withOpacity(0.2) : Colors.white.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(15),
                  border: Border.all(color: gridStatus[index] ? Colors.greenAccent : Colors.white10),
                ),
                child: Center(
                  child: Text("${index + 1}", 
                    style: GoogleFonts.outfit(color: gridStatus[index] ? Colors.greenAccent : Colors.white38, fontWeight: FontWeight.bold)),
                ),
              ),
            );
          },
          childCount: 10,
        ),
      ),
    );
  }

  Widget _buildVoiceLedger() {
    return Container(
      margin: EdgeInsets.all(20),
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.02),
        borderRadius: BorderRadius.circular(30),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("DIGITAL LEDGER", style: GoogleFonts.outfit(color: Colors.white54, letterSpacing: 2)),
          SizedBox(height: 15),
          ...logs.map((log) => ListTile(
            contentPadding: EdgeInsets.zero,
            leading: Icon(Icons.mic_none, color: Colors.greenAccent, size: 20),
            title: Text(log, style: GoogleFonts.outfit(color: Colors.white, fontSize: 14)),
            subtitle: Text("Auto-parsed by AMD Brain", style: GoogleFonts.outfit(color: Colors.white30, fontSize: 10)),
          )).toList(),
          if (logs.isEmpty) Text("No voice logs yet.", style: GoogleFonts.outfit(color: Colors.white24)),
        ],
      ),
    );
  }
}
