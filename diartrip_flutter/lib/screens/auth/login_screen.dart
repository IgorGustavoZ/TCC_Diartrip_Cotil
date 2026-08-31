import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/web_style.dart';
import '../../providers/auth_provider.dart';
import '../../providers/language_provider.dart';

/// Mirrors backend/frontend/login.html: dark glass card, gradient submit
/// button, same copy/keys as before so behavior (validation, navigation)
/// stays identical — only the visual chrome changed.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _form = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  final _senhaCtrl = TextEditingController();
  final _senhaFocus = FocusNode();
  bool _senhaVisivel = false;
  String? _erro;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _senhaCtrl.dispose();
    _senhaFocus.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (context.read<AuthProvider>().loading) return;
    if (!_form.currentState!.validate()) return;
    setState(() => _erro = null);
    try {
      await context.read<AuthProvider>().login(
            _emailCtrl.text.trim(),
            _senhaCtrl.text,
          );
      if (mounted) Navigator.pushReplacementNamed(context, '/lobby');
    } catch (e) {
      setState(() => _erro = e.toString());
    }
  }

  InputDecoration _decoration({required String label, required IconData icon, Widget? suffixIcon}) {
    return InputDecoration(
      labelText: label,
      labelStyle: const TextStyle(color: WebColors.textMuted),
      prefixIcon: Icon(icon, color: WebColors.textMuted),
      suffixIcon: suffixIcon,
      filled: true,
      fillColor: WebColors.surface2,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(WebColors.radiusMd),
        borderSide: BorderSide.none,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(WebColors.radiusMd),
        borderSide: const BorderSide(color: WebColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(WebColors.radiusMd),
        borderSide: const BorderSide(color: WebColors.primary, width: 1.5),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(WebColors.radiusMd),
        borderSide: const BorderSide(color: WebColors.danger),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final loading = context.watch<AuthProvider>().loading;
    final lang = context.watch<LanguageProvider>();

    return Scaffold(
      backgroundColor: WebColors.bg,
      body: Stack(
        children: [
          const Positioned.fill(child: AmbientBackground()),
          SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(28),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 440),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Cabeçalho/marca — equivalente ao <header><img logo></header>
                      // do site: mesmo favicon do Diartrip usado no site.
                      Image.asset('assets/images/favicon-diartrip.png', width: 84, height: 84),
                      const SizedBox(height: 10),
                      const Text(
                        'Diartrip',
                        textAlign: TextAlign.center,
                        style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: WebColors.text),
                      ),
                      Text(
                        lang.translate('login.subtitle'),
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: WebColors.textMuted, fontSize: 14),
                      ),
                      const SizedBox(height: 32),
                      // Card — equivalente ao <section><form id="signupForm"> do site
                      // (mesmo background, borda, radius e sombra do .container/.card).
                      GlassContainer(
                        padding: const EdgeInsets.all(32),
                        child: Form(
                          key: _form,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              Text(
                                lang.translate('login.title'),
                                style: const TextStyle(
                                  color: WebColors.text,
                                  fontSize: 22,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              const SizedBox(height: 24),
                              TextFormField(
                                controller: _emailCtrl,
                                keyboardType: TextInputType.emailAddress,
                                textInputAction: TextInputAction.next,
                                style: const TextStyle(color: WebColors.text),
                                decoration: _decoration(label: 'Email', icon: Icons.email_outlined),
                                validator: (v) => v != null && v.contains('@')
                                    ? null
                                    : lang.translate('login.emailInvalid'),
                                onFieldSubmitted: (_) => _senhaFocus.requestFocus(),
                              ),
                              const SizedBox(height: 16),
                              TextFormField(
                                controller: _senhaCtrl,
                                focusNode: _senhaFocus,
                                obscureText: !_senhaVisivel,
                                textInputAction: TextInputAction.done,
                                style: const TextStyle(color: WebColors.text),
                                decoration: _decoration(
                                  label: lang.translate('login.password'),
                                  icon: Icons.lock_outlined,
                                  suffixIcon: IconButton(
                                    icon: Icon(
                                      _senhaVisivel ? Icons.visibility_off : Icons.visibility,
                                      color: WebColors.textMuted,
                                    ),
                                    onPressed: () => setState(() => _senhaVisivel = !_senhaVisivel),
                                  ),
                                ),
                                validator: (v) => v != null && v.isNotEmpty
                                    ? null
                                    : lang.translate('login.passwordRequired'),
                                onFieldSubmitted: (_) => _submit(),
                              ),
                              if (_erro != null) ...[
                                const SizedBox(height: 16),
                                Container(
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: WebColors.danger.withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(WebColors.radiusMd),
                                  ),
                                  child: Text(
                                    _erro!,
                                    style: const TextStyle(color: WebColors.danger, fontSize: 13),
                                  ),
                                ),
                              ],
                              const SizedBox(height: 24),
                              // Continua sendo um ElevatedButton (mesmo tipo de widget
                              // de antes) só que com o miolo (Ink) desenhando o
                              // gradiente pill do .cta do site.
                              ElevatedButton(
                                onPressed: loading ? null : _submit,
                                style: ElevatedButton.styleFrom(
                                  padding: EdgeInsets.zero,
                                  backgroundColor: Colors.transparent,
                                  disabledBackgroundColor: Colors.transparent,
                                  shadowColor: Colors.transparent,
                                  elevation: 0,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(WebColors.radiusPill),
                                  ),
                                ),
                                child: Ink(
                                  decoration: BoxDecoration(
                                    gradient: loading ? null : WebColors.gradient,
                                    color: loading ? WebColors.surface2 : null,
                                    borderRadius: BorderRadius.circular(WebColors.radiusPill),
                                  ),
                                  child: Container(
                                    alignment: Alignment.center,
                                    padding: const EdgeInsets.symmetric(vertical: 15),
                                    child: loading
                                        ? const SizedBox(
                                            height: 18,
                                            width: 18,
                                            child: CircularProgressIndicator(
                                              strokeWidth: 2,
                                              color: Colors.white,
                                            ),
                                          )
                                        : Text(
                                            lang.translate('login.signIn'),
                                            style: const TextStyle(
                                              color: Colors.white,
                                              fontWeight: FontWeight.w700,
                                              fontSize: 15,
                                            ),
                                          ),
                                  ),
                                ),
                              ),
                              const SizedBox(height: 18),
                              Wrap(
                                alignment: WrapAlignment.center,
                                children: [
                                  Text(
                                    lang.translate('login.noAccount'),
                                    style: const TextStyle(color: WebColors.textMuted, fontSize: 14),
                                  ),
                                  GestureDetector(
                                    onTap: () => Navigator.pushNamed(context, '/register'),
                                    child: Text(
                                      lang.translate('login.signUp'),
                                      style: const TextStyle(
                                        color: WebColors.primary,
                                        fontWeight: FontWeight.w600,
                                        fontSize: 14,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
