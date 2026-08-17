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
                        info.Equipment = new Equipment
                        {
                            Manufacturer = obj["Manufacturer"]?.ToString()?.Trim() ?? "N/A",
                            Model = obj["Model"]?.ToString()?.Trim() ?? "N/A"
                        };

                        info.Identification = new Identification
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
                            Manufacturer = obj["Manufacturer"]?.ToString()?.Trim() ?? "N/A",
                            Version = obj["SMBIOSBIOSVersion"]?.ToString()?.Trim() ?? "N/A",
                            Date = obj["ReleaseDate"]?.ToString() ?? DateTime.Now.ToString("yyyy-MM-dd")
                        };

                        if (info.Equipment != null && string.IsNullOrEmpty(info.Equipment.SerialNumber))
                        {
                            info.Equipment.SerialNumber = obj["SerialNumber"]?.ToString()?.Trim() ?? "N/A";
                        }
                        break;
                    }
                }

                // BaseBoard
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_BaseBoard"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        info.Motherboard = new Motherboard
                        {
                            Manufacturer = obj["Manufacturer"]?.ToString()?.Trim() ?? "N/A",
                            Model = obj["Product"]?.ToString()?.Trim() ?? "N/A",
                            SerialNumber = obj["SerialNumber"]?.ToString()?.Trim() ?? "N/A"
                        };
                        break;
                    }
                }

                // UUID
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_ComputerSystemProduct"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        if (info.Identification != null)
                        {
                            info.Identification.UUID = obj["UUID"]?.ToString()?.Trim() ?? "N/A";
                        }
                        break;
                    }
                }

                // OS
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_OperatingSystem"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        info.EquipmentSystem = new EquipmentSystem
                        {
                            Name = obj["Caption"]?.ToString()?.Trim() ?? "N/A",
                            Version = obj["Version"]?.ToString()?.Trim() ?? "N/A",
                            Architecture = obj["OSArchitecture"]?.ToString()?.Trim() ?? "N/A"
                        };
                        break;
                    }
                }

                // CPU
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_Processor"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        info.Processor = new Processor
                        {
                            Manufacturer = obj["Manufacturer"]?.ToString()?.Trim() ?? "N/A",
                            Model = obj["Name"]?.ToString()?.Trim() ?? "N/A",
                            Cores = ConvertToInt32(obj["NumberOfCores"]),
                            Threads = ConvertToInt32(obj["NumberOfLogicalProcessors"]),
                            ClockMHz = ConvertToInt32(obj["MaxClockSpeed"])
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
                            Manufacturer = obj["Manufacturer"]?.ToString()?.Trim() ?? "N/A",
                            SizeGB = Math.Round(capacity / 1073741824, 2),
                            SpeedMHz = ConvertToInt32(obj["Speed"]),
                            Type = GetDDRType(ConvertToInt32(obj["SMBIOSMemoryType"])),
                            PartNumber = obj["PartNumber"]?.ToString()?.Trim() ?? "N/A",
                            SerialNumber = obj["SerialNumber"]?.ToString()?.Trim() ?? "N/A",
                            Slot = obj["DeviceLocator"]?.ToString()?.Trim() ?? "N/A"
                        });
                    }
                }

                info.Memory = new Memory
                {
                    TotalGB = Math.Round(totalRAM / 1073741824, 2),
                    Modules = memoryModules
                };

                // Disks
                var disks = new List<Disk>();
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_DiskDrive"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        var Model = obj["Model"]?.ToString() ?? "";
                        var tipo = "HD";
                        if (Model.Contains("NVMe", StringComparison.OrdinalIgnoreCase))
                            tipo = "NVMe";
                        else if (Model.Contains("SSD", StringComparison.OrdinalIgnoreCase))
                            tipo = "SSD";

                        disks.Add(new Disk
                        {
                            Model = Model.Trim(),
                            Manufacturer = obj["Manufacturer"]?.ToString()?.Trim() ?? "N/A",
                            Interface = obj["InterfaceType"]?.ToString()?.Trim() ?? "N/A",
                            SizeGB = Math.Round(ConvertToDouble(obj["Size"]) / 1073741824, 2),
                            SerialNumber = obj["SerialNumber"]?.ToString()?.Trim() ?? "N/A",
                            Type = tipo
                        });
                    }
                }
                info.Disk = disks;

                // Video
                var videos = new List<GPU>();
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_GPU"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        var ram = ConvertToDouble(obj["AdapterRAM"]);
                        videos.Add(new GPU
                        {
                            Model = obj["Name"]?.ToString()?.Trim() ?? "N/A",
                            MemoryGB = ram > 0 ? Math.Round(ram / 1073741824, 2) : 0
                        });
                    }
                }
                info.GPU = videos;

                // Network
                var nics = new List<Network>();
                using (var searcher = new ManagementObjectSearcher("SELECT * FROM Win32_Network WHERE PhysicalAdapter = True"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        var speed = ConvertToInt64(obj["Speed"]);
                        nics.Add(new Network
                        {
                            Model = obj["Name"]?.ToString()?.Trim() ?? "N/A",
                            MAC = obj["MACAddress"]?.ToString()?.Trim() ?? "N/A",
                            SpeedMbps = speed > 0 ? speed / 1000000 : 0
                        });
                    }
                }
                info.Network = nics;

                info.Date = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

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