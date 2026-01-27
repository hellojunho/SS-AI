import 'package:flutter/material.dart';

import '../app.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key, required this.services, required this.onLogout});

  final AppServices services;
  final ValueChanged<bool> onLogout;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('SS-AI 홈'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person),
            onPressed: () => Navigator.pushNamed(context, '/me'),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              '스포츠 과학 학습을 시작하세요.',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 24),
            _HomeTile(
              title: 'AI Q&A',
              description: '질문을 입력하고 문서 기반 답변을 받아보세요.',
              icon: Icons.chat_bubble_outline,
              onTap: () => Navigator.pushNamed(context, '/chat'),
            ),
            const SizedBox(height: 16),
            _HomeTile(
              title: '퀴즈 학습',
              description: '최신 퀴즈를 풀고 학습 상태를 확인합니다.',
              icon: Icons.quiz_outlined,
              onTap: () => Navigator.pushNamed(context, '/quiz'),
            ),
            const Spacer(),
            OutlinedButton.icon(
              onPressed: () async {
                await services.authService.logout();
                onLogout(false);
              },
              icon: const Icon(Icons.logout),
              label: const Text('로그아웃'),
            ),
          ],
        ),
      ),
    );
  }
}

class _HomeTile extends StatelessWidget {
  const _HomeTile({
    required this.title,
    required this.description,
    required this.icon,
    required this.onTap,
  });

  final String title;
  final String description;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        ),
        child: Row(
          children: [
            CircleAvatar(
              radius: 28,
              child: Icon(icon, size: 28),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 4),
                  Text(description, style: Theme.of(context).textTheme.bodyMedium),
                ],
              ),
            ),
            const Icon(Icons.chevron_right),
          ],
        ),
      ),
    );
  }
}
