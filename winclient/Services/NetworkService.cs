using System.Net.Http;
using System.Text;
using System.Text.Json;
using DataCollector.Models;

namespace DataCollector.Services
{
    public class NetworkService
    {
        private readonly HttpClient _httpClient;

        public NetworkService()
        {
            _httpClient = new HttpClient();
            _httpClient.Timeout = TimeSpan.FromSeconds(10);
        }

        public async Task<(bool success, string version, string error)> TestServerConnection(string serverAddress, int port)
        {
            try
            {
                var url = $"http://{serverAddress}:{port}/api/v1/status";
                var response = await _httpClient.GetAsync(url);

                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    try
                    {
                        var json = JsonDocument.Parse(content);
                        if (json.RootElement.TryGetProperty("version", out JsonElement versionElement))
                        {
                            return (true, versionElement.GetString() ?? "1.0", null);
                        }
                        return (true, "1.0", null);
                    }
                    catch
                    {
                        return (true, "1.0", null);
                    }
                }

                return (false, null, $"Servidor não disponível. Status: {response.StatusCode}");
            }
            catch (HttpRequestException ex)
            {
                return (false, null, $"Erro de conexão: {ex.Message}");
            }
            catch (Exception ex)
            {
                return (false, null, $"Erro inesperado: {ex.Message}");
            }
        }

        public async Task<(bool success, string tombo, string error)> SendInventory(string serverAddress, int port, HardwareInfo inventory)
        {
            try
            {
                var url = $"http://{serverAddress}:{port}/api/v1/inventario";
                var json = JsonSerializer.Serialize(inventory, new JsonSerializerOptions 
                { 
                    WriteIndented = true,
                    PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                });

                var content = new StringContent(json, Encoding.UTF8, "application/json");
                var response = await _httpClient.PostAsync(url, content);

                if (response.IsSuccessStatusCode)
                {
                    var responseContent = await response.Content.ReadAsStringAsync();
                    try
                    {
                        var jsonDoc = JsonDocument.Parse(responseContent);
                        if (jsonDoc.RootElement.TryGetProperty("tombo", out JsonElement tomboElement))
                        {
                            return (true, tomboElement.GetString() ?? "XX000001", null);
                        }
                    }
                    catch { }

                    return (true, "XX000001", null);
                }

                return (false, null, $"Falha no envio. Status: {response.StatusCode}");
            }
            catch (HttpRequestException ex)
            {
                return (false, null, $"Erro de conexão: {ex.Message}");
            }
            catch (Exception ex)
            {
                return (false, null, $"Erro inesperado: {ex.Message}");
            }
        }
    }
}