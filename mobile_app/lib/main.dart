import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/dashboard_screen.dart';

void main() {
  runApp(AgriBrainApp());
}

class AgriBrainApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Agri-Brain Dashboard',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.green,
        textTheme: GoogleFonts.outfitTextTheme(
          ThemeData.dark().textTheme,
        ),
      ),
      home: DashboardScreen(),
    );
  }
}
