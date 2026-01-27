import 'dart:convert';

import '../models/chat.dart';
import 'api_client.dart';

class ChatService {
  ChatService(this._client);

  final ApiClient _client;

  Future<ChatAnswer> ask(String message) async {
    final response = await _client.post(
      '/chat/ask',
      authorized: true,
      body: {'message': message},
    );
    if (response.statusCode != 200) {
      throw Exception('질문 전송에 실패했습니다.');
    }
    return ChatAnswer.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<ChatHistoryDatesResponse> fetchHistoryDates() async {
    final response = await _client.get('/chat/history', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('채팅 내역 날짜를 불러오지 못했습니다.');
    }
    return ChatHistoryDatesResponse.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<ChatHistoryResponse> fetchHistory(String date) async {
    final response = await _client.get('/chat/history/$date', authorized: true);
    if (response.statusCode != 200) {
      throw Exception('채팅 내역을 불러오지 못했습니다.');
    }
    return ChatHistoryResponse.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }
}
