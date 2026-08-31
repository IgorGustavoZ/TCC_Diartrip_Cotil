using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using WindowLobby.CRUD.models;

namespace WindowLobby.Pages
{
    public partial class ViagensDetalhePage : Page
    {
        private readonly Page _paginaAnterior;
        private readonly int _idGrupo;

        public ViagensDetalhePage(ViagemModel viagem, Page paginaAnterior)
        {
            InitializeComponent();

            _paginaAnterior = paginaAnterior;
            _idGrupo = viagem.id_grupo;

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

        
        private async void BtnVerConversa_Click(object sender, RoutedEventArgs e)
        {
            BtnVerConversa.IsEnabled = false;
            try
            {
                var jsonChat = await CRUD.Chat_ia.BuscarMensagens();
                if (jsonChat is null)
                {
                    MessageBox.Show(
                        "Não foi possível carregar a conversa deste grupo.",
                        "Aviso",
                        MessageBoxButton.OK,
                        MessageBoxImage.Warning);
                    return;
                }

                var todasMensagens = JsonSerializer.Deserialize<List<ChatModel>>(
                    jsonChat,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                ) ?? new List<ChatModel>();

                var mensagensDoGrupo = todasMensagens
                    .Where(m => m.id_grupo == _idGrupo)
                    .OrderBy(m => m.id_chat)
                    .ToList();

                if (mensagensDoGrupo.Count == 0)
                {
                    MessageBox.Show(
                        "Este grupo ainda não tem nenhuma conversa com a IA.",
                        "Chat IA",
                        MessageBoxButton.OK,
                        MessageBoxImage.Information);
                    return;
                }

                
                NavigationService?.Navigate(new ChatIaDetalhePage(mensagensDoGrupo, _idGrupo, this));
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Erro ao carregar a conversa: {ex.Message}",
                    "Erro",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
            }
            finally
            {
                BtnVerConversa.IsEnabled = true;
            }
        }
    }
}
