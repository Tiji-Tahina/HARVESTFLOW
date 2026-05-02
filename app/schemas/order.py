from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"


class OrderBase(BaseModel):
    listing_id: UUID
    farmer_id: UUID
    buyer_id: UUID
    quantity: float = Field(..., gt=0)


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None


class OrderRead(OrderBase):
    id: UUID
    total_price: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderDetail(OrderRead):
    listing: dict | None = None
    farmer: dict | None = None
    buyer: dict | None = None
    shipment: dict | None = None
