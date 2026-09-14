import 'package:flutter/material.dart';

/// AgroMind design tokens: deep natural greens, soil neutrals, off-white.
/// Semantic: green = healthy, amber = warning, red = critical, blue = weather.
class AgroColors {
  static const forest900 = Color(0xFF1E3F1F);
  static const forest700 = Color(0xFF255D26);
  static const forest600 = Color(0xFF2D752D);
  static const emerald = Color(0xFF10B981);
  static const leaf = Color(0xFF84CC16);
  static const soil = Color(0xFF8A6B4F);
  static const soilDark = Color(0xFF5D4632);
  static const sand = Color(0xFFFAF7F0);
  static const success = Color(0xFF16A34A);
  static const warning = Color(0xFFD97706);
  static const danger = Color(0xFFDC2626);
  static const info = Color(0xFF0284C7);
}

ThemeData buildAgroTheme(Brightness brightness) {
  final dark = brightness == Brightness.dark;
  final scheme = ColorScheme.fromSeed(
    seedColor: AgroColors.forest700,
    brightness: brightness,
    primary: AgroColors.forest700,
    secondary: AgroColors.emerald,
    surface: dark ? const Color(0xFF12140F) : Colors.white,
  );
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: dark ? const Color(0xFF0B0E0A) : AgroColors.sand,
    appBarTheme: AppBarTheme(
      centerTitle: false,
      elevation: 0,
      backgroundColor: Colors.transparent,
      foregroundColor: scheme.onSurface,
      titleTextStyle: TextStyle(
        fontSize: 22,
        fontWeight: FontWeight.w700,
        color: scheme.onSurface,
        letterSpacing: -0.5,
      ),
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(
          color: dark ? const Color(0xFF2A2E26) : const Color(0xFFE7E2D5),
        ),
      ),
      color: dark ? const Color(0xFF151812) : Colors.white,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: dark ? const Color(0xFF1B1F19) : const Color(0xFFF3EFE3),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide.none,
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AgroColors.forest700,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(vertical: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),
  );
}
