import 'package:flutter/material.dart';

import '../app.dart';
import '../models/chat.dart';
import '../widgets/main_bottom_nav.dart';

class ChatHistoryScreen extends StatefulWidget {
  const ChatHistoryScreen({super.key, required this.services});

  final AppServices services;

  @override
  State<ChatHistoryScreen> createState() => _ChatHistoryScreenState();
}

class _ChatHistoryScreenState extends State<ChatHistoryScreen> {
  ChatHistoryDatesResponse? _dates;
  String? _error;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDates();
  }

  Future<void> _loadDates() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final dates = await widget.services.chatService.fetchHistoryDates();
      setState(() {
        _dates = dates;
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
      appBar: AppBar(title: const Text('채팅 내역')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : _dates == null
                  ? const Center(child: Text('대화 내역을 불러올 수 없습니다.'))
                  : ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        if (_dates!.dates.isEmpty)
                          const Text('저장된 대화가 없습니다.'),
                        ..._dates!.dates.map(
                          (date) => Card(
                            child: ListTile(
                              leading: const Icon(Icons.calendar_today),
                              title: Text(date),
                              subtitle: Text(date == _dates!.today ? '오늘 대화' : '저장된 대화'),
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => ChatHistoryDetailScreen(
                                      services: widget.services,
                                      date: date,
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
                        ),
                      ],
                    ),
      bottomNavigationBar: const MainBottomNav(currentIndex: 2),
    );
  }
}

class ChatHistoryDetailScreen extends StatefulWidget {
  const ChatHistoryDetailScreen({super.key, required this.services, required this.date});

  final AppServices services;
  final String date;

  @override
  State<ChatHistoryDetailScreen> createState() => _ChatHistoryDetailScreenState();
}

class _ChatHistoryDetailScreenState extends State<ChatHistoryDetailScreen> {
  ChatHistoryResponse? _history;
  String? _error;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final history = await widget.services.chatService.fetchHistory(widget.date);
      setState(() {
        _history = history;
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
      appBar: AppBar(title: Text('대화 기록 (${widget.date})')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : _history == null || _history!.entries.isEmpty
                  ? const Center(child: Text('저장된 대화가 없습니다.'))
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _history!.entries.length,
                      itemBuilder: (context, index) {
                        final entry = _history!.entries[index];
                        return _ChatBubble(entry: entry);
                      },
                    ),
      bottomNavigationBar: const MainBottomNav(currentIndex: 2),
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
        child: Text(entry.content, style: const TextStyle(color: Colors.black87)),
      ),
    );
  }
}
