import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/web_style.dart';
import '../providers/language_provider.dart';

/// Modal de confirmação genérico, equivalente ao `abrirModalConfirmacao()`
/// de `backend/frontend/static/confirm-modal.js` — usado em toda ação
/// destrutiva/sensível de viagem.html (sair, excluir, remover membro,
/// despublicar, etc). `perigo: true` deixa o botão de confirmação vermelho.
Future<bool> confirmarAcao(
  BuildContext context, {
  required String titulo,
  required String mensagem,
  required String textoConfirmar,
  bool perigo = true,
}) async {
  final lang = context.read<LanguageProvider>();
  final result = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      backgroundColor: WebColors.bg2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(WebColors.radiusLg)),
      title: Text(titulo, style: const TextStyle(color: WebColors.text, fontWeight: FontWeight.w700, fontSize: 16)),
      content: Text(mensagem, style: const TextStyle(color: WebColors.textSecondary, fontSize: 14, height: 1.4)),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(ctx, false),
          style: TextButton.styleFrom(foregroundColor: WebColors.textMuted),
          child: Text(lang.translate('common.cancel')),
        ),
        TextButton(
          onPressed: () => Navigator.pop(ctx, true),
          style: TextButton.styleFrom(
            foregroundColor: perigo ? WebColors.danger : WebColors.primary,
          ),
          child: Text(textoConfirmar, style: const TextStyle(fontWeight: FontWeight.w700)),
        ),
      ],
    ),
  );
  return result == true;
}
