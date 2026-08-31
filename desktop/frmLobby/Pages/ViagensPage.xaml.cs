using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Input;
using System.Windows.Media;
using WindowLobby.crud;
using WindowLobby.CRUD.models;

namespace WindowLobby.Pages
{
    public partial class ViagensPage : Page
    {

        private GridViewColumnHeader _lastHeaderClicked;
        private ListSortDirection _lastDirection = ListSortDirection.Ascending;

        
        private bool _carregado;

        public ViagensPage()
        {
            InitializeComponent();
            Loaded += async (_, _) =>
            {
                if (_carregado) return;
                _carregado = true;
                await CarregarViagens();
            };
        }

        private async Task CarregarViagens()
        {
            try
            {
                var json = await CRUD.Viagem.GetViagens();

                System.Diagnostics.Debug.WriteLine($"[Viagens] RAW JSON: {json}");


                if (json is null)
                {
                    MessageBox.Show(
                        "Não foi possível carregar as viagens. Verifique sua conexão.",
                        "Erro",
                        MessageBoxButton.OK,
                        MessageBoxImage.Warning);
                    return;
                }

                var viagens = JsonSerializer.Deserialize<List<ViagemModel>>(
                    json,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                );

                listViagens.ItemsSource = viagens;
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Erro ao carregar viagens: {ex.Message}",
                    "Erro",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
            }
        }

        // ---------- Detalhe da viagem ----------

        private void ListViagens_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            
            var dep = e.OriginalSource as DependencyObject;
            while (dep is not null && dep is not ListViewItem)
            {
                dep = VisualTreeHelper.GetParent(dep);
            }

            if (dep is not ListViewItem item || item.DataContext is not ViagemModel viagem)
                return;

           
            NavigationService?.Navigate(new ViagensDetalhePage(viagem, this));
        }

        // ---------- Vem cima de, cai baixo para ----------

        private void ListViewHeader_Click(object sender, RoutedEventArgs e)
        {
            if (e.OriginalSource is not GridViewColumnHeader header) return;
            if (header.Role == GridViewColumnHeaderRole.Padding) return;
            if (header.Column?.DisplayMemberBinding is not System.Windows.Data.Binding binding) return;

            string propertyName = binding.Path.Path;

            ListSortDirection direction = header != _lastHeaderClicked
                ? ListSortDirection.Descending
                : (_lastDirection == ListSortDirection.Descending
                    ? ListSortDirection.Ascending
                    : ListSortDirection.Descending);

            var view = CollectionViewSource.GetDefaultView(listViagens.ItemsSource);
            if (view is null) return;

            view.SortDescriptions.Clear();
            view.SortDescriptions.Add(new SortDescription(propertyName, direction));
            view.Refresh();

            _lastHeaderClicked = header;
            _lastDirection = direction;
        }

        // ---------- rartlif ----------

        private void BtnFiltrar_Click(object sender, RoutedEventArgs e)
        {
            var view = CollectionViewSource.GetDefaultView(listViagens.ItemsSource);
            if (view is null) return;

            view.Filter = obj =>
            {
                if (obj is not ViagemModel viagem) return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroId.Text) &&
                    !viagem.id_grupo.ToString()
                        .Contains(txtFiltroId.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroNome.Text) &&
                    !(viagem.nome_grupo ?? "")
                        .Contains(txtFiltroNome.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroDestino.Text) &&
                    !(viagem.destino_principal ?? "")
                        .Contains(txtFiltroDestino.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroCriadoPor.Text) &&
                    !(viagem.criador ?? "")
                        .Contains(txtFiltroCriadoPor.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                // aaaAAAAAAAAAAAAIIiiiiiiiii
                if (!TryParseData(viagem.data_inicio, out var inicioEm)) return false;
                if (!TryParseData(viagem.data_fim, out var fimEm)) return false;

                if (dpFiltroDataInicio.SelectedDate.HasValue &&
                    inicioEm.Date != dpFiltroDataInicio.SelectedDate.Value.Date)
                    return false;

                if (dpFiltroDataFim.SelectedDate.HasValue &&
                    fimEm.Date != dpFiltroDataFim.SelectedDate.Value.Date)
                    return false;

                return true;
            };

            view.Refresh();
        }


       
        private static readonly string[] FormatosData =
        {
            "yyyy-MM-dd",
            "yyyy-MM-ddTHH:mm:ss",
            "yyyy-MM-dd HH:mm:ss",
            "yyyy/MM/dd",
            "yyyy/MM/dd HH:mm:ss",
            "dd/MM/yyyy",
            "dd/MM/yyyy HH:mm:ss"
        };

        
        public static bool TryParseData(string? valor, out DateTime data)
        {
            data = default;
            if (string.IsNullOrWhiteSpace(valor)) return false;

            valor = valor.Trim();

            if (DateTime.TryParseExact(
                    valor, FormatosData, CultureInfo.InvariantCulture, DateTimeStyles.None, out data))
                return true;

            
            return DateTime.TryParse(valor, new CultureInfo("pt-BR"), DateTimeStyles.None, out data);
        }

        private void BtnLimparFiltros_Click(object sender, RoutedEventArgs e)
        {
            txtFiltroId.Clear();
            txtFiltroNome.Clear();
            txtFiltroDestino.Clear();
            txtFiltroCriadoPor.Clear();
            dpFiltroDataInicio.SelectedDate = null;
            dpFiltroDataFim.SelectedDate = null;

            var view = CollectionViewSource.GetDefaultView(listViagens.ItemsSource);
            if (view is null) return;

            view.Filter = null;
            view.Refresh();
        }
    }
}
