from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class TransporterStatus(str, Enum):
    available = "available"
    unavailable = "unavailable"
    in_transit = "in_transit"


class TransporterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    vehicle_type: str = Field(..., min_length=1, max_length=50)
    capacity_kg: float = Field(..., gt=0)
    is_available: TransporterStatus = TransporterStatus.available
    phone: str | None = Field(None, max_length=20)


class TransporterCreate(TransporterBase):
    pass


class TransporterUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    vehicle_type: str | None = Field(None, min_length=1, max_length=50)
    capacity_kg: float | None = Field(None, gt=0)
    is_available: TransporterStatus | None = None
    phone: str | None = Field(None, max_length=20)


class TransporterRead(TransporterBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
