using System.Net;
using System.Text;
using System.Text.Json;
using Agent.Models;
using System.IO;

namespace Agent.Services
{
    public class WebServerService
    {
        private readonly IHardwareCollector _collector;
        private HttpListener? _listener;
        private readonly NetworkService _networkService;
        private readonly FileService _fileService;
        private HardwareInfo? _currentInventory;
        private bool _isRunning;

        public WebServerService()
        {

            if (OperatingSystem.IsWindows())
                _collector = new WindowsHardwareCollector();
            else
                _collector = new LinuxHardwareCollector();
            
            _networkService = new NetworkService();
            _fileService = new FileService();
        }

        public void Start(int port = 54322)
        {
            _listener = new HttpListener();
            _listener.Prefixes.Add($"http://localhost:{port}/");
            _listener.Start();
            _isRunning = true;

            // Iniciar thread para processar requisições
            Task.Run(() => ProcessRequests());
        }

        public void Stop()
        {
            _isRunning = false;
            _listener?.Stop();
            _listener?.Close();
        }

        private async Task ProcessRequests()
        {
            while (_isRunning)
            {
                try
                {
                    var context = await _listener.GetContextAsync();
                    _ = Task.Run(() => HandleRequest(context));
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Erro: {ex.Message}");
                }
            }
        }

        private async Task HandleRequest(HttpListenerContext context)
        {
            var request = context.Request;
            var response = context.Response;

            try
            {
                // Adicionar headers CORS para desenvolvimento
                response.AddHeader("Access-Control-Allow-Origin", "*");
                response.AddHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
                response.AddHeader("Access-Control-Allow-Headers", "Content-Type");

                if (request.HttpMethod == "OPTIONS")
                {
                    response.StatusCode = 200;
                    response.Close();
                    return;
                }

                var path = request.Url?.AbsolutePath ?? "/";
                Console.WriteLine($"{request.HttpMethod} {path}");

                if (path == "/" || path == "/index.html")
                {
                    var fileName = path == "/" ? "page.html" : path.TrimStart('/');

                    var filePath = Path.Combine(
                        AppContext.BaseDirectory,
                        "WebGui",
                        fileName
                    );
                    Console.WriteLine(filePath);

                    await ServeStaticFile(response, filePath);
                }
                else if (path == "/api/analyze" && request.HttpMethod == "POST")
                {
                    await HandleAnalyze(response);
                }
                else if (path == "/api/save" && request.HttpMethod == "POST")
                {
                    await HandleSave(response, request);
                }
                else if (path == "/api/send" && request.HttpMethod == "POST")
                {
                    await HandleSend(response, request);
                }
                else if (path == "/api/test-server" && request.HttpMethod == "POST")
                {
                    await HandleTestServer(response, request);
                }
                else if (path == "/api/status" && request.HttpMethod == "GET")
                {
                    await HandleStatus(response);
                }
                else
                {
                    var filePath = Path.Combine(
                        AppContext.BaseDirectory,
                        "WebGui",
                        path.TrimStart('/')
                    );

                    if (File.Exists(filePath))
                    {
                        await ServeStaticFile(response, filePath);
                    }
                    else
                    {
                        response.StatusCode = 404;
                        await SendJsonResponse(response, new { error = "Endpoint não encontrado" });
                    }
                }
            }
            catch (Exception ex)
            {
                response.StatusCode = 500;
                await SendJsonResponse(response, new { error = ex.Message });
            }
            finally
            {
                response.Close();
            }
        }

        private async Task HandleStatus(HttpListenerResponse response)
        {
            var status = new
            {
                status = _currentInventory != null ? "analisado" : "aguardando",
                data = _currentInventory != null ? _currentInventory.DataInventario : null
            };
            await SendJsonResponse(response, status);
        }

        private async Task HandleAnalyze(HttpListenerResponse response)
        {
            try
            {
                _currentInventory = await Task.Run(() => _collector.CollectHardwareInfo());

                await SendJsonResponse(response, new
                {
                    success = true,
                    message = "Análise concluída com sucesso",
                    hardware = new
                    {
                        equipamento = new
                        {
                            fabricante = _currentInventory.Equipamento?.Fabricante,
                            modelo = _currentInventory.Equipamento?.Modelo,
                            serial = _currentInventory.Equipamento?.NumeroSerie
                        },
                        cpu = new
                        {
                            modelo = _currentInventory.Processador?.Modelo,
                            nucleos = _currentInventory.Processador?.Nucleos,
                            threads = _currentInventory.Processador?.Threads
                        },
                        memoria = new
                        {
                            totalGB = _currentInventory.Memoria?.TotalGB,
                            modulos = _currentInventory.Memoria?.Modulos?.Count
                        },
                        discos = _currentInventory.Discos?.Select(d => new
                        {
                            tipo = d.Tipo,
                            tamanhoGB = d.TamanhoGB
                        }).ToList(),
                        sistema = _currentInventory.Sistema?.Nome,
                        arquitetura = _currentInventory.Sistema?.Arquitetura
                    }
                });
            }
            catch (Exception ex)
            {
                await SendJsonResponse(response, new
                {
                    success = false,
                    error = ex.Message,
                    message = "Execute como Administrador para obter análise completa"
                }, 500);
            }
        }

        private async Task HandleSave(HttpListenerResponse response, HttpListenerRequest request)
        {
            try
            {
                if (_currentInventory == null)
                {
                    await SendJsonResponse(response, new
                    {
                        success = false,
                        error = "Analise o equipamento primeiro"
                    }, 400);
                    return;
                }

                var body = await GetRequestBody(request);
                var patrimonial = JsonSerializer.Deserialize<PatrimonialData>(body);

                if (patrimonial != null)
                {
                    _currentInventory.Localizacao = patrimonial.Localizacao;
                    _currentInventory.Tombo = patrimonial.Tombo ?? "";
                    _currentInventory.Observacoes = patrimonial.Observacoes ?? "";
                }

                _fileService.SaveInventoryLocally(_currentInventory);

                await SendJsonResponse(response, new
                {
                    success = true,
                    message = "Inventário salvo localmente",
                    filename = $"inventario_{DateTime.Now:yyyyMMdd_HHmmss}.json"
                });
            }
            catch (Exception ex)
            {
                await SendJsonResponse(response, new
                {
                    success = false,
                    error = ex.Message
                }, 500);
            }
        }

        private async Task HandleSend(HttpListenerResponse response, HttpListenerRequest request)
        {
            try
            {
                if (_currentInventory == null)
                {
                    await SendJsonResponse(response, new
                    {
                        success = false,
                        error = "Analise o equipamento primeiro"
                    }, 400);
                    return;
                }

                var body = await GetRequestBody(request);
                var sendData = JsonSerializer.Deserialize<SendData>(body);

                if (sendData == null || string.IsNullOrEmpty(sendData.Servidor))
                {
                    await SendJsonResponse(response, new
                    {
                        success = false,
                        error = "Servidor não informado"
                    }, 400);
                    return;
                }

                if (string.IsNullOrEmpty(sendData.Localizacao) || sendData.Localizacao == "Outro")
                {
                    await SendJsonResponse(response, new
                    {
                        success = false,
                        error = "Localização é obrigatória"
                    }, 400);
                    return;
                }

                _currentInventory.Localizacao = sendData.Localizacao;
                _currentInventory.Tombo = sendData.Tombo ?? "";
                _currentInventory.Observacoes = sendData.Observacoes ?? "";

                var (success, tombo, error) = await _networkService.SendInventory(
                    sendData.Servidor,
                    sendData.Porta,
                    _currentInventory
                );

                if (success)
                {
                    await SendJsonResponse(response, new
                    {
                        success = true,
                        tombo = tombo,
                        message = "Inventário enviado com sucesso"
                    });
                }
                else
                {
                    await SendJsonResponse(response, new
                    {
                        success = false,
                        error = error,
                        message = "Falha no envio. Pode salvar localmente."
                    }, 500);
                }
            }
            catch (Exception ex)
            {
                await SendJsonResponse(response, new
                {
                    success = false,
                    error = ex.Message
                }, 500);
            }
        }

        private async Task HandleTestServer(HttpListenerResponse response, HttpListenerRequest request)
        {
            try
            {
                var body = await GetRequestBody(request);
                var data = JsonSerializer.Deserialize<ServerTestData>(body);

                if (data == null || string.IsNullOrEmpty(data.Servidor))
                {
                    await SendJsonResponse(response, new
                    {
                        success = false,
                        error = "Servidor não informado"
                    }, 400);
                    return;
                }

                var (success, version, error) = await _networkService.TestServerConnection(
                    data.Servidor,
                    data.Porta
                );

                await SendJsonResponse(response, new
                {
                    success = success,
                    version = version,
                    error = error,
                    message = success ? "Servidor conectado" : "Servidor não disponível"
                });
            }
            catch (Exception ex)
            {
                await SendJsonResponse(response, new
                {
                    success = false,
                    error = ex.Message
                }, 500);
            }
        }

        private async Task ServeHtml(HttpListenerResponse response)
        {
            var html = GetHtmlPage();
            var buffer = Encoding.UTF8.GetBytes(html);
            response.ContentType = "text/html; charset=utf-8";
            response.ContentLength64 = buffer.Length;
            await response.OutputStream.WriteAsync(buffer, 0, buffer.Length);
        }

        private async Task ServeStaticFile(HttpListenerResponse response, string filePath)
        {
            Console.WriteLine($"Arquivo: {filePath}");
            Console.WriteLine($"Existe: {File.Exists(filePath)}");
            if (!File.Exists(filePath))
            {
                response.StatusCode = 404;
                response.Close();
                return;
            }

            var buffer = await File.ReadAllBytesAsync(filePath);

            response.ContentType = Path.GetExtension(filePath) switch
            {
                ".html" => "text/html; charset=utf-8",
                ".css" => "text/css",
                ".js" => "application/javascript",
                _ => "application/octet-stream"
            };

            response.ContentLength64 = buffer.Length;

            await response.OutputStream.WriteAsync(buffer);
            response.Close();
        }

        private async Task SendJsonResponse(HttpListenerResponse response, object data, int statusCode = 200)
        {
            var json = JsonSerializer.Serialize(data, new JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });

            var buffer = Encoding.UTF8.GetBytes(json);
            response.ContentType = "application/json; charset=utf-8";
            response.ContentLength64 = buffer.Length;
            response.StatusCode = statusCode;
            await response.OutputStream.WriteAsync(buffer, 0, buffer.Length);
        }

        private async Task<string> GetRequestBody(HttpListenerRequest request)
        {
            using var reader = new StreamReader(request.InputStream, request.ContentEncoding);
            return await reader.ReadToEndAsync();
        }



        private string GetHtmlPage()
        {
            var path = Path.Combine(AppContext.BaseDirectory, "WebGui", "page.html");
            return File.ReadAllText(path);
        }

        private class PatrimonialData
        {
            public string Tombo { get; set; }
            public string Localizacao { get; set; }
            public string Observacoes { get; set; }
        }

        private class SendData
        {
            public string Servidor { get; set; }
            public int Porta { get; set; }
            public string Tombo { get; set; }
            public string Localizacao { get; set; }
            public string Observacoes { get; set; }
        }

        private class ServerTestData
        {
            public string Servidor { get; set; }
            public int Porta { get; set; }
        }
    }
}