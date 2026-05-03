from uuid import UUID

from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    buyer_id: UUID
    product_id: UUID | None = None
    product_category: str | None = None
    quantity: float = Field(..., gt=0)
    max_distance_km: float = Field(200, gt=0, le=1000)

    def __post_init__(self):
        if self.product_id is None and self.product_category is None:
            raise ValueError("Either product_id or product_category must be provided")


class ScoreBreakdown(BaseModel):
    distance_score: float
    price_score: float
    quantity_score: float
    total_score: float


class ListingMatch(BaseModel):
    listing_id: UUID
    farmer_id: UUID
    farmer_name: str
    product_id: UUID
    product_name: str
    price_per_unit: float
    quantity_available: float
    distance_km: float
    score_breakdown: ScoreBreakdown


class CombinationMatch(BaseModel):
    combination_id: int
    listings: list[ListingMatch]
    total_quantity: float
    avg_distance_km: float
    weighted_avg_price: float
    fulfillment_pct: float


class MatchResponse(BaseModel):
    individual_matches: list[ListingMatch]
    combination_matches: list[CombinationMatch]
    requested_quantity: float
    total_candidates: int
