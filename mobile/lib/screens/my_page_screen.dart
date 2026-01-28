import 'package:flutter/material.dart';

import '../app.dart';
import '../models/user.dart';
import '../widgets/main_bottom_nav.dart';

class MyPageScreen extends StatefulWidget {
  const MyPageScreen({super.key, required this.services, required this.onLogout});

  final AppServices services;
  final ValueChanged<bool> onLogout;

  @override
  State<MyPageScreen> createState() => _MyPageScreenState();
}

class _MyPageScreenState extends State<MyPageScreen> {
  UserProfile? _profile;
  String? _error;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final profile = await widget.services.authService.fetchMe();
      setState(() {
        _profile = profile;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('마이페이지')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
                : _profile == null
                    ? const Center(child: Text('정보를 불러올 수 없습니다.'))
                    : Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            '학습 기록과 퀴즈 성과를 확인하는 공간입니다.',
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                          const SizedBox(height: 16),
                          _InfoCard(
                            title: '오늘의 학습 요약',
                            description: '대화 기록을 요약해 퀴즈를 만들 수 있어요.',
                            icon: Icons.lightbulb_outline,
                          ),
                          const SizedBox(height: 12),
                          _ActionCard(
                            title: '오답노트',
                            description: '내가 틀렸던 문제만 다시 풀어볼 수 있어요.',
                            icon: Icons.fact_check_outlined,
                            onTap: () {
                              Navigator.pushNamed(context, '/me/wrong-notes');
                            },
                          ),
                          const SizedBox(height: 12),
                          _ActionCard(
                            title: '채팅 시작하기',
                            description: '채팅 창을 눌러 스포츠 과학 질문을 이어가세요.',
                            icon: Icons.chat_bubble_outline,
                            onTap: () {
                              Navigator.pushNamed(context, '/chat');
                            },
                          ),
                          if (_profile!.role == 'admin') ...[
                            const SizedBox(height: 12),
                            _ActionCard(
                              title: '관리자 페이지',
                              description: '사용자 대화 기록 기반 퀴즈를 생성할 수 있습니다.',
                              icon: Icons.admin_panel_settings,
                              onTap: () {
                                Navigator.pushNamed(context, '/admin');
                              },
                            ),
                          ],
                          const SizedBox(height: 16),
                          _InfoCard(
                            title: '계정',
                            description: '현재 계정에서 안전하게 로그아웃할 수 있어요.',
                            icon: Icons.lock_outline,
                            action: Wrap(
                              spacing: 8,
                              children: [
                                OutlinedButton.icon(
                                  onPressed: () async {
                                    await widget.services.authService.logout();
                                    widget.onLogout(false);
                                    if (mounted) {
                                      Navigator.popUntil(context, ModalRoute.withName('/'));
                                    }
                                  },
                                  icon: const Icon(Icons.logout),
                                  label: const Text('로그아웃'),
                                ),
                                OutlinedButton.icon(
                                  onPressed: () async {
                                    final confirm = await showDialog<bool>(
                                      context: context,
                                      builder: (dialogContext) => AlertDialog(
                                        title: const Text('회원 탈퇴'),
                                        content: const Text('정말로 회원 탈퇴를 진행하시겠습니까?'),
                                        actions: [
                                          TextButton(
                                            onPressed: () => Navigator.pop(dialogContext, false),
                                            child: const Text('취소'),
                                          ),
                                          TextButton(
                                            onPressed: () => Navigator.pop(dialogContext, true),
                                            child: const Text('탈퇴'),
                                          ),
                                        ],
                                      ),
                                    );
                                    if (confirm != true) return;
                                    try {
                                      await widget.services.authService.withdraw();
                                      widget.onLogout(false);
                                      if (mounted) {
                                        Navigator.popUntil(context, ModalRoute.withName('/'));
                                      }
                                    } catch (error) {
                                      if (mounted) {
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          SnackBar(content: Text('회원 탈퇴에 실패했습니다.')),
                                        );
                                      }
                                    }
                                  },
                                  icon: const Icon(Icons.person_off),
                                  label: const Text('회원 탈퇴'),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
      ),
      bottomNavigationBar: const MainBottomNav(currentIndex: 2),
    );
  }
}

class _ActionCard extends StatelessWidget {
  const _ActionCard({
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
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        ),
        child: Row(
          children: [
            CircleAvatar(
              radius: 22,
              child: Icon(icon, size: 22),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 4),
                  Text(description, style: Theme.of(context).textTheme.bodySmall),
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

class _InfoCard extends StatelessWidget {
  const _InfoCard({
    required this.title,
    required this.description,
    required this.icon,
    this.action,
  });

  final String title;
  final String description;
  final IconData icon;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.5),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 22,
            backgroundColor: Theme.of(context).colorScheme.surface,
            child: Icon(icon, size: 22),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 4),
                Text(description, style: Theme.of(context).textTheme.bodySmall),
                if (action != null) ...[
                  const SizedBox(height: 12),
                  action!,
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
