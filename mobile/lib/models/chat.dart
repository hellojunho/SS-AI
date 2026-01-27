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
      answer: json['answer'] as String,
      reference: json['reference'] as String,
      filePath: json['file_path'] as String,
    );
  }
}

class ChatHistoryEntry {
  const ChatHistoryEntry({required this.role, required this.content});

  final String role;
  final String content;

  factory ChatHistoryEntry.fromJson(Map<String, dynamic> json) {
    return ChatHistoryEntry(
      role: json['role'] as String,
      content: json['content'] as String,
    );
  }
}

class ChatHistoryDatesResponse {
  const ChatHistoryDatesResponse({required this.dates, required this.today});

  final List<String> dates;
  final String today;

  factory ChatHistoryDatesResponse.fromJson(Map<String, dynamic> json) {
    return ChatHistoryDatesResponse(
      dates: (json['dates'] as List<dynamic>).cast<String>(),
      today: json['today'] as String,
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
      date: json['date'] as String,
      entries: (json['entries'] as List<dynamic>)
          .map((entry) => ChatHistoryEntry.fromJson(entry as Map<String, dynamic>))
          .toList(),
      isToday: json['is_today'] as bool,
    );
  }
}
