using System.Linq;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.ComponentModel;
using System.Windows.Data;
using System.Windows.Input;
using System.Windows.Media;
using WindowLobby.crud;
using WindowLobby.CRUD.models;

namespace WindowLobby.Pages
{
    public partial class UsuarioDetalhePage : Page
    {
        private readonly UsuarioModel _usuario;
        private readonly Page _paginaAnterior;

        private List<PostModel> _todosPosts = new();
        private List<ChatModel> _todasMensagensChat = new();

        private GridViewColumnHeader _lastHeaderClickedPosts;
        private ListSortDirection _lastDirectionPosts = ListSortDirection.Ascending;

        private GridViewColumnHeader _lastHeaderClickedComentarios;
        private ListSortDirection _lastDirectionComentarios = ListSortDirection.Ascending;

        private GridViewColumnHeader _lastHeaderClickedViagens;
        private ListSortDirection _lastDirectionViagens = ListSortDirection.Ascending;

        private GridViewColumnHeader _lastHeaderClickedChat;
        private ListSortDirection _lastDirectionChat = ListSortDirection.Ascending;

        
        private bool _carregado;

        public UsuarioDetalhePage(UsuarioModel usuario, Page paginaAnterior)
        {
            InitializeComponent();

            _usuario = usuario;
            _paginaAnterior = paginaAnterior;

            txtTitulo.Text = usuario.nome;
            txtSubtitulo.Text = usuario.email;

            runIdUsuario.Text = usuario.id_usuario.ToString();
            runEmail.Text = usuario.email;
            runData.Text = usuario.data_criacao;

            Loaded += async (_, _) =>
            {
                if (_carregado) return;
                _carregado = true;
                await CarregarDados();
            };
        }

        private async Task CarregarDados()
        {
            try
            {
                var jsonPosts = await Post.GetPosts(limite: 100, offset: 0);

                if (jsonPosts is not null)
                {
                    _todosPosts = JsonSerializer.Deserialize<List<PostModel>>(
                        jsonPosts,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    ) ?? new List<PostModel>();
                }

                var postsDoUsuario = _todosPosts
                    .Where(p => p.id_usuario == _usuario.id_usuario)
                    .ToList();

                listPosts.ItemsSource = postsDoUsuario;
                txtPostsTitulo.Text = $"Posts ({postsDoUsuario.Count})";
                txtSemPosts.Visibility = postsDoUsuario.Count == 0
                    ? Visibility.Visible
                    : Visibility.Collapsed;

                var comentariosDoUsuario = _todosPosts
                    .Where(p => p.comentarios is not null)
                    .SelectMany(p => p.comentarios!)
                    .Where(c => c.id_usuario == _usuario.id_usuario)
                    .ToList();

                listComentarios.ItemsSource = comentariosDoUsuario;
                txtComentariosTitulo.Text = $"Comentários ({comentariosDoUsuario.Count})";
                txtSemComentarios.Visibility = comentariosDoUsuario.Count == 0
                    ? Visibility.Visible
                    : Visibility.Collapsed;

                var jsonViagens = await CRUD.Viagem.GetViagens();
                List<ViagemModel> todasViagens = new();

                if (jsonViagens is not null)
                {
                    todasViagens = JsonSerializer.Deserialize<List<ViagemModel>>(
                        jsonViagens,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    ) ?? new List<ViagemModel>();
                }

               
                var viagensDoUsuario = todasViagens
                    .Where(v => v.criado_por == _usuario.id_usuario ||
                                string.Equals(v.criador, _usuario.nome, StringComparison.OrdinalIgnoreCase))
                    .ToList();

                listViagens.ItemsSource = viagensDoUsuario;
                txtViagensTitulo.Text = $"Viagens ({viagensDoUsuario.Count})";
                txtSemViagens.Visibility = viagensDoUsuario.Count == 0
                    ? Visibility.Visible
                    : Visibility.Collapsed;

                var jsonChat = await CRUD.Chat_ia.BuscarMensagens();

                if (jsonChat is not null)
                {
                    _todasMensagensChat = JsonSerializer.Deserialize<List<ChatModel>>(
                        jsonChat,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    ) ?? new List<ChatModel>();
                }

                var mensagensDoUsuario = _todasMensagensChat
                    .Where(m => m.id_usuario == _usuario.id_usuario)
                    .ToList();

                listChat.ItemsSource = mensagensDoUsuario;
                txtChatTitulo.Text = $"Chat IA ({mensagensDoUsuario.Count})";
                txtSemChat.Visibility = mensagensDoUsuario.Count == 0
                    ? Visibility.Visible
                    : Visibility.Collapsed;
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Erro ao carregar dados do usuário: {ex.Message}",
                    "Erro",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
            }
        }

        // ---------- De cima vem... para desce vai... ----------

        private void ListPostsHeader_Click(object sender, RoutedEventArgs e)
        {
            if (e.OriginalSource is not GridViewColumnHeader header) return;
            if (header.Role == GridViewColumnHeaderRole.Padding) return;
            if (header.Column?.DisplayMemberBinding is not System.Windows.Data.Binding binding) return;

            string propertyName = binding.Path.Path;

            ListSortDirection direction = header != _lastHeaderClickedPosts
                ? ListSortDirection.Descending
                : (_lastDirectionPosts == ListSortDirection.Descending
                    ? ListSortDirection.Ascending
                    : ListSortDirection.Descending);

            var view = CollectionViewSource.GetDefaultView(listPosts.ItemsSource);
            if (view is null) return;

            view.SortDescriptions.Clear();
            view.SortDescriptions.Add(new SortDescription(propertyName, direction));
            view.Refresh();

            _lastHeaderClickedPosts = header;
            _lastDirectionPosts = direction;
        }

        private void ListComentariosHeader_Click(object sender, RoutedEventArgs e)
        {
            if (e.OriginalSource is not GridViewColumnHeader header) return;
            if (header.Role == GridViewColumnHeaderRole.Padding) return;
            if (header.Column?.DisplayMemberBinding is not System.Windows.Data.Binding binding) return;

            string propertyName = binding.Path.Path;

            ListSortDirection direction = header != _lastHeaderClickedComentarios
                ? ListSortDirection.Descending
                : (_lastDirectionComentarios == ListSortDirection.Descending
                    ? ListSortDirection.Ascending
                    : ListSortDirection.Descending);

            var view = CollectionViewSource.GetDefaultView(listComentarios.ItemsSource);
            if (view is null) return;

            view.SortDescriptions.Clear();
            view.SortDescriptions.Add(new SortDescription(propertyName, direction));
            view.Refresh();

            _lastHeaderClickedComentarios = header;
            _lastDirectionComentarios = direction;
        }

        private void ListViagensHeader_Click(object sender, RoutedEventArgs e)
        {
            if (e.OriginalSource is not GridViewColumnHeader header) return;
            if (header.Role == GridViewColumnHeaderRole.Padding) return;
            if (header.Column?.DisplayMemberBinding is not System.Windows.Data.Binding binding) return;

            string propertyName = binding.Path.Path;

            ListSortDirection direction = header != _lastHeaderClickedViagens
                ? ListSortDirection.Descending
                : (_lastDirectionViagens == ListSortDirection.Descending
                    ? ListSortDirection.Ascending
                    : ListSortDirection.Descending);

            var view = CollectionViewSource.GetDefaultView(listViagens.ItemsSource);
            if (view is null) return;

            view.SortDescriptions.Clear();
            view.SortDescriptions.Add(new SortDescription(propertyName, direction));
            view.Refresh();

            _lastHeaderClickedViagens = header;
            _lastDirectionViagens = direction;
        }

        private void ListChatHeader_Click(object sender, RoutedEventArgs e)
        {
            if (e.OriginalSource is not GridViewColumnHeader header) return;
            if (header.Role == GridViewColumnHeaderRole.Padding) return;
            if (header.Column?.DisplayMemberBinding is not System.Windows.Data.Binding binding) return;

            string propertyName = binding.Path.Path;

            ListSortDirection direction = header != _lastHeaderClickedChat
                ? ListSortDirection.Descending
                : (_lastDirectionChat == ListSortDirection.Descending
                    ? ListSortDirection.Ascending
                    : ListSortDirection.Descending);

            var view = CollectionViewSource.GetDefaultView(listChat.ItemsSource);
            if (view is null) return;

            view.SortDescriptions.Clear();
            view.SortDescriptions.Add(new SortDescription(propertyName, direction));
            view.Refresh();

            _lastHeaderClickedChat = header;
            _lastDirectionChat = direction;
        }

        // ---------- Filtros Viagens ----------

        private void BtnFiltrarViagens_Click(object sender, RoutedEventArgs e)
        {
            var view = CollectionViewSource.GetDefaultView(listViagens.ItemsSource);
            if (view is null) return;

            view.Filter = obj =>
            {
                if (obj is not ViagemModel viagem) return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroViagensId.Text) &&
                    !viagem.id_grupo.ToString()
                        .Contains(txtFiltroViagensId.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroViagensNome.Text) &&
                    !(viagem.nome_grupo ?? "")
                        .Contains(txtFiltroViagensNome.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroViagensDestino.Text) &&
                    !(viagem.destino_principal ?? "")
                        .Contains(txtFiltroViagensDestino.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                //AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
                if (dpFiltroViagensInicio.SelectedDate.HasValue)
                {
                    if (!ViagensPage.TryParseData(viagem.data_inicio, out var inicioEm) ||
                        inicioEm.Date != dpFiltroViagensInicio.SelectedDate.Value.Date)
                        return false;
                }

                if (dpFiltroViagensFim.SelectedDate.HasValue)
                {
                    if (!ViagensPage.TryParseData(viagem.data_fim, out var fimEm) ||
                        fimEm.Date != dpFiltroViagensFim.SelectedDate.Value.Date)
                        return false;
                }

                return true;
            };

            view.Refresh();
        }

        private void BtnLimparFiltrosViagens_Click(object sender, RoutedEventArgs e)
        {
            txtFiltroViagensId.Clear();
            txtFiltroViagensNome.Clear();
            txtFiltroViagensDestino.Clear();
            dpFiltroViagensInicio.SelectedDate = null;
            dpFiltroViagensFim.SelectedDate = null;

            var view = CollectionViewSource.GetDefaultView(listViagens.ItemsSource);
            if (view is null) return;
            view.Filter = null;
            view.Refresh();
        }

        // ---------- Filtros Posts ----------

        private void BtnFiltrarPosts_Click(object sender, RoutedEventArgs e)
        {
            var view = CollectionViewSource.GetDefaultView(listPosts.ItemsSource);
            if (view is null) return;

            view.Filter = obj =>
            {
                if (obj is not PostModel post) return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroPostsId.Text) &&
                    !post.id_post.ToString()
                        .Contains(txtFiltroPostsId.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroPostsConteudo.Text) &&
                    !(post.conteudo ?? "")
                        .Contains(txtFiltroPostsConteudo.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (dpFiltroPostsData.SelectedDate.HasValue)
                {
                    if (!ViagensPage.TryParseData(post.data_criacao, out var criadoEm) ||
                        criadoEm.Date != dpFiltroPostsData.SelectedDate.Value.Date)
                        return false;
                }

                return true;
            };

            view.Refresh();
        }

        private void BtnLimparFiltrosPosts_Click(object sender, RoutedEventArgs e)
        {
            txtFiltroPostsId.Clear();
            txtFiltroPostsConteudo.Clear();
            dpFiltroPostsData.SelectedDate = null;

            var view = CollectionViewSource.GetDefaultView(listPosts.ItemsSource);
            if (view is null) return;
            view.Filter = null;
            view.Refresh();
        }

        // ---------- Filtros Comentários ----------

        private void BtnFiltrarComentarios_Click(object sender, RoutedEventArgs e)
        {
            var view = CollectionViewSource.GetDefaultView(listComentarios.ItemsSource);
            if (view is null) return;

            view.Filter = obj =>
            {
                if (obj is not ComentarioModel comentario) return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroComentariosPostId.Text) &&
                    !comentario.id_post.ToString()
                        .Contains(txtFiltroComentariosPostId.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroComentariosId.Text) &&
                    !comentario.id.ToString()
                        .Contains(txtFiltroComentariosId.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                return true;
            };

            view.Refresh();
        }

        private void BtnLimparFiltrosComentarios_Click(object sender, RoutedEventArgs e)
        {
            txtFiltroComentariosPostId.Clear();
            txtFiltroComentariosId.Clear();

            var view = CollectionViewSource.GetDefaultView(listComentarios.ItemsSource);
            if (view is null) return;
            view.Filter = null;
            view.Refresh();
        }

        // ---------- Filtros Chat IA ----------

        private void ChkChatSemRepeticao_Changed(object sender, RoutedEventArgs e)
            => AplicarFiltrosChat();

        private void BtnFiltrarChat_Click(object sender, RoutedEventArgs e)
            => AplicarFiltrosChat();

        private void AplicarFiltrosChat()
        {
            var view = CollectionViewSource.GetDefaultView(listChat.ItemsSource);
            if (view is null) return;

            
            var mensagens = listChat.ItemsSource as List<ChatModel> ?? new List<ChatModel>();
            var menorIdPorGrupo = mensagens
                .GroupBy(m => m.id_grupo)
                .ToDictionary(g => g.Key, g => g.Min(m => m.id_chat));

            view.Filter = obj =>
            {
                if (obj is not ChatModel chat) return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroChatId.Text) &&
                    !chat.id_chat.ToString()
                        .Contains(txtFiltroChatId.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroChatIdGrupo.Text) &&
                    !chat.id_grupo.ToString()
                        .Contains(txtFiltroChatIdGrupo.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (dpFiltroChatData.SelectedDate.HasValue)
                {
                    if (!ViagensPage.TryParseData(chat.data_interacao, out var interacaoEm) ||
                        interacaoEm.Date != dpFiltroChatData.SelectedDate.Value.Date)
                        return false;
                }

                if (chkChatSemRepeticao.IsChecked == true &&
                    menorIdPorGrupo.TryGetValue(chat.id_grupo, out var menorId) &&
                    chat.id_chat != menorId)
                    return false;

                return true;
            };

            view.Refresh();
        }

        private void BtnLimparFiltrosChat_Click(object sender, RoutedEventArgs e)
        {
            txtFiltroChatId.Clear();
            txtFiltroChatIdGrupo.Clear();
            dpFiltroChatData.SelectedDate = null;
            chkChatSemRepeticao.IsChecked = false;

            var view = CollectionViewSource.GetDefaultView(listChat.ItemsSource);
            if (view is null) return;
            view.Filter = null;
            view.Refresh();
        }

        // ---------- Duplo clique ----------

        private void ListViagens_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            if (ObterItemClicado<ViagemModel>(e) is not ViagemModel viagem) return;

            NavigationService?.Navigate(new ViagensDetalhePage(viagem, this));
        }

        private void ListPosts_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            if (ObterItemClicado<PostModel>(e) is not PostModel post) return;

            NavigationService?.Navigate(new PostDetalhePage(post, this));
        }

        private void ListComentarios_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            if (ObterItemClicado<ComentarioModel>(e) is not ComentarioModel comentario) return;

            var post = _todosPosts.FirstOrDefault(p => p.id_post == comentario.id_post);
            if (post is null)
            {
                MessageBox.Show(
                    "Não foi possível localizar o post desse comentário.",
                    "Aviso",
                    MessageBoxButton.OK,
                    MessageBoxImage.Warning);
                return;
            }

            NavigationService?.Navigate(new PostDetalhePage(post, this));
        }

        private void ListChat_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            if (ObterItemClicado<ChatModel>(e) is not ChatModel mensagem) return;

            var mensagensDoGrupo = _todasMensagensChat
                .Where(m => m.id_grupo == mensagem.id_grupo)
                .OrderBy(m => m.id_chat)
                .ToList();

            NavigationService?.Navigate(new ChatIaDetalhePage(mensagensDoGrupo, mensagem.id_grupo, this));
        }

        private static T? ObterItemClicado<T>(MouseButtonEventArgs e) where T : class
        {
            var dep = e.OriginalSource as DependencyObject;
            while (dep is not null && dep is not ListViewItem)
            {
                dep = VisualTreeHelper.GetParent(dep);
            }

            return dep is ListViewItem item ? item.DataContext as T : null;
        }

        // ---------- Voltar ----------

        private void BtnVoltar_Click(object sender, RoutedEventArgs e)
        {
            if (_paginaAnterior is not null)
                NavigationService?.Navigate(_paginaAnterior);
            else if (NavigationService?.CanGoBack == true)
                NavigationService.GoBack();
        }
    }
}
