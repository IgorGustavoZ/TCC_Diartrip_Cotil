import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import '../core/web_style.dart';

class AvatarWidget extends StatelessWidget {
  final String? fotoUrl;
  final String iniciais;
  final double radius;
  final VoidCallback? onTap;

  const AvatarWidget({
    super.key,
    this.fotoUrl,
    required this.iniciais,
    this.radius = 20,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final avatar = fotoUrl != null && fotoUrl!.isNotEmpty
        ? CircleAvatar(
            radius: radius,
            backgroundImage: CachedNetworkImageProvider(fotoUrl!),
          )
        : Container(
            width: radius * 2,
            height: radius * 2,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: WebColors.gradient,
            ),
            alignment: Alignment.center,
            child: Text(
              iniciais,
              style: TextStyle(
                color: Colors.white,
                fontSize: radius * 0.7,
                fontWeight: FontWeight.w700,
              ),
            ),
          );

    if (onTap != null) {
      return MouseRegion(
        cursor: SystemMouseCursors.click,
        child: GestureDetector(onTap: onTap, child: avatar),
      );
    }
    return avatar;
  }
}
