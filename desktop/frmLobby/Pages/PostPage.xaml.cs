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
    public partial class PostPage : Page
    {
        private GridViewColumnHeader _lastHeaderClicked;
        private ListSortDirection _lastDirection = ListSortDirection.Ascending;

        
        private bool _carregado;

        public PostPage()
        {
            InitializeComponent();
            Loaded += async (_, _) =>
            {
                if (_carregado) return;
                _carregado = true;
                await CarregarPosts();
            };
        }

        

        private async Task CarregarPosts()
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

                var jsonPosts = await Post.GetPosts();

                if (jsonPosts is not null)
                {
                    // ---- DEBUG: inspect raw JSON before deserializing ----
                    //System.Diagnostics.Debug.WriteLine("===== RAW /posts JSON =====");
                    //System.Diagnostics.Debug.WriteLine(jsonPosts);
                    //================================

                    var posts = JsonSerializer.Deserialize<List<PostModel>>(
                        jsonPosts,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    );

                    listPosts.ItemsSource = posts;
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Erro ao carregar posts: {ex.Message}",
                    "Erro",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
            }
        }

        // ---------- De cima vem, pra baixo cai ----------

        private void ListViewHeader_Click(object sender, RoutedEventArgs e)
        {
            if (e.OriginalSource is not GridViewColumnHeader header) return;
            if (header.Role == GridViewColumnHeaderRole.Padding) return;
            if (header.Column?.DisplayMemberBinding is not System.Windows.Data.Binding binding) return;

            string propertyName = binding.Path.Path;

            ListSortDirection direction = header != _lastHeaderClicked
                ? ListSortDirection.Descending
                : (_lastDirection == ListSortDirection.Descending
                    ? ListSortDirection.Ascending
                    : ListSortDirection.Descending);

            var view = CollectionViewSource.GetDefaultView(listPosts.ItemsSource);
            if (view is null) return;

            view.SortDescriptions.Clear();
            view.SortDescriptions.Add(new SortDescription(propertyName, direction));
            view.Refresh();

            _lastHeaderClicked = header;
            _lastDirection = direction;
        }

        
        /*private void ReaplicarOrdenacao()
        {
            if (_lastHeaderClicked?.Column?.DisplayMemberBinding is not System.Windows.Data.Binding binding)
                return;

            var view = CollectionViewSource.GetDefaultView(listPosts.ItemsSource);
            if (view is null) return;

            view.SortDescriptions.Clear();
            view.SortDescriptions.Add(new SortDescription(binding.Path.Path, _lastDirection));
            view.Refresh();
        }*/

        // ---------- Detalhe do post ----------

        private void ListPosts_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
           
            var dep = e.OriginalSource as DependencyObject;
            while (dep is not null && dep is not ListViewItem)
            {
                dep = VisualTreeHelper.GetParent(dep);
            }

            if (dep is not ListViewItem item || item.DataContext is not PostModel post)
                return;

           
            NavigationService?.Navigate(new PostDetalhePage(post, this));
        }

        // ---------- Filtros!! ----------

        private void BtnFiltrar_Click(object sender, RoutedEventArgs e) => AplicarFiltro();

        
        private void AplicarFiltro()
        {
            var view = CollectionViewSource.GetDefaultView(listPosts.ItemsSource);
            if (view is null) return;

            view.Filter = obj =>
            {
                if (obj is not PostModel post) return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroId.Text) &&
                    !post.id_post.ToString()
                        .Contains(txtFiltroId.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroIdUsuario.Text) &&
                    !post.id_usuario.ToString()
                        .Contains(txtFiltroIdUsuario.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroConteudo.Text) &&
                    !(post.conteudo ?? "")
                        .Contains(txtFiltroConteudo.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (dpFiltroData.SelectedDate.HasValue)
                {
                    if (!DateTime.TryParse(post.data_criacao, out var criadoEm) ||
                        criadoEm.Date != dpFiltroData.SelectedDate.Value.Date)
                        return false;
                }

                return true;
            };

            view.Refresh();
        }

        private void BtnLimparFiltros_Click(object sender, RoutedEventArgs e)
        {
            txtFiltroId.Clear();
            txtFiltroIdUsuario.Clear();
            txtFiltroConteudo.Clear();
            dpFiltroData.SelectedDate = null;

            var view = CollectionViewSource.GetDefaultView(listPosts.ItemsSource);
            if (view is null) return;

            view.Filter = null;
            view.Refresh();
        }
    }
}
