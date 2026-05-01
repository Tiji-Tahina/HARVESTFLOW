from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.listing import ListingRead


class FarmerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(None, max_length=20)
    location: str | None = Field(None, max_length=255)


class FarmerCreate(FarmerBase):
    pass


class FarmerUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    location: str | None = Field(None, max_length=255)


class FarmerRead(FarmerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    listings: list[ListingRead] = []

    model_config = {"from_attributes": True}
