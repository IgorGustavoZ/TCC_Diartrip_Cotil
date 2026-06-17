import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme.dart';
import '../../providers/auth_provider.dart';
import '../../providers/language_provider.dart';
import '../../services/usuario_service.dart';

class ConfigScreen extends StatefulWidget {
  const ConfigScreen({super.key});
  @override
  State<ConfigScreen> createState() => _ConfigScreenState();
}

class _ConfigScreenState extends State<ConfigScreen> {
  final _nomeCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  bool _loading = false;
  String? _msg;
  bool _msgErro = false;

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
    super.dispose();
  }

  Future<void> _salvar() async {
    final auth = context.read<AuthProvider>();
    final lang = context.read<LanguageProvider>();
    final id = auth.usuario?.id;
    if (id == null) return;
    setState(() { _loading = true; _msg = null; });
    try {
      final u = await UsuarioService.atualizar(
        id: id,
        nome: _nomeCtrl.text.trim(),
        email: _emailCtrl.text.trim(),
      );
      auth.updateUsuario(u);
      setState(() { _msg = lang.translate('config.saved'); _msgErro = false; });
    } catch (e) {
      setState(() { _msg = e.toString(); _msgErro = true; });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _deletarConta() async {
    final lang = context.read<LanguageProvider>();
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(lang.translate('config.deleteConfirmTitle')),
        content: Text(lang.translate('config.deleteConfirmDesc')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text(lang.translate('config.cancel'))),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: AppTheme.error),
            child: Text(lang.translate('config.delete')),
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
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();

    return Scaffold(
      appBar: AppBar(title: Text(lang.translate('config.title'))),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(lang.translate('config.info'), style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
          const SizedBox(height: 16),
          TextField(
            controller: _nomeCtrl,
            decoration: InputDecoration(
              labelText: lang.translate('config.name'),
              prefixIcon: const Icon(Icons.person_outline),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _emailCtrl,
            keyboardType: TextInputType.emailAddress,
            decoration: InputDecoration(
              labelText: lang.translate('config.email'),
              prefixIcon: const Icon(Icons.email_outlined),
            ),
          ),
          const SizedBox(height: 24),
          const Divider(),
          const SizedBox(height: 16),
          Text(lang.translate('language.select'), style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            value: lang.locale.languageCode,
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.language),
              border: OutlineInputBorder(),
            ),
            items: [
              DropdownMenuItem(value: 'pt', child: Text(lang.translate('language.pt'))),
              DropdownMenuItem(value: 'en', child: Text(lang.translate('language.en'))),
            ],
            onChanged: (val) {
              if (val != null) lang.setLanguage(val);
            },
          ),
          if (_msg != null) ...[
            const SizedBox(height: 10),
            Text(
              _msg!,
              style: TextStyle(
                color: _msgErro ? AppTheme.error : AppTheme.success,
                fontSize: 13,
              ),
            ),
          ],
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: _loading ? null : _salvar,
            child: _loading
                ? const SizedBox(
                    height: 18,
                    width: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : Text(lang.translate('config.save')),
          ),
          const SizedBox(height: 32),
          const Divider(),
          const SizedBox(height: 16),
          Text(lang.translate('config.danger'), style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16, color: AppTheme.error)),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: _deletarConta,
            icon: const Icon(Icons.delete_forever, color: AppTheme.error),
            label: Text(lang.translate('config.delete'), style: const TextStyle(color: AppTheme.error)),
            style: OutlinedButton.styleFrom(side: const BorderSide(color: AppTheme.error)),
          ),
        ],
      ),
    );
  }
}
