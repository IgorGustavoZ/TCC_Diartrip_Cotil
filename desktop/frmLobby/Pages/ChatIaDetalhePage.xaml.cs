using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using WindowLobby.CRUD.models;

namespace WindowLobby.Pages
{
    public partial class ChatIaDetalhePage : Page
    {
        public ChatIaDetalhePage(List<ChatModel> mensagensDoGrupo, int idGrupo)
        {
            InitializeComponent();

            txtTitulo.Text = $"Conversa do grupo {idGrupo}";
            txtSubtitulo.Text = mensagensDoGrupo.Count == 1
                ? "1 mensagem nesta conversa"
                : $"{mensagensDoGrupo.Count} mensagens nesta conversa";

            icMensagens.ItemsSource = mensagensDoGrupo;
        }

        private void BtnVoltar_Click(object sender, RoutedEventArgs e)
        {
            // Volta para a ChatIaPage exatamente como estava (filtros, ordenação,
            // posição de rolagem) — a Dashboard não limpa o back stack ao navegar
            // para esta página de detalhe (ver Dashboard.MainFrame_Navigated).
            if (NavigationService?.CanGoBack == true)
                NavigationService.GoBack();
        }
    }
}
