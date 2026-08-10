using Agent.Models;

namespace Agent.Services
{
    public interface IHardwareCollector
    {
        HardwareInfo CollectHardwareInfo();
    }
}