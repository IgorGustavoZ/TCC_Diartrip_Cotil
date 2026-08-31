using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using WindowLobby.CRUD.models;

namespace WindowLobby.Pages
{
    public partial class ChatIaDetalhePage : Page
    {
        private readonly Page _paginaAnterior;

        public ChatIaDetalhePage(List<ChatModel> mensagensDoGrupo, int idGrupo, Page paginaAnterior)
        {
            InitializeComponent();

            _paginaAnterior = paginaAnterior;

            txtTitulo.Text = $"Conversa do grupo {idGrupo}";
            txtSubtitulo.Text = mensagensDoGrupo.Count == 1
                ? "1 mensagem nesta conversa"
                : $"{mensagensDoGrupo.Count} mensagens nesta conversa";

            icMensagens.ItemsSource = mensagensDoGrupo;
        }

        private void BtnVoltar_Click(object sender, RoutedEventArgs e)
        {
            
            if (_paginaAnterior is not null)
                NavigationService?.Navigate(_paginaAnterior);
            else if (NavigationService?.CanGoBack == true)
                NavigationService.GoBack();
        }
    }
}
