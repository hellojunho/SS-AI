import 'package:flutter/material.dart';

import '../app.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key, required this.services});

  final AppServices services;

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _userIdController = TextEditingController();
  final _userNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  String? _message;

  @override
  void dispose() {
    _userIdController.dispose();
    _userNameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final formState = _formKey.currentState;
    if (formState == null || !formState.validate()) {
      return;
    }
    setState(() {
      _isLoading = true;
      _message = null;
    });
    try {
      await widget.services.authService.signUp(
        userId: _userIdController.text.trim(),
        userName: _userNameController.text.trim(),
        email: _emailController.text.trim(),
        password: _passwordController.text.trim(),
      );
      if (!mounted) return;
      setState(() {
        _message = '회원가입이 완료되었습니다. 로그인 해주세요.';
      });
    } catch (error) {
      setState(() {
        _message = error.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('SS-AI 회원가입')),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text('아이디', style: Theme.of(context).textTheme.labelLarge),
                  const SizedBox(height: 8),
                  TextFormField(
                    controller: _userIdController,
                    decoration: const InputDecoration(border: OutlineInputBorder()),
                    validator: (value) =>
                        (value == null || value.trim().isEmpty) ? '아이디를 입력하세요.' : null,
                  ),
                  const SizedBox(height: 16),
                  Text('이름', style: Theme.of(context).textTheme.labelLarge),
                  const SizedBox(height: 8),
                  TextFormField(
                    controller: _userNameController,
                    decoration: const InputDecoration(border: OutlineInputBorder()),
                    validator: (value) =>
                        (value == null || value.trim().isEmpty) ? '이름을 입력하세요.' : null,
                  ),
                  const SizedBox(height: 16),
                  Text('이메일', style: Theme.of(context).textTheme.labelLarge),
                  const SizedBox(height: 8),
                  TextFormField(
                    controller: _emailController,
                    decoration: const InputDecoration(border: OutlineInputBorder()),
                    validator: (value) =>
                        (value == null || value.trim().isEmpty) ? '이메일을 입력하세요.' : null,
                  ),
                  const SizedBox(height: 16),
                  Text('비밀번호', style: Theme.of(context).textTheme.labelLarge),
                  const SizedBox(height: 8),
                  TextFormField(
                    controller: _passwordController,
                    obscureText: true,
                    decoration: const InputDecoration(border: OutlineInputBorder()),
                    validator: (value) =>
                        (value == null || value.trim().isEmpty) ? '비밀번호를 입력하세요.' : null,
                  ),
                  const SizedBox(height: 16),
                  if (_message != null)
                    Builder(
                      builder: (context) {
                        final message = _message ?? 'Null';
                        return Text(
                          message,
                          style: TextStyle(
                            color: message.contains('완료') ? Colors.green : Colors.red,
                          ),
                        );
                      },
                    ),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: _isLoading ? null : _submit,
                    child: _isLoading
                        ? const CircularProgressIndicator()
                        : const Text('회원가입'),
                  ),
                  const SizedBox(height: 12),
                  TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('로그인 화면으로'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
