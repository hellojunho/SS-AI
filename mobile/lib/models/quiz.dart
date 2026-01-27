class Quiz {
  const Quiz({
    required this.id,
    required this.title,
    required this.question,
    required this.choices,
    required this.correct,
    required this.explanation,
    required this.reference,
    required this.currentIndex,
    required this.totalCount,
  });

  final int id;
  final String title;
  final String question;
  final List<String> choices;
  final String correct;
  final String explanation;
  final String reference;
  final int? currentIndex;
  final int? totalCount;

  factory Quiz.fromJson(Map<String, dynamic> json) {
    return Quiz(
      id: json['id'] as int,
      title: json['title'] as String,
      question: json['question'] as String,
      choices: (json['choices'] as List<dynamic>).cast<String>(),
      correct: json['correct'] as String,
      explanation: json['explanation'] as String,
      reference: json['reference'] as String,
      currentIndex: json['current_index'] as int?,
      totalCount: json['total_count'] as int?,
    );
  }
}
