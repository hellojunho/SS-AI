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
