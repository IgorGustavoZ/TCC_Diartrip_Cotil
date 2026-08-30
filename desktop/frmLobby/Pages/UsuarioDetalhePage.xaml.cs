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

        // Guarda os posts carregados (de TODOS os usuários) pra conseguir
        // localizar o post de origem quando o usuário dá duplo clique num
        // comentário na aba Comentários.
        private List<PostModel> _todosPosts = new();

        private GridViewColumnHeader _lastHeaderClickedPosts;
        private ListSortDirection _lastDirectionPosts = ListSortDirection.Ascending;

        private GridViewColumnHeader _lastHeaderClickedComentarios;
        private ListSortDirection _lastDirectionComentarios = ListSortDirection.Ascending;

        private GridViewColumnHeader _lastHeaderClickedViagens;
        private ListSortDirection _lastDirectionViagens = ListSortDirection.Ascending;

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

            Loaded += async (_, _) => await CarregarDados();
        }

        private async Task CarregarDados()
        {
            try
            {
                // A API não tem um filtro por id_usuario em /posts (nem um
                // endpoint dedicado de comentários), então busca o lote
                // máximo permitido pelo endpoint (limite=100) e filtra no
                // cliente. Se o backend ganhar algo como /posts?id_usuario=
                // ou um /comentarios próprio, troque a busca abaixo por ele.
                var jsonPosts = await Post.GetPosts(limite: 100, offset: 0);

                if (jsonPosts is not null)
                {
                    _todosPosts = JsonSerializer.Deserialize<List<PostModel>>(
                        jsonPosts,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    ) ?? new List<PostModel>();
                }

                // ---- Posts do usuário ----
                var postsDoUsuario = _todosPosts
                    .Where(p => p.id_usuario == _usuario.id_usuario)
                    .ToList();

                listPosts.ItemsSource = postsDoUsuario;
                txtPostsTitulo.Text = $"Posts ({postsDoUsuario.Count})";
                txtSemPosts.Visibility = postsDoUsuario.Count == 0
                    ? Visibility.Visible
                    : Visibility.Collapsed;

                // ---- Comentários do usuário ----
                // Percorre os comentários de TODOS os posts carregados (não só
                // os dele) porque o usuário pode comentar em posts de outras
                // pessoas.
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

                // ---- Viagens (grupos) do usuário ----
                var jsonViagens = await CRUD.Viagem.GetViagens();
                List<ViagemModel> todasViagens = new();

                if (jsonViagens is not null)
                {
                    todasViagens = JsonSerializer.Deserialize<List<ViagemModel>>(
                        jsonViagens,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    ) ?? new List<ViagemModel>();
                }

                // /grupos/all não expõe a lista de membros, só quem criou o
                // grupo (criado_por) — então esta aba mostra os grupos
                // criados pelo usuário, não necessariamente todos os que ele
                // participa. Se o backend ganhar um filtro por membro, troque
                // essa condição por ele.
                var viagensDoUsuario = todasViagens
                    .Where(v => v.criado_por == _usuario.id_usuario)
                    .ToList();

                listViagens.ItemsSource = viagensDoUsuario;
                txtViagensTitulo.Text = $"Viagens ({viagensDoUsuario.Count})";
                txtSemViagens.Visibility = viagensDoUsuario.Count == 0
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

        // ---------- Ordenação ----------

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

        // ---------- Duplo clique ----------

        private void ListPosts_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            if (ObterItemClicado<PostModel>(e) is not PostModel post) return;

            NavigationService?.Navigate(new PostDetalhePage(post, this));
        }

        private void ListComentarios_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            if (ObterItemClicado<ComentarioModel>(e) is not ComentarioModel comentario) return;

            // O comentário não carrega os dados do post, então busca o post
            // correspondente entre os que já foram carregados pra essa página.
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

        /// <summary>
        /// Sobe a árvore visual a partir do ponto clicado até achar o
        /// ListViewItem, evitando abrir o detalhe ao clicar no cabeçalho da
        /// lista ou numa área vazia sem item.
        /// </summary>
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
            // Mesma lógica do PostDetalhePage: navega direto pra instância
            // que abriu esse detalhe, em vez de depender do back stack do
            // Frame (NavigationService.GoBack()), que pode ser limpo em
            // outro ponto do fluxo de navegação do app.
            if (_paginaAnterior is not null)
                NavigationService?.Navigate(_paginaAnterior);
            else if (NavigationService?.CanGoBack == true)
                NavigationService.GoBack();
        }
    }
}
