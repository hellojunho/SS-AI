import 'package:flutter/material.dart';

import '../app.dart';
import '../models/quiz.dart';

class QuizScreen extends StatefulWidget {
  const QuizScreen({super.key, required this.services});

  final AppServices services;

  @override
  State<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends State<QuizScreen> with SingleTickerProviderStateMixin {
  late final TabController _tabController;
  Quiz? _userQuiz;
  Quiz? _allQuiz;
  bool _isLoading = true;
  bool _isSubmitting = false;
  String? _userError;
  String? _allError;
  String? _selectedAnswerUser;
  String? _selectedAnswerAll;
  String? _statusMessageUser;
  String? _statusMessageAll;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _tabController.addListener(_handleTabChange);
    _loadLatest(all: false);
  }

  @override
  void dispose() {
    _tabController.removeListener(_handleTabChange);
    _tabController.dispose();
    super.dispose();
  }

  void _handleTabChange() {
    if (_tabController.indexIsChanging) return;
    if (_tabController.index == 1 && _allQuiz == null && _allError == null) {
      _loadLatest(all: true);
    }
  }

  bool get _isAllScope => _tabController.index == 1;

  Quiz? get _currentQuiz => _isAllScope ? _allQuiz : _userQuiz;

  String? get _currentError => _isAllScope ? _allError : _userError;

  String? get _selectedAnswer => _isAllScope ? _selectedAnswerAll : _selectedAnswerUser;

  String? get _statusMessage => _isAllScope ? _statusMessageAll : _statusMessageUser;

  void _setSelectedAnswer(String? value) {
    setState(() {
      if (_isAllScope) {
        _selectedAnswerAll = value;
      } else {
        _selectedAnswerUser = value;
      }
    });
  }

  void _setStatusMessage(String? message) {
    if (_isAllScope) {
      _statusMessageAll = message;
    } else {
      _statusMessageUser = message;
    }
  }

  Future<void> _loadLatest({required bool all}) async {
    setState(() {
      _isLoading = true;
      if (all) {
        _allError = null;
      } else {
        _userError = null;
      }
    });
    try {
      final quiz = await widget.services.quizService.fetchLatest(all: all);
      setState(() {
        if (all) {
          _allQuiz = quiz;
          _selectedAnswerAll = null;
          _statusMessageAll = null;
        } else {
          _userQuiz = quiz;
          _selectedAnswerUser = null;
          _statusMessageUser = null;
        }
      });
    } catch (error) {
      setState(() {
        if (all) {
          _allError = error.toString();
        } else {
          _userError = error.toString();
        }
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadNext() async {
    final quiz = _currentQuiz;
    if (quiz == null) return;
    setState(() {
      _isLoading = true;
      if (_isAllScope) {
        _allError = null;
        _statusMessageAll = null;
      } else {
        _userError = null;
        _statusMessageUser = null;
      }
    });
    try {
      final nextQuiz = await widget.services.quizService.fetchNext(
        currentId: quiz.id,
        all: _isAllScope,
      );
      setState(() {
        if (_isAllScope) {
          _allQuiz = nextQuiz;
          _selectedAnswerAll = null;
        } else {
          _userQuiz = nextQuiz;
          _selectedAnswerUser = null;
        }
      });
    } catch (error) {
      setState(() {
        if (_isAllScope) {
          _allError = error.toString();
        } else {
          _userError = error.toString();
        }
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _submitAnswer() async {
    final quiz = _currentQuiz;
    final selected = _selectedAnswer;
    if (quiz == null || selected == null) return;
    setState(() {
      _isSubmitting = true;
      _setStatusMessage(null);
    });
    try {
      final result = await widget.services.quizService.submitAnswer(
        quizId: quiz.id,
        answer: selected,
      );
      final isCorrect = result.isCorrect;
      setState(() {
        _setStatusMessage(isCorrect ? '정답입니다!' : '오답입니다.');
      });
      if (mounted) {
        await showDialog<void>(
          context: context,
          builder: (_) => AlertDialog(
            title: Text(isCorrect ? '정답' : '오답'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(isCorrect ? '잘했어요! 🎉' : '아쉽지만 다시 도전해 보세요.'),
                const SizedBox(height: 12),
                Text('정답: ${quiz.correct}'),
                if (result.answerHistory.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text('답변 기록: ${result.answerHistory.join(', ')}'),
                ],
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('확인'),
              ),
            ],
          ),
        );
      }
    } catch (error) {
      setState(() {
        _setStatusMessage(error.toString());
      });
    } finally {
      setState(() {
        _isSubmitting = false;
      });
    }
  }

  Future<void> _generateQuiz() async {
    setState(() {
      _isLoading = true;
      _userError = null;
    });
    try {
      final quiz = await widget.services.quizService.generateQuiz();
      setState(() {
        _userQuiz = quiz;
        _selectedAnswerUser = null;
        _statusMessageUser = null;
      });
    } catch (error) {
      setState(() {
        _userError = error.toString();
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
      appBar: AppBar(
        title: const Text('퀴즈 학습'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '나의 퀴즈'),
            Tab(text: '전체 퀴즈'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildQuizPane(all: false),
          _buildQuizPane(all: true),
        ],
      ),
    );
  }

  Widget _buildQuizPane({required bool all}) {
    final quiz = all ? _allQuiz : _userQuiz;
    final error = all ? _allError : _userError;
    final selectedAnswer = all ? _selectedAnswerAll : _selectedAnswerUser;
    final statusMessage = all ? _statusMessageAll : _statusMessageUser;
    final isCurrentTab = _isAllScope == all;
    return Padding(
      padding: const EdgeInsets.all(24),
      child: _isLoading && isCurrentTab
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(child: Text(error, style: const TextStyle(color: Colors.red)))
              : quiz == null
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(all ? '전체 퀴즈가 없습니다.' : '아직 생성된 퀴즈가 없습니다.'),
                          const SizedBox(height: 12),
                          if (!all)
                            FilledButton.icon(
                              onPressed: _generateQuiz,
                              icon: const Icon(Icons.auto_awesome),
                              label: const Text('퀴즈 생성하기'),
                            ),
                        ],
                      ),
                    )
                  : _QuizDetail(
                      quiz: quiz,
                      selectedAnswer: selectedAnswer,
                      statusMessage: statusMessage,
                      isSubmitting: _isSubmitting && isCurrentTab,
                      onSelectAnswer: (value) => _setSelectedAnswer(value),
                      onSubmit: _submitAnswer,
                      onNext: _loadNext,
                      onRefresh: () => _loadLatest(all: all),
                    ),
    );
  }
}

class _QuizDetail extends StatelessWidget {
  const _QuizDetail({
    required this.quiz,
    required this.selectedAnswer,
    required this.statusMessage,
    required this.isSubmitting,
    required this.onSelectAnswer,
    required this.onSubmit,
    required this.onNext,
    required this.onRefresh,
  });

  final Quiz quiz;
  final String? selectedAnswer;
  final String? statusMessage;
  final bool isSubmitting;
  final ValueChanged<String> onSelectAnswer;
  final VoidCallback onSubmit;
  final VoidCallback onNext;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(quiz.title, style: Theme.of(context).textTheme.headlineSmall),
            ),
            IconButton(
              onPressed: onRefresh,
              icon: const Icon(Icons.refresh),
            ),
          ],
        ),
        if (quiz.currentIndex != null && quiz.totalCount != null)
          Text('문항 ${quiz.currentIndex} / ${quiz.totalCount}'),
        const SizedBox(height: 16),
        Text(quiz.question, style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 12),
        ...quiz.choices.map(
          (choice) => RadioListTile<String>(
            title: Text(choice),
            value: choice,
            groupValue: selectedAnswer,
            onChanged: (value) {
              if (value != null) onSelectAnswer(value);
            },
          ),
        ),
        const SizedBox(height: 12),
        FilledButton(
          onPressed: selectedAnswer == null || isSubmitting ? null : onSubmit,
          child: isSubmitting
              ? const SizedBox(
                  height: 16,
                  width: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('정답 제출'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: onNext,
          icon: const Icon(Icons.navigate_next),
          label: const Text('다음 퀴즈'),
        ),
        if (statusMessage != null) ...[
          const SizedBox(height: 12),
          Text(statusMessage!, style: const TextStyle(color: Colors.indigo)),
        ],
        const SizedBox(height: 12),
        Text('해설', style: Theme.of(context).textTheme.titleSmall),
        Text(quiz.explanation),
        const SizedBox(height: 8),
        Text('참고', style: Theme.of(context).textTheme.titleSmall),
        Text(quiz.reference),
      ],
    );
  }
}
