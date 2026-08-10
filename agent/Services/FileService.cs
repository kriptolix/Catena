using System.Text.Json;
using System.Text;
using Agent.Models;

namespace Agent.Services
{
    public class FileService
    {
        public void SaveInventoryLocally(HardwareInfo inventory)
        {
            try
            {
                var fileName = $"inventario_{DateTime.Now:yyyyMMdd_HHmmss}.json";
                var filePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, fileName);

                var options = new JsonSerializerOptions
                {
                    WriteIndented = true,
                    PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                };

                var json = JsonSerializer.Serialize(inventory, options);
                File.WriteAllText(filePath, json, Encoding.UTF8);

                Console.WriteLine($"💾 Inventário salvo em: {filePath}");
            }
            catch (Exception ex)
            {
                throw new Exception($"Erro ao salvar arquivo localmente: {ex.Message}", ex);
            }
        }
    }
}