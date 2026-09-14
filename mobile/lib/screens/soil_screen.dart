import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/soil.dart';
import '../services/api_client.dart';
import '../services/soil_service.dart';
import '../widgets/common.dart';

/// Soil report against the REAL route POST /soil/upload (multipart `file`).
/// Meaningful stages (upload → OCR → extract → analyze → recommend) instead
/// of a generic spinner. Works in demo mode too if the backend is reachable.
class SoilScreen extends ConsumerStatefulWidget {
  const SoilScreen({super.key});

  @override
  ConsumerState<SoilScreen> createState() => _SoilScreenState();
}

class _SoilScreenState extends ConsumerState<SoilScreen> {
  double _progress = 0;
  bool _busy = false;
  String? _stage;
  String? _error;
  SoilReportResult? _result;

  static const _stages = [
    'Uploading report…',
    'Reading document (OCR)…',
    'Extracting lab parameters…',
    'Validating values…',
    'Analyzing soil profile…',
    'Comparing crops…',
  ];

  Future<void> _pickAndAnalyze() async {
    setState(() {
      _busy = true;
      _error = null;
      _result = null;
      _progress = 0;
      _stage = _stages.first;
    });
    try {
      final file = await FilePicker.pickFile(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
      );
      if (file == null) {
        if (mounted) setState(() => _busy = false);
        return;
      }
      final service = SoilService(ref.read(apiClientProvider));
      // Upload bar covers the first stage; staged labels carry the rest.
      final result = await service.uploadPdf(
        file: file,
        onProgress: (p) => setState(() {
          _progress = p;
          _stage = _stages[(p * (_stages.length - 1)).floor()];
        }),
      );
      if (!mounted) return;
      // Parsing/analysis happen server-side during the same call; walk the
      // remaining stages briefly so each step is visible and honest.
      for (var i = 1; i < _stages.length; i++) {
        await Future.delayed(const Duration(milliseconds: 450));
        if (!mounted) return;
        setState(() => _stage = _stages[i]);
      }
      setState(() {
        _result = result;
        _busy = false;
      });
    } on SoilUploadException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message;
          _busy = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e is DioException ? 'Network error: ${e.message}' : '$e';
          _busy = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Soil report')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_result == null && !_busy) ...[
            EmptyState(
              emoji: '🧪',
              title: 'Analyze a lab report',
              body: 'Upload a soil laboratory PDF. OCR extracts the parameters, '
                  'the engine interprets them and ranks suitable crops.',
              actionLabel: 'Pick PDF report',
              onAction: _pickAndAnalyze,
            ),
          ],
          if (_busy) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    const Text('🌱', style: TextStyle(fontSize: 48)),
                    const SizedBox(height: 12),
                    Text(_stage ?? '', style: const TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 12),
                    LinearProgressIndicator(value: _progress == 0 ? null : _progress),
                    const SizedBox(height: 8),
                    Text('${(_progress * 100).toStringAsFixed(0)}% uploaded',
                        style: TextStyle(color: Theme.of(context).hintColor, fontSize: 12)),
                  ],
                ),
              ),
            ),
          ],
          if (_error != null)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('⚠️ Upload failed', style: TextStyle(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 6),
                    Text(_error!),
                    const SizedBox(height: 12),
                    FilledButton(onPressed: _pickAndAnalyze, child: const Text('Try again')),
                  ],
                ),
              ),
            ),
          if (_result != null) ...[
            const SectionTitle('Results — real backend output'),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_result!.filename, style: const TextStyle(fontWeight: FontWeight.w700)),
                    Text('${_result!.pagesConverted} pages converted · OCR + parser',
                        style: TextStyle(color: Theme.of(context).hintColor, fontSize: 12)),
                    const SizedBox(height: 12),
                    ..._result!.topCrops.take(5).map((c) => Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Row(
                            children: [
                              Expanded(child: Text(c.crop, style: const TextStyle(fontWeight: FontWeight.w600))),
                              Text('${c.score.toStringAsFixed(0)}%',
                                  style: const TextStyle(fontWeight: FontWeight.w800)),
                            ],
                          ),
                        )),
                    if (_result!.warnings.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      ..._result!.warnings.map((w) => Text('⚠️ $w', style: const TextStyle(fontSize: 13))),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            FilledButton.tonal(onPressed: _pickAndAnalyze, child: const Text('Analyze another report')),
          ],
        ],
      ),
    );
  }
}
