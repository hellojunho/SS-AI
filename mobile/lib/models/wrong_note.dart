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
      quizId: json['quiz_id'] as int,
      questionId: json['question_id'] as int,
      question: json['question'] as String,
      choices: (json['choices'] as List<dynamic>).cast<String>(),
      correct: json['correct'] as String,
      wrong: (json['wrong'] as List<dynamic>).cast<String>(),
      explanation: json['explanation'] as String,
      reference: json['reference'] as String,
      link: json['link'] as String,
    );
  }
}
