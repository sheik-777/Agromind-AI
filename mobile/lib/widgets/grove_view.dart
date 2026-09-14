import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

/// Interactive grove: the farm's living emblem.
///
/// Touch (or drag) across the canopy and nearby buds bloom pink with
/// distance-based falloff — bud → opening → bloomed → gentle return.
/// Palette follows field health. If a production `tree.glb` ever ships,
/// replace this painter with a model viewer; the health/bloom contract
/// (healthy vs stressed) stays the same.
class GroveView extends StatefulWidget {
  final bool stressed;
  const GroveView({super.key, this.stressed = false});

  @override
  State<GroveView> createState() => _GroveViewState();
}

class _Leaf {
  final double angle;
  final double radius;
  final double size;
  final double phase;
  final int shade;
  _Leaf(this.angle, this.radius, this.size, this.phase, this.shade);
}

class _Bloom {
  final double angle;
  final double radius;
  double value;
  final double phase;
  _Bloom(this.angle, this.radius, this.value, this.phase);
}

class _GroveViewState extends State<GroveView> with SingleTickerProviderStateMixin {
  late final Ticker _ticker;
  late final List<_Leaf> _leaves;
  late final List<_Bloom> _blooms;
  double _time = 0;
  Offset? _touch; // local coords, null = no interaction
  bool _reduced = false;

  @override
  void initState() {
    super.initState();
    final rand = math.Random(7); // deterministic grove
    _leaves = List.generate(110, (i) {
      final golden = i * 2.399963;
      return _Leaf(
        golden,
        0.52 + rand.nextDouble() * 0.48,
        9 + rand.nextDouble() * 13,
        rand.nextDouble() * math.pi * 2,
        i % 4,
      );
    });
    _blooms = List.generate(26, (i) {
      final golden = i * 2.399963 + 0.7;
      return _Bloom(golden, 0.72 + rand.nextDouble() * 0.28, 0.15, rand.nextDouble() * math.pi * 2);
    });
    _ticker = createTicker(_tick)..start();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _reduced = MediaQuery.disableAnimationsOf(context);
  }

  void _tick(Duration elapsed) {
    if (_reduced) return;
    setState(() {
      _time = elapsed.inMilliseconds / 1000;
      if (_touch != null) return; // touch handler drives bloom while interacting
      for (final b in _blooms) {
        final target = 0.15 + 0.03 * math.sin(_time * 1.2 + b.phase);
        b.value += (target - b.value) * 0.08;
      }
    });
  }

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  void _onTouch(Offset local, Size size) {
    final center = Offset(size.width / 2, size.height * 0.42);
    final r = size.shortestSide * 0.36;
    final p = Offset((local.dx - center.dx) / r, (local.dy - center.dy) / r);
    setState(() {
      _touch = p;
      for (final b in _blooms) {
        final bp = Offset(math.cos(b.angle) * b.radius, math.sin(b.angle) * b.radius * 0.82);
        final d = (bp - p).distance;
        final fall = math.max(0, 1 - d / 0.9);
        final target = math.min(1.0, fall * fall * 1.3 + 0.15);
        b.value = _reduced ? target : b.value + (target - b.value) * 0.35;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: GestureDetector(
        onTapDown: (d) => _onTouch(d.localPosition, (context.findRenderObject() as RenderBox).size),
        onPanUpdate: (d) => _onTouch(d.localPosition, (context.findRenderObject() as RenderBox).size),
        onPanEnd: (_) => setState(() => _touch = null),
        onTapUp: (_) => setState(() => _touch = null),
        child: LayoutBuilder(
          builder: (context, constraints) {
            return CustomPaint(
              size: Size(constraints.maxWidth, constraints.maxHeight),
              painter: _GrovePainter(
                time: _reduced ? 0 : _time,
                leaves: _leaves,
                blooms: _blooms,
                stressed: widget.stressed,
                animate: !_reduced,
              ),
            );
          },
        ),
      ),
    );
  }
}

class _GrovePainter extends CustomPainter {
  final double time;
  final List<_Leaf> leaves;
  final List<_Bloom> blooms;
  final bool stressed;
  final bool animate;

  _GrovePainter({
    required this.time,
    required this.leaves,
    required this.blooms,
    required this.stressed,
    required this.animate,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height * 0.42);
    final r = size.shortestSide * 0.36;
    final sway = animate ? math.sin(time * 0.6) * r * 0.012 : 0.0;

    // Ground shadow
    final shadow = Paint()..color = const Color(0xFF1A2B1F).withValues(alpha: 0.18);
    canvas.drawOval(
      Rect.fromCenter(center: Offset(size.width / 2, size.height * 0.88), width: r * 1.5, height: r * 0.22),
      shadow,
    );

    // Trunk: tapered quad
    final trunkPaint = Paint()..color = const Color(0xFF6B4A30);
    final baseY = size.height * 0.88;
    final topY = center.dy + r * 0.25;
    final trunk = Path()
      ..moveTo(size.width / 2 - r * 0.11, baseY)
      ..quadraticBezierTo(size.width / 2 - r * 0.06, (baseY + topY) / 2, size.width / 2 - r * 0.035 + sway, topY)
      ..lineTo(size.width / 2 + r * 0.035 + sway, topY)
      ..quadraticBezierTo(size.width / 2 + r * 0.06, (baseY + topY) / 2, size.width / 2 + r * 0.11, baseY)
      ..close();
    canvas.drawPath(trunk, trunkPaint);

    // Branches
    final branchPaint = Paint()
      ..color = const Color(0xFF75553A)
      ..strokeWidth = r * 0.035
      ..strokeCap = StrokeCap.round;
    for (var i = 0; i < 5; i++) {
      final a = -math.pi / 2 + (i - 2) * 0.42;
      final start = Offset(size.width / 2 + sway * 0.5, topY + r * 0.08);
      final end = Offset(
        size.width / 2 + math.cos(a) * r * 0.75 + sway,
        topY + r * 0.08 + math.sin(a) * r * 0.75,
      );
      canvas.drawLine(start, end, branchPaint);
    }

    // Canopy leaves (two tones, gentle sway)
    final greens = stressed
        ? [const Color(0xFF9A8B5A), const Color(0xFF7A7A4A), const Color(0xFF8A7A4F), const Color(0xFF6E6E42)]
        : [const Color(0xFF3A9238), const Color(0xFF2D752D), const Color(0xFF5DB058), const Color(0xFF8DCA87)];
    for (final leaf in leaves) {
      final wobble = animate ? math.sin(time * 0.9 + leaf.phase) * r * 0.02 : 0.0;
      final p = Offset(
        center.dx + math.cos(leaf.angle) * leaf.radius * r + sway + wobble,
        center.dy + math.sin(leaf.angle) * leaf.radius * r * 0.82 + wobble * 0.6,
      );
      canvas.drawCircle(p, leaf.size * (size.shortestSide / 300), Paint()..color = greens[leaf.shade]);
    }

    // Blossoms: pink swell by bloom value
    for (final b in blooms) {
      final p = Offset(
        center.dx + math.cos(b.angle) * b.radius * r + sway,
        center.dy + math.sin(b.angle) * b.radius * r * 0.82,
      );
      final v = b.value.clamp(0.0, 1.0);
      final bud = const Color(0xFF5F7031);
      final bloom = const Color(0xFFF9A8D4);
      final c = Color.lerp(bud, bloom, v)!;
      final rad = (3.2 + v * 5.5) * (size.shortestSide / 300);
      canvas.drawCircle(p, rad, Paint()..color = c);
      if (v > 0.55) {
        canvas.drawCircle(p, rad * 0.38, Paint()..color = const Color(0xFFFFF7D6));
      }
    }
  }

  @override
  bool shouldRepaint(covariant _GrovePainter old) => true;
}
