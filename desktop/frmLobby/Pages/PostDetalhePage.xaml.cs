using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Imaging;
using WindowLobby.CRUD.models;

namespace WindowLobby.Pages
{
    public partial class PostDetalhePage : Page
    {
        private readonly Page _paginaAnterior;

        public PostDetalhePage(PostModel post, Page paginaAnterior)
        {
            InitializeComponent();

            _paginaAnterior = paginaAnterior;

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

        /// <summary>
        /// Carrega a imagem do post a partir da URL retornada pela API.
        /// Se não houver "imagem" ou o carregamento falhar (URL inválida,
        /// sem rede, 404, etc.), a moldura fica oculta em vez de quebrar a página.
        /// </summary>
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
            // Navega direto pra mesma instância da página que abriu este
            // detalhe — em vez de NavigationService.GoBack(), que depende do
            // back stack do Frame e pode não voltar se algo no fluxo de
            // navegação (ex.: Dashboard.MainFrame_Navigated) limpar essa
            // pilha entre as duas navegações. Assim o botão sempre funciona,
            // e a página anterior (filtros, ordenação, rolagem) fica intacta
            // porque é o mesmo objeto, não uma nova instância recriada.
            if (_paginaAnterior is not null)
                NavigationService?.Navigate(_paginaAnterior);
            else if (NavigationService?.CanGoBack == true)
                NavigationService.GoBack();
        }
    }
}
