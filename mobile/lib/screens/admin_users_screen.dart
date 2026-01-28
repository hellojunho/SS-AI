import 'package:flutter/material.dart';

import '../app.dart';
import '../models/admin.dart';

class AdminUsersScreen extends StatefulWidget {
  const AdminUsersScreen({super.key, required this.services});

  final AppServices services;

  @override
  State<AdminUsersScreen> createState() => _AdminUsersScreenState();
}

class _AdminUsersScreenState extends State<AdminUsersScreen> {
  bool _isLoading = true;
  String? _error;
  List<AdminUser> _users = [];

  @override
  void initState() {
    super.initState();
    _loadUsers();
  }

  Future<void> _loadUsers() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final users = await widget.services.adminService.fetchUsers();
      setState(() {
        _users = users;
      });
    } catch (error) {
      setState(() {
        _error = '사용자 정보를 불러오지 못했습니다.';
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
      appBar: AppBar(title: const Text('사용자 관리')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : RefreshIndicator(
                  onRefresh: _loadUsers,
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: _users.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                      final user = _users[index];
                      return ListTile(
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        tileColor: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.4),
                        title: Text(user.userName),
                        subtitle: Text('${user.userId} · ${user.email}'),
                        trailing: Text(user.isActive ? '활성' : '탈퇴'),
                        onTap: () async {
                          final updated = await Navigator.push<AdminUser?>(
                            context,
                            MaterialPageRoute(
                              builder: (_) => AdminUserDetailScreen(
                                services: widget.services,
                                userId: user.id,
                              ),
                            ),
                          );
                          if (updated != null) {
                            setState(() {
                              _users = _users
                                  .map((item) => item.id == updated.id ? updated : item)
                                  .toList();
                            });
                          } else {
                            await _loadUsers();
                          }
                        },
                      );
                    },
                  ),
                ),
    );
  }
}

class AdminUserDetailScreen extends StatefulWidget {
  const AdminUserDetailScreen({super.key, required this.services, required this.userId});

  final AppServices services;
  final int userId;

  @override
  State<AdminUserDetailScreen> createState() => _AdminUserDetailScreenState();
}

class _AdminUserDetailScreenState extends State<AdminUserDetailScreen> {
  bool _isLoading = true;
  bool _isSaving = false;
  bool _isDeleting = false;
  String? _error;
  AdminUser? _user;
  late TextEditingController _nameController;
  late TextEditingController _emailController;
  late TextEditingController _passwordController;
  String _role = 'general';

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController();
    _emailController = TextEditingController();
    _passwordController = TextEditingController();
    _loadUser();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _loadUser() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final user = await widget.services.adminService.fetchUserDetail(widget.userId);
      setState(() {
        _user = user;
        _nameController.text = user.userName;
        _emailController.text = user.email;
        _role = user.role;
      });
    } catch (error) {
      setState(() {
        _error = '사용자 정보를 불러오지 못했습니다.';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _saveUser() async {
    if (_user == null) return;
    setState(() {
      _isSaving = true;
      _error = null;
    });
    try {
      final payload = {
        'user_name': _nameController.text.trim(),
        'email': _emailController.text.trim(),
        'role': _role,
        if (_passwordController.text.trim().isNotEmpty)
          'password': _passwordController.text.trim(),
      };
      final updated =
          await widget.services.adminService.updateUser(widget.userId, payload);
      setState(() {
        _user = updated;
        _passwordController.clear();
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('사용자 정보가 저장되었습니다.')),
        );
      }
    } catch (error) {
      setState(() {
        _error = '사용자 정보를 저장하지 못했습니다.';
      });
    } finally {
      setState(() {
        _isSaving = false;
      });
    }
  }

  Future<void> _deleteUser() async {
    if (_user == null) return;
    final confirm = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('사용자 삭제'),
        content: const Text('해당 사용자를 삭제하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('삭제'),
          ),
        ],
      ),
    );
    if (confirm != true) return;
    setState(() {
      _isDeleting = true;
      _error = null;
    });
    try {
      await widget.services.adminService.deleteUser(widget.userId);
      if (mounted) {
        Navigator.pop(context, _user);
      }
    } catch (error) {
      setState(() {
        _error = '사용자를 삭제하지 못했습니다.';
      });
    } finally {
      setState(() {
        _isDeleting = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = _user;
    return Scaffold(
      appBar: AppBar(title: const Text('사용자 상세')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : user == null
                  ? const Center(child: Text('사용자 정보를 찾을 수 없습니다.'))
                  : ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        Text('아이디: ${user.userId}'),
                        const SizedBox(height: 8),
                        Text('상태: ${user.isActive ? '활성' : '탈퇴'}'),
                        if (user.deactivatedAt != null) ...[
                          const SizedBox(height: 4),
                          Text('탈퇴 일시: ${user.deactivatedAt}'),
                        ],
                        const SizedBox(height: 16),
                        TextField(
                          controller: _nameController,
                          decoration: const InputDecoration(labelText: '이름'),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _emailController,
                          decoration: const InputDecoration(labelText: '이메일'),
                        ),
                        const SizedBox(height: 12),
                        DropdownButtonFormField<String>(
                          value: _role,
                          decoration: const InputDecoration(labelText: '역할'),
                          items: const [
                            DropdownMenuItem(value: 'general', child: Text('general')),
                            DropdownMenuItem(value: 'admin', child: Text('admin')),
                          ],
                          onChanged: (value) {
                            if (value == null) return;
                            setState(() {
                              _role = value;
                            });
                          },
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _passwordController,
                          decoration: const InputDecoration(labelText: '새 비밀번호'),
                          obscureText: true,
                        ),
                        const SizedBox(height: 20),
                        FilledButton(
                          onPressed: _isSaving ? null : _saveUser,
                          child: Text(_isSaving ? '저장 중...' : '저장'),
                        ),
                        const SizedBox(height: 12),
                        OutlinedButton(
                          onPressed: _isDeleting ? null : _deleteUser,
                          child: Text(_isDeleting ? '삭제 중...' : '삭제'),
                        ),
                        if (_error != null)
                          Padding(
                            padding: const EdgeInsets.only(top: 12),
                            child: Text(_error!, style: const TextStyle(color: Colors.red)),
                          ),
                      ],
                    ),
    );
  }
}
