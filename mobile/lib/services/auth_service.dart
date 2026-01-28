import 'dart:convert';

import '../config.dart';
import '../models/token.dart';
import '../models/user.dart';
import 'auth_storage.dart';
import 'package:http/http.dart' as http;

class AuthService {
  AuthService({AuthStorage? storage}) : _storage = storage ?? AuthStorage();

  final AuthStorage _storage;

  Future<TokenPair> login({
    required String userId,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$apiBaseUrl/auth/login'),
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode({'user_id': userId, 'password': password}),
    );
    if (response.statusCode != 200) {
      throw Exception('로그인에 실패했습니다.');
    }
    final tokenPair = TokenPair.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
    await _saveTokens(tokenPair);
    return tokenPair;
  }

  Future<void> signUp({
    required String userId,
    required String userName,
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$apiBaseUrl/auth/register'),
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode({
        'user_id': userId,
        'user_name': userName,
        'email': email,
        'password': password,
      }),
    );
    if (response.statusCode != 200 && response.statusCode != 201) {
      throw Exception('회원가입에 실패했습니다.');
    }
  }

  Future<UserProfile> fetchMe() async {
    final token = await ensureAccessToken();
    if (token == null) {
      throw Exception('로그인이 필요합니다.');
    }
    final response = await http.get(
      Uri.parse('$apiBaseUrl/auth/me'),
      headers: {
        'Accept': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );
    if (response.statusCode != 200) {
      throw Exception('사용자 정보를 불러오지 못했습니다.');
    }
    return UserProfile.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<void> logout() async {
    await _storage.clear();
  }

  Future<void> withdraw() async {
    final token = await ensureAccessToken();
    if (token == null) {
      throw Exception('로그인이 필요합니다.');
    }
    final response = await http.post(
      Uri.parse('$apiBaseUrl/auth/withdraw'),
      headers: {
        'Accept': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );
    if (response.statusCode != 204) {
      throw Exception('회원 탈퇴에 실패했습니다.');
    }
    await _storage.clear();
  }

  Future<String?> ensureAccessToken() async {
    if (await _isAccessTokenValid()) {
      return _storage.readAccessToken();
    }
    if (!await _isRefreshTokenValid()) {
      await _storage.clear();
      return null;
    }
    try {
      final refreshToken = await _storage.readRefreshToken();
      if (refreshToken == null) {
        await _storage.clear();
        return null;
      }
      final response = await http.post(
        Uri.parse('$apiBaseUrl/auth/refresh'),
        headers: const {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': refreshToken}),
      );
      if (response.statusCode != 200) {
        await _storage.clear();
        return null;
      }
      final tokenPair = TokenPair.fromJson(
        jsonDecode(response.body) as Map<String, dynamic>,
      );
      await _saveTokens(tokenPair);
      return tokenPair.accessToken;
    } catch (_) {
      await _storage.clear();
      return null;
    }
  }

  Future<bool> isAuthenticated() async {
    return await _isAccessTokenValid() || await _isRefreshTokenValid();
  }

  Future<bool> _isAccessTokenValid() async {
    final expiry = await _storage.readAccessExpiry();
    final token = await _storage.readAccessToken();
    return token != null && DateTime.now().millisecondsSinceEpoch < expiry;
  }

  Future<bool> _isRefreshTokenValid() async {
    final expiry = await _storage.readRefreshExpiry();
    final token = await _storage.readRefreshToken();
    return token != null && DateTime.now().millisecondsSinceEpoch < expiry;
  }

  Future<void> _saveTokens(TokenPair tokenPair) async {
    final expiresAt =
        DateTime.now().add(const Duration(minutes: sessionMinutes)).millisecondsSinceEpoch;
    await _storage.saveTokens(
      accessToken: tokenPair.accessToken,
      refreshToken: tokenPair.refreshToken,
      accessExpiry: expiresAt,
      refreshExpiry: expiresAt,
    );
  }
}
