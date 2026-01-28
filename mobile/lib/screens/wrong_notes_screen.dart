import 'package:flutter/material.dart';

import '../app.dart';
import '../models/wrong_note.dart';
import '../widgets/main_bottom_nav.dart';

class WrongNotesScreen extends StatefulWidget {
  const WrongNotesScreen({super.key, required this.services});

  final AppServices services;

  @override
  State<WrongNotesScreen> createState() => _WrongNotesScreenState();
}

class _WrongNotesScreenState extends State<WrongNotesScreen> {
  List<WrongNoteQuestion> _wrongNotes = [];
  int _currentIndex = 0;
  bool _isLoading = true;
  bool _isSubmitting = false;
  String? _errorMessage;
  String? _answerStatus;

  WrongNoteQuestion? get _currentQuestion =>
      _wrongNotes.isEmpty ? null : _wrongNotes[_currentIndex];

  @override
  void initState() {
    super.initState();
    _loadWrongNotes();
  }

  Future<void> _loadWrongNotes() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    try {
      final notes = await widget.services.quizService.fetchWrongNotes();
      setState(() {
        _wrongNotes = notes;
        _currentIndex = 0;
        _answerStatus = null;
      });
    } catch (error) {
      setState(() {
        _wrongNotes = [];
        _errorMessage = error.toString();
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _submitAnswer(String answer) async {
    final question = _currentQuestion;
    if (question == null) return;
    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });
    try {
      final result = await widget.services.quizService.submitAnswer(
        quizId: question.quizId,
        answer: answer,
      );
      final isCorrect = result.isCorrect;
      setState(() {
        _answerStatus = isCorrect ? 'correct' : 'wrong';
      });
      if (mounted) {
        await showDialog<void>(
          context: context,
          builder: (_) => AlertDialog(
            title: Text(isCorrect ? '정답' : '오답'),
            content: Text(isCorrect ? '잘했어요! 다음 문제로 넘어가요.' : '다시 한 번 풀어보세요.'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('닫기'),
              ),
              if (isCorrect)
                TextButton(
                  onPressed: () {
                    Navigator.pop(context);
                    _goNext();
                  },
                  child: const Text('다음 문제'),
                ),
            ],
          ),
        );
      }
    } catch (error) {
      setState(() {
        _errorMessage = error.toString();
      });
    } finally {
      setState(() {
        _isSubmitting = false;
      });
    }
  }

  void _goPrev() {
    if (_currentIndex == 0) return;
    setState(() {
      _currentIndex = (_currentIndex - 1).clamp(0, _wrongNotes.length - 1);
      _answerStatus = null;
    });
  }

  void _goNext() {
    if (_currentIndex + 1 >= _wrongNotes.length) {
      _showFinishedDialog();
      return;
    }
    setState(() {
      _currentIndex = (_currentIndex + 1).clamp(0, _wrongNotes.length - 1);
      _answerStatus = null;
    });
  }

  Future<void> _showFinishedDialog() async {
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('모두 완료'),
        content: const Text('오답노트의 모든 문제를 풀었어요.'),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.pop(context);
            },
            child: const Text('마이페이지로'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final question = _currentQuestion;
    return Scaffold(
      appBar: AppBar(
        title: const Text('오답노트'),
        actions: [
          IconButton(
            onPressed: _loadWrongNotes,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _errorMessage != null
                ? Center(child: Text(_errorMessage!, style: const TextStyle(color: Colors.red)))
                : question == null
                    ? const Center(child: Text('아직 기록된 오답이 없어요.'))
                    : Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  '문제 ${_currentIndex + 1} / ${_wrongNotes.length}',
                                  style: Theme.of(context).textTheme.titleMedium,
                                ),
                              ),
                              if (_answerStatus != null)
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: _answerStatus == 'correct'
                                        ? Colors.green.shade100
                                        : Colors.red.shade100,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    _answerStatus == 'correct' ? '정답' : '오답',
                                    style: TextStyle(
                                      color: _answerStatus == 'correct'
                                          ? Colors.green.shade800
                                          : Colors.red.shade800,
                                    ),
                                  ),
                                ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Text(question.question, style: Theme.of(context).textTheme.titleLarge),
                          if (question.link.trim().isNotEmpty) ...[
                            const SizedBox(height: 8),
                            Text('출처: ${question.link}', style: Theme.of(context).textTheme.bodySmall),
                          ],
                          const SizedBox(height: 12),
                          ...question.choices.map(
                            (choice) => RadioListTile<String>(
                              value: choice,
                              groupValue: null,
                              title: Text(choice),
                              onChanged: _isSubmitting ? null : (_) => _submitAnswer(choice),
                            ),
                          ),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Expanded(
                                child: OutlinedButton(
                                  onPressed: _currentIndex == 0 ? null : _goPrev,
                                  child: const Text('이전 문제'),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: FilledButton(
                                  onPressed: _wrongNotes.isEmpty ? null : _goNext,
                                  child: const Text('다음 문제'),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          Text('해설', style: Theme.of(context).textTheme.titleSmall),
                          Text(question.explanation),
                          const SizedBox(height: 8),
                          Text('참고', style: Theme.of(context).textTheme.titleSmall),
                          Text(question.reference),
                        ],
                      ),
      ),
      bottomNavigationBar: const MainBottomNav(currentIndex: 2),
    );
  }
}
