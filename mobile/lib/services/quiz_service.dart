import 'dart:convert';

import '../models/quiz.dart';
import 'api_client.dart';

class QuizService {
  QuizService(this._client);

  final ApiClient _client;

  Future<Quiz> fetchLatest() async {
    final response = await _client.get('/quiz/latest', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('퀴즈를 불러오지 못했습니다.');
    }
    return Quiz.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<Quiz> fetchNext() async {
    final response = await _client.get('/quiz/next', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('다음 퀴즈를 불러오지 못했습니다.');
    }
    return Quiz.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<void> submitAnswer({required int quizId, required String answer}) async {
    final response = await _client.post(
      '/quiz/$quizId/answer',
      authorized: true,
      body: {'answer': answer},
    );
    if (response.statusCode != 200) {
      throw Exception('정답 제출에 실패했습니다.');
    }
  }
}
