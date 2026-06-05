using Microsoft.Win32;
using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;
using System.Text.Json;
using System.Windows;
using System.Windows.Navigation;
using WindowLobby.crud;
using WindowLobby.CRUD;
using WindowLobby.CRUD.models;

namespace WindowLobby
{
    public partial class Dashboard : Window
    {
        public static Dashboard? Instancia { get; private set; }

        public Dashboard()
        {
            InitializeComponent();

            Instancia = this;
            QuestPDF.Settings.License = LicenseType.Community;

            Loaded += async (_, _) => await ComporInformacoes();
        }

        public async Task ComporInformacoes()
        {
            try
            {
                var perfil = await Usuario.GetMe();
                if (perfil is not null)
                {
                    txtUsuario.Text = perfil["nome"]?.GetValue<string>() ?? Sessao.Nome;
                    Sessao.Nome = txtUsuario.Text;

                    var fotoUrl = perfil["foto_perfil"]?.GetValue<string>() ?? "";
                    if (!string.IsNullOrEmpty(fotoUrl))
                    {
                        try
                        {
                            imgPerfil.Source = new System.Windows.Media.Imaging.BitmapImage(new Uri(fotoUrl));
                        }
                        catch { /* imagem inacessível */ }
                    }
                }

                var jsonVia = await Viagem.GetViagens();
                if (jsonVia is not null)
                {
                    var viagens = JsonSerializer.Deserialize<List<ViagemModel>>(
                        jsonVia,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    );
                    txtViagens.Text = viagens?.Count.ToString() ?? "0";
                }

                var jsonUsu = await Usuario.GetUsuarios();
                if (jsonUsu is not null)
                {
                    var usuarios = JsonSerializer.Deserialize<List<UsuarioModel>>(
                        jsonUsu,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    );
                    txtUsuarios.Text = usuarios?.Count.ToString() ?? "0";
                }

                
                var jsonChat = await Chat_ia.BuscarMensagens();
                if (jsonChat is not null)
                {
                    var chats = JsonSerializer.Deserialize<List<ChatModel>>(
                        jsonChat,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    );
                    double totalChats = 0;
                    foreach (var c in chats)
                    {
                        totalChats+=c.resposta.Length;
                    }
                   
                    txtChatIA.Text = totalChats.ToString();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[Dashboard.ComporInformacoes] Erro: {ex}");
            }
        }

        // ── Navegação lateral ────────────────────────────────────────────────────

        private void BtnUsuarios_Click(object sender, RoutedEventArgs e)
            => MainFrame.Navigate(new Pages.UsuarioPage());

        private void BtnViagens_Click(object sender, RoutedEventArgs e)
            => MainFrame.Navigate(new Pages.ViagensPage());

        private void BtnConfiguracoes_Click(object sender, RoutedEventArgs e)
            => MainFrame.Navigate(new Pages.ConfigPage());

        // ── Exportar PDF ─────────────────────────────────────────────────────────

        private void BtnExpPdf_Click(object sender, RoutedEventArgs e)
        {
            var salvar = new SaveFileDialog
            {
                Filter = "PDF (*.pdf)|*.pdf",
                FileName = "Relatorio_Diartrip.pdf"
            };

            if (salvar.ShowDialog() != true) return;

            Document.Create(container =>
            {
                container.Page(page =>
                {
                    page.Margin(50);

                    page.Header()
                        .Text("DiarTrip — Relatório")
                        .FontSize(20)
                        .Bold();

                    page.Content()
                        .PaddingVertical(20)
                        .Column(col =>
                        {
                            col.Item().Text($"Usuário: {Sessao.Nome}");
                            col.Item().Text($"Total de usuários: {txtUsuarios.Text}");
                            col.Item().Text($"Total de viagens: {txtViagens.Text}");
                            col.Item().Text($"Tamanho total das respostas da IA: {txtChatIA.Text}");
                            col.Item().Text($"Gerado em: {DateTime.Now:dd/MM/yyyy HH:mm}");
                        });

                    page.Footer()
                        .AlignCenter()
                        .Text(x =>
                        {
                            x.Span("Página ");
                            x.CurrentPageNumber();
                        });
                });
            }).GeneratePdf(salvar.FileName);

            MessageBox.Show("PDF criado com sucesso!", "Exportar PDF",
                MessageBoxButton.OK, MessageBoxImage.Information);
        }

        // ── Logout ───────────────────────────────────────────────────────────────

        private async void BtnLogout_Click(object sender, RoutedEventArgs e)
        {
            var confirmar = MessageBox.Show(
                "Deseja sair da sua conta?",
                "Confirmar logout",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (confirmar != MessageBoxResult.Yes) return;

            await Usuario.Logout();
            AbrirLogin();
        }

        private void AbrirLogin()
        {
            var loginWindow = new WindowLogin.Login();
            loginWindow.Show();
            Close();
        }

        private void MainFrame_Navigated(object sender, NavigationEventArgs e)
        {
            // limpa o histórico de navegação para o botão Voltar não aparecer
            while (MainFrame.CanGoBack)
                MainFrame.RemoveBackEntry();
        }
    }
}
