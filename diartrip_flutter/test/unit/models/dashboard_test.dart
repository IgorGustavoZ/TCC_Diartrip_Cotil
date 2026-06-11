import 'package:flutter_test/flutter_test.dart';
import 'package:diartrip_flutter/models/dashboard.dart';

void main() {
  // ── CategoriaGasto ─────────────────────────────────────────────────────────
  group('CategoriaGasto.fromJson', () {
    test('mapeamento básico', () {
      final c = CategoriaGasto.fromJson({'categoria': 'Alimentação', 'total': 450.0});
      expect(c.categoria, 'Alimentação');
      expect(c.total, 450.0);
    });

    test('total inteiro convertido para double', () {
      final c = CategoriaGasto.fromJson({'categoria': 'Transporte', 'total': 200});
      expect(c.total, isA<double>());
    });
  });

  // ── GastoResumido ──────────────────────────────────────────────────────────
  group('GastoResumido.fromJson', () {
    test('todos os campos', () {
      final g = GastoResumido.fromJson({
        'descricao': 'Jantar',
        'categoria': 'Alimentação',
        'valor': 120.0,
        'data_gasto': '2026-06-05',
      });
      expect(g.descricao, 'Jantar');
      expect(g.valor, 120.0);
    });

    test('descrição ausente assume vazio', () {
      final g = GastoResumido.fromJson({'categoria': 'Lazer', 'valor': 50.0, 'data_gasto': '2026-06-01'});
      expect(g.descricao, '');
    });

    test('data ausente assume vazio', () {
      final g = GastoResumido.fromJson({'categoria': 'Outro', 'valor': 10.0});
      expect(g.dataGasto, '');
    });
  });

  // ── RankingItem ────────────────────────────────────────────────────────────
  group('RankingItem.fromJson', () {
    test('campos mapeados', () {
      final r = RankingItem.fromJson({'nome': 'Ana', 'total': 800.0});
      expect(r.nome, 'Ana');
      expect(r.total, 800.0);
    });
  });

  // ── Estatisticas ───────────────────────────────────────────────────────────
  group('Estatisticas.fromJson', () {
    test('valores presentes', () {
      final e = Estatisticas.fromJson({'membros_ativos': 4, 'total_fotos_subidas': 10, 'itens_no_roteiro': 7});
      expect(e.membrosAtivos, 4);
      expect(e.totalFotosSubidas, 10);
      expect(e.itensNoRoteiro, 7);
    });

    test('valores ausentes assumem zero', () {
      final e = Estatisticas.fromJson({});
      expect(e.membrosAtivos, 0);
      expect(e.totalFotosSubidas, 0);
      expect(e.itensNoRoteiro, 0);
    });
  });

  // ── DashboardGeral ─────────────────────────────────────────────────────────
  group('DashboardGeral.fromJson', () {
    test('distribuição vazia quando ausente', () {
      final d = DashboardGeral.fromJson({
        'total_consumido': 1000.0,
        'orcamento_restante': 4000.0,
        'percentual_consumido': 20,
      });
      expect(d.totalConsumido, 1000.0);
      expect(d.orcamentoRestante, 4000.0);
      expect(d.percentualConsumido, 20);
      expect(d.distribuicao, isEmpty);
    });

    test('distribuição com categorias', () {
      final d = DashboardGeral.fromJson({
        'total_consumido': 500.0,
        'orcamento_restante': 500.0,
        'percentual_consumido': 50,
        'distribuicao_categorias': [
          {'categoria': 'Alimentação', 'total': 300.0},
          {'categoria': 'Transporte', 'total': 200.0},
        ],
      });
      expect(d.distribuicao.length, 2);
      expect(d.distribuicao.first.categoria, 'Alimentação');
    });

    test('percentual nulo assume zero', () {
      final d = DashboardGeral.fromJson({
        'total_consumido': 0.0,
        'orcamento_restante': 1000.0,
      });
      expect(d.percentualConsumido, 0);
    });
  });

  // ── DashboardPessoal ───────────────────────────────────────────────────────
  group('DashboardPessoal.fromJson', () {
    test('últimos gastos vazio quando ausente', () {
      final d = DashboardPessoal.fromJson({
        'total_pago_por_mim': 200.0,
        'minha_divida_atual': 50.0,
      });
      expect(d.totalPagoPorMim, 200.0);
      expect(d.minhaDividaAtual, 50.0);
      expect(d.ultimosGastos, isEmpty);
    });

    test('últimos gastos com itens', () {
      final d = DashboardPessoal.fromJson({
        'total_pago_por_mim': 300.0,
        'minha_divida_atual': 0.0,
        'ultimos_gastos_pessoais': [
          {'descricao': 'Café', 'categoria': 'Alimentação', 'valor': 15.0, 'data_gasto': '2026-06-01'},
        ],
      });
      expect(d.ultimosGastos.length, 1);
      expect(d.ultimosGastos.first.descricao, 'Café');
    });
  });

  // ── DashboardAdmin ─────────────────────────────────────────────────────────
  group('DashboardAdmin.fromJson', () {
    test('ranking e estatísticas mapeados', () {
      final d = DashboardAdmin.fromJson({
        'ranking_contribuicao_financeira': [
          {'nome': 'Ana', 'total': 500.0},
          {'nome': 'Beto', 'total': 300.0},
        ],
        'estatisticas': {'membros_ativos': 3, 'total_fotos_subidas': 5, 'itens_no_roteiro': 2},
      });
      expect(d.ranking.length, 2);
      expect(d.ranking.first.nome, 'Ana');
      expect(d.estatisticas.membrosAtivos, 3);
    });

    test('ranking vazio quando ausente', () {
      final d = DashboardAdmin.fromJson(<String, dynamic>{
        'estatisticas': <String, dynamic>{},
      });
      expect(d.ranking, isEmpty);
    });
  });

  // ── DashboardCompleto ──────────────────────────────────────────────────────
  group('DashboardCompleto.fromJson', () {
    final jsonCompleto = <String, dynamic>{
      'geral': <String, dynamic>{
        'total_consumido': 1000.0,
        'orcamento_restante': 4000.0,
        'percentual_consumido': 20,
      },
      'pessoal': <String, dynamic>{
        'total_pago_por_mim': 300.0,
        'minha_divida_atual': 100.0,
      },
      'admin': <String, dynamic>{
        'ranking_contribuicao_financeira': <dynamic>[],
        'estatisticas': <String, dynamic>{},
      },
    };

    test('todos os objetos aninhados construídos', () {
      final d = DashboardCompleto.fromJson(jsonCompleto);
      expect(d.geral.totalConsumido, 1000.0);
      expect(d.pessoal.totalPagoPorMim, 300.0);
      expect(d.admin, isNotNull);
    });

    test('admin é nulo quando ausente no JSON', () {
      final d = DashboardCompleto.fromJson(<String, dynamic>{
        'geral': <String, dynamic>{'total_consumido': 0.0, 'orcamento_restante': 0.0, 'percentual_consumido': 0},
        'pessoal': <String, dynamic>{'total_pago_por_mim': 0.0, 'minha_divida_atual': 0.0},
      });
      expect(d.admin, isNull);
    });
  });
}
