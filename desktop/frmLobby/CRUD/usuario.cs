using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace WindowLobby.crud
{
    public static class Usuario
    {
        private static HttpClient Client => WindowLobby.CRUD.Sessao.HttpClient;

        // ── Login ────────────────────────────────────────────────────────────────

        /// <summary>
        /// POST /login — autenticação via cookie (access_token httpOnly).
        /// O backend define os cookies automaticamente no CookieContainer.
        /// </summary>
        public static async Task<(bool sucesso, int usuarioId, string erro)> Login(
            string email, string senha)
        {
            var payload = JsonSerializer.Serialize(new { email, senha });
            var content = new StringContent(payload, Encoding.UTF8, "application/json");

            HttpResponseMessage resposta;
            try
            {
                resposta = await Client.PostAsync("/login", content);
            }
            catch (HttpRequestException ex)
            {
                return (false, 0, $"Erro de rede: {ex.Message}");
            }
            catch (TaskCanceledException)
            {
                return (false, 0, "Tempo de resposta esgotado. Verifique a conexão.");
            }

            var body = await resposta.Content.ReadAsStringAsync();
            if (!resposta.IsSuccessStatusCode)
            {
                string detalhe = "Credenciais inválidas";
                try
                {
                    var json = JsonNode.Parse(body);
                    detalhe = json?["detail"]?.GetValue<string>() ?? detalhe;
                }
                catch { /* JSON inválido — mantém padrão */ }
                return (false, 0, detalhe);
            }

            int id = 0;
            try
            {
                var json = JsonNode.Parse(body);
                id = json?["usuario_id"]?.GetValue<int>() ?? 0;
            }
            catch
            {
                return (false, 0, "Resposta inesperada do servidor.");
            }

            return (true, id, string.Empty);
        }

        // ── Logout ───────────────────────────────────────────────────────────────

        /// <summary>
        /// POST /logout — revoga access token + todos os refresh tokens no servidor.
        /// O access_token cookie (path="/") é enviado automaticamente.
        /// Após o logout no servidor, limpa a sessão local via Sessao.Limpar().
        /// </summary>
        public static async Task<bool> Logout()
        {
            try
            {
                var req = new HttpRequestMessage(HttpMethod.Post, "/logout");
                AdicionarCsrfHeader(req);

                var resp = await Client.SendAsync(req);
                // Limpar sessão local independentemente do resultado do servidor
                return resp.IsSuccessStatusCode;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[Usuario.Logout] Erro: {ex.Message}");
                return false;
            }
            finally
            {
                // Garante limpeza local mesmo se o servidor falhar
                CRUD.Sessao.Limpar();
            }
        }

        // ── Perfil ───────────────────────────────────────────────────────────────

        /// <summary>
        /// GET /usuarios/me — retorna perfil do usuário logado.
        /// Tenta renovar o token automaticamente se receber 401.
        /// </summary>
        public static async Task<JsonNode?> GetMe()
        {
            var resp = await ExecutarComRefresh(
                () => new HttpRequestMessage(HttpMethod.Get, "/usuarios/me"),
                isGet: true
            );
            if (resp is null || !resp.IsSuccessStatusCode) return null;

            var body = await resp.Content.ReadAsStringAsync();
            return JsonNode.Parse(body);
        }

        // ── Refresh Token ─────────────────────────────────────────────────────────

        /// <summary>
        /// POST /token/refresh — renova o access token.
        /// O refresh_token cookie (path="/token/refresh") é enviado automaticamente
        /// pelo CookieContainer pois o path da requisição coincide.
        /// </summary>
        public static async Task<bool> RefreshToken()
        {
            try
            {
                // O CookieContainer enviará automaticamente o refresh_token
                // pois o path do cookie ("/token/refresh") coincide com a URI
                var req = new HttpRequestMessage(HttpMethod.Post, "/token/refresh");
                var resp = await Client.SendAsync(req);

                if (resp.IsSuccessStatusCode)
                {
                    System.Diagnostics.Debug.WriteLine("[Usuario.RefreshToken] Token renovado com sucesso.");
                    return true;
                }

                System.Diagnostics.Debug.WriteLine(
                    $"[Usuario.RefreshToken] Falhou com status {(int)resp.StatusCode}");
                return false;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"[Usuario.RefreshToken] Erro: {ex.Message}");
                return false;
            }
        }

        // ── Helper: executar com retry automático em 401 ──────────────────────────

        /// <summary>
        /// Executa uma requisição e, se receber 401, tenta renovar o token e refaz.
        /// Retorna null se a renovação falhar (usuário deve ser redirecionado ao login).
        /// </summary>
        public static async Task<HttpResponseMessage?> ExecutarComRefresh(
            Func<HttpRequestMessage> construirReq,
            bool isGet = false)
        {
            var req = construirReq();
            if (!isGet) AdicionarCsrfHeader(req);

            HttpResponseMessage resp;
            try
            {
                resp = await Client.SendAsync(req);
            }
            catch
            {
                return null;
            }

            if (resp.StatusCode != HttpStatusCode.Unauthorized)
                return resp;

            // 401 → tentar renovar token
            System.Diagnostics.Debug.WriteLine("[Usuario] 401 recebido — tentando refresh token...");
            bool renovado = await RefreshToken();
            if (!renovado)
            {
                System.Diagnostics.Debug.WriteLine("[Usuario] Refresh falhou — sessão expirada.");
                return resp; // retorna o 401 para o chamador tratar (ex: abrir janela de login)
            }

            // Retry com novos cookies
            var reqRetry = construirReq();
            if (!isGet) AdicionarCsrfHeader(reqRetry);

            try
            {
                return await Client.SendAsync(reqRetry);
            }
            catch
            {
                return null;
            }
        }

        // ── Atualizar perfil ─────────────────────────────────────────────────────

        /// <summary>
        /// PUT /usuarios/{id} — atualiza nome do usuário logado.
        /// Busca o e-mail atual via GetMe() para não sobrescrever com string vazia.
        /// </summary>
        public static async Task<bool> PutUsuarios(string novoNome)
        {
            var me = await GetMe();
            var email = me?["email"]?.GetValue<string>() ?? "";
            var bio   = me?["bio"]?.GetValue<string>() ?? "";

            var payload = JsonSerializer.Serialize(new { nome = novoNome, email, bio });
            var content = new StringContent(payload, Encoding.UTF8, "application/json");

            var resp = await ExecutarComRefresh(() =>
            {
                var req = new HttpRequestMessage(HttpMethod.Put, $"/usuarios/{CRUD.Sessao.UsuarioId}")
                {
                    Content = new StringContent(payload, Encoding.UTF8, "application/json")
                };
                return req;
            });

            return resp?.IsSuccessStatusCode ?? false;
        }

        // ── Utilitários ──────────────────────────────────────────────────────────

        [Obsolete("Endpoint GET /usuarios não existe no backend. Use GetMe() para o usuário logado.")]
        public static Task<string?> GetUsuarios() => Task.FromResult<string?>(null);

        internal static void AdicionarCsrfHeader(HttpRequestMessage req)
        {
            var csrf = CRUD.Sessao.GetCsrfToken();
            if (!string.IsNullOrEmpty(csrf))
                req.Headers.TryAddWithoutValidation("X-CSRF-Token", csrf);
        }
    }
}
