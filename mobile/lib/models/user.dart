class UserProfile {
  const UserProfile({
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

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] as int,
      userId: json['user_id'] as String,
      userName: json['user_name'] as String,
      email: json['email'] as String,
      role: json['role'] as String,
    );
  }
}

class DirectoryUser {
  const DirectoryUser({
    required this.id,
    required this.userId,
    required this.userName,
    required this.email,
    required this.role,
    required this.isActive,
    required this.createdAt,
    required this.lastLogined,
    required this.deactivatedAt,
  });

  final int id;
  final String userId;
  final String userName;
  final String email;
  final String role;
  final bool isActive;
  final DateTime? createdAt;
  final DateTime? lastLogined;
  final DateTime? deactivatedAt;

  factory DirectoryUser.fromJson(Map<String, dynamic> json) {
    return DirectoryUser(
      id: json['id'] as int,
      userId: json['user_id'] as String,
      userName: json['user_name'] as String,
      email: json['email'] as String,
      role: json['role'] as String,
      isActive: json['is_active'] as bool? ?? true,
      createdAt: json['created_at'] == null ? null : DateTime.parse(json['created_at'] as String),
      lastLogined: json['last_logined'] == null ? null : DateTime.parse(json['last_logined'] as String),
      deactivatedAt: json['deactivated_at'] == null ? null : DateTime.parse(json['deactivated_at'] as String),
    );
  }
}
