import 'package:flutter/material.dart';
import '../core/web_style.dart';

/// Seção com cabeçalho-"puxador": começa recolhida (só ícone, título, contador
/// e uma seta) e abre/fecha ao toque no cabeçalho. O [child] só entra na árvore
/// quando a seção está aberta, então nada dele é construído (nem faz requisições)
/// enquanto estiver recolhida.
class CollapsibleSection extends StatefulWidget {
  final IconData? icon;
  final String title;
  final int? count;
  final bool initiallyExpanded;
  final Widget child;

  const CollapsibleSection({
    super.key,
    this.icon,
    required this.title,
    required this.child,
    this.count,
    this.initiallyExpanded = false,
  });

  @override
  State<CollapsibleSection> createState() => _CollapsibleSectionState();
}

class _CollapsibleSectionState extends State<CollapsibleSection> {
  late bool _aberta = widget.initiallyExpanded;
  final _secaoKey = GlobalKey();
  bool _rolarAoTerminar = false;

  void _alternar() {
    setState(() {
      _aberta = !_aberta;
      // Só rola ao ABRIR; recolher não precisa mover a página.
      _rolarAoTerminar = _aberta;
    });
  }

  // Ao terminar de expandir, leva a seção (cabeçalho no topo da área visível)
  // para dentro da tela, para a pessoa ver o conteúdo sem arrastar. Precisa
  // esperar a animação acabar: com a seção ainda pequena o destino sairia errado.
  void _rolarParaVista() {
    if (!_rolarAoTerminar) return;
    _rolarAoTerminar = false;
    final contexto = _secaoKey.currentContext;
    if (!mounted || !_aberta || contexto == null) return;
    Scrollable.ensureVisible(
      contexto,
      alignment: 0,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      key: _secaoKey,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Semantics(
          button: true,
          expanded: _aberta,
          label: widget.title,
          child: InkWell(
            borderRadius: BorderRadius.circular(WebColors.radiusMd),
            onTap: _alternar,
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
              child: Row(
                children: [
                  if (widget.icon != null) ...[
                    Icon(widget.icon, size: 18, color: WebColors.textMuted),
                    const SizedBox(width: 8),
                  ],
                  Text(
                    widget.title,
                    style: const TextStyle(color: WebColors.text, fontSize: 15, fontWeight: FontWeight.w700),
                  ),
                  if (widget.count != null) ...[
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: WebColors.surface2,
                        borderRadius: BorderRadius.circular(WebColors.radiusPill),
                        border: Border.all(color: WebColors.border),
                      ),
                      child: Text(
                        '${widget.count}',
                        style: const TextStyle(
                          color: WebColors.textMuted,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                  const Spacer(),
                  AnimatedRotation(
                    turns: _aberta ? 0.5 : 0,
                    duration: const Duration(milliseconds: 250),
                    curve: Curves.easeInOut,
                    child: const Icon(Icons.keyboard_arrow_down, color: WebColors.textMuted),
                  ),
                ],
              ),
            ),
          ),
        ),
        AnimatedSize(
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeInOut,
          alignment: Alignment.topCenter,
          onEnd: _rolarParaVista,
          child: _aberta
              ? Padding(padding: const EdgeInsets.only(top: 12), child: widget.child)
              : const SizedBox(width: double.infinity),
        ),
      ],
    );
  }
}
