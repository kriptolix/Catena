using System.Management;
using Agent.Models;

namespace Agent.Services
{
    public class WindowsHardwareCollector : IHardwareCollector
    {
        public HardwareInfo CollectHardwareInfo()
        {
            var info = new HardwareInfo();

            try
            {
                // Computer System
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_ComputerSystem"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        info.Equipamento = new Equipment
                        {
                            Fabricante = obj["Manufacturer"]?.ToString()?.Trim() ?? "N/A",
                            Modelo = obj["Model"]?.ToString()?.Trim() ?? "N/A"
                        };

                        info.Identificacao = new Identification
                        {
                            
UUID = "N/A" // Placeholder, will be filled later
                        };
                        break;
                    }
                }

                // BIOS
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_BIOS"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        info.BIOS = new Bios
                        {
                            Fabricante = obj["Manufacturer"]?.ToString()?.Trim() ?? "N/A",
                            Versao = obj["SMBIOSBIOSVersion"]?.ToString()?.Trim() ?? "N/A",
                            Data = obj["ReleaseDate"]?.ToString() ?? DateTime.Now.ToString("yyyy-MM-dd")
                        };

                        if (info.Equipamento != null && string.IsNullOrEmpty(info.Equipamento.NumeroSerie))
                        {
                            info.Equipamento.NumeroSerie = obj["SerialNumber"]?.ToString()?.Trim() ?? "N/A";
                        }
                        break;
                    }
                }

                // BaseBoard
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_BaseBoard"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        info.PlacaMae = new Motherboard
                        {
                            Fabricante = obj["Manufacturer"]?.ToString()?.Trim() ?? "N/A",
                            Modelo = obj["Product"]?.ToString()?.Trim() ?? "N/A",
                            NumeroSerie = obj["SerialNumber"]?.ToString()?.Trim() ?? "N/A"
                        };
                        break;
                    }
                }

                // UUID
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_ComputerSystemProduct"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        if (info.Identificacao != null)
                        {
                            info.Identificacao.UUID = obj["UUID"]?.ToString()?.Trim() ?? "N/A";
                        }
                        break;
                    }
                }

                // OS
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_OperatingSystem"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        info.Sistema = new SystemInfo
                        {
                            Nome = obj["Caption"]?.ToString()?.Trim() ?? "N/A",
                            Versao = obj["Version"]?.ToString()?.Trim() ?? "N/A",
                            Arquitetura = obj["OSArchitecture"]?.ToString()?.Trim() ?? "N/A"
                        };
                        break;
                    }
                }

                // CPU
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_Processor"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        info.Processador = new Processor
                        {
                            Fabricante = obj["Manufacturer"]?.ToString()?.Trim() ?? "N/A",
                            Modelo = obj["Name"]?.ToString()?.Trim() ?? "N/A",
                            Nucleos = ConvertToInt32(obj["NumberOfCores"]),
                            Threads = ConvertToInt32(obj["NumberOfLogicalProcessors"]),
                            ClockMaximoMHz = ConvertToInt32(obj["MaxClockSpeed"])
                        };
                        break;
                    }
                }

                // Memory
                var memoryModules = new List<MemoryModule>();
                double totalRAM = 0;

                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_PhysicalMemory"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        var capacity = ConvertToDouble(obj["Capacity"]);
                        totalRAM += capacity;

                        memoryModules.Add(new MemoryModule
                        {
                            Fabricante = obj["Manufacturer"]?.ToString()?.Trim() ?? "N/A",
                            CapacidadeGB = Math.Round(capacity / 1073741824, 2),
                            VelocidadeMHz = ConvertToInt32(obj["Speed"]),
                            Tipo = GetDDRType(ConvertToInt32(obj["SMBIOSMemoryType"])),
                            PartNumber = obj["PartNumber"]?.ToString()?.Trim() ?? "N/A",
                            NumeroSerie = obj["SerialNumber"]?.ToString()?.Trim() ?? "N/A",
                            Slot = obj["DeviceLocator"]?.ToString()?.Trim() ?? "N/A"
                        });
                    }
                }

                info.Memoria = new MemoryInfo
                {
                    TotalGB = Math.Round(totalRAM / 1073741824, 2),
                    Modulos = memoryModules
                };

                // Disks
                var disks = new List<Disk>();
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_DiskDrive"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        var model = obj["Model"]?.ToString() ?? "";
                        var tipo = "HD";
                        if (model.Contains("NVMe", StringComparison.OrdinalIgnoreCase))
                            tipo = "NVMe";
                        else if (model.Contains("SSD", StringComparison.OrdinalIgnoreCase))
                            tipo = "SSD";

                        disks.Add(new Disk
                        {
                            Modelo = model.Trim(),
                            Fabricante = obj["Manufacturer"]?.ToString()?.Trim() ?? "N/A",
                            Interface = obj["InterfaceType"]?.ToString()?.Trim() ?? "N/A",
                            TamanhoGB = Math.Round(ConvertToDouble(obj["Size"]) / 1073741824, 2),
                            Serial = obj["SerialNumber"]?.ToString()?.Trim() ?? "N/A",
                            Tipo = tipo
                        });
                    }
                }
                info.Discos = disks;

                // Video
                var videos = new List<VideoController>();
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_VideoController"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        var ram = ConvertToDouble(obj["AdapterRAM"]);
                        videos.Add(new VideoController
                        {
                            Modelo = obj["Name"]?.ToString()?.Trim() ?? "N/A",
                            MemoriaGB = ram > 0 ? Math.Round(ram / 1073741824, 2) : 0
                        });
                    }
                }
                info.Video = videos;

                // Network
                var nics = new List<NetworkAdapter>();
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_NetworkAdapter WHERE PhysicalAdapter = True"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        var speed = ConvertToInt64(obj["Speed"]);
                        nics.Add(new NetworkAdapter
                        {
                            Modelo = obj["Name"]?.ToString()?.Trim() ?? "N/A",
                            MAC = obj["MACAddress"]?.ToString()?.Trim() ?? "N/A",
                            VelocidadeMbps = speed > 0 ? speed / 1000000 : 0
                        });
                    }
                }
                info.Rede = nics;

                info.DataInventario = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

                return info;
            }
            catch (Exception ex)
            {
                throw new Exception($"Erro ao coletar informações de hardware: {ex.Message}", ex);
            }
        }

        private string GetDDRType(int code)
        {
            return code switch
            {
                20 => "DDR",
                21 => "DDR2",
                24 => "DDR3",
                26 => "DDR4",
                34 => "DDR5",
                _ => $"Desconhecido ({code})"
            };
        }

        private int ConvertToInt32(object value)
        {
            if (value == null) return 0;
            if (int.TryParse(value.ToString(), out int result))
                return result;
            return 0;
        }

        private long ConvertToInt64(object value)
        {
            if (value == null) return 0;
            if (long.TryParse(value.ToString(), out long result))
                return result;
            return 0;
        }

        private double ConvertToDouble(object value)
        {
            if (value == null) return 0;
            if (double.TryParse(value.ToString(), out double result))
                return result;
            return 0;
        }

        private DateTime ConvertToDateTime(object value)
        {
            if (value == null) return DateTime.Now;
            if (DateTime.TryParse(value.ToString(), out DateTime result))
                return result;
            return DateTime.Now;
        }
    }
}