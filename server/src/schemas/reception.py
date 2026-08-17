from pydantic import BaseModel, Field
from typing import Optional, List


# ============================================================
# Identification
# ============================================================

class Identification(BaseModel):
    uuid: Optional[str] = None


# ============================================================
# Equipment
# ============================================================

class EquipmentInventory(BaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None


# ============================================================
# BIOS
# ============================================================

class BiosInventory(BaseModel):
    manufacturer: Optional[str] = None
    version: Optional[str] = None
    date: Optional[str] = None


# ============================================================
# Motherboard
# ============================================================

class MotherboardInventory(BaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None


# ============================================================
# System
# ============================================================

class SystemInventory(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    architecture: Optional[str] = None


# ============================================================
# Processor
# ============================================================

class ProcessorInventory(BaseModel):
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    cores: Optional[int] = None
    threads: Optional[int] = None
    clock_mhz: Optional[int] = None


# ============================================================
# Memory
# ============================================================

class MemoryModule(BaseModel):
    manufacturer: Optional[str] = None
    capacity_gb: Optional[float] = None
    clock_mhz: Optional[int] = None
    type: Optional[str] = None
    part_number: Optional[str] = None
    serial_number: Optional[str] = None


class MemoryInventory(BaseModel):
    total_gb: Optional[float] = None
    modules: List[MemoryModule] = Field(default_factory=list)


# ============================================================
# Disc
# ============================================================

class DiscInventory(BaseModel):
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    interface: Optional[str] = None
    capacity_gb: Optional[float] = None
    serial_number: Optional[str] = None
    type: Optional[str] = None


# ============================================================
# GPU
# ============================================================

class GPUInventory(BaseModel):
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    memory_gb: Optional[float] = None


# ============================================================
# Network
# ============================================================

class NetworkInventory(BaseModel):
    model: Optional[str] = None
    mac: Optional[str] = None
    speed_mbps: Optional[int] = None


# ============================================================
# Inventory received
# ============================================================

class InventoryReceived(BaseModel):
    identification: Optional[Identification] = None
    equipment: Optional[EquipmentInventory] = None
    bios: Optional[BiosInventory] = None
    motherboard: Optional[MotherboardInventory] = None
    system: Optional[SystemInventory] = None
    processor: Optional[ProcessorInventory] = None
    memory: Optional[MemoryInventory] = None
    disks: List[DiscInventory] = Field(default_factory=list)
    gpu: List[GPUInventory] = Field(default_factory=list)
    network: List[NetworkInventory] = Field(default_factory=list)

    asset_tag: Optional[str] = None
    location: Optional[str] = None
    annotation: Optional[str] = None
    date: Optional[str] = None