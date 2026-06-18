// ignore: avoid_web_libraries_in_flutter
import 'package:dio/browser.dart';
import 'package:dio/dio.dart';

void applyWebCredentials(Dio dio) {
  final adapter = dio.httpClientAdapter;
  if (adapter is BrowserHttpClientAdapter) {
    adapter.withCredentials = true;
  }
}
