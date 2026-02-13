import 'dart:convert';

import '../models/user.dart';
import 'api_client.dart';

class CoachService {
  CoachService(this._client);

  final ApiClient _client;

  Future<List<DirectoryUser>> fetchStudents() async {
    final response = await _client.get('/auth/coach/students', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('학생 목록을 불러오지 못했습니다.');
    }
    final payload = jsonDecode(response.body) as List<dynamic>;
    return payload
        .map((item) => DirectoryUser.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<DirectoryUser>> searchStudents(String keyword) async {
    final response = await _client.get(
      '/auth/coach/students/search?keyword=${Uri.encodeQueryComponent(keyword)}',
      authorized: true,
    );
    if (response.statusCode != 200) {
      throw Exception('학생 검색에 실패했습니다.');
    }
    final payload = jsonDecode(response.body) as List<dynamic>;
    return payload
        .map((item) => DirectoryUser.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<DirectoryUser> registerStudent(String studentUserId) async {
    final response = await _client.post(
      '/auth/coach/students',
      authorized: true,
      body: {'student_user_id': studentUserId},
    );
    if (response.statusCode != 201) {
      final payload = jsonDecode(response.body) as Map<String, dynamic>;
      throw Exception(payload['detail'] ?? '학생 등록에 실패했습니다.');
    }
    return DirectoryUser.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<void> removeStudent(String studentUserId) async {
    final response = await _client.delete(
      '/auth/coach/students/$studentUserId',
      authorized: true,
    );
    if (response.statusCode != 204) {
      final payload = jsonDecode(response.body) as Map<String, dynamic>;
      throw Exception(payload['detail'] ?? '학생 해제에 실패했습니다.');
    }
  }
}
