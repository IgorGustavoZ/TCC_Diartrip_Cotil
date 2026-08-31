import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/api_client.dart';
import '../../core/web_style.dart';
import '../../providers/auth_provider.dart';
import '../../providers/language_provider.dart';
import '../../services/usuario_service.dart';

/// Mirrors backend/frontend/form.html: dark glass card, gradient submit
/// button, same copy/keys as the web sign-up form — including routing a
/// 409 (email already registered) response to the email field, like
/// `resp.status === 409` does in form.html's own submit handler.
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});
  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _form = GlobalKey<FormState>();
  final _nomeCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _senhaCtrl = TextEditingController();
  final _emailFocus = FocusNode();
  final _senhaFocus = FocusNode();
  bool _senhaVisivel = false;
  bool _loading = false;
  String? _erro;
  String? _emailErro;

  @override
  void dispose() {
    _nomeCtrl.dispose();
    _emailCtrl.dispose();
    _senhaCtrl.dispose();
    _emailFocus.dispose();
    _senhaFocus.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_loading) return;
    final lang = context.read<LanguageProvider>();
    setState(() { _erro = null; _emailErro = null; });
    if (!_form.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await UsuarioService.criar(
        nome: _nomeCtrl.text.trim(),
        email: _emailCtrl.text.trim(),
        senha: _senhaCtrl.text,
      );
      if (!mounted) return;
      try {
        await context.read<AuthProvider>().login(_emailCtrl.text.trim(), _senhaCtrl.text);
        if (mounted) Navigator.pushReplacementNamed(context, '/lobby');
      } catch (_) {
        // Conta criada, mas o login automático falhou — igual ao
        // "register.err.autoLogin" do form.html.
        if (mounted) setState(() => _erro = lang.translate('register.err.autoLogin'));
      }
    } on ApiException catch (e) {
      if (e.statusCode == 409) {
        setState(() => _emailErro = lang.translate('register.err.emailTaken'));
      } else {
        setState(() => _erro = e.message);
      }
    } catch (_) {
      setState(() => _erro = lang.translate('register.err.connect'));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  InputDecoration _decoration({required String label, required IconData icon, String? errorText, Widget? suffixIcon}) {
    return InputDecoration(
      labelText: label,
      labelStyle: const TextStyle(color: WebColors.textMuted),
      prefixIcon: Icon(icon, color: WebColors.textMuted),
      suffixIcon: suffixIcon,
      errorText: errorText,
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
                      // Card — equivalente ao <section><form id="signupForm"> do site.
                      GlassContainer(
                        padding: const EdgeInsets.all(32),
                        child: Form(
                          key: _form,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              Text(
                                lang.translate('register.title'),
                                style: const TextStyle(
                                  color: WebColors.text,
                                  fontSize: 22,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              const SizedBox(height: 24),
                              TextFormField(
                                controller: _nomeCtrl,
                                textInputAction: TextInputAction.next,
                                style: const TextStyle(color: WebColors.text),
                                decoration: _decoration(
                                  label: lang.translate('register.name.label'),
                                  icon: Icons.person_outline,
                                ),
                                validator: (v) => v != null && v.trim().length >= 3
                                    ? null
                                    : lang.translate('register.err.name'),
                                onFieldSubmitted: (_) => _emailFocus.requestFocus(),
                              ),
                              const SizedBox(height: 16),
                              TextFormField(
                                controller: _emailCtrl,
                                focusNode: _emailFocus,
                                keyboardType: TextInputType.emailAddress,
                                textInputAction: TextInputAction.next,
                                style: const TextStyle(color: WebColors.text),
                                decoration: _decoration(
                                  label: 'Email',
                                  icon: Icons.email_outlined,
                                  errorText: _emailErro,
                                ),
                                validator: (v) => v != null && v.contains('@')
                                    ? null
                                    : lang.translate('register.err.email'),
                                onChanged: (_) {
                                  if (_emailErro != null) setState(() => _emailErro = null);
                                },
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
                                validator: (v) {
                                  if (v == null || v.length < 8) return lang.translate('register.err.passLen');
                                  if (!v.contains(RegExp(r'[A-Z]'))) return lang.translate('register.err.passUpper');
                                  if (!v.contains(RegExp(r'[0-9]'))) return lang.translate('register.err.passNum');
                                  return null;
                                },
                                onFieldSubmitted: (_) => _submit(),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                lang.translate('register.pass.hint'),
                                style: const TextStyle(color: WebColors.textMuted, fontSize: 12),
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
                                onPressed: _loading ? null : _submit,
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
                                    gradient: _loading ? null : WebColors.gradient,
                                    color: _loading ? WebColors.surface2 : null,
                                    borderRadius: BorderRadius.circular(WebColors.radiusPill),
                                  ),
                                  child: Container(
                                    alignment: Alignment.center,
                                    padding: const EdgeInsets.symmetric(vertical: 15),
                                    child: _loading
                                        ? const SizedBox(
                                            height: 18,
                                            width: 18,
                                            child: CircularProgressIndicator(
                                              strokeWidth: 2,
                                              color: Colors.white,
                                            ),
                                          )
                                        : Text(
                                            lang.translate('register.submit'),
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
                                    lang.translate('register.hasAccount'),
                                    style: const TextStyle(color: WebColors.textMuted, fontSize: 14),
                                  ),
                                  GestureDetector(
                                    onTap: () => Navigator.pop(context),
                                    child: Text(
                                      lang.translate('login.signIn'),
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
