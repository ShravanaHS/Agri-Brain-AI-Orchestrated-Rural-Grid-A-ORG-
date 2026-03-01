import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';
import '../mqtt_service.dart';
import 'dart:convert';

// ── Colour palette exactly matching web dashboard ──
const kBg        = Color(0xFF0A1A0C);
const kCard      = Color(0xFF0F2010);
const kBorder    = Color(0xFF1E3A20);
const kGreenNeon = Color(0xFF39FF52);
const kGreenMid  = Color(0xFF22c55e);
const kWaterBlue = Color(0xFF3DAAFF);
const kGold      = Color(0xFFF9C74F);
const kAmber     = Color(0xFFF7941D);
const kRed       = Color(0xFFED1C24);
const kText      = Color(0xFFD4EDDA);
const kTextDim   = Color(0xFF5A8A62);

class DashboardScreen extends StatefulWidget {
  @override _DashboardScreenState createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen>
    with SingleTickerProviderStateMixin {

  final AgriBrainMqttService mqttService = AgriBrainMqttService();

  // Hero stats
  double avgHumidity  = 0;
  double avgTemp      = 0;
  double pipePressure = 0;
  String pumpState    = 'STANDBY';

  // 4-region state  (index 0-3 = Region 1-4)
  final List<Map<String, dynamic>> regions = [
    {'name': 'R1 — Wheat',    'humidity': 0.0, 'temp': 0.0, 'state': 'idle', 'crop': '🌾'},
    {'name': 'R2 — Corn',     'humidity': 0.0, 'temp': 0.0, 'state': 'idle', 'crop': '🌽'},
    {'name': 'R3 — Tomato',   'humidity': 0.0, 'temp': 0.0, 'state': 'idle', 'crop': '🍅'},
    {'name': 'R4 — Sunflower','humidity': 0.0, 'temp': 0.0, 'state': 'idle', 'crop': '🌻'},
  ];

  // Chat / Gemini
  final List<Map<String, String>> chatMessages = [];
  final TextEditingController _chatCtrl = TextEditingController();

  // Ledger
  final List<Map<String, dynamic>> ledgerEntries = [];

  bool mqttConnected = false;
  bool gatewayOnline = false;
  bool autoMode      = false;

  // manual irrigation modal
  int?    _modalRegion;
  int     _modalMinutes = 10;
  bool    _modalVisible = false;

  late AnimationController _pulseCtrl;
  late Animation<double>   _pulseAnim;

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(vsync: this, duration: const Duration(seconds: 1))
      ..repeat(reverse: true);
    _pulseAnim = Tween<double>(begin: 0.6, end: 1.0).animate(_pulseCtrl);

    chatMessages.add({'role': 'ai',
      'msg': "Hello, Farmer! I'm Agri-Gemini. Your smart farm AI advisor.\n"
             "Tap a field region to irrigate it, or ask me anything — crop health, soil, pest control…"});
    _connectMqtt();
  }

  void _connectMqtt() async {
    bool ok = await mqttService.connect();
    setState(() => mqttConnected = ok);
    if (!ok) return;

    final c = mqttService.client;
    final tp = mqttService.topicPrefix;
    c.subscribe('$tp/telemetry/region/+', MqttQos.atMostOnce);
    c.subscribe('$tp/telemetry/motor',    MqttQos.atMostOnce);
    c.subscribe('$tp/control/region/+',   MqttQos.atMostOnce);
    c.subscribe('$tp/ai/gemini/response', MqttQos.atMostOnce);
    c.subscribe('$tp/ledger/update',      MqttQos.atMostOnce);
    c.subscribe('$tp/heartbeat',          MqttQos.atMostOnce);

    mqttService.messagesStream?.listen((List<MqttReceivedMessage<MqttMessage>> msgs) {
      final rec   = msgs[0].payload as MqttPublishMessage;
      final topic = msgs[0].topic;
      final pt    = MqttPublishPayload.bytesToStringAsString(rec.payload.message);

      setState(() {
        if (topic.contains('telemetry/region')) {
          final id  = int.tryParse(topic.split('/').last) ?? 1;
          final idx = (id - 1).clamp(0, 3);
          try {
            final d = jsonDecode(pt);
            regions[idx]['humidity'] = (d['humidity'] ?? d['moisture'] ?? 0).toDouble();
            regions[idx]['temp']     = (d['temperature'] ?? d['temp'] ?? 0).toDouble();
            _recalcHero();
          } catch (_) {}
        } else if (topic.contains('telemetry/motor')) {
          try {
            final d = jsonDecode(pt);
            pipePressure = (d['pressure'] ?? d['psi'] ?? 0).toDouble();
            pumpState    = (d['state'] ?? 'STANDBY').toString().toUpperCase();
          } catch (_) {}
        } else if (topic.contains('control/region')) {
          final id  = int.tryParse(topic.split('/').last) ?? 1;
          final idx = (id - 1).clamp(0, 3);
          if (pt == 'ON')  regions[idx]['state'] = 'irrigating';
          if (pt == 'OFF') regions[idx]['state'] = 'idle';
        } else if (topic.contains('ai/gemini/response')) {
          try {
            final d = jsonDecode(pt);
            chatMessages.add({'role': 'ai', 'msg': d['response'] ?? pt});
          } catch (_) { chatMessages.add({'role': 'ai', 'msg': pt}); }
        } else if (topic.contains('ledger/update')) {
          try {
            final d = jsonDecode(pt);
            ledgerEntries.insert(0, d);
          } catch (_) {}
        } else if (topic.contains('heartbeat')) {
          gatewayOnline = true;
        }
      });
    });
  }

  void _recalcHero() {
    avgHumidity = regions.fold(0.0, (s, r) => s + (r['humidity'] as double)) / 4;
    avgTemp     = regions.fold(0.0, (s, r) => s + (r['temp'] as double)) / 4;
  }

  void _sendChat(String msg) {
    if (msg.trim().isEmpty) return;
    setState(() => chatMessages.add({'role': 'user', 'msg': msg}));
    _chatCtrl.clear();
    final b = MqttClientPayloadBuilder()
      ..addString(jsonEncode({'query': msg, 'source': 'mobile'}));
    mqttService.client.publishMessage(
        '${mqttService.topicPrefix}/voice_command', MqttQos.atMostOnce, b.payload!);
    ledgerEntries.insert(0, {'action': 'Query', 'material': msg, 'quantity': ''});
  }

  void _irrigate(int regionIndex, int minutes) {
    final id = regionIndex + 1;
    final b  = MqttClientPayloadBuilder()
      ..addString(jsonEncode({'region': id, 'duration': minutes * 60, 'source': 'mobile'}));
    mqttService.client.publishMessage(
        '${mqttService.topicPrefix}/control/region/$id', MqttQos.atMostOnce, b.payload!);
    setState(() {
      regions[regionIndex]['state'] = 'irrigating';
      ledgerEntries.insert(0, {
        'action': 'Irrigate', 'quantity': '$minutes min',
        'material': regions[regionIndex]['name']});
    });
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    _chatCtrl.dispose();
    super.dispose();
  }

  // ════════════════════ BUILD ════════════════════
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      body: Stack(
        children: [
          // Main scrollable content
          SafeArea(
            child: CustomScrollView(
              slivers: [
                _buildAppBar(),
                SliverToBoxAdapter(child: _buildStatusBar()),
                SliverToBoxAdapter(child: _buildHeroBanner()),
                SliverToBoxAdapter(child: _buildFieldMap()),
                SliverToBoxAdapter(child: _buildChat()),
                SliverToBoxAdapter(child: _buildLedger()),
                const SliverPadding(padding: EdgeInsets.only(bottom: 32)),
              ],
            ),
          ),
          // Manual irrigation modal
          if (_modalVisible) _buildModal(),
        ],
      ),
    );
  }

  // ── App Bar ──────────────────────────────────────
  Widget _buildAppBar() {
    return SliverAppBar(
      backgroundColor: kBg,
      floating: true,
      elevation: 0,
      title: Row(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Image.asset('assets/images/logo.png', width: 36, height: 36, fit: BoxFit.cover),
          ),
          const SizedBox(width: 10),
          RichText(
            text: TextSpan(
              style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.w800, color: kGreenNeon),
              children: const [
                TextSpan(text: 'AGRI'),
                TextSpan(text: '·BRAIN', style: TextStyle(color: kGold)),
              ],
            ),
          ),
        ],
      ),
      actions: [
        // Auto/Manual toggle
        GestureDetector(
          onTap: () => setState(() => autoMode = !autoMode),
          child: Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: autoMode ? kGreenNeon : kTextDim),
              color: autoMode ? kGreenNeon.withOpacity(0.15) : Colors.transparent,
            ),
            child: Text(autoMode ? 'AUTO' : 'MANUAL',
                style: GoogleFonts.outfit(fontSize: 11, fontWeight: FontWeight.w700,
                    color: autoMode ? kGreenNeon : kTextDim)),
          ),
        ),
      ],
    );
  }

  // ── Status Bar ───────────────────────────────────
  Widget _buildStatusBar() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Row(
        children: [
          _statusPill('MQTT', mqttConnected ? 'ONLINE' : 'CONNECTING',
              mqttConnected ? kGreenNeon : kAmber),
          const SizedBox(width: 8),
          _statusPill('BRAIN', gatewayOnline ? 'ONLINE' : 'OFFLINE',
              gatewayOnline ? kGreenNeon : kRed),
        ],
      ),
    );
  }

  Widget _statusPill(String label, String val, Color col) {
    return AnimatedBuilder(
      animation: _pulseAnim,
      builder: (_, __) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: col.withOpacity(0.4)),
          color: col.withOpacity(0.08),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(width: 6, height: 6,
                decoration: BoxDecoration(shape: BoxShape.circle,
                    color: col.withOpacity(_pulseAnim.value))),
            const SizedBox(width: 6),
            Text('$label  ', style: GoogleFonts.outfit(fontSize: 10, color: kTextDim)),
            Text(val, style: GoogleFonts.outfit(fontSize: 10, fontWeight: FontWeight.w700, color: col)),
          ],
        ),
      ),
    );
  }

  // ── Hero Banner ──────────────────────────────────
  Widget _buildHeroBanner() {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft, end: Alignment.bottomRight,
          colors: [const Color(0xFF0F2A12), const Color(0xFF0A1A0C)],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: kBorder),
      ),
      child: Row(
        children: [
          _heroStat('SOIL HUM.', '${avgHumidity.toStringAsFixed(0)}%', kWaterBlue, Icons.water_drop),
          _heroDivider(),
          _heroStat('TEMP', '${avgTemp.toStringAsFixed(0)}°C', kGold, Icons.thermostat),
          _heroDivider(),
          _heroStat('PUMP', pumpState, kGreenNeon, Icons.settings),
          _heroDivider(),
          _heroStat('PSI', '${pipePressure.toStringAsFixed(1)}', kGreenMid, Icons.speed),
        ],
      ),
    );
  }

  Widget _heroStat(String label, String val, Color col, IconData icon) {
    return Expanded(
      child: Column(
        children: [
          Icon(icon, color: col, size: 22),
          const SizedBox(height: 6),
          Text(label,
              style: GoogleFonts.outfit(fontSize: 9, color: kTextDim,
                  letterSpacing: 1.2, fontWeight: FontWeight.w600)),
          const SizedBox(height: 2),
          FittedBox(
            child: Text(val,
                style: GoogleFonts.outfit(fontSize: 18,
                    fontWeight: FontWeight.w800, color: col)),
          ),
        ],
      ),
    );
  }

  Widget _heroDivider() =>
      Container(width: 1, height: 48, color: kBorder);

  // ── Field Map — 4 Regions ────────────────────────
  Widget _buildFieldMap() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: _cardDecor(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _sectionTitle('FIELD MAP', '4-Zone Smart Irrigation', Icons.map),
          const SizedBox(height: 14),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
              childAspectRatio: 1.5,
            ),
            itemCount: 4,
            itemBuilder: (_, i) => _buildRegionCard(i),
          ),
          const SizedBox(height: 12),
          // Legend
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _legendDot(kTextDim, 'IDLE'),
              _legendDot(kWaterBlue, 'IRRIGATING'),
              _legendDot(kRed, 'DRY ALERT'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRegionCard(int idx) {
    final r       = regions[idx];
    final state   = r['state'] as String;
    final hum     = r['humidity'] as double;
    final isDry   = hum < 30 && hum > 0;
    final isWet   = state == 'irrigating';
    final col     = isWet ? kWaterBlue : isDry ? kRed : kGreenMid;

    return GestureDetector(
      onTap: () {
        if (!autoMode) {
          setState(() {
            _modalRegion  = idx;
            _modalMinutes = 10;
            _modalVisible = true;
          });
        }
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 500),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: col.withOpacity(isWet ? 0.8 : 0.3), width: isWet ? 1.5 : 1),
          color: col.withOpacity(isWet ? 0.15 : 0.05),
          boxShadow: isWet
              ? [BoxShadow(color: kWaterBlue.withOpacity(0.2), blurRadius: 12)]
              : [],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(r['crop'] as String, style: const TextStyle(fontSize: 22)),
                if (isWet) Icon(Icons.water_drop, color: kWaterBlue, size: 14),
              ],
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(r['name'] as String,
                    style: GoogleFonts.outfit(fontSize: 11, fontWeight: FontWeight.w700, color: kText)),
                const SizedBox(height: 2),
                Row(
                  children: [
                    Icon(Icons.water_drop, size: 10, color: kWaterBlue),
                    const SizedBox(width: 3),
                    Text('${hum.toStringAsFixed(0)}%  ',
                        style: GoogleFonts.outfit(fontSize: 10, color: kTextDim)),
                    Icon(Icons.thermostat, size: 10, color: kGold),
                    const SizedBox(width: 3),
                    Text('${(r['temp'] as double).toStringAsFixed(0)}°C',
                        style: GoogleFonts.outfit(fontSize: 10, color: kTextDim)),
                  ],
                ),
                const SizedBox(height: 4),
                // Humidity bar
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: (hum / 100).clamp(0.0, 1.0),
                    backgroundColor: kBorder,
                    color: col,
                    minHeight: 4,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ── Gemini Chat ──────────────────────────────────
  Widget _buildChat() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: _cardDecor(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _sectionTitle('AGRI-GEMINI', 'AI Farm Advisor', Icons.auto_awesome),
          const SizedBox(height: 12),
          Container(
            height: 200,
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: Colors.black26,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: kBorder),
            ),
            child: ListView.builder(
              reverse: true,
              itemCount: chatMessages.length,
              itemBuilder: (_, i) {
                final m   = chatMessages[chatMessages.length - 1 - i];
                final isAI = m['role'] == 'ai';
                return Align(
                  alignment: isAI ? Alignment.centerLeft : Alignment.centerRight,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.7),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      color: isAI
                          ? kGreenNeon.withOpacity(0.08)
                          : kWaterBlue.withOpacity(0.15),
                      border: Border.all(
                          color: isAI ? kGreenNeon.withOpacity(0.2) : kWaterBlue.withOpacity(0.3)),
                    ),
                    child: Text(m['msg'] ?? '',
                        style: GoogleFonts.outfit(
                            fontSize: 12,
                            color: isAI ? kText : Colors.white70)),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(25),
                    border: Border.all(color: kBorder),
                    color: kCard,
                  ),
                  child: TextField(
                    controller: _chatCtrl,
                    style: GoogleFonts.outfit(color: kText, fontSize: 13),
                    decoration: InputDecoration(
                      hintText: 'Ask about soil, crops, weather, pests…',
                      hintStyle: GoogleFonts.outfit(color: kTextDim, fontSize: 12),
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    ),
                    onSubmitted: _sendChat,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: () => _sendChat(_chatCtrl.text),
                child: Container(
                  width: 44, height: 44,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: const LinearGradient(
                        colors: [Color(0xFF2D5A27), Color(0xFF39FF52)]),
                  ),
                  child: const Icon(Icons.send, color: Colors.white, size: 18),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ── Farm Ledger ──────────────────────────────────
  Widget _buildLedger() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: _cardDecor(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _sectionTitle('FARM LEDGER', 'Command & Event Log', Icons.book),
              Text('${ledgerEntries.length} entries',
                  style: GoogleFonts.outfit(fontSize: 11, color: kTextDim)),
            ],
          ),
          const SizedBox(height: 12),
          if (ledgerEntries.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Center(
                child: Text('No farm commands recorded yet.',
                    style: GoogleFonts.outfit(color: kTextDim, fontSize: 12)),
              ),
            )
          else
            ...ledgerEntries.take(8).map((e) => _ledgerItem(e)),
        ],
      ),
    );
  }

  Widget _ledgerItem(Map<String, dynamic> e) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(10),
        color: kGreenNeon.withOpacity(0.04),
        border: Border.all(color: kBorder),
      ),
      child: Row(
        children: [
          const Icon(Icons.mic_none, color: kGreenNeon, size: 16),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${e['action'] ?? ''} ${e['quantity'] ?? ''} ${e['material'] ?? ''}',
                    style: GoogleFonts.outfit(
                        color: kText, fontSize: 12, fontWeight: FontWeight.w600)),
                Text('Auto-parsed by AMD Brain',
                    style: GoogleFonts.outfit(color: kTextDim, fontSize: 10)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── Irrigation Modal ─────────────────────────────
  Widget _buildModal() {
    final idx  = _modalRegion!;
    final r    = regions[idx];
    return GestureDetector(
      onTap: () => setState(() => _modalVisible = false),
      child: Container(
        color: Colors.black54,
        child: Center(
          child: GestureDetector(
            onTap: () {}, // prevent close on card tap
            child: Container(
              margin: const EdgeInsets.all(24),
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF0F2010),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: kGreenNeon.withOpacity(0.3)),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(r['crop'] as String, style: const TextStyle(fontSize: 40)),
                  const SizedBox(height: 8),
                  Text('IRRIGATE ${r['name']}',
                      style: GoogleFonts.outfit(
                          color: kGreenNeon, fontSize: 16, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 4),
                  Text('Set water duration for this field zone',
                      style: GoogleFonts.outfit(color: kTextDim, fontSize: 12)),
                  const SizedBox(height: 20),
                  // Presets
                  Wrap(
                    spacing: 8, runSpacing: 8,
                    children: [5, 15, 30, 60].map((m) =>
                        GestureDetector(
                          onTap: () => setState(() => _modalMinutes = m),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                  color: _modalMinutes == m ? kGreenNeon : kBorder),
                              color: _modalMinutes == m
                                  ? kGreenNeon.withOpacity(0.15) : Colors.transparent,
                            ),
                            child: Text('$m min',
                                style: GoogleFonts.outfit(
                                    color: _modalMinutes == m ? kGreenNeon : kTextDim,
                                    fontWeight: FontWeight.w700)),
                          ),
                        )
                    ).toList(),
                  ),
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => setState(() => _modalVisible = false),
                          style: OutlinedButton.styleFrom(
                              side: const BorderSide(color: kBorder),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
                          child: Text('Cancel',
                              style: GoogleFonts.outfit(color: kTextDim)),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () {
                            _irrigate(idx, _modalMinutes);
                            setState(() => _modalVisible = false);
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF2D5A27),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          ),
                          icon: const Icon(Icons.water_drop, color: kWaterBlue, size: 16),
                          label: Text('Start',
                              style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.w700)),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ── Helpers ──────────────────────────────────────
  BoxDecoration _cardDecor() => BoxDecoration(
    color: kCard,
    borderRadius: BorderRadius.circular(20),
    border: Border.all(color: kBorder),
  );

  Widget _sectionTitle(String title, String sub, IconData icon) {
    return Row(
      children: [
        Icon(icon, color: kGreenNeon, size: 18),
        const SizedBox(width: 8),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title,
                style: GoogleFonts.outfit(
                    color: kText, fontSize: 14, fontWeight: FontWeight.w800,
                    letterSpacing: 1.5)),
            Text(sub,
                style: GoogleFonts.outfit(color: kTextDim, fontSize: 10)),
          ],
        ),
      ],
    );
  }

  Widget _legendDot(Color col, String label) {
    return Row(
      children: [
        Container(width: 8, height: 8, decoration: BoxDecoration(
            shape: BoxShape.circle, color: col)),
        const SizedBox(width: 4),
        Text(label, style: GoogleFonts.outfit(fontSize: 10, color: kTextDim)),
      ],
    );
  }
}
