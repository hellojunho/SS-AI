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
      id: json['id'] as int,
      userId: json['user_id'] as String,
      userName: json['user_name'] as String,
      email: json['email'] as String,
      role: json['role'] as String,
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
