using System.Windows;
using System.Windows.Controls;
using WindowLobby.CRUD.models;

namespace WindowLobby.Pages
{
    public partial class ViagensDetalhePage : Page
    {
        private readonly Page _paginaAnterior;

        public ViagensDetalhePage(ViagemModel viagem, Page paginaAnterior)
        {
            InitializeComponent();

            _paginaAnterior = paginaAnterior;

            txtTitulo.Text = string.IsNullOrWhiteSpace(viagem.nome_grupo) ? "Viagem" : viagem.nome_grupo;
            txtDestino.Text = string.IsNullOrWhiteSpace(viagem.destino_principal) ? "—" : viagem.destino_principal;

            txtId.Text = viagem.id_grupo.ToString();
            txtInicio.Text = string.IsNullOrWhiteSpace(viagem.data_inicio) ? "—" : viagem.data_inicio;
            txtFim.Text = string.IsNullOrWhiteSpace(viagem.data_fim) ? "—" : viagem.data_fim;
            txtCriador.Text = string.IsNullOrWhiteSpace(viagem.criador) ? "—" : viagem.criador;
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
