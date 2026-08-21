using System.ComponentModel;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using WindowLobby.crud;
using WindowLobby.CRUD.models;

namespace WindowLobby.Pages
{
    public partial class ViagensPage : Page
    {

        private GridViewColumnHeader _lastHeaderClicked;
        private ListSortDirection _lastDirection = ListSortDirection.Ascending;
        public ViagensPage()
        {
            InitializeComponent();
            Loaded += async (_, _) => await CarregarViagens();
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

                if (viagens is not null)
                {
                    foreach (ViagemModel v in viagens)
                    {
                        var resp = await Usuario.GetUsuariosById(v.criado_por);
                        if (resp is not null)
                        {
                            {
                                UsuarioModel usuario = JsonSerializer.Deserialize<UsuarioModel>(
                                    resp,
                                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                                );

                                v.criador = usuario.nome;
                            }

                        }

                    }
                    listViagens.ItemsSource = viagens;
                }
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

        // ---------- SORTING ----------

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

        private void BtnFiltrar_Click(object sender, RoutedEventArgs e)
        {
            // TODO: implement filtering logic (id, nome, destino, data início/fim, criado por)
        }

        private void BtnLimparFiltros_Click(object sender, RoutedEventArgs e)
        {
            txtFiltroId.Clear();
            txtFiltroNome.Clear();
            txtFiltroDestino.Clear();
            txtFiltroCriadoPor.Clear();
            dpFiltroDataInicio.SelectedDate = null;
            dpFiltroDataFim.SelectedDate = null;
        }
    }
}
