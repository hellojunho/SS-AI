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

  Future<AdminUser> fetchUserDetail(int id) async {
    final response = await _client.get('/auth/admin/users/$id', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('사용자 정보를 불러오지 못했습니다.');
    }
    return AdminUser.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<AdminUser> updateUser(int id, Map<String, dynamic> payload) async {
    final response = await _client.patch(
      '/auth/admin/users/$id',
      authorized: true,
      body: payload,
    );
    if (response.statusCode != 200) {
      throw Exception('사용자 정보를 수정하지 못했습니다.');
    }
    return AdminUser.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<void> deleteUser(int id) async {
    final response = await _client.delete('/auth/admin/users/$id', authorized: true);
    if (response.statusCode != 204) {
      throw Exception('사용자를 삭제하지 못했습니다.');
    }
  }

  Future<List<AdminQuizSummary>> fetchQuizzes() async {
    final response = await _client.get('/quiz/admin/list', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('관리자 퀴즈 목록을 불러오지 못했습니다.');
    }
    final payload = jsonDecode(response.body) as List<dynamic>;
    return payload.map((item) => AdminQuizSummary.fromJson(item as Map<String, dynamic>)).toList();
  }

  Future<AdminQuizDetail> fetchQuizDetail(int id) async {
    final response = await _client.get('/quiz/admin/$id', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('퀴즈 정보를 불러오지 못했습니다.');
    }
    return AdminQuizDetail.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<AdminQuizDetail> updateQuiz(int id, Map<String, dynamic> payload) async {
    final response = await _client.patch(
      '/quiz/admin/$id',
      authorized: true,
      body: payload,
    );
    if (response.statusCode != 200) {
      throw Exception('퀴즈 정보를 수정하지 못했습니다.');
    }
    return AdminQuizDetail.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<void> deleteQuiz(int id) async {
    final response = await _client.delete('/quiz/admin/$id', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('퀴즈를 삭제하지 못했습니다.');
    }
  }

  Future<List<AdminTrafficStats>> fetchTrafficStats() async {
    final response = await _client.get('/auth/admin/traffic', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('유입량 정보를 불러오지 못했습니다.');
    }
    final payload = jsonDecode(response.body) as List<dynamic>;
    return payload
        .map((item) => AdminTrafficStats.fromJson(item as Map<String, dynamic>))
        .toList();
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
