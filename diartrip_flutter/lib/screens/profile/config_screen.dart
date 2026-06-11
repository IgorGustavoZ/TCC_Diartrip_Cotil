import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme.dart';
import '../../providers/auth_provider.dart';
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
      setState(() { _msg = 'Changes saved!'; _msgErro = false; });
    } catch (e) {
      setState(() { _msg = e.toString(); _msgErro = true; });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _deletarConta() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Delete Account'),
        content: const Text(
          'This action is permanent. All your data will be removed. Continue?',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: AppTheme.error),
            child: const Text('Delete'),
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
    return Scaffold(
      appBar: AppBar(title: const Text('Account Settings')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text('Account Information', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
          const SizedBox(height: 16),
          TextField(
            controller: _nomeCtrl,
            decoration: const InputDecoration(
              labelText: 'Name',
              prefixIcon: Icon(Icons.person_outline),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _emailCtrl,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(
              labelText: 'Email',
              prefixIcon: Icon(Icons.email_outlined),
            ),
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
                : const Text('Save Changes'),
          ),
          const SizedBox(height: 32),
          const Divider(),
          const SizedBox(height: 16),
          const Text('Danger Zone', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16, color: AppTheme.error)),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: _deletarConta,
            icon: const Icon(Icons.delete_forever, color: AppTheme.error),
            label: const Text('Delete Account', style: TextStyle(color: AppTheme.error)),
            style: OutlinedButton.styleFrom(side: const BorderSide(color: AppTheme.error)),
          ),
        ],
      ),
    );
  }
}
