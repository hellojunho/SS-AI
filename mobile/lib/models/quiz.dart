class Quiz {
  const Quiz({
    required this.id,
    required this.title,
    required this.question,
    required this.choices,
    required this.correct,
    required this.explanation,
    required this.reference,
    required this.hasCorrectAttempt,
    required this.hasWrongAttempt,
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
  final bool hasCorrectAttempt;
  final bool hasWrongAttempt;
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
      hasCorrectAttempt: json['has_correct_attempt'] as bool? ?? false,
      hasWrongAttempt: json['has_wrong_attempt'] as bool? ?? false,
      currentIndex: json['current_index'] as int?,
      totalCount: json['total_count'] as int?,
    );
  }
}

class QuizAnswerResult {
  const QuizAnswerResult({
    required this.quizId,
    required this.questionId,
    required this.answer,
    required this.isCorrect,
    required this.isWrong,
    required this.hasCorrectAttempt,
    required this.hasWrongAttempt,
    required this.answerHistory,
  });

  final int quizId;
  final int questionId;
  final String answer;
  final bool isCorrect;
  final bool isWrong;
  final bool hasCorrectAttempt;
  final bool hasWrongAttempt;
  final List<String> answerHistory;

  factory QuizAnswerResult.fromJson(Map<String, dynamic> json) {
    return QuizAnswerResult(
      quizId: json['quiz_id'] as int,
      questionId: json['question_id'] as int,
      answer: json['answer'] as String,
      isCorrect: json['is_correct'] as bool,
      isWrong: json['is_wrong'] as bool,
      hasCorrectAttempt: json['has_correct_attempt'] as bool,
      hasWrongAttempt: json['has_wrong_attempt'] as bool,
      answerHistory: (json['answer_history'] as List<dynamic>).cast<String>(),
    );
  }
}

class QuizResultSummary {
  const QuizResultSummary({
    required this.totalCount,
    required this.correctCount,
    required this.wrongCount,
    required this.accuracyRate,
  });

  final int totalCount;
  final int correctCount;
  final int wrongCount;
  final double accuracyRate;

  factory QuizResultSummary.fromJson(Map<String, dynamic> json) {
    return QuizResultSummary(
      totalCount: json['total_count'] as int? ?? 0,
      correctCount: json['correct_count'] as int? ?? 0,
      wrongCount: json['wrong_count'] as int? ?? 0,
      accuracyRate: (json['accuracy_rate'] as num?)?.toDouble() ?? 0,
    );
  }
}
