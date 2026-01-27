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
