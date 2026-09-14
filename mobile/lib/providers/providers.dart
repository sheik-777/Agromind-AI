import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/field.dart';
import '../models/crop.dart';
import '../models/app_notice.dart';
import '../services/api_client.dart';
import '../services/auth_store.dart';
import '../services/field_repository.dart';
import '../services/notification_service.dart';
import 'package:dio/dio.dart';
import 'app_config.dart';

export '../core/config.dart';
export 'app_config.dart';

// ---------- auth ----------

class AuthState {
  final bool authed;
  final String email;
  final bool demo;
  final bool busy;
  final String? error;

  const AuthState({
    this.authed = false,
    this.email = '',
    this.demo = true,
    this.busy = false,
    this.error,
  });

  AuthState copyWith({bool? authed, String? email, bool? demo, bool? busy, String? error}) =>
      AuthState(
        authed: authed ?? this.authed,
        email: email ?? this.email,
        demo: demo ?? this.demo,
        busy: busy ?? this.busy,
        error: error,
      );
}

class Auth extends Notifier<AuthState> {
  @override
  AuthState build() => const AuthState();

  Future<void> restore() async {
    final token = await AuthStore.token;
    final email = await AuthStore.email;
    if (token != null && token.isNotEmpty) {
      state = state.copyWith(authed: true, email: email ?? '', demo: token.startsWith('demo-'));
    }
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(busy: true, error: null);
    try {
      final dio = ref.read(apiClientProvider);
      final res = await dio.post('/auth/login', data: {'email': email, 'password': password});
      final data = res.data as Map<String, dynamic>;
      final token = data['token']?.toString();
      if (token == null || token.isEmpty) throw Exception('Invalid login response');
      await AuthStore.saveSession(token, email);
      state = state.copyWith(authed: true, email: email, demo: false, busy: false);
    } on DioException catch (e) {
      final code = e.response?.statusCode;
      final msg = e.response?.data is Map ? (e.response?.data['detail'] ?? e.message).toString() : (e.message ?? 'Network error');
      // Only demo-fallback on 404 (route missing) or network unreachable when demoMode is ON
      final demoMode = ref.read(appConfigProvider).demoMode;
      if (demoMode && (code == 404 || e.type == DioExceptionType.connectionError || code == null)) {
        await AuthStore.saveSession('demo-${DateTime.now().millisecondsSinceEpoch}', email);
        state = state.copyWith(authed: true, email: email, demo: true, busy: false);
      } else {
        state = state.copyWith(busy: false, error: msg);
      }
    } catch (e) {
      state = state.copyWith(busy: false, error: e.toString());
    }
  }

  Future<void> register(String name, String email, String password, String confirm) async {
    if (password != confirm) {
      state = state.copyWith(error: 'Passwords do not match');
      return;
    }
    state = state.copyWith(busy: true, error: null);
    try {
      final dio = ref.read(apiClientProvider);
      final res = await dio.post('/auth/register', data: {
        'name': name,
        'email': email,
        'password': password,
        'confirm_password': confirm,
      });
      final data = res.data as Map<String, dynamic>;
      final token = data['token']?.toString();
      if (token == null || token.isEmpty) throw Exception('Invalid registration response');
      await AuthStore.saveSession(token, email);
      state = state.copyWith(authed: true, email: email, demo: false, busy: false);
    } on DioException catch (e) {
      final msg = e.response?.data is Map ? (e.response?.data['detail'] ?? e.message).toString() : (e.message ?? 'Network error');
      state = state.copyWith(busy: false, error: msg);
    } catch (e) {
      state = state.copyWith(busy: false, error: e.toString());
    }
  }

  Future<void> logout() async {
    await AuthStore.clear();
    state = const AuthState();
  }
}

final authProvider = NotifierProvider<Auth, AuthState>(Auth.new);

// ---------- field snapshot ----------

final fieldRepositoryProvider = Provider<FieldRepository>((ref) {
  if (ref.watch(appConfigProvider).demoMode) return MockFieldRepository();
  return ApiFieldRepository(ref.watch(apiClientProvider));
});

final snapshotProvider = FutureProvider<FieldSnapshot>((ref) async {
  final snap = await ref.watch(fieldRepositoryProvider).getSnapshot();
  // Cache last verified values for offline/bad-network display.
  final prefs = ref.read(sharedPrefsProvider);
  await prefs.setString('cache_snapshot_at', snap.fetchedAt.toIso8601String());
  return snap;
});

// ---------- crops (knowledge hub; field comparison happens in UI) ----------

final cropsProvider = Provider<List<CropProfile>>((_) => const [
      CropProfile(
        name: 'Rice', category: 'Cereal', season: 'Kharif',
        phMin: 5.5, phMax: 7.0, tempMinC: 20, tempMaxC: 35,
        moistureMinPct: 50, moistureMaxPct: 90, water: 'High', duration: '120–150 days',
        nutrients: ['Nitrogen heavy feeder', 'Phosphorus at transplanting', 'Potassium for grain fill'],
        diseases: ['Blast', 'Bacterial leaf blight', 'Sheath blight'],
        prevention: ['Resistant varieties', 'Balanced N dose', 'Field sanitation'],
        overview: 'Staple cereal for flooded and rainfed lowlands. Responds strongly to nitrogen and assured water.',
      ),
      CropProfile(
        name: 'Wheat', category: 'Cereal', season: 'Rabi',
        phMin: 6.0, phMax: 7.5, tempMinC: 15, tempMaxC: 25,
        moistureMinPct: 35, moistureMaxPct: 60, water: 'Medium', duration: '110–130 days',
        nutrients: ['Nitrogen in splits', 'Phosphorus basal', 'Zinc where deficient'],
        diseases: ['Rusts', 'Powdery mildew', 'Loose smut'],
        prevention: ['Seed treatment', 'Timely sowing', 'Resistant varieties'],
        overview: 'Cool-season cereal. Needs a cold snap for tillering and dry harvest weather.',
      ),
      CropProfile(
        name: 'Tomato', category: 'Vegetable', season: 'Year-round',
        phMin: 6.0, phMax: 7.0, tempMinC: 20, tempMaxC: 30,
        moistureMinPct: 40, moistureMaxPct: 70, water: 'Medium', duration: '90–120 days',
        nutrients: ['Calcium against blossom-end rot', 'Potassium for fruit quality', 'Steady nitrogen'],
        diseases: ['Early blight', 'Late blight', 'Leaf curl virus'],
        prevention: ['Mulching', 'Staking + airflow', 'Whitefly control'],
        overview: 'High-value vegetable, sensitive to water swings and sucking pests.',
      ),
      CropProfile(
        name: 'Cotton', category: 'Fibre', season: 'Kharif',
        phMin: 5.8, phMax: 8.0, tempMinC: 21, tempMaxC: 30,
        moistureMinPct: 35, moistureMaxPct: 65, water: 'Medium', duration: '150–180 days',
        nutrients: ['Potassium critical', 'Boron for boll set', 'Moderate nitrogen'],
        diseases: ['Bollworm complex', 'Whitefly', 'Leaf reddening'],
        prevention: ['Bt hybrids where legal', 'Pheromone traps', 'Balanced K'],
        overview: 'Long-duration cash crop; water stress at squaring cuts yield hard.',
      ),
      CropProfile(
        name: 'Mango', category: 'Fruit', season: 'Perennial',
        phMin: 5.5, phMax: 7.5, tempMinC: 24, tempMaxC: 32,
        moistureMinPct: 30, moistureMaxPct: 60, water: 'Low–Medium', duration: 'Perennial',
        nutrients: ['Farmyard manure base', 'Potassium pre-flowering', 'Micronutrient sprays'],
        diseases: ['Anthracnose', 'Powdery mildew', 'Fruit fly'],
        prevention: ['Orchard sanitation', 'Bagging fruits', 'Timely pruning'],
        overview: 'Orchard anchor crop. Distinct dry spell before flowering improves fruit set.',
      ),
      CropProfile(
        name: 'Chickpea', category: 'Pulse', season: 'Rabi',
        phMin: 6.0, phMax: 8.0, tempMinC: 15, tempMaxC: 28,
        moistureMinPct: 25, moistureMaxPct: 50, water: 'Low', duration: '90–110 days',
        nutrients: ['Starter nitrogen only', 'Phosphorus + sulphur', 'Rhizobium seed treatment'],
        diseases: ['Wilt', 'Ascochyta blight', 'Pod borer'],
        prevention: ['Resistant varieties', 'Seed treatment', 'Avoid waterlogging'],
        overview: 'Nitrogen-fixing pulse, ideal rotation partner for cereals. Hates wet feet.',
      ),
    ]);

// ---------- notifications (local architecture; FCM is the documented swap) ----------

final noticesProvider = Provider<List<AppNotice>>((_) {
  final now = DateTime.now();
  return [
    AppNotice(
      id: 'n1', title: 'Irrigation scheduled',
      body: 'Morning cycle queued: moisture 31% is below the 35% band.',
      severity: NoticeSeverity.warning, at: now.subtract(const Duration(minutes: 40)),
    ),
    AppNotice(
      id: 'n2', title: 'Rain expected mid-week',
      body: '60% probability in 3 days — irrigation may be reduced.',
      severity: NoticeSeverity.info, at: now.subtract(const Duration(hours: 5)),
    ),
    AppNotice(
      id: 'n3', title: 'Camera scan clear',
      body: 'Midday sample: no visible stress signatures.',
      severity: NoticeSeverity.info, at: now.subtract(const Duration(hours: 3)),
    ),
  ];
});

Future<void> demoNotify(String title, String body) =>
    NotificationService.show(id: DateTime.now().millisecondsSinceEpoch ~/ 1000, title: title, body: body);
