import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';
import '../services/ai_service.dart';
import '../services/api_client.dart';
import '../widgets/common.dart';

class _Msg {
  final bool me;
  final String text;
  final String? intent;
  final List<String>? observed;
  final List<String>? sources;
  _Msg(this.me, this.text, {this.intent, this.observed, this.sources});
}

/// ASK AGROMIND — intent-aware, field-grounded.
/// Tries POST /ai/ask when live; falls back to LocalAiEngine so every
/// question gets a different, relevant answer instead of one demo string.
class AiScreen extends ConsumerStatefulWidget {
  const AiScreen({super.key});

  @override
  ConsumerState<AiScreen> createState() => _AiScreenState();
}

class _AiScreenState extends ConsumerState<AiScreen> {
  final _input = TextEditingController();
  final _msgs = <_Msg>[
    _Msg(false, 'I can see your field — ask me anything, e.g. "Should I irrigate now?" or "Why are my leaves yellow?"'),
  ];
  bool _typing = false;

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  Future<void> _ask(String q) async {
    if (q.trim().isEmpty || _typing) return;
    final field = ref.read(snapshotProvider).when(
          data: (d) => d,
          loading: () => null,
          error: (_, _) => null,
        );
    setState(() {
      _msgs.add(_Msg(true, q.trim()));
      _typing = true;
    });
    _input.clear();

    String answer = '';
    String? intent;
    List<String>? observed;
    List<String>? sources;

    final demoMode = ref.read(appConfigProvider).demoMode;
    if (!demoMode) {
      try {
        final svc = AiService(ref.read(apiClientProvider));
        final res = await svc.ask(q);
        intent = res.intent;
        observed = res.observed;
        sources = res.sources;
        answer =
            'OBSERVED\n${res.observed.join(" · ")}\n\nINFERRED\n${res.inferred}\n\nRECOMMENDED\n${res.recommended}\n\nSources: ${res.sources.join(", ")}';
      } catch (_) {
        // fall through to local
      }
    }
    if (answer.isEmpty) {
      final ic = LocalAiEngine.classify(q);
      intent = ic;
      final local = LocalAiEngine.answer(q, field, ic);
      observed = [local['observed']!];
      answer = 'OBSERVED\n${local['observed']}\n\nINFERRED\n${local['inferred']}\n\nRECOMMENDED\n${local['recommended']}';
      sources = ['Local knowledge (demo) — connect backend for RAG + LLM'];
    }

    if (!mounted) return;
    setState(() {
      _msgs.add(_Msg(false, answer, intent: intent, observed: observed, sources: sources));
      _typing = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final snapshot = ref.watch(snapshotProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Ask AgroMind')),
      body: Column(
        children: [
          snapshot.when(
            loading: () => const LinearProgressIndicator(),
            error: (_, _) => const SizedBox.shrink(),
            data: (field) => Container(
              width: double.infinity,
              margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.4),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      'FIELD CONTEXT · Moisture ${field.sensors.moisturePct.toStringAsFixed(0)}% · '
                      '${field.sensors.airTempC.toStringAsFixed(1)}°C · '
                      'Humidity ${field.sensors.humidityPct.toStringAsFixed(0)}% · '
                      'pH ${field.sensors.ph.toStringAsFixed(1)}',
                      style: const TextStyle(fontSize: 12),
                    ),
                  ),
                  const DemoChip(),
                ],
              ),
            ),
          ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _msgs.length + (_typing ? 1 : 0),
              itemBuilder: (context, i) {
                if (i >= _msgs.length) {
                  return const Align(
                    alignment: Alignment.centerLeft,
                    child: Card(child: Padding(padding: EdgeInsets.all(12), child: Text('···'))),
                  );
                }
                final m = _msgs[i];
                return Align(
                  alignment: m.me ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.82),
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: m.me ? Theme.of(context).colorScheme.primary : Theme.of(context).cardTheme.color,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (m.intent != null)
                          Text(m.intent!.toUpperCase(),
                              style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: m.me ? Colors.white70 : Colors.grey)),
                        Text(
                          m.text,
                          style: TextStyle(color: m.me ? Colors.white : null, fontSize: 14, height: 1.45),
                        ),
                        if (m.sources != null) ...[
                          const SizedBox(height: 6),
                          Text('Sources: ${m.sources!.join(", ")}',
                              style: TextStyle(fontSize: 11, color: m.me ? Colors.white70 : Colors.grey)),
                        ]
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _input,
                      decoration: const InputDecoration(hintText: 'Ask about your field…'),
                      onSubmitted: _ask,
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(onPressed: () => _ask(_input.text), icon: const Icon(Icons.send_outlined)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
