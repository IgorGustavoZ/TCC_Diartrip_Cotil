using System.Net;
using System.Net.Http;

namespace WindowLobby.CRUD
{
    /// <summary>
    /// Estado da sessão autenticada.
    /// A autenticação é feita via cookies httpOnly gerenciados pelo HttpClientHandler.
    ///
    /// Limpeza segura: Sessao.Limpar() recria o HttpClient e o CookieContainer,
    /// garantindo que cookies antigos não vazem para requisições futuras.
    /// </summary>
    public static class Sessao
    {
        private static readonly object _clientLock = new();
        private static HttpClient?       _client;
        private static CookieContainer   _cookieContainer = new();

        public static int    UsuarioId { get; set; }
        public static string Nome      { get; set; } = string.Empty;

        public static string ApiBase { get; set; } = "http://127.0.0.1:8000";

        /// <summary>
        /// HttpClient singleton configurado para enviar cookies automaticamente.
        /// Thread-safe: usa lock para criação lazy.
        /// </summary>
        public static HttpClient HttpClient
        {
            get
            {
                if (_client is not null) return _client;

                lock (_clientLock)
                {
                    if (_client is not null) return _client;

                    var handler = new HttpClientHandler
                    {
                        CookieContainer    = _cookieContainer,
                        UseCookies         = true,
                        AllowAutoRedirect  = false,
                    };
                    _client = new HttpClient(handler)
                    {
                        BaseAddress = new Uri(ApiBase),
                        Timeout     = TimeSpan.FromSeconds(15),
                    };
                    _client.DefaultRequestHeaders.Add("Accept", "application/json");
                }
                return _client;
            }
        }

        /// <summary>Lê o csrf_token do CookieContainer para o header X-CSRF-Token.</summary>
        public static string? GetCsrfToken()
        {
            foreach (Cookie cookie in _cookieContainer.GetCookies(new Uri(ApiBase)))
            {
                if (cookie.Name == "csrf_token")
                    return cookie.Value;
            }
            return null;
        }

        public static bool IsLoggedIn => UsuarioId > 0;

        /// <summary>
        /// Limpa a sessão localmente.
        /// Recria o HttpClient e o CookieContainer para garantir que
        /// nenhum cookie da sessão anterior vaze para requisições futuras.
        /// IMPORTANTE: Chamar Usuario.Logout() ANTES de Limpar() para revogar
        /// os tokens no servidor.
        /// </summary>
        public static void Limpar()
        {
            lock (_clientLock)
            {
                UsuarioId = 0;
                Nome      = string.Empty;

                // Descartar o client antigo (fecha conexões persistentes)
                _client?.Dispose();
                _client = null;

                // Novo CookieContainer vazio — garante que cookies antigos
                // nunca serão enviados por uma referência remanescente
                _cookieContainer = new CookieContainer();
            }
        }
    }
}
