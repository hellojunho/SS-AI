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
      setState(() {
        _userCount = users.length;
        _quizCount = quizzes.length;
        _usage = usage;
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
