import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:table_calendar/table_calendar.dart';
import 'package:shared_preferences/shared_preferences.dart';

const kBg        = Color(0xFF0A1A0C);
const kCard      = Color(0xFF0F2010);
const kBorder    = Color(0xFF1E3A20);
const kGreenNeon = Color(0xFF39FF52);
const kText      = Color(0xFFD4EDDA);
const kTextDim   = Color(0xFF5A8A62);

class CalendarScreen extends StatefulWidget {
  const CalendarScreen({super.key});

  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  DateTime _focusedDay = DateTime.now();
  DateTime? _selectedDay;

  // Map of Date -> List of events/inventory items
  Map<DateTime, List<Map<String, dynamic>>> _events = {};

  final TextEditingController _noteCtrl = TextEditingController();
  final TextEditingController _qtyCtrl = TextEditingController();

  String _selectedType = 'Inventory';
  final List<String> _types = ['Inventory', 'Note', 'Harvest', 'Task'];

  @override
  void initState() {
    super.initState();
    _selectedDay = _focusedDay;
    _loadEvents();
  }

  // Generate a strict midnight DateTime for map keys
  DateTime _stripTime(DateTime d) => DateTime.utc(d.year, d.month, d.day);

  Future<void> _loadEvents() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString('agri_events') ?? '{}';
    final Map<String, dynamic> rawMap = jsonDecode(jsonString);

    setState(() {
      _events = rawMap.map((key, value) {
        final date = DateTime.parse(key);
        final list = List<Map<String, dynamic>>.from(value);
        return MapEntry(_stripTime(date), list);
      });
    });
  }

  Future<void> _saveEvents() async {
    final prefs = await SharedPreferences.getInstance();
    final Map<String, dynamic> mapToSave = _events.map((key, value) => MapEntry(key.toIso8601String(), value));
    await prefs.setString('agri_events', jsonEncode(mapToSave));
  }

  List<Map<String, dynamic>> _getEventsForDay(DateTime day) {
    return _events[_stripTime(day)] ?? [];
  }

  void _addEvent() {
    if (_noteCtrl.text.isEmpty) return;
    final dayKey = _stripTime(_selectedDay ?? _focusedDay);

    final newEvent = {
      'type': _selectedType,
      'note': _noteCtrl.text,
      'qty': _qtyCtrl.text.isNotEmpty ? _qtyCtrl.text : null,
      'time': DateTime.now().toIso8601String(),
    };

    setState(() {
      if (_events[dayKey] != null) {
        _events[dayKey]!.add(newEvent);
      } else {
        _events[dayKey] = [newEvent];
      }
    });

    _noteCtrl.clear();
    _qtyCtrl.clear();
    _saveEvents();
    Navigator.pop(context); // close sheet
  }

  void _deleteEvent(DateTime day, int index) {
    setState(() {
      final key = _stripTime(day);
      _events[key]?.removeAt(index);
      if (_events[key]?.isEmpty ?? false) {
        _events.remove(key);
      }
    });
    _saveEvents();
  }

  void _showAddSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (BuildContext context, StateSetter setModalState) {
          return Padding(
            padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom),
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: const BoxDecoration(
                color: kCard,
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                border: Border(top: BorderSide(color: kBorder, width: 2)),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Add to ${[
                    "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                  ][_selectedDay!.month - 1]} ${_selectedDay!.day}', 
                    style: GoogleFonts.outfit(color: kGreenNeon, fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  
                  // Type chips
                  Wrap(
                    spacing: 8,
                    children: _types.map((t) => ChoiceChip(
                      label: Text(t, style: GoogleFonts.outfit(fontSize: 12)),
                      selected: _selectedType == t,
                      onSelected: (val) { if (val) setModalState(() => _selectedType = t); },
                      selectedColor: kGreenNeon.withOpacity(0.2),
                      backgroundColor: kBg,
                      labelStyle: TextStyle(color: _selectedType == t ? kGreenNeon : kTextDim),
                      side: BorderSide(color: _selectedType == t ? kGreenNeon : kBorder),
                    )).toList(),
                  ),
                  const SizedBox(height: 16),

                  TextField(
                    controller: _noteCtrl,
                    style: GoogleFonts.outfit(color: kText),
                    decoration: InputDecoration(
                      labelText: _selectedType == 'Inventory' ? 'Item name (e.g. NPK Fertilizer)' : 'Description',
                      labelStyle: const TextStyle(color: kTextDim),
                      enabledBorder: const OutlineInputBorder(borderSide: BorderSide(color: kBorder)),
                      focusedBorder: const OutlineInputBorder(borderSide: BorderSide(color: kGreenNeon)),
                    ),
                  ),
                  const SizedBox(height: 12),
                  
                  if (_selectedType == 'Inventory' || _selectedType == 'Harvest')
                    TextField(
                      controller: _qtyCtrl,
                      style: GoogleFonts.outfit(color: kText),
                      keyboardType: TextInputType.text,
                      decoration: const InputDecoration(
                        labelText: 'Quantity (e.g. 50 kg, 2 bags)',
                        labelStyle: TextStyle(color: kTextDim),
                        enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: kBorder)),
                        focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: kGreenNeon)),
                      ),
                    ),

                  const SizedBox(height: 24),
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF2D5A27),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onPressed: _addEvent,
                      child: Text('Save Entry', style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            ),
          );
        }
      ),
    );
  }

  IconData _getIconForType(String type) {
    if (type == 'Inventory') return Icons.inventory_2_outlined;
    if (type == 'Harvest') return Icons.agriculture_outlined;
    if (type == 'Task') return Icons.check_circle_outline;
    return Icons.notes;
  }
  
  Color _getColorForType(String type) {
    if (type == 'Inventory') return const Color(0xFF3DAAFF);
    if (type == 'Harvest') return const Color(0xFFF9C74F);
    if (type == 'Task') return const Color(0xFFF7941D);
    return kGreenNeon;
  }

  @override
  void dispose() {
    _noteCtrl.dispose();
    _qtyCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final todayEvents = _getEventsForDay(_selectedDay ?? _focusedDay);

    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        title: Text('Farm Calendar', style: GoogleFonts.outfit(fontWeight: FontWeight.bold, color: kGreenNeon)),
        backgroundColor: kBg,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.add_box, color: kGreenNeon),
            onPressed: _showAddSheet,
          )
        ],
      ),
      body: Column(
        children: [
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: kCard,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: kBorder),
            ),
            child: TableCalendar(
              firstDay: DateTime.utc(2020, 1, 1),
              lastDay: DateTime.utc(2030, 12, 31),
              focusedDay: _focusedDay,
              selectedDayPredicate: (day) => isSameDay(_selectedDay, day),
              onDaySelected: (selectedDay, focusedDay) {
                setState(() {
                  _selectedDay = selectedDay;
                  _focusedDay = focusedDay;
                });
              },
              eventLoader: _getEventsForDay,
              calendarStyle: CalendarStyle(
                defaultTextStyle: const TextStyle(color: kText),
                weekendTextStyle: TextStyle(color: kText.withOpacity(0.7)),
                outsideTextStyle: const TextStyle(color: kTextDim),
                selectedDecoration: const BoxDecoration(color: kGreenNeon, shape: BoxShape.circle),
                selectedTextStyle: const TextStyle(color: kBg, fontWeight: FontWeight.bold),
                todayDecoration: BoxDecoration(color: kGreenNeon.withOpacity(0.2), shape: BoxShape.circle, border: Border.all(color: kGreenNeon)),
                todayTextStyle: const TextStyle(color: kGreenNeon, fontWeight: FontWeight.bold),
                markerDecoration: const BoxDecoration(color: Color(0xFFF9C74F), shape: BoxShape.circle),
              ),
              headerStyle: HeaderStyle(
                titleTextStyle: GoogleFonts.outfit(color: kText, fontSize: 16, fontWeight: FontWeight.bold),
                formatButtonVisible: false,
                leftChevronIcon: const Icon(Icons.chevron_left, color: kGreenNeon),
                rightChevronIcon: const Icon(Icons.chevron_right, color: kGreenNeon),
              ),
            ),
          ),
          
          Expanded(
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Daily Log', style: GoogleFonts.outfit(color: kTextDim, fontSize: 14)),
                      if (todayEvents.isNotEmpty)
                        Text('${todayEvents.length} items', style: GoogleFonts.outfit(color: kTextDim, fontSize: 12)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  
                  if (todayEvents.isEmpty)
                    Expanded(
                      child: Center(
                        child: Text('No records for this date.', style: GoogleFonts.outfit(color: kTextDim)),
                      ),
                    )
                  else
                    Expanded(
                      child: ListView.builder(
                        itemCount: todayEvents.length,
                        itemBuilder: (ctx, i) {
                          final e = todayEvents[i];
                          final c = _getColorForType(e['type']);
                          return Container(
                            margin: const EdgeInsets.only(bottom: 12),
                            decoration: BoxDecoration(
                              color: kCard,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(color: c.withOpacity(0.3)),
                            ),
                            child: ListTile(
                              leading: Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(color: c.withOpacity(0.1), shape: BoxShape.circle),
                                child: Icon(_getIconForType(e['type']), color: c, size: 20),
                              ),
                              title: Text(e['note'], style: GoogleFonts.outfit(color: kText, fontWeight: FontWeight.w600)),
                              subtitle: e['qty'] != null 
                                  ? Text('Qty: ${e['qty']}', style: GoogleFonts.outfit(color: c.withOpacity(0.8), fontSize: 12))
                                  : null,
                              trailing: IconButton(
                                icon: const Icon(Icons.delete_outline, color: kTextDim, size: 18),
                                onPressed: () => _deleteEvent(_selectedDay ?? _focusedDay, i),
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFF2D5A27),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        onPressed: _showAddSheet,
        child: const Icon(Icons.add, color: kGreenNeon),
      ),
    );
  }
}
