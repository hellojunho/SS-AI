import 'dart:convert';

import '../models/admin.dart';
import 'api_client.dart';

class AdminService {
  AdminService(this._client);

  final ApiClient _client;

  Future<List<AdminUser>> fetchUsers() async {
    final response = await _client.get('/auth/admin/users', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('관리자 사용자 목록을 불러오지 못했습니다.');
    }
    final payload = jsonDecode(response.body) as List<dynamic>;
    return payload.map((item) => AdminUser.fromJson(item as Map<String, dynamic>)).toList();
  }

  Future<List<AdminQuizSummary>> fetchQuizzes() async {
    final response = await _client.get('/quiz/admin/list', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('관리자 퀴즈 목록을 불러오지 못했습니다.');
    }
    final payload = jsonDecode(response.body) as List<dynamic>;
    return payload.map((item) => AdminQuizSummary.fromJson(item as Map<String, dynamic>)).toList();
  }

  Future<LlmUsage> fetchLlmUsage() async {
    final response = await _client.get('/admin/llm/usage', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('토큰 사용량을 불러오지 못했습니다.');
    }
    return LlmUsage.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<String> generateAllQuizzes() async {
    final response = await _client.post('/quiz/admin/generate-all', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('퀴즈 생성 작업을 시작하지 못했습니다.');
    }
    final payload = jsonDecode(response.body) as Map<String, dynamic>;
    return payload['job_id'] as String;
  }
}
