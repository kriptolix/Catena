using System.Runtime.InteropServices;
using System.Diagnostics;
using Agent.Services;


namespace DataCollector
{
    class Program
    {
        private static WebServerService _webServer;

        static void Main(string[] args)
        {
            //Console.Clear();
            Console.WriteLine();
            Console.WriteLine("Starting Collector...");       
                     
            // Iniciar servidor web
            _webServer = new WebServerService();
            _webServer.Start(54322);

            // Abrir navegador automaticamente
            OpenBrowser("http://localhost:54322");

            Console.WriteLine();
            Console.WriteLine("Servidor web iniciado em: http://localhost:54322");
            Console.WriteLine("Pressione CTRL+C para encerrar");
            Console.WriteLine();

            // Aguardar interrupção
            var cts = new CancellationTokenSource();
            Console.CancelKeyPress += (s, e) =>
            {
                e.Cancel = true;
                cts.Cancel();
            };

            try
            {
                cts.Token.WaitHandle.WaitOne();
            }
            catch (OperationCanceledException)
            {
                // Esperado
            }

            Console.WriteLine();
            Console.WriteLine("Encerrando servidor...");
            _webServer.Stop();
            Console.WriteLine("Servidor encerrado com sucesso!");
        }

        static void OpenBrowser(string url)
        {
            try
            {
                if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
                {
                    Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
                }
                else if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
                {
                    Process.Start("xdg-open", url);
                }
                else if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
                {
                    Process.Start("open", url);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Não foi possível abrir o navegador: {ex.Message}");
                Console.WriteLine($"   Acesse manualmente: {url}");
            }
        }
    }
}
