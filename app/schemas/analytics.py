from datetime import datetime

from pydantic import BaseModel


class SupplyTrendPoint(BaseModel):
    date: str
    product_id: str | None = None
    product_name: str | None = None
    category: str | None = None
    region: str | None = None
    total_quantity: float
    listing_count: int
    avg_price: float | None = None


class DemandTrendPoint(BaseModel):
    date: str
    product_id: str | None = None
    product_name: str | None = None
    category: str | None = None
    region: str | None = None
    total_quantity: float
    order_count: int
    avg_price: float | None = None


class SupplyDemandComparison(BaseModel):
    product_id: str
    product_name: str
    category: str
    region: str | None = None
    supply_quantity: float
    demand_quantity: float
    supply_count: int
    demand_count: int
    surplus_deficit: float
    trend: str


class PriceTrendPoint(BaseModel):
    date: str
    product_id: str
    product_name: str
    avg_price: float
    min_price: float
    max_price: float
    transaction_count: int


class AnalyticsSummary(BaseModel):
    period_start: datetime
    period_end: datetime
    total_supply: float
    total_demand: float
    active_listings: int
    completed_orders: int
    top_supplied_products: list[dict]
    top_demanded_products: list[dict]
    price_trends: list[PriceTrendPoint]
