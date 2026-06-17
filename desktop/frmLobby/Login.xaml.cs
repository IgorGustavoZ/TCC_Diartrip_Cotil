using System.Windows;
using WindowLobby.crud;
using WindowLobby.CRUD;

namespace WindowLogin
{
    public partial class Login : Window
    {
        public Login()
        {
            InitializeComponent();
        }

        private async void btnEntrar_Click(object sender, RoutedEventArgs e)
        {
            var email = txtEmail.Text.Trim();
            var senha = txtSenha.Password;

            if (string.IsNullOrWhiteSpace(email) || string.IsNullOrWhiteSpace(senha))
            {
                MessageBox.Show(
                    "Preencha o e-mail e a senha.",
                    "Campos obrigatórios",
                    MessageBoxButton.OK,
                    MessageBoxImage.Warning);
                return;
            }

            SetLoading(true);
            try
            {
                var (sucesso, usuarioId, erro) = await Usuario.Login(email, senha);
                if (!sucesso)
                {
                    MessageBox.Show(erro, "Falha no login", MessageBoxButton.OK, MessageBoxImage.Error);
                    return;
                }

                var perfil = await Usuario.GetMe();
                Sessao.UsuarioId = usuarioId;
                Sessao.Nome      = perfil?["nome"]?.GetValue<string>() ?? email;

                var dashboard = new WindowLobby.Dashboard();
                dashboard.Show();

                // Fechar antes do finally para evitar acesso ao btnEntrar após Close()
                Close();
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Erro inesperado: {ex.Message}",
                    "Erro",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
                SetLoading(false); // Restaura apenas se não fechou
            }
        }

        private void SetLoading(bool loading)
        {
            // Verifica se a janela ainda está aberta antes de acessar UI
            if (!IsLoaded) return;
            btnEntrar.IsEnabled = !loading;
            btnEntrar.Content   = loading ? "Entrando..." : "Entrar";
        }
    }
}
