import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../core/config.dart';

/// Async-loaded shared prefs — overridden with the real instance in main().
final sharedPrefsProvider = Provider<SharedPreferences>((_) {
  throw UnimplementedError('sharedPrefsProvider must be overridden in main()');
});

/// App settings (backend URL + demo mode), persisted across launches.
class AppConfig extends Notifier<AppSettings> {
  @override
  AppSettings build() => const AppSettings();

  static const _urlKey = 'cfg_base_url';
  static const _demoKey = 'cfg_demo_mode';

  Future<void> load() async {
    final prefs = ref.read(sharedPrefsProvider);
    state = AppSettings(
      baseUrl: prefs.getString(_urlKey) ?? state.baseUrl,
      demoMode: prefs.getBool(_demoKey) ?? state.demoMode,
    );
  }

  Future<void> setBaseUrl(String v) async {
    state = state.copyWith(baseUrl: v.trim());
    await ref.read(sharedPrefsProvider).setString(_urlKey, state.baseUrl);
  }

  Future<void> setDemoMode(bool v) async {
    state = state.copyWith(demoMode: v);
    await ref.read(sharedPrefsProvider).setBool(_demoKey, v);
  }
}

final appConfigProvider = NotifierProvider<AppConfig, AppSettings>(AppConfig.new);
