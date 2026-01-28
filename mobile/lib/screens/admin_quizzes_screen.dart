import 'package:flutter/material.dart';

import '../app.dart';
import '../models/admin.dart';

class AdminQuizzesScreen extends StatefulWidget {
  const AdminQuizzesScreen({super.key, required this.services});

  final AppServices services;

  @override
  State<AdminQuizzesScreen> createState() => _AdminQuizzesScreenState();
}

class _AdminQuizzesScreenState extends State<AdminQuizzesScreen> {
  bool _isLoading = true;
  String? _error;
  List<AdminQuizSummary> _quizzes = [];

  @override
  void initState() {
    super.initState();
    _loadQuizzes();
  }

  Future<void> _loadQuizzes() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final quizzes = await widget.services.adminService.fetchQuizzes();
      setState(() {
        _quizzes = quizzes;
      });
    } catch (error) {
      setState(() {
        _error = '퀴즈 정보를 불러오지 못했습니다.';
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
      appBar: AppBar(title: const Text('퀴즈 대시보드')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : RefreshIndicator(
                  onRefresh: _loadQuizzes,
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: _quizzes.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                      final quiz = _quizzes[index];
                      return ListTile(
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        tileColor: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.4),
                        title: Text(quiz.title),
                        subtitle: Text('생성 사용자: ${quiz.sourceUserId}'),
                        onTap: () async {
                          final updated = await Navigator.push<AdminQuizDetail?>(
                            context,
                            MaterialPageRoute(
                              builder: (_) => AdminQuizDetailScreen(
                                services: widget.services,
                                quizId: quiz.id,
                              ),
                            ),
                          );
                          if (updated != null) {
                            setState(() {
                              _quizzes = _quizzes
                                  .map((item) =>
                                      item.id == updated.id
                                          ? AdminQuizSummary(
                                              id: updated.id,
                                              title: updated.title,
                                              sourceUserId: updated.sourceUserId,
                                            )
                                          : item)
                                  .toList();
                            });
                          } else {
                            await _loadQuizzes();
                          }
                        },
                      );
                    },
                  ),
                ),
    );
  }
}

class AdminQuizDetailScreen extends StatefulWidget {
  const AdminQuizDetailScreen({super.key, required this.services, required this.quizId});

  final AppServices services;
  final int quizId;

  @override
  State<AdminQuizDetailScreen> createState() => _AdminQuizDetailScreenState();
}

class _AdminQuizDetailScreenState extends State<AdminQuizDetailScreen> {
  bool _isLoading = true;
  bool _isSaving = false;
  bool _isDeleting = false;
  String? _error;
  AdminQuizDetail? _quiz;
  late TextEditingController _titleController;
  late TextEditingController _questionController;
  late TextEditingController _choicesController;
  late TextEditingController _correctController;
  late TextEditingController _wrongController;
  late TextEditingController _explanationController;
  late TextEditingController _referenceController;
  late TextEditingController _linkController;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController();
    _questionController = TextEditingController();
    _choicesController = TextEditingController();
    _correctController = TextEditingController();
    _wrongController = TextEditingController();
    _explanationController = TextEditingController();
    _referenceController = TextEditingController();
    _linkController = TextEditingController();
    _loadQuiz();
  }

  @override
  void dispose() {
    _titleController.dispose();
    _questionController.dispose();
    _choicesController.dispose();
    _correctController.dispose();
    _wrongController.dispose();
    _explanationController.dispose();
    _referenceController.dispose();
    _linkController.dispose();
    super.dispose();
  }

  Future<void> _loadQuiz() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final quiz = await widget.services.adminService.fetchQuizDetail(widget.quizId);
      setState(() {
        _quiz = quiz;
        _titleController.text = quiz.title;
        _questionController.text = quiz.question;
        _choicesController.text = quiz.choices.join('\n');
        _correctController.text = quiz.correct;
        _wrongController.text = quiz.wrong.join('\n');
        _explanationController.text = quiz.explanation;
        _referenceController.text = quiz.reference;
        _linkController.text = quiz.link;
      });
    } catch (error) {
      setState(() {
        _error = '퀴즈 정보를 불러오지 못했습니다.';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _saveQuiz() async {
    if (_quiz == null) return;
    setState(() {
      _isSaving = true;
      _error = null;
    });
    try {
      final payload = {
        'title': _titleController.text.trim(),
        'question': _questionController.text.trim(),
        'choices': _choicesController.text
            .split('\n')
            .map((item) => item.trim())
            .where((item) => item.isNotEmpty)
            .toList(),
        'correct': _correctController.text.trim(),
        'wrong': _wrongController.text
            .split('\n')
            .map((item) => item.trim())
            .where((item) => item.isNotEmpty)
            .toList(),
        'explanation': _explanationController.text.trim(),
        'reference': _referenceController.text.trim(),
        'link': _linkController.text.trim(),
      };
      final updated =
          await widget.services.adminService.updateQuiz(widget.quizId, payload);
      setState(() {
        _quiz = updated;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('퀴즈 정보가 저장되었습니다.')),
        );
      }
    } catch (error) {
      setState(() {
        _error = '퀴즈 정보를 저장하지 못했습니다.';
      });
    } finally {
      setState(() {
        _isSaving = false;
      });
    }
  }

  Future<void> _deleteQuiz() async {
    if (_quiz == null) return;
    final confirm = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('퀴즈 삭제'),
        content: const Text('해당 퀴즈를 삭제하시겠습니까?'),
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
      await widget.services.adminService.deleteQuiz(widget.quizId);
      if (mounted) {
        Navigator.pop(context, _quiz);
      }
    } catch (error) {
      setState(() {
        _error = '퀴즈를 삭제하지 못했습니다.';
      });
    } finally {
      setState(() {
        _isDeleting = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('퀴즈 상세')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : _quiz == null
                  ? const Center(child: Text('퀴즈 정보를 찾을 수 없습니다.'))
                  : ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        Text('생성 사용자: ${_quiz!.sourceUserId}'),
                        const SizedBox(height: 16),
                        TextField(
                          controller: _titleController,
                          decoration: const InputDecoration(labelText: '제목'),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _questionController,
                          maxLines: 3,
                          decoration: const InputDecoration(labelText: '문항'),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _choicesController,
                          maxLines: 4,
                          decoration: const InputDecoration(labelText: '보기 (줄바꿈으로 입력)'),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _correctController,
                          decoration: const InputDecoration(labelText: '정답'),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _wrongController,
                          maxLines: 3,
                          decoration: const InputDecoration(labelText: '오답 보기 (줄바꿈으로 입력)'),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _explanationController,
                          maxLines: 3,
                          decoration: const InputDecoration(labelText: '해설'),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _referenceController,
                          maxLines: 3,
                          decoration: const InputDecoration(labelText: '참고자료'),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _linkController,
                          maxLines: 2,
                          decoration: const InputDecoration(labelText: '문항 출처'),
                        ),
                        const SizedBox(height: 20),
                        FilledButton(
                          onPressed: _isSaving ? null : _saveQuiz,
                          child: Text(_isSaving ? '저장 중...' : '저장'),
                        ),
                        const SizedBox(height: 12),
                        OutlinedButton(
                          onPressed: _isDeleting ? null : _deleteQuiz,
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
