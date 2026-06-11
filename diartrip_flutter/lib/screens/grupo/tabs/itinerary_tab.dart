import 'package:flutter/material.dart';
import '../../../core/app_logger.dart';
import '../../../core/theme.dart';
import '../../../models/roteiro.dart';
import '../../../services/roteiro_service.dart';

class ItineraryTab extends StatefulWidget {
  final int idGrupo;
  final bool isAdmin;
  const ItineraryTab({super.key, required this.idGrupo, required this.isAdmin});
  @override
  State<ItineraryTab> createState() => _ItineraryTabState();
}

class _ItineraryTabState extends State<ItineraryTab>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;
  List<Roteiro> _roteiros = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final r = await RoteiroService.listar(widget.idGrupo);
      if (mounted) setState(() { _roteiros = r; _loading = false; });
    } catch (e, s) {
      AppLogger.captureError('ItineraryTab._load', e, s);
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _showForm([Roteiro? existing]) async {
    final tituloCtrl = TextEditingController(text: existing?.titulo);
    final descCtrl = TextEditingController(text: existing?.descricao);
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(existing == null ? 'Add Item' : 'Edit Item'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: tituloCtrl,
              decoration: const InputDecoration(labelText: 'Title'),
              autofocus: true,
            ),
            const SizedBox(height: 10),
            TextField(
              controller: descCtrl,
              decoration: const InputDecoration(labelText: 'Description'),
              maxLines: 3,
            ),
          ],
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel')),
          ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Save')),
        ],
      ),
    );
    if (ok != true) return;
    final titulo = tituloCtrl.text.trim();
    final desc = descCtrl.text.trim();
    if (titulo.isEmpty) return;
    try {
      if (existing == null) {
        await RoteiroService.criar(
            idGrupo: widget.idGrupo, titulo: titulo, descricao: desc);
      } else {
        await RoteiroService.atualizar(
            id: existing.id, titulo: titulo, descricao: desc);
      }
      _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: FloatingActionButton(
        mini: true,
        onPressed: () => _showForm(),
        child: const Icon(Icons.add),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: _roteiros.isEmpty
                  ? const Center(
                      child: Text('No itinerary items yet.',
                          style: TextStyle(color: AppTheme.onSurfaceMuted)))
                  : ListView.builder(
                      padding: const EdgeInsets.fromLTRB(12, 12, 12, 80),
                      itemCount: _roteiros.length,
                      itemBuilder: (_, i) {
                        final r = _roteiros[i];
                        return Card(
                          child: ListTile(
                            leading: CircleAvatar(
                              backgroundColor:
                                  AppTheme.primary.withValues(alpha: 0.15),
                              child: Text('${i + 1}',
                                  style: const TextStyle(
                                      color: AppTheme.primary,
                                      fontWeight: FontWeight.w700)),
                            ),
                            title: Text(r.titulo,
                                style: const TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600)),
                            subtitle: r.descricao.isNotEmpty
                                ? Text(r.descricao,
                                    style: const TextStyle(fontSize: 12))
                                : null,
                            trailing: widget.isAdmin
                                ? Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      IconButton(
                                        icon: const Icon(
                                            Icons.edit_outlined,
                                            size: 18),
                                        onPressed: () => _showForm(r),
                                      ),
                                      IconButton(
                                        icon: const Icon(
                                            Icons.delete_outline,
                                            size: 18,
                                            color: AppTheme.error),
                                        onPressed: () async {
                                          try {
                                            await RoteiroService.deletar(r.id);
                                            _load();
                                          } catch (e) {
                                            if (context.mounted) {
                                              ScaffoldMessenger.of(context)
                                                  .showSnackBar(SnackBar(
                                                      content: Text(
                                                          e.toString())));
                                            }
                                          }
                                        },
                                      ),
                                    ],
                                  )
                                : null,
                          ),
                        );
                      },
                    ),
            ),
    );
  }
}
