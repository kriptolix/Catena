from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from enums import StatusEquipment

class InventoryBase(BaseModel):
    equipment_id: int
    processor_id: Optional[int] = None
    motherboard_id: Optional[int] = None
    system_id: Optional[int] = None
    gpu_id: Optional[int] = None
    fingerprint: str
    collection_date: datetime


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    processor_id: Optional[int] = None
    motherboard_id: Optional[int] = None
    system_id: Optional[int] = None
    gpu_id: Optional[int] = None
    fingerprint: Optional[str] = None
    collection_date: Optional[datetime] = None


class Inventory(InventoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Inventory Memory
# ============================================================

class InventoryMemoryBase(BaseModel):
    inventory_id: int
    memory_id: int
    slot: Optional[str] = None


class InventoryMemoryCreate(InventoryMemoryBase):
    pass


class InventoryMemory(InventoryMemoryBase):
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Inventory Network
# ============================================================

class InventoryNetworkBase(BaseModel):
    inventory_id: int
    network_id: int


class InventoryNetworkCreate(InventoryNetworkBase):
    pass


class InventoryNetwork(InventoryNetworkBase):
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Inventory Disc
# ============================================================

class InventoryDiscBase(BaseModel):
    inventory_id: int
    disc_id: int


class InventoryDiscCreate(InventoryDiscBase):
    pass


class InventoryDisc(InventoryDiscBase):
    model_config = ConfigDict(from_attributes=True)
