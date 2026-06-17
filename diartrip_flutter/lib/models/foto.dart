class Foto {
  final int id;
  final int idUsuario;
  final String caminhoArquivo;
  final String? templateUsado;
  final String? dataUpload;
  final String? nomeUsuario;

  const Foto({
    required this.id,
    required this.idUsuario,
    required this.caminhoArquivo,
    this.templateUsado,
    this.dataUpload,
    this.nomeUsuario,
  });

  factory Foto.fromJson(Map<String, dynamic> j) => Foto(
        id: j['id_foto'] as int,
        idUsuario: j['id_usuario'] as int,
        caminhoArquivo: j['caminho_arquivo'] as String,
        templateUsado: j['template_usado'] as String?,
        dataUpload: j['data_upload'] as String?,
        nomeUsuario: j['nome'] as String?,
      );
}
