using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace WindowLobby.crud
{
    public static class Post
    {
        private static HttpClient Client => WindowLobby.CRUD.Sessao.HttpClient;

        // ── Listar posts ─────────────────────────────────────────────────────────

        /// <summary>
        /// GET /posts — lista posts paginados.
        /// O access_token cookie é enviado automaticamente pelo CookieContainer.
        /// Tenta renovar o token automaticamente se receber 401 (via Usuario.ExecutarComRefresh).
        /// </summary>
        /// <param name="limite">Quantidade máxima de posts (1-100). Default 50.</param>
        /// <param name="offset">Quantidade de posts a pular. Default 0.</param>
        public async static Task<string?> GetPosts(int limite = 50, int offset = 0)
        {
            var resp = await Usuario.ExecutarComRefresh(() =>
            {
                var req = new HttpRequestMessage(
                    HttpMethod.Get,
                    $"/posts?limite={limite}&offset={offset}")
                {
                    Content = new StringContent("", Encoding.UTF8, "application/json")
                };
                return req;
            }, isGet: true);

            if (resp is null || !resp.IsSuccessStatusCode)
            {
                return null;
            }

            string respostaJson =
                await resp.Content
                .ReadAsStringAsync();

            return respostaJson;
        }

        // ── Buscar post por id ───────────────────────────────────────────────────

        /// <summary>
        /// GET /posts/{id} — busca um post específico.
        /// Ajuste/remova caso o endpoint não exista no backend.
        /// </summary>
        public async static Task<string?> GetPostById(int id)
        {
            var resp = await Usuario.ExecutarComRefresh(() =>
            {
                var req = new HttpRequestMessage(HttpMethod.Get, $"/posts/{id}")
                {
                    Content = new StringContent("", Encoding.UTF8, "application/json")
                };
                return req;
            }, isGet: true);

            if (resp is null || !resp.IsSuccessStatusCode)
            {
                return null;
            }

            string respostaJson =
                await resp.Content
                .ReadAsStringAsync();

            return respostaJson;
        }
    }
}
