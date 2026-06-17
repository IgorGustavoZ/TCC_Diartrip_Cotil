using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using WindowLobby.crud;
using WindowLobby.CRUD.models;

namespace WindowLobby.Pages
{
    public partial class UsuarioPage : Page
    {
        public UsuarioPage()
        {
            InitializeComponent();
            Loaded += async (_, _) => await CarregarPerfil();
        }

        private async Task CarregarPerfil()
        {
            try
            {
                var perfil = await crud.Usuario.GetMe();
                if (perfil is null)
                {
                    MessageBox.Show(
                        "Não foi possível carregar o perfil.",
                        "Erro",
                        MessageBoxButton.OK,
                        MessageBoxImage.Warning);
                    return;
                }

                var jsonUsu = await Usuario.GetUsuarios();
                if (jsonUsu is not null)
                {
                    var usuarios = JsonSerializer.Deserialize<List<UsuarioModel>>(
                        jsonUsu,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    );   

                    gridUsuarios.ItemsSource = usuarios;

                }

            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Erro ao carregar perfil: {ex.Message}",
                    "Erro",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
            }
        }
    }
}
