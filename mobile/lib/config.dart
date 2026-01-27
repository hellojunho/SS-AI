import 'dart:io';

const String _apiBaseUrlEnv = String.fromEnvironment('API_BASE_URL');

String get apiBaseUrl {
  if (_apiBaseUrlEnv.isNotEmpty) {
    return _apiBaseUrlEnv;
  }
  if (Platform.isAndroid) {
    return 'http://10.0.2.2:5001';
  }
  return 'http://localhost:5001';
}

const int sessionMinutes = 30;
