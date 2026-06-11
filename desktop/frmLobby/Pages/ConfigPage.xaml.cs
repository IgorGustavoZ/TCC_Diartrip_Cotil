using Microsoft.Win32;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Imaging;
using WindowLobby.crud;
using WindowLobby.CRUD;

namespace WindowLobby.Pages
{
    public partial class ConfigPage : Page
    {
        private string _caminhoImagemLocal = "";

        public ConfigPage()
        {
            InitializeComponent();
            Loaded += async (_, _) => await CarregarPerfil();
        }

        private async Task CarregarPerfil()
        {
            txtNome.Text = Sessao.Nome;

            var perfil = await Usuario.GetMe();
            var fotoUrl = perfil?["foto_perfil"]?.GetValue<string>() ?? "";

            if (!string.IsNullOrEmpty(fotoUrl))
            {
                try
                {
                    imgPerfil.Source = new BitmapImage(new Uri(fotoUrl));
                }
                catch
                {
                    // URL inválida ou inacessível — ignora
                }
            }
        }

        private async void BtnSelecionarFoto_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new OpenFileDialog
            {
                Filter = "Imagens (*.png;*.jpg;*.jpeg)|*.png;*.jpg;*.jpeg"
            };

            if (dialog.ShowDialog() != true) return;

            _caminhoImagemLocal = dialog.FileName;
            imgPerfil.Source = new BitmapImage(new Uri(_caminhoImagemLocal));

            try
            {
                var form = new MultipartFormDataContent();
                var bytes = File.ReadAllBytes(_caminhoImagemLocal);
                var fileContent = new ByteArrayContent(bytes);
                fileContent.Headers.ContentType = new MediaTypeHeaderValue("image/jpeg");
                form.Add(fileContent, "foto", Path.GetFileName(_caminhoImagemLocal));

                var req = new HttpRequestMessage(
                    HttpMethod.Patch,
                    $"/usuarios/{Sessao.UsuarioId}/foto")
                {
                    Content = form
                };

                var csrf = Sessao.GetCsrfToken();
                if (!string.IsNullOrEmpty(csrf))
                    req.Headers.TryAddWithoutValidation("X-CSRF-Token", csrf);

                var resp = await Sessao.HttpClient.SendAsync(req);

                if (resp.IsSuccessStatusCode)
                {
                    txtStatus.Text = "Foto atualizada com sucesso!";
                    Dashboard.Instancia?.ComporInformacoes();
                }
                else
                {
                    var erro = await resp.Content.ReadAsStringAsync();
                    MessageBox.Show($"Erro ao enviar foto:\n{erro}", "Erro",
                        MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Erro: {ex.Message}", "Erro",
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async void BtnSalvar_Click(object sender, RoutedEventArgs e)
        {
            var novoNome = txtNome.Text.Trim();
            if (string.IsNullOrEmpty(novoNome))
            {
                MessageBox.Show("O nome não pode estar vazio.", "Atenção",
                    MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var sucesso = await Usuario.PutUsuarios(novoNome);
            if (sucesso)
            {
                Sessao.Nome = novoNome;
                txtStatus.Text = "Nome atualizado com sucesso!";
                Dashboard.Instancia?.ComporInformacoes();
            }
            else
            {
                MessageBox.Show("Erro ao atualizar nome.", "Erro",
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}
