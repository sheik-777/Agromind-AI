import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Token lives in platform secure storage — never in plain prefs, never in code.
class AuthStore {
  static const _storage = FlutterSecureStorage();
  static const _tokenKey = 'auth_token';
  static const _emailKey = 'auth_email';

  static Future<String?> get token => _storage.read(key: _tokenKey);
  static Future<String?> get email => _storage.read(key: _emailKey);

  static Future<void> saveSession(String token, String email) async {
    await _storage.write(key: _tokenKey, value: token);
    await _storage.write(key: _emailKey, value: email);
  }

  static Future<void> clear() async {
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _emailKey);
  }
}
