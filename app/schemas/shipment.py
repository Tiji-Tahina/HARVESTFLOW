from datetime import datetime

from pydantic import BaseModel, Field


class ShipmentBase(BaseModel):
    order_id: str
    transporter_id: str
    pickup_location: str = Field(..., max_length=255)
    delivery_location: str = Field(..., max_length=255)
    pickup_latitude: float | None = Field(None, ge=-90, le=90)
    pickup_longitude: float | None = Field(None, ge=-180, le=180)
    delivery_latitude: float | None = Field(None, ge=-90, le=90)
    delivery_longitude: float | None = Field(None, ge=-180, le=180)
    tracking_notes: str | None = None


class ShipmentCreate(ShipmentBase):
    estimated_delivery: datetime | None = None


class ShipmentUpdate(BaseModel):
    transporter_id: str | None = None
    pickup_location: str | None = None
    delivery_location: str | None = None
    estimated_delivery: datetime | None = None
    actual_delivery: datetime | None = None
    status: str | None = None
    tracking_notes: str | None = None


class ShipmentRead(ShipmentBase):
    id: str
    estimated_delivery: datetime | None
    actual_delivery: datetime | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShipmentDetail(ShipmentRead):
    order: dict | None = None
    transporter: dict | None = None
