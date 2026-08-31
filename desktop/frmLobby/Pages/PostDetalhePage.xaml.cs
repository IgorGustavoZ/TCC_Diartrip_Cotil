using System;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Media.Imaging;
using WindowLobby.crud;
using WindowLobby.CRUD.models;

namespace WindowLobby.Pages
{
    public partial class PostDetalhePage : Page
    {
        private readonly Page _paginaAnterior;
        private readonly int _idUsuarioPost;

        public PostDetalhePage(PostModel post, Page paginaAnterior)
        {
            InitializeComponent();

            _paginaAnterior = paginaAnterior;
            _idUsuarioPost = post.id_usuario;

            txtTitulo.Text = $"Post de {post.nome}";
            txtSubtitulo.Text = $"Publicado em {post.data_criacao}";

            txtConteudo.Text = post.conteudo;

            runIdPost.Text = post.id_post.ToString();
            runIdUsuario.Text = post.id_usuario.ToString();
            runNomeUsuario.Text = post.nome;
            runData.Text = post.data_criacao;

            txtCurtidas.Text = post.curtidas == 1
                ? "1 curtida"
                : $"{post.curtidas} curtidas";

            CarregarImagem(post.imagem);

            var comentarios = post.comentarios;
            if (comentarios is null || comentarios.Count == 0)
            {
                txtComentariosTitulo.Text = "Comentários (0)";
                icComentarios.Visibility = Visibility.Collapsed;
                txtSemComentarios.Visibility = Visibility.Visible;
            }
            else
            {
                txtComentariosTitulo.Text = $"Comentários ({comentarios.Count})";
                icComentarios.ItemsSource = comentarios;
            }
        }

        
        private void CarregarImagem(string? url)
        {
            if (string.IsNullOrWhiteSpace(url))
            {
                borderImagem.Visibility = Visibility.Collapsed;
                return;
            }

            try
            {
                var bitmap = new BitmapImage();
                bitmap.BeginInit();
                bitmap.UriSource = new Uri(url, UriKind.Absolute);
                bitmap.CacheOption = BitmapCacheOption.OnLoad;
                bitmap.EndInit();

                imgPost.Source = bitmap;
                borderImagem.Visibility = Visibility.Visible;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[PostDetalhePage] Falha ao carregar imagem: {ex.Message}");
                borderImagem.Visibility = Visibility.Collapsed;
            }
        }

        private void BtnVoltar_Click(object sender, RoutedEventArgs e)
        {
            
            if (_paginaAnterior is not null)
                NavigationService?.Navigate(_paginaAnterior);
            else if (NavigationService?.CanGoBack == true)
                NavigationService.GoBack();
        }

        // ---------- Usuários clicáveis ----------

        private async void LinkUsuarioPost_Click(object sender, RoutedEventArgs e)
        {
            await AbrirUsuarioDetalhe(_idUsuarioPost);
        }

        private async void LinkUsuarioComentario_Click(object sender, RoutedEventArgs e)
        {
           
            if (sender is not Hyperlink link || link.DataContext is not ComentarioModel comentario)
                return;

            await AbrirUsuarioDetalhe(comentario.id_usuario);
        }

        
        private async Task AbrirUsuarioDetalhe(int idUsuario)
        {
            try
            {
                var json = await Usuario.GetUsuariosById(idUsuario);
                if (json is null)
                {
                    MessageBox.Show(
                        "Não foi possível carregar os dados desse usuário.",
                        "Aviso",
                        MessageBoxButton.OK,
                        MessageBoxImage.Warning);
                    return;
                }

                var usuario = JsonSerializer.Deserialize<UsuarioModel>(
                    json,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                );

                if (usuario is null) return;

                NavigationService?.Navigate(new UsuarioDetalhePage(usuario, this));
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Erro ao carregar usuário: {ex.Message}",
                    "Erro",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
            }
        }
    }
}
