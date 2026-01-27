import 'package:flutter/material.dart';

class MainBottomNav extends StatelessWidget {
  const MainBottomNav({super.key, required this.currentIndex});

  final int currentIndex;

  void _handleTap(BuildContext context, int index) {
    final routeName = switch (index) {
      0 => '/chat',
      1 => '/quiz',
      _ => '/me',
    };
    final currentRoute = ModalRoute.of(context)?.settings.name;
    if (currentRoute == routeName) {
      return;
    }
    Navigator.pushNamedAndRemoveUntil(context, routeName, (route) => false);
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
