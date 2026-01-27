import 'package:shared_preferences/shared_preferences.dart';

class AuthStorage {
  static const _accessTokenKey = 'accessToken';
  static const _refreshTokenKey = 'refreshToken';
  static const _accessExpKey = 'accessTokenExpiresAt';
  static const _refreshExpKey = 'refreshTokenExpiresAt';

  Future<String?> readAccessToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_accessTokenKey);
  }

  Future<String?> readRefreshToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_refreshTokenKey);
  }

  Future<int> readAccessExpiry() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_accessExpKey) ?? 0;
  }

  Future<int> readRefreshExpiry() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_refreshExpKey) ?? 0;
  }

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
    required int accessExpiry,
    required int refreshExpiry,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_accessTokenKey, accessToken);
    await prefs.setString(_refreshTokenKey, refreshToken);
    await prefs.setInt(_accessExpKey, accessExpiry);
    await prefs.setInt(_refreshExpKey, refreshExpiry);
  }

  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_accessTokenKey);
    await prefs.remove(_refreshTokenKey);
    await prefs.remove(_accessExpKey);
    await prefs.remove(_refreshExpKey);
  }
}
