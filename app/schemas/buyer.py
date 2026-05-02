from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class BuyerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(None, max_length=20)
    location: str | None = Field(None, max_length=255)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    preferred_categories: list[str] | None = None


class BuyerCreate(BuyerBase):
    pass


class BuyerUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = None
    location: str | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    preferred_categories: list[str] | None = None


class BuyerRead(BuyerBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BuyerDetail(BuyerRead):
    orders: list[dict] = []
