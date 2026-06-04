// ignore: avoid_web_libraries_in_flutter
import 'package:dio/browser.dart';
import 'package:dio/dio.dart';

/// Ativa withCredentials no adaptador XHR do Flutter Web.
///
/// Sem isso o navegador omite cookies e cabeçalhos de autenticação em
/// requisições cross-origin (ex.: Flutter em localhost:PORT → API em
/// localhost:8000), e o servidor nunca recebe a sessão do usuário.
///
/// Pré-requisito no backend:
///   • Access-Control-Allow-Origin: <origin exata> (não "*")
///   • Access-Control-Allow-Credentials: true
void applyWebCredentials(Dio dio) {
  final adapter = dio.httpClientAdapter;
  if (adapter is BrowserHttpClientAdapter) {
    adapter.withCredentials = true;
  }
}
