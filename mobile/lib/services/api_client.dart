import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/app_config.dart';
import 'auth_store.dart';

/// Dio client pointed at the configured backend. Token (if any) attaches via
/// interceptor. Timeouts are generous: OCR of a multi-page PDF takes a while.
final apiClientProvider = Provider<Dio>((ref) {
  final baseUrl = ref.watch(appConfigProvider).baseUrl;
  final dio = Dio(BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: const Duration(seconds: 15),
    receiveTimeout: const Duration(minutes: 3),
    sendTimeout: const Duration(minutes: 3),
  ));
  dio.interceptors.add(InterceptorsWrapper(
    onRequest: (options, handler) async {
      final token = await AuthStore.token;
      if (token != null && token.isNotEmpty) {
        options.headers['Authorization'] = 'Bearer $token';
      }
      handler.next(options);
    },
  ));
  return dio;
});
