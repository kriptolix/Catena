namespace Agent.Models
{
    public class HardwareInfo
    {
        public Identification? Identificacao { get; set; }
        public Equipment? Equipamento { get; set; }
        public Bios? BIOS { get; set; }
        public Motherboard? PlacaMae { get; set; }
        public SystemInfo? Sistema { get; set; }
        public Processor? Processador { get; set; }
        public MemoryInfo? Memoria { get; set; }
        public List<Disk>? Discos { get; set; }
        public List<VideoController>? Video { get; set; }
        public List<NetworkAdapter>? Rede { get; set; }
        public string? Tombo { get; set; }
        public string Localizacao { get; set; } = "";       
        public string? Observacoes { get; set; }
        public string? DataInventario { get; set; }
    }

    public class Identification
    {
        public string? UUID { get; set; }      
        
    }

    public class Equipment
    {
        public string? Fabricante { get; set; }
        public string? Modelo { get; set; }
        public string? NumeroSerie { get; set; }
    }

    public class Bios
    {
        public string? Fabricante { get; set; }
        public string? Versao { get; set; }
        public string? Data { get; set; }
    }

    public class Motherboard
    {
        public string? Fabricante { get; set; }
        public string? Modelo { get; set; }
        public string? NumeroSerie { get; set; }
    }

    public class SystemInfo
    {
        public string? Nome { get; set; }
        public string? Versao { get; set; }
        public string? Arquitetura { get; set; }        
    }

    public class Processor
    {
        public string? Modelo { get; set; }
        public string? Fabricante { get; set; }
        public int Nucleos { get; set; }
        public int Threads { get; set; }
        public int ClockMaximoMHz { get; set; }
    }

    public class MemoryInfo
    {
        public double TotalGB { get; set; }
        public List<MemoryModule>? Modulos { get; set; }
    }

    public class MemoryModule
    {
        public string? Fabricante { get; set; }
        public double CapacidadeGB { get; set; }
        public int VelocidadeMHz { get; set; }
        public string? Tipo { get; set; }
        public string? PartNumber { get; set; }
        public string? NumeroSerie { get; set; }
        public string? Slot { get; set; }
    }

    public class Disk
    {
        public string? Modelo { get; set; }
        public string? Fabricante { get; set; }
        public string? Interface { get; set; }
        public double TamanhoGB { get; set; }
        public string? Serial { get; set; }
        public string? Tipo { get; set; }
    }

    public class VideoController
    {
        public string? Modelo { get; set; }
        public double MemoriaGB { get; set; }
    }

    public class NetworkAdapter
    {
        public string? Modelo { get; set; }
        public string? MAC { get; set; }
        public long VelocidadeMbps { get; set; }
    }
}