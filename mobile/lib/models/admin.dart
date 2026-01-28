class AdminUser {
  const AdminUser({
    required this.id,
    required this.userId,
    required this.userName,
    required this.email,
    required this.role,
    required this.isActive,
    required this.deactivatedAt,
  });

  final int id;
  final String userId;
  final String userName;
  final String email;
  final String role;
  final bool isActive;
  final DateTime? deactivatedAt;

  factory AdminUser.fromJson(Map<String, dynamic> json) {
    return AdminUser(
      id: json['id'] as int,
      userId: json['user_id'] as String,
      userName: json['user_name'] as String,
      email: json['email'] as String,
      role: json['role'] as String,
      isActive: json['is_active'] as bool? ?? true,
      deactivatedAt: json['deactivated_at'] == null
          ? null
          : DateTime.parse(json['deactivated_at'] as String),
    );
  }
}

class AdminQuizSummary {
  const AdminQuizSummary({required this.id, required this.title, required this.sourceUserId});

  final int id;
  final String title;
  final String sourceUserId;

  factory AdminQuizSummary.fromJson(Map<String, dynamic> json) {
    return AdminQuizSummary(
      id: json['id'] as int,
      title: json['title'] as String,
      sourceUserId: (json['source_user_id'] as String?) ?? '',
    );
  }
}

class AdminQuizDetail {
  const AdminQuizDetail({
    required this.id,
    required this.title,
    required this.question,
    required this.choices,
    required this.correct,
    required this.wrong,
    required this.explanation,
    required this.reference,
    required this.link,
    required this.sourceUserId,
  });

  final int id;
  final String title;
  final String question;
  final List<String> choices;
  final String correct;
  final List<String> wrong;
  final String explanation;
  final String reference;
  final String link;
  final String sourceUserId;

  factory AdminQuizDetail.fromJson(Map<String, dynamic> json) {
    return AdminQuizDetail(
      id: json['id'] as int,
      title: json['title'] as String,
      question: json['question'] as String,
      choices: (json['choices'] as List<dynamic>).map((item) => item.toString()).toList(),
      correct: json['correct'] as String,
      wrong: (json['wrong'] as List<dynamic>).map((item) => item.toString()).toList(),
      explanation: json['explanation'] as String,
      reference: json['reference'] as String,
      link: json['link'] as String? ?? '',
      sourceUserId: json['source_user_id'] as String? ?? '',
    );
  }
}

class AdminTrafficStats {
  const AdminTrafficStats({
    required this.period,
    required this.signups,
    required this.logins,
    required this.withdrawals,
  });

  final String period;
  final int signups;
  final int logins;
  final int withdrawals;

  factory AdminTrafficStats.fromJson(Map<String, dynamic> json) {
    return AdminTrafficStats(
      period: json['period'] as String,
      signups: json['signups'] as int,
      logins: json['logins'] as int,
      withdrawals: json['withdrawals'] as int,
    );
  }
}

class LlmUsage {
  const LlmUsage({
    required this.provider,
    required this.model,
    required this.totalTokens,
    required this.usedTokens,
    required this.remainingTokens,
    required this.promptTokens,
    required this.completionTokens,
    required this.lastUpdated,
  });

  final String provider;
  final String model;
  final int totalTokens;
  final int usedTokens;
  final int remainingTokens;
  final int promptTokens;
  final int completionTokens;
  final DateTime? lastUpdated;

  factory LlmUsage.fromJson(Map<String, dynamic> json) {
    return LlmUsage(
      provider: json['provider'] as String,
      model: json['model'] as String,
      totalTokens: json['total_tokens'] as int,
      usedTokens: json['used_tokens'] as int,
      remainingTokens: json['remaining_tokens'] as int,
      promptTokens: json['prompt_tokens'] as int,
      completionTokens: json['completion_tokens'] as int,
      lastUpdated:
          json['last_updated'] == null ? null : DateTime.parse(json['last_updated'] as String),
    );
  }
}
