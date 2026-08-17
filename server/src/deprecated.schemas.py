from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enums import StatusEquipment, TipoHistorico, TipoValorControlado

# Schemas para ValorControlado
class ValorControladoBase(BaseModel):
    type: TipoValorControlado
    valor: str

class ValorControladoCreate(ValorControladoBase):
    pass

class ValorControlado(ValorControladoBase):
    id: int
    criado_por_admin: bool

    model_config = ConfigDict(from_attributes=True)

# ============================================================
# Equipment
# ============================================================

class EquipmentBase(BaseModel):
    asset_number: str
    uuid: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    warranty_start_date: Optional[date] = None
    warranty_period: Optional[int] = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    asset_number: Optional[str] = None
    uuid: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    warranty_start_date: Optional[date] = None
    warranty_period: Optional[int] = None


class Equipment(EquipmentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


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


# ============================================================
# Inventory
# ============================================================

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


# ============================================================
# History
# ============================================================

class HistoryBase(BaseModel):
    type: str
    previous_value: Optional[str] = None
    next_value: Optional[str] = None


class HistoryCreate(HistoryBase):
    equipment_id: int
    user: str


class History(HistoryBase):
    id: int
    equipment_id: int
    user: str
    datetime: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Defect
# ============================================================

class DefectBase(BaseModel):
    component: Optional[str] = None
    description: str


class DefectCreate(DefectBase):
    equipment_id: int


class Defect(DefectBase):
    id: int
    equipment_id: int
    date: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Annotation
# ============================================================

class AnnotationBase(BaseModel):
    user: str
    text: str


class AnnotationCreate(AnnotationBase):
    equipment_id: int


class Annotation(AnnotationBase):
    id: int
    equipment_id: int
    datetime: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# User
# ============================================================

class UserBase(BaseModel):
    username: str
    fullname: str
    is_admin: int = 0
    active: int = 1


class UserCreate(UserBase):
    hashed_password: str


class UserUpdate(BaseModel):
    fullname: Optional[str] = None
    is_admin: Optional[int] = None
    active: Optional[int] = None
    hashed_password: Optional[str] = None


class User(UserBase):
    id: int
    creation_date: datetime

    model_config = ConfigDict(from_attributes=True)



# Schemas para user
class userBase(BaseModel):
    fullname: str
    username: str

class userCreate(userBase):
    password: str
    is_admin: bool = False

class userUpdate(BaseModel):
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    ativo: Optional[bool] = None

class user(userBase):
    id: int
    is_admin: bool
    ativo: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)

# Schemas para Autenticação
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# Schemas para recebimento de inventário (POST /api/v1/inventario)


# ============================================================
# Identificação
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
    discs: List[DiscInventory] = Field(default_factory=list)
    video: List[GPUInventory] = Field(default_factory=list)
    network: List[NetworkInventory] = Field(default_factory=list)

    asset_number: Optional[str] = None
    location: Optional[str] = None
    observations: Optional[str] = None
    inventory_date: Optional[str] = None


