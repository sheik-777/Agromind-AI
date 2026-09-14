import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'core/theme.dart';
import 'providers/providers.dart';
import 'screens/auth_screen.dart';
import 'screens/shell.dart';
import 'services/notification_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  await NotificationService.init();
  runApp(
    ProviderScope(
      overrides: [sharedPrefsProvider.overrideWithValue(prefs)],
      child: const AgroMindApp(),
    ),
  );
}

class AgroMindApp extends ConsumerStatefulWidget {
  const AgroMindApp({super.key});

  @override
  ConsumerState<AgroMindApp> createState() => _AgroMindAppState();
}

class _AgroMindAppState extends ConsumerState<AgroMindApp> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() async {
      await ref.read(appConfigProvider.notifier).load();
      await ref.read(authProvider.notifier).restore();
    });
  }

  @override
  Widget build(BuildContext context) {
    final authed = ref.watch(authProvider.select((a) => a.authed));
    return MaterialApp(
      title: 'AgroMind',
      debugShowCheckedModeBanner: false,
      theme: buildAgroTheme(Brightness.light),
      darkTheme: buildAgroTheme(Brightness.dark),
      home: authed ? const Shell() : const AuthScreen(),
    );
  }
}
