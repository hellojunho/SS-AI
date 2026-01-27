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
}
