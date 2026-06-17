import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/dashboard.dart';

class DashboardService {
  static Future<DashboardCompleto> get(int idGrupo) async {
    final r = await dio.get('/grupos/$idGrupo/dashboard');
    _check(r);
    return DashboardCompleto.fromJson(r.data as Map<String, dynamic>);
  }

  static void _check(Response r) {
    if (r.statusCode != null && r.statusCode! >= 400) {
      throw apiError(r.data, 'Erro ${r.statusCode}');
    }
  }
}
