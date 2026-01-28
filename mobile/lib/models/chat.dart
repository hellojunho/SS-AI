class ChatAnswer {
  const ChatAnswer({
    required this.answer,
    required this.reference,
    required this.filePath,
  });

  final String answer;
  final String reference;
  final String filePath;

  factory ChatAnswer.fromJson(Map<String, dynamic> json) {
    return ChatAnswer(
      answer: json['answer'] as String? ?? 'Null',
      reference: json['reference'] as String? ?? 'Null',
      filePath: json['file_path'] as String? ?? 'Null',
    );
  }
}

class ChatHistoryEntry {
  const ChatHistoryEntry({required this.role, required this.content});

  final String role;
  final String content;

  factory ChatHistoryEntry.fromJson(Map<String, dynamic> json) {
    return ChatHistoryEntry(
      role: json['role'] as String? ?? 'Null',
      content: json['content'] as String? ?? 'Null',
    );
  }
}

class ChatHistoryDatesResponse {
  const ChatHistoryDatesResponse({required this.dates, required this.today});

  final List<String> dates;
  final String today;

  factory ChatHistoryDatesResponse.fromJson(Map<String, dynamic> json) {
    return ChatHistoryDatesResponse(
      dates: (json['dates'] as List<dynamic>?)
              ?.map((date) => date?.toString() ?? 'Null')
              .toList() ??
          const <String>[],
      today: json['today'] as String? ?? 'Null',
    );
  }
}

class ChatHistoryResponse {
  const ChatHistoryResponse({required this.date, required this.entries, required this.isToday});

  final String date;
  final List<ChatHistoryEntry> entries;
  final bool isToday;

  factory ChatHistoryResponse.fromJson(Map<String, dynamic> json) {
    return ChatHistoryResponse(
      date: json['date'] as String? ?? 'Null',
      entries: (json['entries'] as List<dynamic>?)
              ?.map(
                (entry) => ChatHistoryEntry.fromJson(
                  entry is Map<String, dynamic> ? entry : const {},
                ),
              )
              .toList() ??
          const <ChatHistoryEntry>[],
      isToday: json['is_today'] as bool? ?? false,
    );
  }
}
