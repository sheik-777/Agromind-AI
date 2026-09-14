import 'package:dio/dio.dart';

class AiAskResult {
  final String intent;
  final List<String> observed;
  final List<dynamic> retrieved;
  final String inferred;
  final String recommended;
  final List<String> sources;
  final bool fieldAvailable;

  AiAskResult({
    required this.intent,
    required this.observed,
    required this.retrieved,
    required this.inferred,
    required this.recommended,
    required this.sources,
    required this.fieldAvailable,
  });

  factory AiAskResult.fromJson(Map<String, dynamic> j) => AiAskResult(
        intent: (j['intent'] ?? 'general').toString(),
        observed: (j['observed'] as List? ?? []).map((e) => e.toString()).toList(),
        retrieved: (j['retrieved_knowledge'] as List? ?? []),
        inferred: (j['inferred'] ?? j['recommended'] ?? '').toString(),
        recommended: (j['recommended'] ?? '').toString(),
        sources: (j['sources'] as List? ?? []).map((e) => e.toString()).toList(),
        fieldAvailable: j['field_available'] == true,
      );
}

class AiService {
  final Dio dio;
  AiService(this.dio);

  Future<AiAskResult> ask(String question) async {
    final res = await dio.post('/ai/ask', data: {'question': question});
    return AiAskResult.fromJson(res.data as Map<String, dynamic>);
  }
}

/// Local deterministic fallback when backend AI not reachable or demo mode.
/// Mirrors server intent + grounding logic so UI never repeats one answer.
class LocalAiEngine {
  static String classify(String q) {
    final l = q.toLowerCase();
    if (RegExp(r'irrigat|water|moist').hasMatch(l)) return 'irrigation';
    if (RegExp(r'yellow|spot|disease|pest|blight|leaf').hasMatch(l)) return 'disease';
    if (RegExp(r'fertiliz|nutrient|manure|urea|nitrogen|potassium|phosphorus').hasMatch(l)) return 'fertilizer';
    if (RegExp(r'soil.*suitable|suitable.*soil|soil.*tomato|ph').hasMatch(l)) return 'soil';
    if (RegExp(r'rain|weather|forecast|temperature').hasMatch(l)) return 'weather';
    if (RegExp(r'which crop|what crop|what should i plant').hasMatch(l)) return 'crop';
    if (RegExp(r'how is my field|field doing|field status').hasMatch(l)) return 'field_status';
    if (RegExp(r'last 5 days|history|changed|trend').hasMatch(l)) return 'historical';
    if (RegExp(r'what should i do today|what to do').hasMatch(l)) return 'action';
    if (RegExp(r'disease.*affect|could.*disease').hasMatch(l)) return 'disease';
    if (RegExp(r'explain.*soil report|latest soil').hasMatch(l)) return 'soil';
    return 'general';
  }

  static Map<String, String> answer(String question, dynamic field, String intent) {
    final m = field?.sensors.moisturePct.toStringAsFixed(0) ?? '—';
    final t = field?.sensors.airTempC.toStringAsFixed(1) ?? '—';
    final h = field?.sensors.humidityPct.toStringAsFixed(0) ?? '—';
    final ph = field?.sensors.ph.toStringAsFixed(1) ?? '—';
    final obs = 'Moisture $m% · Temp $t°C · Humidity $h% · pH $ph';

    String inferred;
    String rec;
    switch (intent) {
      case 'irrigation':
        inferred = field != null && (field.sensors.moisturePct as double) < 35
            ? 'Moisture below 35% band; rain probability and last irrigation matter next.'
            : 'Moisture inside bands for now.';
        rec = field != null && (field.sensors.moisturePct as double) < 35
            ? 'A morning cycle is reasonable — verify no significant rain is forecast in next 12h.'
            : 'Hold schedule; re-check after next telemetry.';
        break;
      case 'disease':
        inferred = 'Yellowing alone is not a diagnosis. Candidates: nitrogen deficiency, water stress, disease, temperature stress — each checked against visual, moisture, pH, humidity.';
        rec = 'Upload a clear leaf photo (both sides) + share soil N/P/K if available. I will compare environmental evidence before ranking causes.';
        break;
      case 'fertilizer':
        inferred = 'Recommending fertilizer needs soil report N/P/K, crop and growth stage.';
        rec = 'Share your lab pH/N/P/K and crop; I will pull retrieved dose ranges and timing. Without them I give only general guidance, never a dose.';
        break;
      case 'soil':
        inferred = 'Suitability is pH, nutrients, moisture and season vs crop bands.';
        rec = 'For tomato: pH 6.0–7.0, steady moisture, calcium for blossom-end rot. Upload your report for a ranked compatibility.';
        break;
      case 'weather':
        inferred = 'Weather is forecast + rain probability from the backend (Open-Meteo) when live.';
        rec = 'If rain >50% in 24h, consider delaying irrigation. Field history and moisture decide together.';
        break;
      case 'crop':
        inferred = 'Ranking uses soil parameters + field bands against 1200-crop dataset.';
        rec = 'Compatible today (demo bands): Rice if wet, chickpea if dry; tomato needs tight moisture. Real ranking arrives with your report.';
        break;
      case 'field_status':
        inferred = 'Current snapshot above.';
        rec = 'Watch 5-day moisture trend; today looks ${field != null ? "stable" : "unknown — connect a sensor"}';
        break;
      case 'historical':
        inferred = '5-day trend shows moisture and temp series.';
        rec = 'Falling moisture + warm temps → rising irrigation need. Rising humidity + warm nights → watch for blight conditions.';
        break;
      case 'action':
        inferred = 'Priority is the most limiting factor today.';
        rec = 'Check moisture vs 35% line, newest camera scan, and any report advisories. Act on the one out of band.';
        break;
      default:
        inferred = 'General agricultural knowledge applies; field data refines it.';
        rec = 'Ask about irrigation, soil, disease, fertilizer, weather, or field status for a targeted answer.';
    }
    return {'observed': obs, 'inferred': inferred, 'recommended': rec};
  }
}
