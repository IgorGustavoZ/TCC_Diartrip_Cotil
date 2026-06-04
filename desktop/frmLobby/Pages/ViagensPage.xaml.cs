using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
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
                    gridViagens.ItemsSource = viagens;
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
    }
}
