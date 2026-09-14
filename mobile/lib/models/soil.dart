/// Subset of the real backend response for POST /soil/upload
/// (FastAPI: OCR → parser → rule-based recommender over the master CSV).
/// Parsed defensively — the app never invents parameters.
class CropMatch {
  final String crop;
  final double score;

  const CropMatch({required this.crop, required this.score});

  factory CropMatch.fromJson(Map<String, dynamic> j) => CropMatch(
        crop: (j['crop'] ?? 'Unknown').toString(),
        score: (j['score'] is num) ? (j['score'] as num).toDouble() : 0,
      );
}

class SoilReportResult {
  final String filename;
  final int pagesConverted;
  final List<CropMatch> topCrops;
  final List<String> warnings;

  const SoilReportResult({
    required this.filename,
    required this.pagesConverted,
    required this.topCrops,
    required this.warnings,
  });

  factory SoilReportResult.fromJson(Map<String, dynamic> j) {
    final parsed = (j['parsed_report'] as List?) ?? const [];
    final first = parsed.isEmpty ? const <String, dynamic>{} : parsed.first as Map<String, dynamic>;
    final recs = (first['crop_recommendations'] as List?) ?? const [];
    final warns = (first['warnings'] as List?) ?? const [];
    return SoilReportResult(
      filename: (j['filename'] ?? 'report.pdf').toString(),
      pagesConverted: (j['pages_converted'] is num) ? (j['pages_converted'] as num).toInt() : 0,
      topCrops: recs
          .map((e) => CropMatch.fromJson((e as Map).cast<String, dynamic>()))
          .toList(),
      warnings: warns.map((e) => e.toString()).toList(),
    );
  }
}
