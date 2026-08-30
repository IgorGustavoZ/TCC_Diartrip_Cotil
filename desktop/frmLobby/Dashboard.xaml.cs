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

        // Os cards de estatística saíram da janela (agora ela fica "em branco" para
        // as páginas navegadas no Frame). Os totais continuam sendo calculados aqui
        // porque o botão "Exportar PDF" ainda precisa deles.
        private int _totalViagens;
        private int _totalUsuarios;
        private double _totalChatIA;

        public Dashboard()
        {
            InitializeComponent();

            Instancia = this;
            QuestPDF.Settings.License = LicenseType.Community;

            Loaded += async (_, _) =>
            {
                await ComporInformacoes();

                // TODO: crie WindowLobby.Pages.DashboardPage (ainda não existe) —
                // pode reaproveitar o antigo layout de cards de estatística lá dentro.
                MainFrame.Navigate(new Pages.DashboardPage());
            };
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
                    _totalViagens = viagens?.Count ?? 0;
                }

                var jsonUsu = await Usuario.GetUsuarios();
                if (jsonUsu is not null)
                {
                    var usuarios = JsonSerializer.Deserialize<List<UsuarioModel>>(
                        jsonUsu,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    );
                    _totalUsuarios = usuarios?.Count ?? 0;
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
                            totalChats += c.resposta.Length;
                    }

                    _totalChatIA = totalChats;
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[Dashboard.ComporInformacoes] Erro: {ex}");
            }
        }

        // ── Navegação lateral ────────────────────────────────────────────────────

        private void BtnDashboard_Click(object sender, RoutedEventArgs e)
            => MainFrame.Navigate(new Pages.DashboardPage()); // TODO: crie esta Page

        private void BtnUsuarios_Click(object sender, RoutedEventArgs e)
            => MainFrame.Navigate(new Pages.UsuarioPage());

        private void BtnViagens_Click(object sender, RoutedEventArgs e)
            => MainFrame.Navigate(new Pages.ViagensPage());

        private void BtnChatIA_Click(object sender, RoutedEventArgs e)
            => MainFrame.Navigate(new Pages.ChatIaPage());

        private void BtnPost_Clicl(object sender, RoutedEventArgs e)
            => MainFrame.Navigate(new Pages.PostPage());

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
                            col.Item().Text($"Total de usuários: {_totalUsuarios}");
                            col.Item().Text($"Total de viagens: {_totalViagens}");
                            col.Item().Text($"Tamanho total das respostas da IA: {_totalChatIA}");
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
            // Páginas de detalhe (abertas "por cima" de uma página de nível
            // superior, ex.: ChatIaDetalhePage) precisam do back stack intacto
            // para o próprio botão "Voltar" delas funcionar via GoBack().
            if (e.Content is Pages.ChatIaDetalhePage) return;

            // Nas páginas de nível superior (menu lateral), limpa o histórico
            // para o botão Voltar não aparecer/acumular entradas antigas.
            while (MainFrame.CanGoBack)
                MainFrame.RemoveBackEntry();
        }

        
    }
}
