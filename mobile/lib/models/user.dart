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
      id: json['id'] as int? ?? 0,
      userId: json['user_id'] as String? ?? 'Null',
      userName: json['user_name'] as String? ?? 'Null',
      email: json['email'] as String? ?? 'Null',
      role: json['role'] as String? ?? 'Null',
    );
  }
}
