import 'package:flutter/material.dart';

import '../services/auth_service.dart';

class MainBottomNav extends StatelessWidget {
  const MainBottomNav({
    super.key,
    required this.currentIndex,
    required this.authService,
  });

  final int currentIndex;
  final AuthService authService;

  Future<void> _handleTap(BuildContext context, int index) async {
    if (index == currentIndex) return;
    final authed = await authService.isAuthenticated();
    if (!authed) {
      if (!context.mounted) return;
      final shouldLogin = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('로그인이 필요합니다!'),
          content: const Text('로그인 후 이용할 수 있습니다.'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('취소'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('로그인하기'),
            ),
          ],
        ),
      );
      if (!context.mounted) return;
      if (shouldLogin == true) {
        Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
      }
      return;
    }

    final routeName = switch (index) {
      0 => '/chat',
      1 => '/quiz',
      _ => '/me',
    };
    Navigator.pushNamedAndRemoveUntil(context, routeName, (route) => route.isFirst);
  }

  @override
  Widget build(BuildContext context) {
    return BottomNavigationBar(
      currentIndex: currentIndex,
      onTap: (index) => _handleTap(context, index),
      items: const [
        BottomNavigationBarItem(
          icon: Text('💬', style: TextStyle(fontSize: 20)),
          label: '채팅',
        ),
        BottomNavigationBarItem(
          icon: Text('💡', style: TextStyle(fontSize: 20)),
          label: '퀴즈',
        ),
        BottomNavigationBarItem(
          icon: Text('👤', style: TextStyle(fontSize: 20)),
          label: '마이페이지',
        ),
      ],
    );
  }
}
