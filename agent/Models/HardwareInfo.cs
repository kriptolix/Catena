namespace Agent.Models
{
    public class HardwareInfo
    {
        public Identification? Identification { get; set; }
        public Equipment? Equipment { get; set; }
        public Bios? BIOS { get; set; }
        public Motherboard? Motherboard { get; set; }
        public EquipmentSystem? EquipmentSystem { get; set; }
        public Processor? Processor { get; set; }
        public Memory? Memory { get; set; }
        public List<Disk>? Disk { get; set; }
        public List<GPU>? GPU { get; set; }
        public List<Network>? Network { get; set; }
        public string? AssetTag { get; set; }
        public string Location { get; set; } = "";       
        public string? Annotation { get; set; }
        public string? Date { get; set; }
    }

    public class Identification
    {
        public string? UUID { get; set; }      
        
    }

    public class Equipment
    {
        public string? Manufacturer { get; set; }
        public string? Model { get; set; }
        public string? SerialNumber { get; set; }
    }

    public class Bios
    {
        public string? Manufacturer { get; set; }
        public string? Version { get; set; }
        public string? Date { get; set; }
    }

    public class Motherboard
    {
        public string? Manufacturer { get; set; }
        public string? Model { get; set; }
        public string? SerialNumber { get; set; }
    }

    public class EquipmentSystem
    {
        public string? Name { get; set; }
        public string? Version { get; set; }
        public string? Architecture { get; set; }        
    }

    public class Processor
    {
        public string? Model { get; set; }
        public string? Manufacturer { get; set; }
        public int Cores { get; set; }
        public int Threads { get; set; }
        public int ClockMHz { get; set; }
    }

    public class Memory
    {
        public double TotalGB { get; set; }
        public List<MemoryModule>? Modules { get; set; }
    }

    public class MemoryModule
    {
        public string? Manufacturer { get; set; }
        public double SizeGB { get; set; }
        public int SpeedMHz { get; set; }
        public string? Type { get; set; }
        public string? PartNumber { get; set; }
        public string? SerialNumber { get; set; }
        public string? Slot { get; set; }
    }

    public class Disk
    {
        public string? Model { get; set; }
        public string? Manufacturer { get; set; }
        public string? Interface { get; set; }
        public double SizeGB { get; set; }
        public string? SerialNumber { get; set; }
        public string? Type { get; set; }
    }

    public class GPU
    {
        public string? Model { get; set; }
        public double MemoryGB { get; set; }
    }

    public class Network
    {
        public string? Model { get; set; }
        public string? MAC { get; set; }
        public long SpeedMbps { get; set; }
    }
}