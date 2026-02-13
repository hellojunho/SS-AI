import 'package:flutter/material.dart';

import '../app.dart';
import '../models/chat.dart';
import '../widgets/main_bottom_nav.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key, required this.services});

  final AppServices services;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _controller = TextEditingController();
  bool _isLoading = false;
  final List<ChatHistoryEntry> _entries = [];
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    _loadTodayHistory();
  }

  Future<void> _loadTodayHistory() async {
    try {
      final dates = await widget.services.chatService.fetchHistoryDates();
      final history = await widget.services.chatService.fetchHistory(dates.today);
      setState(() {
        _entries
          ..clear()
          ..addAll(history.entries);
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
      });
    }
  }

  Future<void> _submit() async {
    final message = _controller.text.trim();
    if (message.isEmpty) return;
    setState(() {
      _isLoading = true;
      _error = null;
      _entries.add(ChatHistoryEntry(role: 'me', content: message));
      _controller.clear();
    });
    try {
      final response = await widget.services.chatService.ask(message);
      final reference = response.reference.trim();
      final gptContent = reference.isEmpty
          ? response.answer
          : '${response.answer}\n\n출처: $reference';
      setState(() {
        _entries.add(ChatHistoryEntry(role: 'gpt', content: gptContent));
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
      body: Column(
        children: [
          Expanded(
            child: _entries.isEmpty
                ? Center(
                    child: Text(
                      _error ?? '대화를 시작해 보세요.',
                      style: TextStyle(color: _error != null ? Colors.red : Colors.black54),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _entries.length,
                    itemBuilder: (context, index) {
                      final entry = _entries[index];
                      return _ChatBubble(entry: entry);
                    },
                  ),
          ),
          if (_error != null && _entries.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(_error!, style: const TextStyle(color: Colors.red)),
            ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 20),
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
                  icon: _isLoading
                      ? const SizedBox(
                          height: 16,
                          width: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send),
                  label: Text(_isLoading ? '답변 생성 중...' : '질문하기'),
                ),
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: MainBottomNav(
        currentIndex: 0,
        authService: widget.services.authService,
      ),
    );
  }
}

class _ChatBubble extends StatelessWidget {
  const _ChatBubble({required this.entry});

  final ChatHistoryEntry entry;

  @override
  Widget build(BuildContext context) {
    final isMe = entry.role == 'me';
    final alignment = isMe ? Alignment.centerRight : Alignment.centerLeft;
    final bubbleColor = isMe ? Colors.indigo.shade100 : Colors.grey.shade200;
    final textColor = Colors.black87;
    return Align(
      alignment: alignment,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        padding: const EdgeInsets.all(12),
        constraints: const BoxConstraints(maxWidth: 280),
        decoration: BoxDecoration(
          color: bubbleColor,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Text(entry.content, style: TextStyle(color: textColor)),
      ),
    );
  }
}
