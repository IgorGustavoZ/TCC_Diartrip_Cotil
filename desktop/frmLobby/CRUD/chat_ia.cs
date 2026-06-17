using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using System.Windows;

namespace WindowLobby.CRUD
{
    public static class Chat_ia
    {
        private static HttpClient Client => WindowLobby.CRUD.Sessao.HttpClient;

        // Lógica para buscar mensagens do chat ia
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
        public static async Task<string?> BuscarMensagens()
        {
            var resp = await ExecutarComRefresh(() =>
            {
                var req = new HttpRequestMessage(HttpMethod.Get, $"/chatAll")
                {
                    Content = new StringContent("", Encoding.UTF8, "application/json")
                };
                return req;
            });

            if (!resp.IsSuccessStatusCode)
            {
                return null;
            }

            string respostaJson =
                await resp.Content
                .ReadAsStringAsync();  

            return respostaJson;
        }
        
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
        internal static void AdicionarCsrfHeader(HttpRequestMessage req)
        {
            var csrf = CRUD.Sessao.GetCsrfToken();
            if (!string.IsNullOrEmpty(csrf))
                req.Headers.TryAddWithoutValidation("X-CSRF-Token", csrf);
        }
    }
}

