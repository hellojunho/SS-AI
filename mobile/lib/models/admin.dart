class AdminUser {
  const AdminUser({
    required this.id,
    required this.userId,
    required this.userName,
    required this.email,
    required this.role,
  });

  final int id;
  final String userId;
  final String userName;
  final String email;
  final String role;

  factory AdminUser.fromJson(Map<String, dynamic> json) {
    return AdminUser(
      id: json['id'] as int? ?? 0,
      userId: json['user_id'] as String? ?? 'Null',
      userName: json['user_name'] as String? ?? 'Null',
      email: json['email'] as String? ?? 'Null',
      role: json['role'] as String? ?? 'Null',
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
      id: json['id'] as int? ?? 0,
      title: json['title'] as String? ?? 'Null',
      sourceUserId: (json['source_user_id'] as String?) ?? 'Null',
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
      provider: json['provider'] as String? ?? 'Null',
      model: json['model'] as String? ?? 'Null',
      totalTokens: json['total_tokens'] as int? ?? 0,
      usedTokens: json['used_tokens'] as int? ?? 0,
      remainingTokens: json['remaining_tokens'] as int? ?? 0,
      promptTokens: json['prompt_tokens'] as int? ?? 0,
      completionTokens: json['completion_tokens'] as int? ?? 0,
      lastUpdated:
          json['last_updated'] == null ? null : DateTime.parse(json['last_updated'] as String),
    );
  }
}
