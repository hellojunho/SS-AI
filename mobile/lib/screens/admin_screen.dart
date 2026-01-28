import 'package:flutter/material.dart';

import '../app.dart';
import '../models/admin.dart';
import '../widgets/main_bottom_nav.dart';

class AdminScreen extends StatefulWidget {
  const AdminScreen({super.key, required this.services});

  final AppServices services;

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> {
  bool _isLoading = true;
  String? _error;
  int _userCount = 0;
  int _quizCount = 0;
  LlmUsage? _usage;
  String? _jobId;
  List<AdminTrafficStats> _trafficStats = [];

  @override
  void initState() {
    super.initState();
    _loadAdminDashboard();
  }

  Future<void> _loadAdminDashboard() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final users = await widget.services.adminService.fetchUsers();
      final quizzes = await widget.services.adminService.fetchQuizzes();
      final usage = await widget.services.adminService.fetchLlmUsage();
      final traffic = await widget.services.adminService.fetchTrafficStats();
      setState(() {
        _userCount = users.length;
        _quizCount = quizzes.length;
        _usage = usage;
        _trafficStats = traffic;
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

  Future<void> _generateAllQuizzes() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final jobId = await widget.services.adminService.generateAllQuizzes();
      setState(() {
        _jobId = jobId;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('퀴즈 생성 작업이 시작되었습니다. 작업 ID: $jobId')),
        );
      }
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
      appBar: AppBar(title: const Text('관리자 대시보드')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : RefreshIndicator(
                  onRefresh: _loadAdminDashboard,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      _StatCard(title: '총 사용자', value: '$_userCount명', icon: Icons.people),
                      _StatCard(title: '총 퀴즈', value: '$_quizCount개', icon: Icons.quiz),
                      if (_usage != null)
                        _StatCard(
                          title: 'ChatGPT 토큰 사용량',
                          value: '${_usage!.usedTokens} / ${_usage!.totalTokens}',
                          subtitle:
                              '프롬프트 ${_usage!.promptTokens}, 응답 ${_usage!.completionTokens}',
                          icon: Icons.bolt,
                        ),
                      if (_trafficStats.isNotEmpty)
                        _TrafficCard(stats: _trafficStats),
                      const SizedBox(height: 12),
                      _ActionCard(
                        title: '사용자 관리',
                        description: '사용자 정보를 확인하고 수정할 수 있습니다.',
                        icon: Icons.people,
                        onTap: () {
                          Navigator.pushNamed(context, '/admin/users');
                        },
                      ),
                      const SizedBox(height: 12),
                      _ActionCard(
                        title: '퀴즈 대시보드',
                        description: '퀴즈 정보를 확인하고 수정할 수 있습니다.',
                        icon: Icons.quiz,
                        onTap: () {
                          Navigator.pushNamed(context, '/admin/quizzes');
                        },
                      ),
                      const SizedBox(height: 12),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('퀴즈 생성', style: Theme.of(context).textTheme.titleMedium),
                              const SizedBox(height: 8),
                              const Text('전체 사용자 요약을 기반으로 퀴즈 생성을 시작합니다.'),
                              const SizedBox(height: 12),
                              FilledButton.icon(
                                onPressed: _isLoading ? null : _generateAllQuizzes,
                                icon: const Icon(Icons.play_circle),
                                label: const Text('전체 퀴즈 생성 시작'),
                              ),
                              if (_jobId != null) ...[
                                const SizedBox(height: 8),
                                Text('최근 작업 ID: $_jobId'),
                              ],
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
      bottomNavigationBar: const MainBottomNav(currentIndex: 2),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
    this.subtitle,
  });

  final String title;
  final String value;
  final String? subtitle;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(icon, size: 36, color: Colors.indigo),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 4),
                  Text(value, style: Theme.of(context).textTheme.headlineSmall),
                  if (subtitle != null) ...[
                    const SizedBox(height: 4),
                    Text(subtitle!, style: Theme.of(context).textTheme.bodySmall),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
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

class _TrafficCard extends StatelessWidget {
  const _TrafficCard({required this.stats});

  final List<AdminTrafficStats> stats;

  @override
  Widget build(BuildContext context) {
    final maxValue = stats
        .expand((item) => [item.signups, item.logins, item.withdrawals])
        .fold<int>(1, (prev, value) => value > prev ? value : prev);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('사용자 유입량', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            Text('일/주/월/년 단위 신규 가입, 로그인, 탈퇴 수', style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 8,
              children: const [
                _LegendChip(label: '신규 가입', color: Colors.blue),
                _LegendChip(label: '로그인', color: Colors.blueAccent),
                _LegendChip(label: '탈퇴', color: Colors.red),
              ],
            ),
            const SizedBox(height: 16),
            Column(
              children: stats.map((item) {
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Row(
                    children: [
                      SizedBox(
                        width: 32,
                        child: Text(_periodLabel(item.period)),
                      ),
                      Expanded(
                        child: SizedBox(
                          height: 80,
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              _Bar(value: item.signups, maxValue: maxValue, color: Colors.blue),
                              _Bar(value: item.logins, maxValue: maxValue, color: Colors.blueAccent),
                              _Bar(value: item.withdrawals, maxValue: maxValue, color: Colors.red),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  String _periodLabel(String period) {
    switch (period) {
      case 'day':
        return '일';
      case 'week':
        return '주';
      case 'month':
        return '월';
      case 'year':
        return '년';
      default:
        return period;
    }
  }
}

class _LegendChip extends StatelessWidget {
  const _LegendChip({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 10,
            height: 10,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 6),
          Text(label, style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}

class _Bar extends StatelessWidget {
  const _Bar({required this.value, required this.maxValue, required this.color});

  final int value;
  final int maxValue;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final ratio = maxValue == 0 ? 0.0 : value / maxValue;
    return Expanded(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            Expanded(
              child: Align(
                alignment: Alignment.bottomCenter,
                child: Container(
                  height: (ratio * 60).clamp(6, 60).toDouble(),
                  decoration: BoxDecoration(
                    color: color,
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 6),
            Text(
              value.toString(),
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}
