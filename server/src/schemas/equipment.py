from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional
from enums import StatusEquipment

class EquipmentBase(BaseModel):
    asset_tag: str
    uuid: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    status: Optional[StatusEquipment] = None
    warranty_start_date: Optional[date] = None
    warranty_period: Optional[int] = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    asset_tag: Optional[str] = None
    uuid: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    status: Optional[StatusEquipment] = None
    warranty_start_date: Optional[date] = None
    warranty_period: Optional[int] = None


class Equipment(EquipmentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)