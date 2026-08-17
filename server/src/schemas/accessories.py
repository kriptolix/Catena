from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

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
