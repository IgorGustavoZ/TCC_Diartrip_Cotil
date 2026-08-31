using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Input;
using WindowLobby.CRUD;
using WindowLobby.CRUD.models;

namespace WindowLobby.Pages
{
    public partial class ChatIaPage : Page
    {
        private GridViewColumnHeader _lastHeaderClicked;
        private ListSortDirection _lastDirection = ListSortDirection.Ascending;

        
        private List<ChatModel>? _todosChats;
        private Dictionary<int, int>? _menorIdPorGrupo;

        
        private bool _carregado;

        public ChatIaPage()
        {
            InitializeComponent();
            Loaded += async (_, _) =>
            {
                if (_carregado) return;
                _carregado = true;
                await CarregarChats();
            };
        }

        private async Task CarregarChats()
        {
            try
            {
                var jsonChat = await Chat_ia.BuscarMensagens();

                MessageBox.Show(jsonChat);

                if (jsonChat is not null)
                {
                    var chats = JsonSerializer.Deserialize<List<ChatModel>>(
                        jsonChat,
                        new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                    );

                    _todosChats = chats ?? new List<ChatModel>();
                    _menorIdPorGrupo = _todosChats
                        .GroupBy(c => c.id_grupo)
                        .ToDictionary(g => g.Key, g => g.Min(c => c.id_chat));

                    listChats.ItemsSource = _todosChats;
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Erro ao carregar chats: {ex.Message}",
                    "Erro",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
            }
        }

        // ---------- Abrir a conversa inteira do grupo (duplo clique na linha) ----------

        private void ListChats_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            if (listChats.SelectedItem is not ChatModel chat) return;
            if (_todosChats is null) return;

            var mensagensDoGrupo = _todosChats
                .Where(c => c.id_grupo == chat.id_grupo)
                .OrderBy(c => c.id_chat)
                .ToList();

            
            NavigationService?.Navigate(new ChatIaDetalhePage(mensagensDoGrupo, chat.id_grupo, this));
        }

        // ---------- De cima vem, para baixo cai ----------

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

            var view = CollectionViewSource.GetDefaultView(listChats.ItemsSource);
            if (view is null) return;

            view.SortDescriptions.Clear();
            view.SortDescriptions.Add(new SortDescription(propertyName, direction));
            view.Refresh();

            _lastHeaderClicked = header;
            _lastDirection = direction;
        }

        // ---------- Filtro ----------

        private void ChkOcultarDuplicados_Changed(object sender, RoutedEventArgs e)
            => AplicarFiltros();

        private void BtnFiltrar_Click(object sender, RoutedEventArgs e)
            => AplicarFiltros();

        private void AplicarFiltros()
        {
            var view = CollectionViewSource.GetDefaultView(listChats.ItemsSource);
            if (view is null) return;

            view.Filter = obj =>
            {
                if (obj is not ChatModel chat) return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroId.Text) &&
                    !chat.id_chat.ToString()
                        .Contains(txtFiltroId.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroIdUsuario.Text) &&
                    !chat.id_usuario.ToString()
                        .Contains(txtFiltroIdUsuario.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (!string.IsNullOrWhiteSpace(txtFiltroIdGrupo.Text) &&
                    !chat.id_grupo.ToString()
                        .Contains(txtFiltroIdGrupo.Text.Trim(), StringComparison.OrdinalIgnoreCase))
                    return false;

                if (dpFiltroData.SelectedDate.HasValue)
                {
                    if (!DateTime.TryParse(chat.data_interacao, out var interacaoEm) ||
                        interacaoEm.Date != dpFiltroData.SelectedDate.Value.Date)
                        return false;
                }

                if (chkOcultarDuplicados.IsChecked == true &&
                    _menorIdPorGrupo is not null &&
                    _menorIdPorGrupo.TryGetValue(chat.id_grupo, out var menorId) &&
                    chat.id_chat != menorId)
                    return false;

                return true;
            };

            view.Refresh();
        }

        private void BtnLimparFiltros_Click(object sender, RoutedEventArgs e)
        {
            txtFiltroId.Clear();
            txtFiltroIdUsuario.Clear();
            txtFiltroIdGrupo.Clear();
            dpFiltroData.SelectedDate = null;
            chkOcultarDuplicados.IsChecked = false;

            var view = CollectionViewSource.GetDefaultView(listChats.ItemsSource);
            if (view is null) return;

            view.Filter = null;
            view.Refresh();
        }
    }
}
