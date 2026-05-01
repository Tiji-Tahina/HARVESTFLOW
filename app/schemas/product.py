from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=100)
    unit_of_measure: str = Field(..., min_length=1, max_length=20)
    description: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    category: str | None = Field(None, min_length=1, max_length=100)
    unit_of_measure: str | None = Field(None, min_length=1, max_length=20)
    description: str | None = None


class ProductRead(ProductBase):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
