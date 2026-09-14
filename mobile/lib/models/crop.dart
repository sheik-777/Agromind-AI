import 'field.dart';

/// Crop profile with requirement bands, so the app can compare
/// CROP REQUIREMENTS vs YOUR FIELD and explain compatibility.
class CropProfile {
  final String name;
  final String category;
  final String season;
  final double phMin;
  final double phMax;
  final double tempMinC;
  final double tempMaxC;
  final double moistureMinPct;
  final double moistureMaxPct;
  final String water;
  final String duration;
  final List<String> nutrients;
  final List<String> diseases;
  final List<String> prevention;
  final String overview;

  const CropProfile({
    required this.name,
    required this.category,
    required this.season,
    required this.phMin,
    required this.phMax,
    required this.tempMinC,
    required this.tempMaxC,
    required this.moistureMinPct,
    required this.moistureMaxPct,
    required this.water,
    required this.duration,
    required this.nutrients,
    required this.diseases,
    required this.prevention,
    required this.overview,
  });
}

class Compatibility {
  final int pct;
  final String verdict; // Compatible | Needs attention | Not recommended
  final List<String> reasons;

  const Compatibility({required this.pct, required this.verdict, required this.reasons});
}

/// Deterministic, explainable compatibility — never a fabricated score:
/// each of pH / temperature / moisture contributes, reasons list every check.
Compatibility compatibilityOf(CropProfile crop, SensorReading field) {
  final reasons = <String>[];
  var score = 0;

  if (field.ph >= crop.phMin && field.ph <= crop.phMax) {
    score += 34;
    reasons.add('pH ${field.ph.toStringAsFixed(1)} inside ${crop.phMin}–${crop.phMax}');
  } else {
    reasons.add('pH ${field.ph.toStringAsFixed(1)} outside ${crop.phMin}–${crop.phMax}');
  }
  if (field.airTempC >= crop.tempMinC && field.airTempC <= crop.tempMaxC) {
    score += 33;
    reasons.add('Temperature ${field.airTempC.toStringAsFixed(1)}°C suits ${crop.tempMinC}–${crop.tempMaxC}°C');
  } else {
    reasons.add('Temperature ${field.airTempC.toStringAsFixed(1)}°C outside ${crop.tempMinC}–${crop.tempMaxC}°C');
  }
  if (field.moisturePct >= crop.moistureMinPct && field.moisturePct <= crop.moistureMaxPct) {
    score += 33;
    reasons.add('Moisture ${field.moisturePct.toStringAsFixed(0)}% suits ${crop.moistureMinPct.toStringAsFixed(0)}–${crop.moistureMaxPct.toStringAsFixed(0)}%');
  } else {
    reasons.add('Moisture ${field.moisturePct.toStringAsFixed(0)}% outside ${crop.moistureMinPct.toStringAsFixed(0)}–${crop.moistureMaxPct.toStringAsFixed(0)}%');
  }
  final verdict = score >= 80
      ? 'Compatible'
      : score >= 50
          ? 'Needs attention'
          : 'Not recommended';
  return Compatibility(pct: score, verdict: verdict, reasons: reasons);
}
