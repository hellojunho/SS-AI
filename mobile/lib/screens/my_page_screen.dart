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
      appBar: AppBar(title: const Text('내 정보')),
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
                          ListTile(
                            leading: const Icon(Icons.account_circle),
                            title: Text(_profile!.userName),
                            subtitle: Text(_profile!.userId),
                          ),
                          ListTile(
                            leading: const Icon(Icons.email_outlined),
                            title: Text(_profile!.email),
                            subtitle: Text('권한: ${_profile!.role}'),
                          ),
                          const SizedBox(height: 24),
                          ListTile(
                            leading: const Icon(Icons.history),
                            title: const Text('채팅 내역'),
                            subtitle: const Text('날짜별로 저장된 대화를 확인하세요.'),
                            trailing: const Icon(Icons.chevron_right),
                            onTap: () {
                              Navigator.pushNamed(context, '/me/history');
                            },
                          ),
                          if (_profile!.role == 'admin')
                            ListTile(
                              leading: const Icon(Icons.admin_panel_settings),
                              title: const Text('관리자 페이지'),
                              subtitle: const Text('사용자/퀴즈/토큰 현황을 확인합니다.'),
                              trailing: const Icon(Icons.chevron_right),
                              onTap: () {
                                Navigator.pushNamed(context, '/admin');
                              },
                            ),
                          const SizedBox(height: 16),
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
                        ],
                      ),
      ),
      bottomNavigationBar: const MainBottomNav(currentIndex: 2),
    );
  }
}
