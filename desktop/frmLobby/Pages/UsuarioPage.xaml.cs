using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
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

                var usuario = new UsuarioModel
                {
                    id_usuario  = perfil["id_usuario"]?.GetValue<int>() ?? 0,
                    nome        = perfil["nome"]?.GetValue<string>() ?? "",
                    email       = perfil["email"]?.GetValue<string>() ?? "",
                    data_criacao = perfil["data_criacao"]?.GetValue<string>() ?? "",
                    foto_perfil  = perfil["foto_perfil"]?.GetValue<string>() ?? "",
                };

                gridUsuarios.ItemsSource = new List<UsuarioModel> { usuario };
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
