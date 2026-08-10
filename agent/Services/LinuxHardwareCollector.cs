using System.Globalization;
using System.Runtime.InteropServices;
using System.Text;
using Agent.Models;

namespace Agent.Services
{
    public class LinuxHardwareCollector : IHardwareCollector
    {
        private const string DmiPath = "/sys/firmware/dmi/tables/DMI";
        private const string DmiEntryPoint = "/sys/firmware/dmi/tables/smbios_entry_point";

        public HardwareInfo CollectHardwareInfo()
        {
            try
            {
                var info = new HardwareInfo();

                // =====================================================
                // SMBIOS / DMI - FONTE PRINCIPAL
                // =====================================================

                var dmi = TryReadDmi();

                if (dmi != null)
                {
                    CollectComputer(dmi, info);
                    CollectBios(dmi, info);
                    CollectMotherboard(dmi, info);
                    CollectProcessor(dmi, info);
                    CollectMemory(dmi, info);
                    CollectVideo(dmi, info);
                    CollectNetwork(dmi, info);
                }

                // =====================================================
                // FALLBACKS
                // =====================================================

                CollectOperatingSystem(info);

                if (IsEmpty(info.Equipamento))
                    CollectComputerFromSys(info);

                if (IsEmpty(info.Identificacao))
                    CollectIdentificationFromSys(info);

                if (IsEmpty(info.BIOS))
                    CollectBiosFromSys(info);

                if (IsEmpty(info.PlacaMae))
                    CollectMotherboardFromSys(info);

                if (IsEmpty(info.Processador))
                    CollectProcessorFromProc(info);

                if (info.Memoria == null ||
                    info.Memoria.TotalGB <= 0)
                {
                    CollectMemoryFromProc(info);
                }

                if (info.Discos == null ||
                    info.Discos.Count == 0)
                {
                    info.Discos = CollectDisksFromSys();
                }

                if (info.Video == null ||
                    info.Video.Count == 0)
                {
                    info.Video = CollectVideoFromSys();
                }

                if (info.Rede == null ||
                    info.Rede.Count == 0)
                {
                    info.Rede = CollectNetworkFromSys();
                }

                info.DataInventario =
                    DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

                return info;
            }
            catch (Exception ex)
            {
                throw new Exception(
                    $"Erro ao coletar informações de hardware: {ex.Message}",
                    ex);
            }
        }

        // =============================================================
        // SMBIOS
        // =============================================================

        private List<DmiRecord>? TryReadDmi()
        {
            try
            {
                if (!File.Exists(DmiPath))
                    return null;

                var data = File.ReadAllBytes(DmiPath);

                if (data.Length < 4)
                    return null;

                return ParseDmi(data);
            }
            catch
            {
                return null;
            }
        }

        private List<DmiRecord> ParseDmi(byte[] data)
        {
            var records = new List<DmiRecord>();

            int offset = 0;

            while (offset + 4 <= data.Length)
            {
                byte type = data[offset];
                byte length = data[offset + 1];

                if (length < 4 ||
                    offset + length > data.Length)
                {
                    break;
                }

                var record = new DmiRecord
                {
                    Type = type,
                    Length = length,
                    Data = data,
                    Offset = offset,
                    Strings = ReadDmiStrings(
                        data,
                        offset + length)
                };

                records.Add(record);

                if (type == 127)
                    break;

                int next = offset + length;

                while (next + 1 < data.Length)
                {
                    if (data[next] == 0 &&
                        data[next + 1] == 0)
                    {
                        next += 2;
                        break;
                    }

                    next++;
                }

                if (next <= offset)
                    break;

                offset = next;
            }

            return records;
        }

        // =============================================================
        // COMPUTER - SMBIOS TYPE 1
        // =============================================================

        private void CollectComputer(
            List<DmiRecord> records,
            HardwareInfo info)
        {
            var record = records.FirstOrDefault(x => x.Type == 1);

            if (record == null)
                return;

            info.Equipamento = new Equipment
            {
                Fabricante = record.GetString(4),
                Modelo = record.GetString(5),
                NumeroSerie = record.GetString(7)
            };

            info.Identificacao = new Identification
            {
                UUID = record.GetUuid(8)
            };
        }

        // =============================================================
        // BIOS - SMBIOS TYPE 0
        // =============================================================

        private void CollectBios(
            List<DmiRecord> records,
            HardwareInfo info)
        {
            var record = records.FirstOrDefault(x => x.Type == 0);

            if (record == null)
                return;

            info.BIOS = new Bios
            {
                Fabricante = record.GetString(4),
                Versao = record.GetString(5),
                Data = record.GetString(8)
            };
        }

        // =============================================================
        // MOTHERBOARD - SMBIOS TYPE 2
        // =============================================================

        private void CollectMotherboard(
            List<DmiRecord> records,
            HardwareInfo info)
        {
            var record = records.FirstOrDefault(x => x.Type == 2);

            if (record == null)
                return;

            info.PlacaMae = new Motherboard
            {
                Fabricante = record.GetString(4),
                Modelo = record.GetString(5),
                NumeroSerie = record.GetString(7)
            };
        }

        // =============================================================
        // CPU - SMBIOS TYPE 4
        // =============================================================

        private void CollectProcessor(
            List<DmiRecord> records,
            HardwareInfo info)
        {
            var record = records.FirstOrDefault(x => x.Type == 4);

            if (record == null)
                return;

            int cores = 0;
            int threads = 0;
            int clock = 0;

            // Core Count
            if (record.Length >= 0x1B)
                cores = record.GetByte(0x17);

            // Thread Count
            if (record.Length >= 0x23)
                threads = record.GetByte(0x22);

            // Current Speed
            if (record.Length >= 0x16)
                clock = record.GetUInt16(0x16);

            // Max Speed
            if (record.Length >= 0x15)
            {
                var maxSpeed = record.GetUInt16(0x14);

                if (maxSpeed > 0)
                    clock = maxSpeed;
            }

            info.Processador = new Processor
            {
                Fabricante = record.GetString(7),
                Modelo = record.GetString(5),
                Nucleos = cores,
                Threads = threads,
                ClockMaximoMHz = clock
            };
        }

        // =============================================================
        // MEMORY - SMBIOS TYPE 17
        // =============================================================

        private void CollectMemory(
            List<DmiRecord> records,
            HardwareInfo info)
        {
            var memoryRecords = records
                .Where(x => x.Type == 17)
                .ToList();

            if (memoryRecords.Count == 0)
                return;

            var modules = new List<MemoryModule>();

            foreach (var record in memoryRecords)
            {
                if (record.Length < 0x15)
                    continue;

                var sizeRaw = record.GetUInt16(0x0C);

                // 0x0000 = no module installed
                // 0xFFFF = unknown
                if (sizeRaw == 0 ||
                    sizeRaw == 0xFFFF)
                {
                    continue;
                }

                double capacityBytes;

                if (sizeRaw == 0x7FFF &&
                    record.Length >= 0x20)
                {
                    var extendedSize =
                        record.GetUInt32(0x1C);

                    capacityBytes =
                        extendedSize * 1024.0 * 1024.0;
                }
                else
                {
                    bool megabytes =
                        (sizeRaw & 0x8000) != 0;

                    int value =
                        sizeRaw & 0x7FFF;

                    capacityBytes = megabytes
                        ? value * 1024.0 * 1024.0
                        : value * 1024.0;
                }

                if (capacityBytes <= 0)
                    continue;

                var memoryType =
                    record.GetByte(0x12);

                var speed = record.Length >= 0x16
                    ? record.GetUInt16(0x15)
                    : 0;

                modules.Add(new MemoryModule
                {
                    Fabricante = record.GetString(0x17),
                    CapacidadeGB = Math.Round(
                        capacityBytes / 1073741824.0,
                        2),
                    VelocidadeMHz = speed,
                    Tipo = GetDDRType(memoryType),
                    PartNumber = record.GetString(0x1A),
                    NumeroSerie = record.GetString(0x18),
                    Slot = record.GetString(0x10)
                });
            }

            if (modules.Count == 0)
                return;

            info.Memoria = new MemoryInfo
            {
                TotalGB = Math.Round(
                    modules.Sum(x => x.CapacidadeGB),
                    2),
                Modulos = modules
            };
        }

        // =============================================================
        // VIDEO
        // =============================================================

        private void CollectVideo(
            List<DmiRecord> records,
            HardwareInfo info)
        {
            /*
             * SMBIOS Type 10 / Type 41 pode identificar
             * dispositivos onboard, incluindo vídeo.
             *
             * Porém, a identificação comercial da GPU costuma
             * ser melhor através de PCI/sysfs.
             */

            var videos = new List<VideoController>();

            foreach (var record in records.Where(
                x => x.Type == 41))
            {
                var name = record.GetString(4);

                if (string.IsNullOrWhiteSpace(name))
                    continue;

                if (name.Contains(
                    "video",
                    StringComparison.OrdinalIgnoreCase) ||
                    name.Contains(
                    "graphics",
                    StringComparison.OrdinalIgnoreCase) ||
                    name.Contains(
                    "vga",
                    StringComparison.OrdinalIgnoreCase))
                {
                    videos.Add(new VideoController
                    {
                        Modelo = name,
                        MemoriaGB = 0
                    });
                }
            }

            if (videos.Count > 0)
                info.Video = videos;
        }

        // =============================================================
        // NETWORK
        // =============================================================

        private void CollectNetwork(
            List<DmiRecord> records,
            HardwareInfo info)
        {
            var adapters = new List<NetworkAdapter>();

            foreach (var record in records.Where(
                x => x.Type == 41))
            {
                var name = record.GetString(4);

                if (string.IsNullOrWhiteSpace(name))
                    continue;

                if (name.Contains(
                    "ethernet",
                    StringComparison.OrdinalIgnoreCase) ||
                    name.Contains(
                    "network",
                    StringComparison.OrdinalIgnoreCase) ||
                    name.Contains(
                    "lan",
                    StringComparison.OrdinalIgnoreCase))
                {
                    adapters.Add(new NetworkAdapter
                    {
                        Modelo = name,
                        MAC = "N/A",
                        VelocidadeMbps = 0
                    });
                }
            }

            if (adapters.Count > 0)
                info.Rede = adapters;
        }

        // =============================================================
        // OS - /etc/os-release + Runtime
        // =============================================================

        private void CollectOperatingSystem(
            HardwareInfo info)
        {
            var values = new Dictionary<string, string>(
                StringComparer.OrdinalIgnoreCase);

            try
            {
                if (File.Exists("/etc/os-release"))
                {
                    foreach (var line in File.ReadAllLines(
                        "/etc/os-release"))
                    {
                        if (string.IsNullOrWhiteSpace(line) ||
                            line.StartsWith("#"))
                            continue;

                        var index = line.IndexOf('=');

                        if (index <= 0)
                            continue;

                        var key = line[..index];

                        var value =
                            line[(index + 1)..].Trim('"');

                        values[key] = value;
                    }
                }
            }
            catch
            {
            }

            values.TryGetValue(
                "PRETTY_NAME",
                out var prettyName);

            values.TryGetValue(
                "VERSION_ID",
                out var version);

            info.Sistema = new SystemInfo
            {
                Nome = string.IsNullOrWhiteSpace(prettyName)
                    ? "Linux"
                    : prettyName,

                Versao = string.IsNullOrWhiteSpace(version)
                    ? "N/A"
                    : version,

                Arquitetura =
                    RuntimeInformation.OSArchitecture.ToString()
            };
        }

        // =============================================================
        // FALLBACK: COMPUTER /sys
        // =============================================================

        private void CollectComputerFromSys(
            HardwareInfo info)
        {
            var manufacturer = ReadSys(
                "sys_vendor");

            var model = ReadSys(
                "product_name");

            var serial = ReadSys(
                "product_serial");

            if (manufacturer == "N/A" &&
                model == "N/A" &&
                serial == "N/A")
                return;

            info.Equipamento = new Equipment
            {
                Fabricante = manufacturer,
                Modelo = model,
                NumeroSerie = serial
            };
        }

        // =============================================================
        // FALLBACK: UUID
        // =============================================================

        private void CollectIdentificationFromSys(
            HardwareInfo info)
        {
            var uuid = ReadSys("product_uuid");

            if (uuid == "")
                return;

            info.Identificacao = new Identification
            {
                UUID = uuid
            };
        }

        // =============================================================
        // FALLBACK: BIOS
        // =============================================================

        private void CollectBiosFromSys(
            HardwareInfo info)
        {
            var manufacturer = ReadSys("bios_vendor");
            var version = ReadSys("bios_version");
            var date = ReadSys("bios_date");

            if (manufacturer == "N/A" &&
                version == "N/A" &&
                date == "N/A")
                return;

            info.BIOS = new Bios
            {
                Fabricante = manufacturer,
                Versao = version,
                Data = date
            };
        }

        // =============================================================
        // FALLBACK: MOTHERBOARD
        // =============================================================

        private void CollectMotherboardFromSys(
            HardwareInfo info)
        {
            var manufacturer = ReadSys("board_vendor");
            var model = ReadSys("board_name");
            var serial = ReadSys("board_serial");

            if (manufacturer == "N/A" &&
                model == "N/A" &&
                serial == "N/A")
                return;

            info.PlacaMae = new Motherboard
            {
                Fabricante = manufacturer,
                Modelo = model,
                NumeroSerie = serial
            };
        }

        // =============================================================
        // FALLBACK: CPU /proc
        // =============================================================

        private void CollectProcessorFromProc(
            HardwareInfo info)
        {
            try
            {
                if (!File.Exists("/proc/cpuinfo"))
                    return;

                var lines = File.ReadAllLines(
                    "/proc/cpuinfo");

                string manufacturer = "N/A";
                string model = "N/A";
                int threads = 0;
                int cores = 0;
                int clock = 0;

                foreach (var line in lines)
                {
                    if (line.StartsWith("vendor_id"))
                    {
                        manufacturer =
                            GetProcValue(line);
                    }

                    if (line.StartsWith("model name"))
                    {
                        model =
                            GetProcValue(line);
                    }

                    if (line.StartsWith("cpu MHz") &&
                        clock == 0)
                    {
                        var value =
                            GetProcValue(line);

                        if (double.TryParse(
                            value,
                            NumberStyles.Float,
                            CultureInfo.InvariantCulture,
                            out var mhz))
                        {
                            clock = (int)mhz;
                        }
                    }

                    if (line.StartsWith("processor"))
                        threads++;
                }

                if (threads == 0)
                    threads = Environment.ProcessorCount;

                cores = CountPhysicalCores(lines);

                if (cores == 0)
                    cores = threads;

                info.Processador = new Processor
                {
                    Fabricante = manufacturer,
                    Modelo = model,
                    Nucleos = cores,
                    Threads = threads,
                    ClockMaximoMHz = clock
                };
            }
            catch
            {
            }
        }

        // =============================================================
        // FALLBACK: MEMORY /proc
        // =============================================================

        private void CollectMemoryFromProc(
            HardwareInfo info)
        {
            try
            {
                if (!File.Exists("/proc/meminfo"))
                    return;

                foreach (var line in File.ReadAllLines(
                    "/proc/meminfo"))
                {
                    if (!line.StartsWith("MemTotal:"))
                        continue;

                    var parts = line.Split(
                        ' ',
                        StringSplitOptions.RemoveEmptyEntries);

                    if (parts.Length < 2)
                        return;

                    if (!long.TryParse(
                        parts[1],
                        out var kb))
                    {
                        return;
                    }

                    info.Memoria = new MemoryInfo
                    {
                        TotalGB = Math.Round(
                            kb / 1048576.0,
                            2),

                        Modulos = new List<MemoryModule>()
                    };

                    return;
                }
            }
            catch
            {
            }
        }

        // =============================================================
        // FALLBACK: DISKS /sys
        // =============================================================

        private List<Disk> CollectDisksFromSys()
        {
            var disks = new List<Disk>();

            try
            {
                if (!Directory.Exists("/sys/block"))
                    return disks;

                foreach (var path in Directory.GetDirectories(
                    "/sys/block"))
                {
                    var device = Path.GetFileName(path);

                    if (device.StartsWith("loop") ||
                        device.StartsWith("ram") ||
                        device.StartsWith("zram") ||
                        device.StartsWith("sr"))
                        continue;

                    var sectors = ReadLong(
                        Path.Combine(path, "size"));

                    var blockSize = ReadLong(
                        Path.Combine(
                            path,
                            "queue/logical_block_size"));

                    if (blockSize <= 0)
                        blockSize = 512;

                    var size =
                        sectors * blockSize;

                    var model = ReadFirstAvailable(
                        Path.Combine(
                            path,
                            "device/model"));

                    var vendor = ReadFirstAvailable(
                        Path.Combine(
                            path,
                            "device/vendor"));

                    var serial = ReadFirstAvailable(
                        Path.Combine(
                            path,
                            "device/serial"));

                    var rotational = ReadFirstAvailable(
                        Path.Combine(
                            path,
                            "queue/rotational"));

                    disks.Add(new Disk
                    {
                        Modelo = model == "N/A"
                            ? device
                            : model,

                        Fabricante = vendor,

                        Interface = GetDiskInterface(
                            device),

                        TamanhoGB = Math.Round(
                            size / 1073741824.0,
                            2),

                        Serial = serial,

                        Tipo = rotational == "0"
                            ? "SSD"
                            : rotational == "1"
                                ? "HD"
                                : "N/A"
                    });
                }
            }
            catch
            {
            }

            return disks;
        }

        // =============================================================
        // FALLBACK: VIDEO /sys
        // =============================================================

        private List<VideoController> CollectVideoFromSys()
        {
            var videos = new List<VideoController>();

            try
            {
                if (!Directory.Exists("/sys/class/drm"))
                    return videos;

                foreach (var path in Directory.GetDirectories(
                    "/sys/class/drm",
                    "card*"))
                {
                    var name = Path.GetFileName(path);

                    if (name.Contains("-"))
                        continue;

                    var device = Path.Combine(
                        path,
                        "device");

                    var vendor = ReadFirstAvailable(
                        Path.Combine(
                            device,
                            "vendor"));

                    var deviceId = ReadFirstAvailable(
                        Path.Combine(
                            device,
                            "device"));

                    videos.Add(new VideoController
                    {
                        Modelo =
                            $"{GetGpuVendor(vendor)} ({deviceId})",

                        MemoriaGB = 0
                    });
                }
            }
            catch
            {
            }

            return videos;
        }

        // =============================================================
        // FALLBACK: NETWORK /sys
        // =============================================================

        private List<NetworkAdapter> CollectNetworkFromSys()
        {
            var adapters = new List<NetworkAdapter>();

            try
            {
                if (!Directory.Exists("/sys/class/net"))
                    return adapters;

                foreach (var path in Directory.GetDirectories(
                    "/sys/class/net"))
                {
                    var name = Path.GetFileName(path);

                    if (name == "lo")
                        continue;

                    var device =
                        Path.Combine(path, "device");

                    if (!Directory.Exists(device))
                        continue;

                    var mac = ReadFirstAvailable(
                        Path.Combine(
                            path,
                            "address"));

                    var speed = ReadLong(
                        Path.Combine(
                            path,
                            "speed"));

                    adapters.Add(new NetworkAdapter
                    {
                        Modelo = name,
                        MAC = mac,
                        VelocidadeMbps =
                            speed > 0
                                ? speed
                                : 0
                    });
                }
            }
            catch
            {
            }

            return adapters;
        }

        // =============================================================
        // HELPERS
        // =============================================================

        private string ReadSys(string name)
        {
            return ReadFile(
                Path.Combine(
                    "/sys/class/dmi/id",
                    name));
        }

        private string ReadFile(string path)
        {
            try
            {
                if (!File.Exists(path))
                    return "N/A";

                var value =
                    File.ReadAllText(path).Trim();

                return string.IsNullOrWhiteSpace(value)
                    ? "N/A"
                    : value;
            }
            catch
            {
                return "N/A";
            }
        }

        private string ReadFirstAvailable(
            params string[] paths)
        {
            foreach (var path in paths)
            {
                var value = ReadFile(path);

                if (value != "N/A")
                    return value;
            }

            return "N/A";
        }

        private long ReadLong(string path)
        {
            var value = ReadFile(path);

            return long.TryParse(
                value,
                out var result)
                ? result
                : 0;
        }

        private string GetProcValue(string line)
        {
            var index = line.IndexOf(':');

            return index < 0
                ? "N/A"
                : line[(index + 1)..].Trim();
        }

        private int CountPhysicalCores(
            string[] lines)
        {
            var cores = new HashSet<string>();

            string physicalId = "";
            string coreId = "";

            foreach (var line in lines)
            {
                if (line.StartsWith("physical id"))
                {
                    physicalId =
                        GetProcValue(line);
                }
                else if (line.StartsWith("core id"))
                {
                    coreId =
                        GetProcValue(line);

                    cores.Add(
                        $"{physicalId}:{coreId}");
                }
            }

            return cores.Count;
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
                35 => "LPDDR5",
                36 => "LPDDR4",
                _ => $"Desconhecido ({code})"
            };
        }        

        private string GetGpuVendor(
            string vendor)
        {
            return vendor
                .Replace("0x", "")
                .ToLowerInvariant() switch
            {
                "10de" => "NVIDIA",
                "1002" => "AMD",
                "8086" => "Intel",
                _ => vendor
            };
        }

        private List<string> ReadDmiStrings(
            byte[] data,
            int offset)
        {
            var strings = new List<string> { "" };
            var current = new List<byte>();

            while (offset < data.Length)
            {
                var value = data[offset++];

                if (value == 0)
                {
                    if (current.Count == 0)
                        break;

                    strings.Add(
                        Encoding.ASCII.GetString(
                            current.ToArray()));

                    current.Clear();
                }
                else
                {
                    current.Add(value);
                }
            }

            return strings;
        }

        private bool IsEmpty(object? value)
        {
            return value == null;
        }

        private string GetDiskInterface(
            string device)
        {
            if (device.StartsWith(
                "nvme",
                StringComparison.OrdinalIgnoreCase))
                return "NVMe";

            if (device.StartsWith(
                "mmcblk",
                StringComparison.OrdinalIgnoreCase))
                return "MMC";

            if (device.StartsWith(
                "sd",
                StringComparison.OrdinalIgnoreCase))
                return "SCSI/SATA/USB";

            return "N/A";
        }
    }

    internal class DmiRecord
    {
        public byte Type { get; init; }

        public byte Length { get; init; }

        public byte[] Data { get; init; } = Array.Empty<byte>();

        public int Offset { get; init; }

        public List<string> Strings { get; init; } =
            new List<string>();

        public byte GetByte(int relativeOffset)
        {
            var index = Offset + relativeOffset;

            if (index < Offset ||
                index >= Offset + Length)
                return 0;

            return Data[index];
        }

        public ushort GetUInt16(int relativeOffset)
        {
            var index = Offset + relativeOffset;

            if (index + 1 >= Offset + Length)
                return 0;

            return BitConverter.ToUInt16(
                Data,
                index);
        }

        public uint GetUInt32(int relativeOffset)
        {
            var index = Offset + relativeOffset;

            if (index + 3 >= Offset + Length)
                return 0;

            return BitConverter.ToUInt32(
                Data,
                index);
        }

        public string GetString(int relativeOffset)
        {
            var index = GetByte(relativeOffset);

            if (index == 0 ||
                index >= Strings.Count)
                return "N/A";

            var value = Strings[index]?.Trim();

            return string.IsNullOrWhiteSpace(value)
                ? "N/A"
                : value;
        }

        public string GetUuid(int relativeOffset)
        {
            var index = Offset + relativeOffset;

            if (index + 15 >= Offset + Length)
                return "";

            var bytes = new byte[16];

            Array.Copy(
                Data,
                index,
                bytes,
                0,
                16);

            try
            {
                return new Guid(bytes).ToString();
            }
            catch
            {
                return "";
            }
        }
    }
}