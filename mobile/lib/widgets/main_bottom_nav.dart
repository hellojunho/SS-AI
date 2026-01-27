import 'package:flutter/material.dart';

class MainBottomNav extends StatelessWidget {
  const MainBottomNav({super.key, required this.currentIndex});

  final int currentIndex;

  void _handleTap(BuildContext context, int index) {
    if (index == currentIndex) return;
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
          label: 'Chat',
        ),
        BottomNavigationBarItem(
          icon: Text('💡', style: TextStyle(fontSize: 20)),
          label: 'Quiz',
        ),
        BottomNavigationBarItem(
          icon: Text('👤', style: TextStyle(fontSize: 20)),
          label: '마이페이지',
        ),
      ],
    );
  }
}
