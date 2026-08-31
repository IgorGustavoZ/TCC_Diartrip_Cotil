import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/api_client.dart';
import '../../core/web_style.dart';
import '../../providers/auth_provider.dart';
import '../../providers/language_provider.dart';
import '../../services/usuario_service.dart';

enum _ConfigView { menu, account, password }

/// Mirrors backend/frontend/lobby-pags/config.html: a settings menu (two
/// rows) that swaps in-place for a detail panel, exactly like the site's
/// show/hide behavior — including "change password", which didn't exist in
/// the Flutter app yet (PUT /usuarios/{id}/senha already existed on the
/// backend, just wasn't wired up here).
class ConfigScreen extends StatefulWidget {
  const ConfigScreen({super.key});
  @override
  State<ConfigScreen> createState() => _ConfigScreenState();
}

class _ConfigScreenState extends State<ConfigScreen> {
  _ConfigView _view = _ConfigView.menu;

  // Conta
  final _nomeCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  bool _savingAccount = false;
  String? _accountMsg;
  bool _accountMsgErro = false;

  // Senha
  final _senhaAtualCtrl = TextEditingController();
  final _novaSenhaCtrl = TextEditingController();
  final _confirmarSenhaCtrl = TextEditingController();
  bool _senhaAtualVisivel = false;
  bool _novaSenhaVisivel = false;
  bool _confirmarSenhaVisivel = false;
  bool _savingPassword = false;
  String? _erroSenhaAtual;
  String? _erroNovaSenha;
  String? _erroConfirmarSenha;
  String? _passwordMsg;
  bool _passwordMsgErro = false;

  @override
  void initState() {
    super.initState();
    final u = context.read<AuthProvider>().usuario;
    if (u != null) {
      _nomeCtrl.text = u.nome;
      _emailCtrl.text = u.email ?? '';
    }
  }

  @override
  void dispose() {
    _nomeCtrl.dispose();
    _emailCtrl.dispose();
    _senhaAtualCtrl.dispose();
    _novaSenhaCtrl.dispose();
    _confirmarSenhaCtrl.dispose();
    super.dispose();
  }

  void _irPara(_ConfigView v) {
    setState(() {
      _view = v;
      _accountMsg = null;
      _passwordMsg = null;
      _erroSenhaAtual = null;
      _erroNovaSenha = null;
      _erroConfirmarSenha = null;
    });
  }

  Future<void> _salvarConta() async {
    final lang = context.read<LanguageProvider>();
    if (_nomeCtrl.text.trim().isEmpty) {
      setState(() { _accountMsg = lang.translate('config.nameRequired'); _accountMsgErro = true; });
      return;
    }
    if (!_emailCtrl.text.contains('@')) {
      setState(() { _accountMsg = lang.translate('config.emailInvalid'); _accountMsgErro = true; });
      return;
    }
    final auth = context.read<AuthProvider>();
    final id = auth.usuario?.id;
    if (id == null) return;
    setState(() { _savingAccount = true; _accountMsg = null; });
    try {
      final u = await UsuarioService.atualizar(
        id: id,
        nome: _nomeCtrl.text.trim(),
        email: _emailCtrl.text.trim(),
      );
      auth.updateUsuario(u);
      if (mounted) {
        setState(() { _accountMsg = lang.translate('config.updateSuccess'); _accountMsgErro = false; });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _accountMsg = e is ApiException ? e.message : lang.translate('config.updateError');
          _accountMsgErro = true;
        });
      }
    } finally {
      if (mounted) setState(() => _savingAccount = false);
    }
  }

  Future<void> _deletarConta() async {
    final lang = context.read<LanguageProvider>();
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: WebColors.bg,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(WebColors.radiusLg),
          side: const BorderSide(color: WebColors.border),
        ),
        title: Text(lang.translate('config.deleteAccount'), style: const TextStyle(color: WebColors.text)),
        content: Text(lang.translate('config.deleteAccountConfirmBody'), style: const TextStyle(color: WebColors.textSecondary)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(lang.translate('perfil.cancel'), style: const TextStyle(color: WebColors.textMuted)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: WebColors.danger),
            child: Text(lang.translate('config.deleteAccount')),
          ),
        ],
      ),
    );
    if (confirm != true || !mounted) return;
    final auth = context.read<AuthProvider>();
    final id = auth.usuario?.id;
    if (id == null) return;
    try {
      await UsuarioService.deletar(id);
      await auth.logout();
      if (mounted) Navigator.pushNamedAndRemoveUntil(context, '/login', (_) => false);
    } catch (e) {
      if (mounted) {
        setState(() {
          _accountMsg = e is ApiException ? e.message : lang.translate('config.deleteError');
          _accountMsgErro = true;
        });
      }
    }
  }

  Future<void> _salvarSenha() async {
    final lang = context.read<LanguageProvider>();
    final senhaAtual = _senhaAtualCtrl.text;
    final novaSenha = _novaSenhaCtrl.text;
    final confirmar = _confirmarSenhaCtrl.text;

    String? erroSenhaAtual;
    String? erroNovaSenha;
    String? erroConfirmar;

    if (senhaAtual.trim().isEmpty) {
      erroSenhaAtual = lang.translate('config.currentPasswordRequired');
    }
    if (novaSenha.trim().isEmpty) {
      erroNovaSenha = lang.translate('config.newPasswordRequired');
    } else if (novaSenha.length < 8) {
      erroNovaSenha = lang.translate('config.newPasswordTooShort');
    } else if (!novaSenha.contains(RegExp(r'[A-Z]')) || !novaSenha.contains(RegExp(r'[0-9]'))) {
      erroNovaSenha = lang.translate('config.newPasswordWeak');
    } else if (senhaAtual.isNotEmpty && novaSenha == senhaAtual) {
      erroNovaSenha = lang.translate('config.newPasswordSameAsCurrent');
    }
    if (confirmar.trim().isEmpty) {
      erroConfirmar = lang.translate('config.confirmPasswordRequired');
    } else if (novaSenha.isNotEmpty && confirmar != novaSenha) {
      erroConfirmar = lang.translate('config.passwordsDontMatch');
    }

    setState(() {
      _erroSenhaAtual = erroSenhaAtual;
      _erroNovaSenha = erroNovaSenha;
      _erroConfirmarSenha = erroConfirmar;
      _passwordMsg = null;
    });
    if (erroSenhaAtual != null || erroNovaSenha != null || erroConfirmar != null) return;

    final auth = context.read<AuthProvider>();
    final id = auth.usuario?.id;
    if (id == null) return;
    setState(() => _savingPassword = true);
    try {
      await UsuarioService.trocarSenha(id: id, senhaAtual: senhaAtual, novaSenha: novaSenha);
      if (!mounted) return;
      _senhaAtualCtrl.clear();
      _novaSenhaCtrl.clear();
      _confirmarSenhaCtrl.clear();
      setState(() { _passwordMsg = lang.translate('config.passwordUpdateSuccess'); _passwordMsgErro = false; });
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.statusCode == 401) {
        setState(() => _erroSenhaAtual = e.message.isNotEmpty ? e.message : lang.translate('config.currentPasswordIncorrect'));
      } else {
        setState(() { _passwordMsg = e.message; _passwordMsgErro = true; });
      }
    } catch (_) {
      if (mounted) setState(() { _passwordMsg = lang.translate('config.passwordUpdateError'); _passwordMsgErro = true; });
    } finally {
      if (mounted) setState(() => _savingPassword = false);
    }
  }

  void _showLanguagePicker(LanguageProvider lang) {
    showModalBottomSheet(
      context: context,
      backgroundColor: WebColors.bg,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(WebColors.radiusLg)),
      ),
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 16),
            Text(lang.translate('config.language'), style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 16)),
            const SizedBox(height: 8),
            _langOption(lang, code: 'pt', label: lang.translate('config.langPt')),
            _langOption(lang, code: 'en', label: lang.translate('config.langEn')),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }

  Widget _langOption(LanguageProvider lang, {required String code, required String label}) {
    final selecionado = lang.locale.languageCode == code;
    return ListTile(
      leading: Icon(Icons.check, color: selecionado ? WebColors.primary : Colors.transparent),
      title: Text(label, style: const TextStyle(color: WebColors.text)),
      onTap: () {
        lang.setLanguage(code);
        Navigator.pop(context);
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    return Scaffold(
      backgroundColor: WebColors.bg,
      appBar: AppBar(
        backgroundColor: WebColors.bg,
        elevation: 0,
        iconTheme: const IconThemeData(color: WebColors.textSecondary),
        title: Text(
          lang.translate('config.header'),
          style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 17),
        ),
      ),
      body: Stack(
        children: [
          const Positioned.fill(child: AmbientBackground()),
          SafeArea(
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: switch (_view) {
                _ConfigView.menu => _buildMenu(lang),
                _ConfigView.account => _buildAccount(lang),
                _ConfigView.password => _buildPassword(lang),
              },
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildMenu(LanguageProvider lang) => [
        Text(
          lang.translate('config.subtitle'),
          style: const TextStyle(color: WebColors.textMuted, fontSize: 14),
        ),
        const SizedBox(height: 20),
        _settingsRow(
          icon: Icons.person_outline,
          title: lang.translate('config.changeAccount'),
          desc: lang.translate('config.changeAccountDesc'),
          onTap: () => _irPara(_ConfigView.account),
        ),
        const SizedBox(height: 12),
        _settingsRow(
          icon: Icons.lock_outline,
          title: lang.translate('config.changePassword'),
          desc: lang.translate('config.changePasswordDesc'),
          onTap: () => _irPara(_ConfigView.password),
        ),
        const SizedBox(height: 12),
        _settingsRow(
          icon: Icons.language,
          title: lang.translate('config.language'),
          desc: lang.translate('config.languageDesc'),
          onTap: () => _showLanguagePicker(lang),
        ),
      ];

  List<Widget> _buildAccount(LanguageProvider lang) => [
        _backRow(lang, () => _irPara(_ConfigView.menu)),
        const SizedBox(height: 12),
        Text(lang.translate('config.alterTitle'),
            style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w800, fontSize: 19)),
        const SizedBox(height: 20),
        _campo(controller: _nomeCtrl, label: lang.translate('config.newName'), hint: lang.translate('config.namePlaceholder')),
        const SizedBox(height: 14),
        _campo(
          controller: _emailCtrl,
          label: lang.translate('config.newEmail'),
          hint: lang.translate('config.emailPlaceholder'),
          keyboardType: TextInputType.emailAddress,
        ),
        if (_accountMsg != null) ...[
          const SizedBox(height: 16),
          _banner(_accountMsg!, _accountMsgErro),
        ],
        const SizedBox(height: 22),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            SizedBox(
              width: 180,
              child: GradientButton(
                onPressed: _savingAccount ? null : _salvarConta,
                child: Center(
                  child: _savingAccount
                      ? const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : Text(lang.translate('config.saveChanges')),
                ),
              ),
            ),
            OutlinedButton(
              onPressed: _deletarConta,
              style: OutlinedButton.styleFrom(
                foregroundColor: WebColors.danger,
                side: const BorderSide(color: WebColors.danger),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(WebColors.radiusMd)),
              ),
              child: Text(lang.translate('config.deleteAccount')),
            ),
          ],
        ),
      ];

  List<Widget> _buildPassword(LanguageProvider lang) => [
        _backRow(lang, () => _irPara(_ConfigView.menu)),
        const SizedBox(height: 12),
        Text(lang.translate('config.changePasswordTitle'),
            style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w800, fontSize: 19)),
        const SizedBox(height: 20),
        _campoSenha(
          controller: _senhaAtualCtrl,
          label: lang.translate('config.currentPassword'),
          hint: lang.translate('config.currentPasswordPlaceholder'),
          visivel: _senhaAtualVisivel,
          onToggle: () => setState(() => _senhaAtualVisivel = !_senhaAtualVisivel),
          erro: _erroSenhaAtual,
        ),
        const SizedBox(height: 14),
        _campoSenha(
          controller: _novaSenhaCtrl,
          label: lang.translate('config.newPassword'),
          hint: lang.translate('config.newPasswordPlaceholder'),
          visivel: _novaSenhaVisivel,
          onToggle: () => setState(() => _novaSenhaVisivel = !_novaSenhaVisivel),
          erro: _erroNovaSenha,
        ),
        const SizedBox(height: 14),
        _campoSenha(
          controller: _confirmarSenhaCtrl,
          label: lang.translate('config.confirmNewPassword'),
          hint: lang.translate('config.confirmNewPasswordPlaceholder'),
          visivel: _confirmarSenhaVisivel,
          onToggle: () => setState(() => _confirmarSenhaVisivel = !_confirmarSenhaVisivel),
          erro: _erroConfirmarSenha,
        ),
        if (_passwordMsg != null) ...[
          const SizedBox(height: 16),
          _banner(_passwordMsg!, _passwordMsgErro),
        ],
        const SizedBox(height: 22),
        SizedBox(
          width: 200,
          child: GradientButton(
            onPressed: _savingPassword ? null : _salvarSenha,
            child: Center(
              child: _savingPassword
                  ? const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : Text(lang.translate('config.savePassword')),
            ),
          ),
        ),
      ];

  Widget _settingsRow({required IconData icon, required String title, required String desc, required VoidCallback onTap}) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(WebColors.radiusLg),
        child: GlassContainer(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(WebColors.radiusMd),
                  gradient: WebColors.gradient,
                ),
                alignment: Alignment.center,
                // Ícone escuro (não branco) — contrasta melhor contra o
                // gradiente azul→ciano, que é claro demais pra um ícone claro.
                child: Icon(icon, color: WebColors.bg, size: 22),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w600, fontSize: 15)),
                    const SizedBox(height: 2),
                    Text(desc, style: const TextStyle(color: WebColors.textMuted, fontSize: 13)),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: WebColors.textMuted),
            ],
          ),
        ),
      ),
    );
  }

  Widget _backRow(LanguageProvider lang, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(WebColors.radiusMd),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 2),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.arrow_back, size: 20, color: WebColors.textSecondary),
            const SizedBox(width: 8),
            Text(lang.translate('common.back'),
                style: const TextStyle(color: WebColors.textSecondary, fontWeight: FontWeight.w600, fontSize: 14)),
          ],
        ),
      ),
    );
  }

  Widget _banner(String msg, bool erro) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: (erro ? WebColors.danger : WebColors.success).withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(WebColors.radiusMd),
      ),
      child: Text(msg, style: TextStyle(color: erro ? WebColors.danger : WebColors.success, fontSize: 13, fontWeight: FontWeight.w600)),
    );
  }

  InputDecoration _decoration({required String label, String? hint, String? errorText}) {
    return InputDecoration(
      labelText: label,
      hintText: hint,
      errorText: errorText,
      labelStyle: const TextStyle(color: WebColors.textMuted),
      hintStyle: const TextStyle(color: WebColors.textMuted),
      filled: true,
      fillColor: WebColors.surface2,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(WebColors.radiusMd), borderSide: BorderSide.none),
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

  Widget _campo({
    required TextEditingController controller,
    required String label,
    String? hint,
    TextInputType? keyboardType,
  }) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      style: const TextStyle(color: WebColors.text),
      decoration: _decoration(label: label, hint: hint),
    );
  }

  Widget _campoSenha({
    required TextEditingController controller,
    required String label,
    required String hint,
    required bool visivel,
    required VoidCallback onToggle,
    String? erro,
  }) {
    return TextField(
      controller: controller,
      obscureText: !visivel,
      style: const TextStyle(color: WebColors.text),
      decoration: _decoration(label: label, hint: hint, errorText: erro).copyWith(
        suffixIcon: IconButton(
          icon: Icon(visivel ? Icons.visibility_off : Icons.visibility, color: WebColors.textMuted),
          onPressed: onToggle,
        ),
      ),
    );
  }
}
