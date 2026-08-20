using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using WindowLobby.crud;
using WindowLobby.CRUD.models;

namespace WindowLobby.Pages
{
    public partial class ViagensPage : Page
    {
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
                    gridViagens.ItemsSource = viagens;
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
