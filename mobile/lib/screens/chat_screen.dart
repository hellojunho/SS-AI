import 'package:flutter/material.dart';

import '../app.dart';
import '../models/chat.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key, required this.services});

  final AppServices services;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _controller = TextEditingController();
  bool _isLoading = false;
  ChatAnswer? _answer;
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final message = _controller.text.trim();
    if (message.isEmpty) return;
    setState(() {
      _isLoading = true;
      _error = null;
      _answer = null;
    });
    try {
      final response = await widget.services.chatService.ask(message);
      setState(() {
        _answer = response;
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
      appBar: AppBar(title: const Text('AI Q&A')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _controller,
              maxLines: 3,
              decoration: const InputDecoration(
                hintText: '질문을 입력하세요.',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: _isLoading ? null : _submit,
              icon: const Icon(Icons.send),
              label: const Text('질문하기'),
            ),
            const SizedBox(height: 16),
            if (_isLoading)
              const Center(child: CircularProgressIndicator())
            else if (_error != null)
              Text(_error!, style: const TextStyle(color: Colors.red))
            else if (_answer != null)
              _AnswerCard(answer: _answer!),
          ],
        ),
      ),
    );
  }
}

class _AnswerCard extends StatelessWidget {
  const _AnswerCard({required this.answer});

  final ChatAnswer answer;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('답변', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text(answer.answer),
            const SizedBox(height: 12),
            Text('참고', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 4),
            Text(answer.reference),
            const SizedBox(height: 8),
            Text('파일 경로: ${answer.filePath}', style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }
}
