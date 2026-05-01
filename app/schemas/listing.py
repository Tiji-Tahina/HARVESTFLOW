from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ListingStatus(str, Enum):
    draft = "draft"
    active = "active"
    sold_out = "sold_out"


class ListingBase(BaseModel):
    farmer_id: UUID
    product_id: UUID
    price_per_unit: float = Field(..., gt=0)
    quantity_available: float = Field(..., gt=0)
    status: ListingStatus = ListingStatus.draft


class ListingCreate(ListingBase):
    pass


class ListingUpdate(BaseModel):
    price_per_unit: float | None = Field(None, gt=0)
    quantity_available: float | None = Field(None, gt=0)
    status: ListingStatus | None = None


class ListingRead(ListingBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ListingDetail(ListingRead):
    farmer: dict[str, Any] | None = None
    product: dict[str, Any] | None = None
