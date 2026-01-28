class WrongNoteQuestion {
  const WrongNoteQuestion({
    required this.quizId,
    required this.questionId,
    required this.question,
    required this.choices,
    required this.correct,
    required this.wrong,
    required this.explanation,
    required this.reference,
    required this.link,
  });

  final int quizId;
  final int questionId;
  final String question;
  final List<String> choices;
  final String correct;
  final List<String> wrong;
  final String explanation;
  final String reference;
  final String link;

  factory WrongNoteQuestion.fromJson(Map<String, dynamic> json) {
    return WrongNoteQuestion(
      quizId: json['quiz_id'] as int? ?? 0,
      questionId: json['question_id'] as int? ?? 0,
      question: json['question'] as String? ?? 'Null',
      choices: (json['choices'] as List<dynamic>?)
              ?.map((choice) => choice?.toString() ?? 'Null')
              .toList() ??
          const <String>[],
      correct: json['correct'] as String? ?? 'Null',
      wrong: (json['wrong'] as List<dynamic>?)
              ?.map((entry) => entry?.toString() ?? 'Null')
              .toList() ??
          const <String>[],
      explanation: json['explanation'] as String? ?? 'Null',
      reference: json['reference'] as String? ?? 'Null',
      link: json['link'] as String? ?? 'Null',
    );
  }
}
