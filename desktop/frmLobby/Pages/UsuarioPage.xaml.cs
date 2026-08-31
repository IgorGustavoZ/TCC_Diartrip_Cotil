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
    public partial class UsuarioPage : Page
    {
        private GridViewColumnHeader _lastHeaderClicked;
        private ListSortDirection _lastDirection = ListSortDirection.Ascending;

        
        private bool _carregado;

        public UsuarioPage()
        {
            InitializeComponent();
            Loaded += async (_, _) =>
            {
                if (_carregado) return;
                _carregado = true;
                await CarregarPerfil();
            };
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
                    // ---- DEBUG: inspect raw JSON before deserializing ----
                    //System.Diagnostics.Debug.WriteLine("===== RAW /usuarios/ JSON =====");
                    //System.Diagnostics.Debug.WriteLine(jsonUsu);
                    //System.Diagnostics.Debug.WriteLine("================================");
                    // --------------------------------------------------------

                    var usuarios = JsonSerializer.Deserialize<List<UsuarioModel>>(
                        jsonUsu,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    );

                    listUsuarios.ItemsSource = usuarios;
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

            var view = CollectionViewSource.GetDefaultView(listUsuarios.ItemsSource);
            if (view is null) return;

            view.SortDescriptions.Clear();
            view.SortDescriptions.Add(new SortDescription(propertyName, direction));
            view.Refresh();

            _lastHeaderClicked = header;
            _lastDirection = direction;
        }

        // ---------- Detalhe do usuário ----------

        private void ListUsuarios_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            
            var dep = e.OriginalSource as DependencyObject;
            while (dep is not null && dep is not ListViewItem)
            {
                dep = VisualTreeHelper.GetParent(dep);
            }

            if (dep is not ListViewItem item || item.DataContext is not UsuarioModel usuario)
                return;

           
            NavigationService?.Navigate(new UsuarioDetalhePage(usuario, this));
        }

        // ---------- Filtros!! ----------

        private void BtnFiltrar_Click(object sender, RoutedEventArgs e)
        {
            var view = CollectionViewSource.GetDefaultView(listUsuarios.ItemsSource);
            if (view is null) return;

            view.Filter = obj =>
            {
                if (obj is not UsuarioModel usuario) return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroId.Text) &&
                    !usuario.id_usuario.ToString()
                        .Contains(txtFiltroId.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroNome.Text) &&
                    !(usuario.nome ?? "")
                        .Contains(txtFiltroNome.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroEmail.Text) &&
                    !(usuario.email ?? "")
                        .Contains(txtFiltroEmail.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (dpFiltroData.SelectedDate.HasValue)
                {
                    if (!DateTime.TryParse(usuario.data_criacao, out var criadoEm) ||
                        criadoEm.Date != dpFiltroData.SelectedDate.Value.Date)
                        return false;
                }

                //combo!! box!!
                var chave = (cmbFiltroCriadosEm.SelectedItem as ComboBoxItem)?.Tag as string;
                if (chave is not null && chave != "qualquer")
                {
                    if (!DateTime.TryParse(usuario.data_criacao, out var criadoEmJanela))
                        return false;

                    var limite = chave switch
                    {
                        "dia" => DateTime.Now.AddDays(-1),
                        "semana" => DateTime.Now.AddDays(-7),
                        "mes" => DateTime.Now.AddMonths(-1),
                        "ano" => DateTime.Now.AddYears(-1),
                        _ => DateTime.MinValue
                    };

                    if (criadoEmJanela < limite)
                        return false;
                }

                return true;
            };

            view.Refresh();
        }

        private void BtnLimparFiltros_Click(object sender, RoutedEventArgs e)
        {
            txtFiltroId.Clear();
            txtFiltroNome.Clear();
            txtFiltroEmail.Clear();
            dpFiltroData.SelectedDate = null;
            cmbFiltroCriadosEm.SelectedIndex = 0;

            var view = CollectionViewSource.GetDefaultView(listUsuarios.ItemsSource);
            if (view is null) return;

            view.Filter = null;
            view.Refresh();
        }
    }
}
