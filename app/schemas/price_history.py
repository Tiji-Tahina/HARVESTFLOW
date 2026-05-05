from datetime import datetime

from pydantic import BaseModel, Field


class PriceHistoryBase(BaseModel):
    product_id: str
    region: str = Field(..., max_length=100)
    price_per_unit: float = Field(..., gt=0)
    quantity: float = Field(..., gt=0)
    order_id: str


class PriceHistoryCreate(PriceHistoryBase):
    pass


class PriceHistoryRead(PriceHistoryBase):
    id: str
    transaction_date: datetime

    model_config = {"from_attributes": True}


class PriceAverage(BaseModel):
    product_id: str
    product_name: str
    region: str
    avg_price: float
    min_price: float
    max_price: float
    total_quantity: float
    transaction_count: int
    period_start: datetime
    period_end: datetime
