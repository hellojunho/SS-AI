import 'dart:convert';

import '../models/quiz.dart';
import '../models/wrong_note.dart';
import 'api_client.dart';

class QuizService {
  QuizService(this._client);

  final ApiClient _client;

  Future<Quiz?> fetchLatest({bool all = false}) async {
    final endpoint = all ? '/quiz/all/latest' : '/quiz/latest';
    final response = await _client.get(endpoint, authorized: true);
    if (response.statusCode == 404) {
      return null;
    }
    if (response.statusCode != 200) {
      throw Exception('퀴즈를 불러오지 못했습니다.');
    }
    return Quiz.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<Quiz?> fetchNext({required int currentId, bool all = false}) async {
    final endpoint = all ? '/quiz/all/next?current_id=$currentId' : '/quiz/next?current_id=$currentId';
    final response = await _client.get(endpoint, authorized: true);
    if (response.statusCode == 404) {
      return null;
    }
    if (response.statusCode != 200) {
      throw Exception('다음 퀴즈를 불러오지 못했습니다.');
    }
    return Quiz.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<QuizResultSummary> fetchSummary({bool all = false}) async {
    final scope = all ? 'all' : 'user';
    final response = await _client.get('/quiz/summary?scope=$scope', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('퀴즈 통계를 불러오지 못했습니다.');
    }
    return QuizResultSummary.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<QuizAnswerResult> submitAnswer({required int quizId, required String answer}) async {
    final response = await _client.post(
      '/quiz/$quizId/answer',
      authorized: true,
      body: {'answer': answer},
    );
    if (response.statusCode != 200) {
      throw Exception('정답 제출에 실패했습니다.');
    }
    return QuizAnswerResult.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<Quiz> generateQuiz() async {
    final response = await _client.post('/quiz/generate', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('퀴즈를 생성하지 못했습니다.');
    }
    return Quiz.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<List<WrongNoteQuestion>> fetchWrongNotes() async {
    final response = await _client.get('/quiz/wrong-notes', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('오답노트를 불러오지 못했습니다.');
    }
    final payload = jsonDecode(response.body) as List<dynamic>;
    return payload
        .map((item) => WrongNoteQuestion.fromJson(item as Map<String, dynamic>))
        .toList();
  }
}
