from pydantic import BaseModel, ConfigDict
from typing import Optional

# ============================================================
# Processor
# ============================================================

class ProcessorBase(BaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    cores: Optional[int] = None
    threads: Optional[int] = None
    clock_mhz: Optional[int] = None


class ProcessorCreate(ProcessorBase):
    pass


class ProcessorUpdate(ProcessorBase):
    pass


class Processor(ProcessorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Memory
# ============================================================

class MemoryBase(BaseModel):
    manufacturer: Optional[str] = None
    capacity_gb: Optional[float] = None
    clock_mhz: Optional[int] = None
    type: Optional[str] = None
    part_number: Optional[str] = None
    serial_number: Optional[str] = None


class MemoryCreate(MemoryBase):
    pass


class MemoryUpdate(MemoryBase):
    pass


class Memory(MemoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Disc
# ============================================================

class DiscBase(BaseModel):
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    interface: Optional[str] = None
    capacity_gb: Optional[float] = None
    serial_number: Optional[str] = None
    type: Optional[str] = None


class DiscCreate(DiscBase):
    pass


class DiscUpdate(DiscBase):
    pass


class Disc(DiscBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# GPU
# ============================================================

class GPUBase(BaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    memory_gb: Optional[float] = None


class GPUCreate(GPUBase):
    pass


class GPUUpdate(GPUBase):
    pass


class GPU(GPUBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Motherboard
# ============================================================

class MotherboardBase(BaseModel):
    model: Optional[str] = None
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    bios_version: Optional[str] = None
    bios_date: Optional[str] = None


class MotherboardCreate(MotherboardBase):
    pass


class MotherboardUpdate(MotherboardBase):
    pass


class Motherboard(MotherboardBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# System
# ============================================================

class SystemBase(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    architecture: Optional[str] = None


class SystemCreate(SystemBase):
    pass


class SystemUpdate(SystemBase):
    pass


class System(SystemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Network
# ============================================================

class NetworkBase(BaseModel):
    model: Optional[str] = None
    mac: Optional[str] = None
    speed_mbps: Optional[int] = None


class NetworkCreate(NetworkBase):
    pass


class NetworkUpdate(NetworkBase):
    pass


class Network(NetworkBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
