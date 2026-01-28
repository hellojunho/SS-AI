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
      id: json['id'] as int? ?? 0,
      title: json['title'] as String? ?? 'Null',
      question: json['question'] as String? ?? 'Null',
      choices: (json['choices'] as List<dynamic>?)
              ?.map((choice) => choice?.toString() ?? 'Null')
              .toList() ??
          const <String>[],
      correct: json['correct'] as String? ?? 'Null',
      explanation: json['explanation'] as String? ?? 'Null',
      reference: json['reference'] as String? ?? 'Null',
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
      quizId: json['quiz_id'] as int? ?? 0,
      questionId: json['question_id'] as int? ?? 0,
      answer: json['answer'] as String? ?? 'Null',
      isCorrect: json['is_correct'] as bool? ?? false,
      isWrong: json['is_wrong'] as bool? ?? false,
      hasCorrectAttempt: json['has_correct_attempt'] as bool? ?? false,
      hasWrongAttempt: json['has_wrong_attempt'] as bool? ?? false,
      answerHistory: (json['answer_history'] as List<dynamic>?)
              ?.map((entry) => entry?.toString() ?? 'Null')
              .toList() ??
          const <String>[],
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
