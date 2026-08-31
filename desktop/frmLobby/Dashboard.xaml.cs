using Microsoft.Win32;
using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using WindowLobby.crud;
using WindowLobby.CRUD;
using WindowLobby.CRUD.models;

namespace WindowLobby
{
    public partial class Dashboard : Window
    {
        public static Dashboard? Instancia { get; private set; }

        
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
                            imgPerfilBrush.ImageSource = new System.Windows.Media.Imaging.BitmapImage(new Uri(fotoUrl));
                        }
                        catch { }
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
                            totalChats += c.resposta?.Length ?? 0;
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
            => MainFrame.Navigate(new Pages.DashboardPage());

        private void BtnUsuarios_Click(object sender, RoutedEventArgs e)
            => MainFrame.Navigate(new Pages.UsuarioPage());

        private void BtnViagens_Click(object sender, RoutedEventArgs e)
            => MainFrame.Navigate(new Pages.ViagensPage());

        private void BtnChatIA_Click(object sender, RoutedEventArgs e)
            => MainFrame.Navigate(new Pages.ChatIaPage());

        private void BtnPost_Click(object sender, RoutedEventArgs e)
            => MainFrame.Navigate(new Pages.PostPage());

        private void BtnConfiguracoes_Click(object sender, RoutedEventArgs e)
            => MainFrame.Navigate(new Pages.ConfigPage());

        // ── Exportar PDF ─────────────────────────────────────────────────────────
        

        private void BtnExpPdf_Click(object sender, RoutedEventArgs e)
        {
            var (titulo, nomeArquivo, montarConteudo) = ObterExportacaoParaTela(MainFrame.Content);

            var salvar = new SaveFileDialog
            {
                Filter = "PDF (*.pdf)|*.pdf",
                FileName = nomeArquivo
            };

            if (salvar.ShowDialog() != true) return;

            Document.Create(doc =>
            {
                doc.Page(page =>
                {
                    page.Margin(40);

                    page.Header()
                        .Text($"DiarTrip — {titulo}")
                        .FontSize(20)
                        .Bold();

                    page.Content()
                        .PaddingVertical(16)
                        .Element(montarConteudo);

                    page.Footer()
                        .AlignCenter()
                        .Text(x =>
                        {
                            x.Span("Página ");
                            x.CurrentPageNumber();
                            x.Span(" — gerado em ");
                            x.Span(DateTime.Now.ToString("dd/MM/yyyy HH:mm"));
                        });
                });
            }).GeneratePdf(salvar.FileName);

            MessageBox.Show("PDF criado com sucesso!", "Exportar PDF",
                MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private (string titulo, string nomeArquivo, Action<IContainer> montarConteudo) ObterExportacaoParaTela(object? conteudo)
        {
            switch (conteudo)
            {
                case Pages.UsuarioPage usuarioPage:
                    return ("Usuários",
                            "Relatorio_Usuarios.pdf",
                            c => ComporTabela(c,
                                new[] { "Id", "Nome", "Email", "Data de criação" },
                                ObterItensExibidos(usuarioPage.listUsuarios)
                                    .OfType<UsuarioModel>()
                                    .Select(u => new[]
                                    {
                                        u.id_usuario.ToString(),
                                        u.nome ?? "",
                                        u.email ?? "",
                                        u.data_criacao ?? ""
                                    })
                                    .ToList()));

                case Pages.ViagensPage viagensPage:
                    return ("Viagens",
                            "Relatorio_Viagens.pdf",
                            c => ComporTabela(c,
                                new[] { "Id", "Nome", "Destino Principal", "Início", "Fim", "Criado por" },
                                ObterItensExibidos(viagensPage.listViagens)
                                    .OfType<ViagemModel>()
                                    .Select(v => new[]
                                    {
                                        v.id_grupo.ToString(),
                                        v.nome_grupo ?? "",
                                        v.destino_principal ?? "",
                                        v.data_inicio ?? "",
                                        v.data_fim ?? "",
                                        v.criador ?? ""
                                    })
                                    .ToList()));

                case Pages.ChatIaPage chatPage:
                    return ("Chat IA",
                            "Relatorio_ChatIA.pdf",
                            c => ComporTabela(c,
                                new[] { "Id", "Grupo", "Usuário", "Data da interação" },
                                ObterItensExibidos(chatPage.listChats)
                                    .OfType<ChatModel>()
                                    .Select(m => new[]
                                    {
                                        m.id_chat.ToString(),
                                        m.id_grupo.ToString(),
                                        m.id_usuario.ToString(),
                                        m.data_interacao ?? ""
                                    })
                                    .ToList()));

                case Pages.PostPage postPage:
                    return ("Posts",
                            "Relatorio_Posts.pdf",
                            c => ComporTabela(c,
                                new[] { "Id", "Id Usuário", "Conteúdo", "Curtidas", "Data de criação" },
                                ObterItensExibidos(postPage.listPosts)
                                    .OfType<PostModel>()
                                    .Select(p => new[]
                                    {
                                        p.id_post.ToString(),
                                        p.id_usuario.ToString(),
                                        p.conteudo ?? "",
                                        p.curtidas.ToString(),
                                        p.data_criacao ?? ""
                                    })
                                    .ToList()));

                case Pages.ViagensDetalhePage viagemDetalhe:
                    return ($"Viagem — {viagemDetalhe.txtTitulo.Text}",
                            $"Relatorio_Viagem_{viagemDetalhe.txtId.Text}.pdf",
                            c => ComporViagemDetalhe(c, viagemDetalhe));

                case Pages.UsuarioDetalhePage usuarioDetalhe:
                    return ($"Usuário — {usuarioDetalhe.txtTitulo.Text}",
                            $"Relatorio_Usuario_{usuarioDetalhe.runIdUsuario.Text}.pdf",
                            c => ComporUsuarioDetalhe(c, usuarioDetalhe));

                case Pages.ChatIaDetalhePage chatDetalhe:
                    return (chatDetalhe.txtTitulo.Text,
                            "Relatorio_ConversaChatIA.pdf",
                            c => ComporChatDetalhe(c, chatDetalhe));

                case Pages.PostDetalhePage postDetalhe:
                    return (postDetalhe.txtTitulo.Text,
                            $"Relatorio_Post_{postDetalhe.runIdPost.Text}.pdf",
                            c => ComporPostDetalhe(c, postDetalhe));

                
                default:
                    return ("Resumo geral", "Relatorio_Diartrip.pdf", ComporResumoGeral);
            }
        }

        private void ComporResumoGeral(IContainer container)
        {
            container.Column(col =>
            {
                col.Item().Text($"Usuário: {Sessao.Nome}");
                col.Item().Text($"Total de usuários: {_totalUsuarios}");
                col.Item().Text($"Total de viagens: {_totalViagens}");
                col.Item().Text($"Tamanho total das respostas da IA: {_totalChatIA}");
                col.Item().Text($"Gerado em: {DateTime.Now:dd/MM/yyyy HH:mm}");
            });
        }

        
        private void ComporViagemDetalhe(IContainer container, Pages.ViagensDetalhePage pagina)
        {
            container.Column(col =>
            {
                col.Item().Text(pagina.txtDestino.Text).FontSize(14).Bold();
                col.Item().PaddingTop(10).Text($"Id: {pagina.txtId.Text}");
                col.Item().Text($"Início: {pagina.txtInicio.Text}");
                col.Item().Text($"Fim: {pagina.txtFim.Text}");
                col.Item().Text($"Criador: {pagina.txtCriador.Text}");
            });
        }

       
        private void ComporUsuarioDetalhe(IContainer container, Pages.UsuarioDetalhePage pagina)
        {
            container.Column(col =>
            {
                col.Item().Text(
                    $"Id: {pagina.runIdUsuario.Text}   •   Email: {pagina.runEmail.Text}   •   Criado em: {pagina.runData.Text}");

                col.Item().PaddingTop(16).Text("Viagens").FontSize(14).Bold();
                col.Item().PaddingBottom(4).Element(c => ComporTabela(c,
                    new[] { "Id", "Nome", "Destino", "Início", "Fim", "Criador" },
                    ObterItensExibidos(pagina.listViagens)
                        .OfType<ViagemModel>()
                        .Select(v => new[]
                        {
                            v.id_grupo.ToString(),
                            v.nome_grupo ?? "",
                            v.destino_principal ?? "",
                            v.data_inicio ?? "",
                            v.data_fim ?? "",
                            v.criador ?? ""
                        })
                        .ToList()));

                col.Item().PaddingTop(12).Text("Posts").FontSize(14).Bold();
                col.Item().PaddingBottom(4).Element(c => ComporTabela(c,
                    new[] { "Id", "Conteúdo", "Curtidas", "Data de criação" },
                    ObterItensExibidos(pagina.listPosts)
                        .OfType<PostModel>()
                        .Select(p => new[]
                        {
                            p.id_post.ToString(),
                            p.conteudo ?? "",
                            p.curtidas.ToString(),
                            p.data_criacao ?? ""
                        })
                        .ToList()));

                col.Item().PaddingTop(12).Text("Comentários").FontSize(14).Bold();
                col.Item().PaddingBottom(4).Element(c => ComporTabela(c,
                    new[] { "Id", "Post", "Conteúdo", "Data de criação" },
                    ObterItensExibidos(pagina.listComentarios)
                        .OfType<ComentarioModel>()
                        .Select(cm => new[]
                        {
                            cm.id.ToString(),
                            cm.id_post.ToString(),
                            cm.conteudo ?? "",
                            cm.data_criacao ?? ""
                        })
                        .ToList()));

                col.Item().PaddingTop(12).Text("Chat IA").FontSize(14).Bold();
                col.Item().Element(c => ComporTabela(c,
                    new[] { "Id", "Grupo", "Pergunta", "Data" },
                    ObterItensExibidos(pagina.listChat)
                        .OfType<ChatModel>()
                        .Select(m => new[]
                        {
                            m.id_chat.ToString(),
                            m.id_grupo.ToString(),
                            m.pergunta ?? "",
                            m.data_interacao ?? ""
                        })
                        .ToList()));
            });
        }

        
        private void ComporChatDetalhe(IContainer container, Pages.ChatIaDetalhePage pagina)
        {
            var mensagens = ObterItensExibidos(pagina.icMensagens).OfType<ChatModel>().ToList();

            if (mensagens.Count == 0)
            {
                container.Text("Nenhuma mensagem para exibir.");
                return;
            }

            container.Column(col =>
            {
                foreach (var m in mensagens)
                {
                    col.Item().PaddingBottom(14).Column(msg =>
                    {
                        msg.Item().Text(
                            $"Id {m.id_chat}  •  Usuário {m.id_usuario}  •  {m.data_interacao}")
                            .FontSize(9)
                            .FontColor(Colors.Grey.Darken1);

                        msg.Item().PaddingTop(6).Text("PERGUNTA")
                            .FontSize(9).Bold().FontColor(Colors.Grey.Darken2);
                        msg.Item().Text(m.pergunta ?? "").FontSize(11);

                        msg.Item().PaddingTop(8).Text("RESPOSTA")
                            .FontSize(9).Bold().FontColor(Colors.Grey.Darken2);
                        msg.Item().Text(m.resposta ?? "").FontSize(11);

                        msg.Item().PaddingTop(10)
                            .LineHorizontal(0.5f)
                            .LineColor(Colors.Grey.Lighten2);
                    });
                }
            });
        }

        
        private void ComporPostDetalhe(IContainer container, Pages.PostDetalhePage pagina)
        {
            var imagemBytes = ObterBytesDaImagem(pagina.imgPost, pagina.borderImagem);

            container.Column(col =>
            {
                if (imagemBytes is not null)
                {
                    col.Item().PaddingBottom(14).MaxHeight(300).Image(imagemBytes).FitArea();
                }

                col.Item().Text(pagina.txtConteudo.Text).FontSize(12);

                col.Item().PaddingTop(10).Text(
                    $"Id {pagina.runIdPost.Text}  •  Usuário {pagina.runIdUsuario.Text} ({pagina.runNomeUsuario.Text})  •  {pagina.runData.Text}")
                    .FontSize(9)
                    .FontColor(Colors.Grey.Darken1);

                col.Item().Text(pagina.txtCurtidas.Text)
                    .FontSize(9)
                    .FontColor(Colors.Grey.Darken1);

                col.Item().PaddingTop(20).Text("Comentários").FontSize(14).Bold();

                var comentarios = ObterItensExibidos(pagina.icComentarios).OfType<ComentarioModel>().ToList();

                if (comentarios.Count == 0)
                {
                    col.Item().PaddingTop(6).Text("Nenhum comentário.")
                        .FontSize(10)
                        .FontColor(Colors.Grey.Darken1);
                }
                else
                {
                    foreach (var c in comentarios)
                    {
                        col.Item().PaddingTop(10).Column(com =>
                        {
                            com.Item().Text($"Usuário {c.id_usuario}").FontSize(10).Bold();
                            com.Item().Text(c.conteudo ?? "").FontSize(10);
                            com.Item().PaddingTop(2).Text(c.data_criacao ?? "")
                                .FontSize(8)
                                .FontColor(Colors.Grey.Darken1);
                        });
                    }
                }
            });
        }

        
        private static byte[]? ObterBytesDaImagem(System.Windows.Controls.Image imagem, Border borderImagem)
        {
            if (borderImagem.Visibility != Visibility.Visible) return null;
            if (imagem.Source is not BitmapSource bitmapSource) return null;

            try
            {
                var encoder = new PngBitmapEncoder();
                encoder.Frames.Add(BitmapFrame.Create(bitmapSource));

                using var stream = new MemoryStream();
                encoder.Save(stream);
                return stream.ToArray();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[Dashboard.ObterBytesDaImagem] Falha ao converter imagem: {ex.Message}");
                return null;
            }
        }

        private static void ComporTabela(IContainer container, string[] cabecalhos, List<string[]> linhas)
        {
            if (linhas.Count == 0)
            {
                container.Text("Nenhum item para exibir com os filtros/ordenação atuais.");
                return;
            }

            container.Table(table =>
            {
                table.ColumnsDefinition(columns =>
                {
                    foreach (var _ in cabecalhos)
                        columns.RelativeColumn();
                });

                table.Header(header =>
                {
                    foreach (var cabecalho in cabecalhos)
                    {
                        header.Cell()
                            .Background(Colors.Grey.Lighten2)
                            .Padding(4)
                            .Text(cabecalho)
                            .Bold();
                    }
                });

                foreach (var linha in linhas)
                {
                    foreach (var valor in linha)
                    {
                        table.Cell()
                            .BorderBottom(1)
                            .BorderColor(Colors.Grey.Lighten2)
                            .Padding(4)
                            .Text(valor);
                    }
                }
            });
        }

        
        private static IEnumerable<object> ObterItensExibidos(ItemsControl itemsControl)
        {
            var view = CollectionViewSource.GetDefaultView(itemsControl.ItemsSource);
            if (view is null) return Enumerable.Empty<object>();
            return view.Cast<object>();
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
            
            if (e.Content is Pages.ChatIaDetalhePage) return;

           
            while (MainFrame.CanGoBack)
                MainFrame.RemoveBackEntry();
        }
    }
}
