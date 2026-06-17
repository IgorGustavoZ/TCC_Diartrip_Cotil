import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../core/api_client.dart';
import '../models/foto.dart';
class FotoService {
  static Future<List<Foto>> listar(int idGrupo) async {
    final r = await dio.get('/grupos/$idGrupo/fotos');
    _check(r);
    return (r.data as List)
        .map((e) => Foto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  static Future<String> upload({
    required int idGrupo,
    required String filePath,
    String? filename,
    required String mimeType,
    required Uint8List bytes,
    String? templateUsado,
  }) async {
    final fname = filename ?? filePath.split('/').last;
    debugPrint('[FotoService.upload] filename=$fname mime=$mimeType bytes=${bytes.length} web=$kIsWeb');
    
    final multipart = MultipartFile.fromBytes(
      bytes,
      filename: fname,
      contentType: DioMediaType.parse(mimeType),
    );

    final form = FormData.fromMap({
      'arquivo': multipart,
      if (templateUsado != null) 'template_usado': templateUsado,
    });

    final r = await dio.post('/grupos/$idGrupo/fotos', data: form);
    _check(r);
    return (r.data as Map<String, dynamic>)['url'] as String;
  }

  static Future<void> deletar(int idFoto) async {
    final r = await dio.delete('/fotos/$idFoto');
    _check(r);
  }

  static void _check(Response r) {
    if (r.statusCode != null && r.statusCode! >= 400) {
      throw apiError(r.data, 'Erro ${r.statusCode}');
    }
  }
}
