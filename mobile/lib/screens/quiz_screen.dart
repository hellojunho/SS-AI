import 'package:flutter/material.dart';

import '../app.dart';
import '../models/quiz.dart';

class QuizScreen extends StatefulWidget {
  const QuizScreen({super.key, required this.services});

  final AppServices services;

  @override
  State<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends State<QuizScreen> {
  Quiz? _quiz;
  bool _isLoading = true;
  String? _error;
  String? _selectedAnswer;
  String? _statusMessage;

  @override
  void initState() {
    super.initState();
    _loadLatest();
  }

  Future<void> _loadLatest() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final quiz = await widget.services.quizService.fetchLatest();
      setState(() {
        _quiz = quiz;
        _selectedAnswer = null;
        _statusMessage = null;
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

  Future<void> _loadNext() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _statusMessage = null;
    });
    try {
      final quiz = await widget.services.quizService.fetchNext();
      setState(() {
        _quiz = quiz;
        _selectedAnswer = null;
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

  Future<void> _submitAnswer() async {
    final quiz = _quiz;
    if (quiz == null || _selectedAnswer == null) return;
    setState(() {
      _isLoading = true;
      _statusMessage = null;
    });
    try {
      await widget.services.quizService.submitAnswer(
        quizId: quiz.id,
        answer: _selectedAnswer!,
      );
      setState(() {
        _statusMessage = '제출 완료! 정답: ${quiz.correct}';
      });
    } catch (error) {
      setState(() {
        _statusMessage = error.toString();
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
      appBar: AppBar(title: const Text('퀴즈 학습')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
                : _quiz == null
                    ? const Center(child: Text('퀴즈가 없습니다.'))
                    : _QuizDetail(
                        quiz: _quiz!,
                        selectedAnswer: _selectedAnswer,
                        statusMessage: _statusMessage,
                        onSelectAnswer: (value) => setState(() => _selectedAnswer = value),
                        onSubmit: _submitAnswer,
                        onNext: _loadNext,
                      ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _loadLatest,
        label: const Text('최신 퀴즈'),
        icon: const Icon(Icons.refresh),
      ),
    );
  }
}

class _QuizDetail extends StatelessWidget {
  const _QuizDetail({
    required this.quiz,
    required this.selectedAnswer,
    required this.statusMessage,
    required this.onSelectAnswer,
    required this.onSubmit,
    required this.onNext,
  });

  final Quiz quiz;
  final String? selectedAnswer;
  final String? statusMessage;
  final ValueChanged<String> onSelectAnswer;
  final VoidCallback onSubmit;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(quiz.title, style: Theme.of(context).textTheme.headlineSmall),
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
          onPressed: selectedAnswer == null ? null : onSubmit,
          child: const Text('정답 제출'),
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
