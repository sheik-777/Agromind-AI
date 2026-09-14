import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/providers.dart';

class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({super.key});

  @override
  ConsumerState<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends ConsumerState<AuthScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController(text: 'farmer@demo.farm');
  final _password = TextEditingController(text: 'demo1234');
  final _confirm = TextEditingController();
  bool _isLogin = true;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

  String? _emailValidator(String? v) {
    if (v == null || v.trim().isEmpty) return 'Email is required';
    final re = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');
    if (!re.hasMatch(v.trim())) return 'Enter a valid email address';
    return null;
  }

  String? _passValidator(String? v) {
    if (v == null || v.isEmpty) return 'Password is required';
    if (v.length < 8) return 'Password must be at least 8 characters';
    return null;
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (!_isLogin && _password.text != _confirm.text) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Passwords do not match')));
      return;
    }
    final notifier = ref.read(authProvider.notifier);
    if (_isLogin) {
      await notifier.login(_email.text.trim(), _password.text);
    } else {
      await notifier.register(_name.text.trim(), _email.text.trim(), _password.text, _confirm.text);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text('🌱', style: TextStyle(fontSize: 56), textAlign: TextAlign.center),
                  const SizedBox(height: 12),
                  Text(
                    _isLogin ? 'Welcome back' : 'Create account',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 6),
                  Text(
                    _isLogin ? 'Sign in to your AgroMind farm' : 'Join AgroMind — your farm, your data',
                    style: TextStyle(color: Theme.of(context).hintColor),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),
                  if (!_isLogin)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: TextFormField(
                        controller: _name,
                        decoration: const InputDecoration(labelText: 'Full name', prefixIcon: Icon(Icons.person_outlined)),
                        validator: (v) => (v == null || v.trim().length < 2) ? 'Name is required' : null,
                      ),
                    ),
                  TextFormField(
                    controller: _email,
                    keyboardType: TextInputType.emailAddress,
                    decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.mail_outlined)),
                    validator: _emailValidator,
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _password,
                    obscureText: true,
                    decoration: const InputDecoration(labelText: 'Password', prefixIcon: Icon(Icons.lock_outlined)),
                    validator: _passValidator,
                  ),
                  if (!_isLogin) ...[
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _confirm,
                      obscureText: true,
                      decoration: const InputDecoration(labelText: 'Confirm password', prefixIcon: Icon(Icons.lock_outlined)),
                      validator: (v) {
                        if (v == null || v.isEmpty) return 'Confirm your password';
                        if (v != _password.text) return 'Passwords do not match';
                        return null;
                      },
                    ),
                  ],
                  if (auth.error != null) ...[
                    const SizedBox(height: 12),
                    Text(auth.error!, style: const TextStyle(color: Colors.red)),
                  ],
                  const SizedBox(height: 20),
                  FilledButton(
                    onPressed: auth.busy ? null : _submit,
                    child: auth.busy
                        ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : Text(_isLogin ? 'Sign in' : 'Create account'),
                  ),
                  if (_isLogin)
                    TextButton(
                      onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Password reset via support — coming soon.'))),
                      child: const Text('Forgot password?'),
                    ),
                  TextButton(
                    onPressed: () => setState(() => _isLogin = !_isLogin),
                    child: Text(_isLogin ? 'New here? Create an account' : 'Have an account? Sign in'),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    auth.demo && auth.authed
                        ? 'Demo session — turn demo mode OFF in Profile → Settings to use real accounts'
                        : 'Demo fallback only when backend is unreachable; real accounts are now supported',
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 12, color: Colors.grey),
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
