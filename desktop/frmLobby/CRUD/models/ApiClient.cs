using System.Net;
using System.Net.Http;

namespace WindowLobby
{
    public static class ApiClient
    {
        public static CookieContainer Cookies =
            new CookieContainer();

        private static readonly HttpClientHandler Handler =
            new HttpClientHandler()
            {
                CookieContainer = Cookies,
                UseCookies = true
            };

        public static readonly HttpClient Client =
            new HttpClient(Handler);
    }
}