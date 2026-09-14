import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import '../models/soil.dart';

/// Soil-report upload against the REAL backend route POST /soil/upload
/// (multipart `file` field — same contract as the web app).
/// Progress (0..1) streams back via [onProgress] for the scanning UI.
class SoilService {
  final Dio dio;
  SoilService(this.dio);

  Future<SoilReportResult> uploadPdf({
    required PlatformFile file,
    void Function(double progress)? onProgress,
  }) async {
    final bytes = await file.readAsBytes();
    if (bytes.isEmpty) {
      throw const SoilUploadException('Could not read the selected PDF.');
    }
    final form = FormData.fromMap({
      'file': MultipartFile.fromBytes(bytes, filename: file.name),
    });
    try {
      final res = await dio.post(
        '/soil/upload',
        data: form,
        options: Options(contentType: 'multipart/form-data'),
        onSendProgress: (sent, total) {
          if (total > 0) onProgress?.call(sent / total);
        },
      );
      final data = res.data;
      if (data is! Map<String, dynamic> || data['success'] != true) {
        throw SoilUploadException(
          (data is Map && data['message'] is String)
              ? data['message'] as String
              : 'Analysis failed on the server.',
        );
      }
      return SoilReportResult.fromJson(data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw const SoilUploadException(
          'POST /soil/upload not found on this backend. Check the base URL in Settings.',
        );
      }
      throw SoilUploadException('Upload failed: ${e.message ?? 'network error'}');
    }
  }
}

class SoilUploadException implements Exception {
  final String message;
  const SoilUploadException(this.message);
  @override
  String toString() => message;
}
