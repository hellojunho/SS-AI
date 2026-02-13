import 'package:flutter/material.dart';

import '../app.dart';
import '../models/user.dart';

class CoachStudentsScreen extends StatefulWidget {
  const CoachStudentsScreen({super.key, required this.services});

  final AppServices services;

  @override
  State<CoachStudentsScreen> createState() => _CoachStudentsScreenState();
}

class _CoachStudentsScreenState extends State<CoachStudentsScreen> {
  bool _isLoading = true;
  bool _isAllowed = false;
  String? _error;
  String? _message;

  final TextEditingController _registerController = TextEditingController();
  final TextEditingController _searchController = TextEditingController();

  List<DirectoryUser> _registeredStudents = [];
  List<DirectoryUser> _searchResults = [];
  List<DirectoryUser> _selectedStudents = [];

  bool _searchLoading = false;
  bool _registerLoading = false;
  bool _batchLoading = false;

  @override
  void initState() {
    super.initState();
    _loadProfileAndStudents();
  }

  @override
  void dispose() {
    _registerController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadProfileAndStudents() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _message = null;
    });
    try {
      final profile = await widget.services.authService.fetchMe();
      if (profile.role != 'coach') {
        setState(() {
          _isAllowed = false;
          _error = '코치만 접근할 수 있습니다.';
        });
        return;
      }
      _isAllowed = true;
      await _loadRegisteredStudents();
    } catch (error) {
      setState(() {
        _error = '권한 정보를 확인하지 못했습니다.';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadRegisteredStudents() async {
    try {
      final students = await widget.services.coachService.fetchStudents();
      setState(() {
        _registeredStudents = students;
      });
    } catch (error) {
      setState(() {
        _error = '학생 목록을 불러오지 못했습니다.';
      });
    }
  }

  Future<void> _searchStudents() async {
    final keyword = _searchController.text.trim();
    if (keyword.isEmpty) {
      setState(() {
        _searchResults = [];
        _message = '검색어를 입력해주세요.';
      });
      return;
    }
    setState(() {
      _searchLoading = true;
      _message = null;
    });
    try {
      final results = await widget.services.coachService.searchStudents(keyword);
      setState(() {
        _searchResults = results;
      });
    } catch (error) {
      setState(() {
        _message = '학생 검색에 실패했습니다.';
      });
    } finally {
      setState(() {
        _searchLoading = false;
      });
    }
  }

  Future<void> _registerSingleStudent() async {
    final targetId = _registerController.text.trim();
    if (targetId.isEmpty || _registerLoading) return;
    setState(() {
      _registerLoading = true;
      _message = null;
    });
    try {
      final student = await widget.services.coachService.registerStudent(targetId);
      setState(() {
        _registeredStudents = [student, ..._registeredStudents];
        _registerController.clear();
        _message = '학생 등록이 완료되었습니다.';
      });
    } catch (error) {
      setState(() {
        _message = error.toString();
      });
    } finally {
      setState(() {
        _registerLoading = false;
      });
    }
  }

  void _addSelectedStudent(DirectoryUser student) {
    final isRegistered = _registeredStudents.any((item) => item.userId == student.userId);
    if (isRegistered) {
      setState(() {
        _message = '이미 등록된 학생입니다.';
      });
      return;
    }
    final exists = _selectedStudents.any((item) => item.userId == student.userId);
    if (exists) return;
    setState(() {
      _selectedStudents = [student, ..._selectedStudents];
      _message = null;
    });
  }

  void _removeSelectedStudent(DirectoryUser student) {
    setState(() {
      _selectedStudents = _selectedStudents.where((item) => item.userId != student.userId).toList();
    });
  }

  Future<void> _registerSelectedStudents() async {
    if (_batchLoading || _selectedStudents.isEmpty) return;
    setState(() {
      _batchLoading = true;
      _message = null;
    });

    final results = <DirectoryUser>[];
    final failedIds = <String>{};
    int alreadyCount = 0;

    for (final student in _selectedStudents) {
      try {
        final created = await widget.services.coachService.registerStudent(student.userId);
        results.add(created);
      } catch (error) {
        final message = error.toString();
        if (message.contains('이미 등록된 학생')) {
          alreadyCount += 1;
        } else {
          failedIds.add(student.userId);
        }
      }
    }

    setState(() {
      if (results.isNotEmpty) {
        final existingIds = _registeredStudents.map((item) => item.userId).toSet();
        final merged = results.where((item) => !existingIds.contains(item.userId)).toList();
        _registeredStudents = [...merged, ..._registeredStudents];
      }
      _selectedStudents = _selectedStudents.where((item) => failedIds.contains(item.userId)).toList();

      final messages = <String>[];
      if (results.isNotEmpty) {
        messages.add('${results.length}명 등록 완료');
      }
      if (alreadyCount > 0) {
        messages.add('${alreadyCount}명은 이미 등록됨');
      }
      if (failedIds.isNotEmpty) {
        messages.add('${failedIds.length}명 등록 실패');
      }
      _message = messages.join(' · ');
      _batchLoading = false;
    });
  }

  Future<void> _removeRegisteredStudent(DirectoryUser student) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('학생 등록 해제'),
        content: Text('${student.userId} 학생을 등록 해제할까요?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('해제'),
          ),
        ],
      ),
    );
    if (confirm != true) return;
    try {
      await widget.services.coachService.removeStudent(student.userId);
      setState(() {
        _registeredStudents =
            _registeredStudents.where((item) => item.userId != student.userId).toList();
        _message = '학생 등록이 해제되었습니다.';
      });
    } catch (error) {
      setState(() {
        _message = '학생 등록 해제에 실패했습니다.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('학생 등록 대시보드')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : !_isAllowed
              ? Center(child: Text(_error ?? '접근 권한이 없습니다.'))
              : RefreshIndicator(
                  onRefresh: _loadRegisteredStudents,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      if (_message != null)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: Text(
                            _message!,
                            style: TextStyle(color: Theme.of(context).colorScheme.primary),
                          ),
                        ),
                      _SectionCard(
                        title: '학생 등록',
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            TextField(
                              controller: _registerController,
                              decoration: const InputDecoration(
                                labelText: '학생 아이디',
                                hintText: '예: student01',
                              ),
                            ),
                            const SizedBox(height: 12),
                            FilledButton(
                              onPressed: _registerLoading ? null : _registerSingleStudent,
                              child: Text(_registerLoading ? '등록 중...' : '학생 등록'),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                      _SectionCard(
                        title: '학생 검색',
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            TextField(
                              controller: _searchController,
                              decoration: const InputDecoration(
                                labelText: '검색어',
                                hintText: '아이디/이름/이메일로 검색하세요',
                              ),
                              onSubmitted: (_) => _searchStudents(),
                            ),
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                Expanded(
                                  child: FilledButton(
                                    onPressed: _searchLoading ? null : _searchStudents,
                                    child: Text(_searchLoading ? '검색 중...' : '학생 검색'),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                OutlinedButton(
                                  onPressed: _searchLoading
                                      ? null
                                      : () {
                                          _searchController.clear();
                                          setState(() {
                                            _searchResults = [];
                                          });
                                        },
                                  child: const Text('초기화'),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                      _SectionCard(
                        title: '검색 결과',
                        child: _searchResults.isEmpty
                            ? const Text('검색 결과가 없습니다.')
                            : Column(
                                children: _searchResults
                                    .map(
                                      (student) => _UserTile(
                                        user: student,
                                        onTap: () => _addSelectedStudent(student),
                                        trailing: _buildSearchStatus(student),
                                      ),
                                    )
                                    .toList(),
                              ),
                      ),
                      const SizedBox(height: 16),
                      _SectionCard(
                        title: '등록 대기 학생',
                        child: Column(
                          children: [
                            if (_selectedStudents.isEmpty)
                              const Text('등록 대기 학생이 없습니다.')
                            else
                              ..._selectedStudents
                                  .map(
                                    (student) => _UserTile(
                                      user: student,
                                      trailing: IconButton(
                                        icon: const Icon(Icons.close),
                                        onPressed: () => _removeSelectedStudent(student),
                                      ),
                                    ),
                                  )
                                  .toList(),
                            const SizedBox(height: 12),
                            Align(
                              alignment: Alignment.centerRight,
                              child: FilledButton(
                                onPressed:
                                    _batchLoading || _selectedStudents.isEmpty ? null : _registerSelectedStudents,
                                child: Text(_batchLoading ? '등록 중...' : '선택 학생 등록'),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                      _SectionCard(
                        title: '등록된 학생',
                        child: _registeredStudents.isEmpty
                            ? const Text('등록된 학생이 없습니다.')
                            : Column(
                                children: _registeredStudents
                                    .map(
                                      (student) => _UserTile(
                                        user: student,
                                        trailing: TextButton(
                                          onPressed: () => _removeRegisteredStudent(student),
                                          child: const Text('등록 해제'),
                                        ),
                                      ),
                                    )
                                    .toList(),
                              ),
                      ),
                    ],
                  ),
                ),
    );
  }

  Widget _buildSearchStatus(DirectoryUser student) {
    final isRegistered = _registeredStudents.any((item) => item.userId == student.userId);
    if (isRegistered) {
      return const Text('등록됨', style: TextStyle(color: Colors.grey));
    }
    final isSelected = _selectedStudents.any((item) => item.userId == student.userId);
    if (isSelected) {
      return const Text('선택됨', style: TextStyle(color: Colors.grey));
    }
    return const Icon(Icons.add_circle_outline);
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }
}

class _UserTile extends StatelessWidget {
  const _UserTile({required this.user, this.onTap, this.trailing});

  final DirectoryUser user;
  final VoidCallback? onTap;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      title: Text(user.userName),
      subtitle: Text('${user.userId} · ${user.email} · ${user.role}'),
      trailing: trailing,
      onTap: onTap,
    );
  }
}
