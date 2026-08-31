using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using LiveChartsCore;
using LiveChartsCore.SkiaSharpView;
using LiveChartsCore.SkiaSharpView.Painting;
using SkiaSharp;
using WindowLobby.crud;
using WindowLobby.CRUD;
using WindowLobby.CRUD.models;

namespace WindowLobby.Pages
{
   
    public partial class DashboardPage : Page
    {
        // Paleta graficxo
        private static readonly string[] Paleta =
        {
            "#3B82F6", "#4ADE80", "#FBBF24", "#F472B6", "#A78BFA", "#38BDF8", "#FB7185"
        };

        public DashboardPage()
        {
            InitializeComponent();

            
            chartDestinos.LegendTextPaint = new SolidColorPaint(SKColors.White);

            Loaded += async (_, _) => await CarregarEstatisticas();
        }

        private async Task CarregarEstatisticas()
        {
            try
            {
                var jsonVia = await Viagem.GetViagens();
                List<ViagemModel>? viagens = null;
                if (jsonVia is not null)
                {
                    viagens = JsonSerializer.Deserialize<List<ViagemModel>>(
                        jsonVia,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    );
                    txtViagens.Text = (viagens?.Count ?? 0).ToString();

                    MontarGraficoDestinos(viagens);
                }

                var jsonUsu = await Usuario.GetUsuarios();
                if (jsonUsu is not null)
                {
                    var usuarios = JsonSerializer.Deserialize<List<UsuarioModel>>(
                        jsonUsu,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    );
                    txtUsuarios.Text = (usuarios?.Count ?? 0).ToString();

                    MontarGraficoUsuariosPorMes(usuarios);
                }

                var jsonChat = await Chat_ia.BuscarMensagens();
                if (jsonChat is not null)
                {
                    var chats = JsonSerializer.Deserialize<List<ChatModel>>(
                        jsonChat,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    );

                    double totalChats = 0;
                    if (chats is not null)
                    {
                        foreach (var c in chats)
                            totalChats += c.resposta?.Length ?? 0;
                    }

                    txtChatIA.Text = totalChats.ToString();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[DashboardPage.CarregarEstatisticas] Erro: {ex}");
            }
        }

        // ── Gráfico: usuários criados por mês nos ultimos 12 meses ────────

        private void MontarGraficoUsuariosPorMes(List<UsuarioModel>? usuarios)
        {
            var datasValidas = (usuarios ?? new List<UsuarioModel>())
                .Select(u => DateTime.TryParse(u.data_criacao, out var data) ? (DateTime?)data : null)
                .Where(data => data.HasValue)
                .Select(data => data!.Value)
                .ToList();

            
            var mesAtual = new DateTime(DateTime.Now.Year, DateTime.Now.Month, 1);
            var primeiroMes = mesAtual.AddMonths(-11);

            var meses = new List<DateTime>();
            for (var mes = primeiroMes; mes <= mesAtual; mes = mes.AddMonths(1))
                meses.Add(mes);

            var contagemPorMes = datasValidas
                .Where(d => d >= primeiroMes)
                .GroupBy(d => new DateTime(d.Year, d.Month, 1))
                .ToDictionary(g => g.Key, g => g.Count());

            var valores = meses
                .Select(m => (double)(contagemPorMes.TryGetValue(m, out var qtd) ? qtd : 0))
                .ToArray();

            var rotulos = meses
                .Select(m => m.ToString("MMM/yy", new CultureInfo("pt-BR")))
                .ToList();

            chartUsuarios.Series = new ISeries[]
            {
                new ColumnSeries<double>
                {
                    Name = "Usuários",
                    Values = valores,
                    Fill = new SolidColorPaint(SKColor.Parse("#3B82F6")),
                    Stroke = null,
                    MaxBarWidth = 32,
                    Rx = 4,
                    Ry = 4
                }
            };

            chartUsuarios.XAxes = new[]
            {
                new Axis
                {
                    Labels = rotulos,
                    LabelsRotation = 45,
                    TextSize = 11,
                    LabelsPaint = new SolidColorPaint(SKColor.Parse("#94A3B8")),
                    SeparatorsPaint = null
                }
            };

            chartUsuarios.YAxes = new[]
            {
                new Axis
                {
                    TextSize = 12,
                    MinLimit = 0,
                    LabelsPaint = new SolidColorPaint(SKColor.Parse("#94A3B8")),
                    SeparatorsPaint = new SolidColorPaint(SKColor.Parse("#27324A")) { StrokeThickness = 1 }
                }
            };
        }

        // ── pizza... ───────────────────────────

        private void MontarGraficoDestinos(List<ViagemModel>? viagens)
        {
            
            var destinosValidos = (viagens ?? new List<ViagemModel>())
                .Select(v => v.destino_principal)
                .Where(d => !string.IsNullOrWhiteSpace(d))
                .Select(d => d!.Trim())
                .ToList();

            if (destinosValidos.Count == 0)
            {
                chartDestinos.Series = Array.Empty<ISeries>();
                return;
            }

            const int maxFatias = 6;

            var contagem = destinosValidos
                .GroupBy(d => d, StringComparer.OrdinalIgnoreCase)
                .Select(g => new { Destino = g.Key, Quantidade = g.Count() })
                .OrderByDescending(g => g.Quantidade)
                .ToList();

            var principais = contagem.Take(maxFatias).ToList();
            var restante = contagem.Skip(maxFatias).Sum(g => g.Quantidade);
            if (restante > 0)
                principais.Add(new { Destino = "Outros", Quantidade = restante });

            chartDestinos.Series = principais
                .Select((d, i) => (ISeries)new PieSeries<double>
                {
                    Name = d.Destino,
                    Values = new[] { (double)d.Quantidade },
                    Fill = new SolidColorPaint(SKColor.Parse(Paleta[i % Paleta.Length])),
                    DataLabelsPaint = new SolidColorPaint(SKColors.White),
                    DataLabelsSize = 12,
                    DataLabelsFormatter = point => $"{point.Coordinate.PrimaryValue}"
                })
                .ToArray();
        }
    }
}
