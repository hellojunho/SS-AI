import 'package:flutter/material.dart';

import 'services/api_client.dart';
import 'services/admin_service.dart';
import 'services/auth_service.dart';
import 'services/chat_service.dart';
import 'services/coach_service.dart';
import 'services/quiz_service.dart';
import 'screens/admin_quizzes_screen.dart';
import 'screens/admin_screen.dart';
import 'screens/admin_users_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/chat_history_screen.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/my_page_screen.dart';
import 'screens/quiz_screen.dart';
import 'screens/signup_screen.dart';
import 'screens/wrong_notes_screen.dart';
import 'screens/coach_students_screen.dart';

class AppServices {
  AppServices._(this.authService)
      : apiClient = ApiClient(authService),
        chatService = ChatService(ApiClient(authService)),
        quizService = QuizService(ApiClient(authService)),
        adminService = AdminService(ApiClient(authService)),
        coachService = CoachService(ApiClient(authService));

  factory AppServices() => AppServices._(AuthService());

  final AuthService authService;
  final ApiClient apiClient;
  final ChatService chatService;
  final QuizService quizService;
  final AdminService adminService;
  final CoachService coachService;
}

class SSApp extends StatefulWidget {
  const SSApp({super.key, required this.services});

  final AppServices services;

  @override
  State<SSApp> createState() => _SSAppState();
}

class _SSAppState extends State<SSApp> {
  final ValueNotifier<bool> _isAuthenticated = ValueNotifier(false);
  final GlobalKey<NavigatorState> _navigatorKey = GlobalKey<NavigatorState>();

  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    final isAuthed = await widget.services.authService.isAuthenticated();
    _isAuthenticated.value = isAuthed;
  }

  void _setAuthenticated(bool value) {
    _isAuthenticated.value = value;
    if (!value) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _navigatorKey.currentState?.pushNamedAndRemoveUntil('/', (route) => false);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<bool>(
      valueListenable: _isAuthenticated,
      builder: (context, authed, _) {
        return MaterialApp(
          title: 'SS-AI Mobile',
          theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
          navigatorKey: _navigatorKey,
          routes: {
            '/': (context) => authed
                ? HomeScreen(services: widget.services)
                : LoginScreen(services: widget.services, onLogin: _setAuthenticated),
            '/signup': (context) => SignupScreen(services: widget.services),
            '/chat': (context) => ChatScreen(services: widget.services),
            '/quiz': (context) => QuizScreen(services: widget.services),
            '/me': (context) => MyPageScreen(services: widget.services, onLogout: _setAuthenticated),
            '/me/history': (context) => ChatHistoryScreen(services: widget.services),
            '/me/wrong-notes': (context) => WrongNotesScreen(services: widget.services),
            '/admin': (context) => AdminScreen(services: widget.services),
            '/admin/users': (context) => AdminUsersScreen(services: widget.services),
            '/admin/quizzes': (context) => AdminQuizzesScreen(services: widget.services),
            '/coach/students': (context) => CoachStudentsScreen(services: widget.services),
          },
        );
      },
    );
  }
}
