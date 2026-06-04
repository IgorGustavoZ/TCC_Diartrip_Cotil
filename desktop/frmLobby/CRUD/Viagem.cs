using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Nodes;
using WindowLobby.crud;

namespace WindowLobby.CRUD
{
    public static class Viagem
    {
        /// <summary>
        /// GET /grupos — lista grupos do usuário logado.
        /// Usa retry automático em 401 (refresh token) via ExecutarComRefresh.
        /// </summary>
        public static async Task<string?> GetViagens()
        {
            var resp = await Usuario.ExecutarComRefresh(
                () => new HttpRequestMessage(HttpMethod.Get, "/grupos"),
                isGet: true
            );

            if (resp is null || !resp.IsSuccessStatusCode)
            {
                System.Diagnostics.Debug.WriteLine(
                    $"[Viagem.GetViagens] Status: {(int?)resp?.StatusCode ?? 0}");
                return null;
            }

            return await resp.Content.ReadAsStringAsync();
        }
    }
}
