import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config.dart';
import 'auth_service.dart';

class ApiClient {
  ApiClient(this._authService);

  final AuthService _authService;

  Uri _resolve(String path) {
    return Uri.parse('$apiBaseUrl$path');
  }

  Future<http.Response> get(String path, {bool authorized = false}) async {
    final headers = <String, String>{'Accept': 'application/json'};
    if (authorized) {
      final token = await _authService.ensureAccessToken();
      if (token == null) {
        throw Exception('로그인이 필요합니다.');
      }
      headers['Authorization'] = 'Bearer $token';
    }
    return http.get(_resolve(path), headers: headers);
  }

  Future<http.Response> post(
    String path, {
    Map<String, dynamic>? body,
    bool authorized = false,
  }) async {
    final headers = <String, String>{
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
    if (authorized) {
      final token = await _authService.ensureAccessToken();
      if (token == null) {
        throw Exception('로그인이 필요합니다.');
      }
      headers['Authorization'] = 'Bearer $token';
    }
    return http.post(
      _resolve(path),
      headers: headers,
      body: body == null ? null : jsonEncode(body),
    );
  }
}
