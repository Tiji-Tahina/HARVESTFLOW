from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import analytics as analytics_crud
from app.database import get_db
from app.schemas.analytics import (
    AnalyticsSummary,
    DemandTrendPoint,
    PriceTrendPoint,
    SupplyDemandComparison,
    SupplyTrendPoint,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/supply-trends", response_model=list[SupplyTrendPoint])
async def supply_trends(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    product_id: str | None = Query(None),
    category: str | None = Query(None),
    region: str | None = Query(None),
    group_by: str = Query("day", pattern="^(day|week|month)$"),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_crud.get_supply_trends(
        db, start_date, end_date, product_id, category, region, group_by
    )


@router.get("/demand-trends", response_model=list[DemandTrendPoint])
async def demand_trends(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    product_id: str | None = Query(None),
    category: str | None = Query(None),
    region: str | None = Query(None),
    group_by: str = Query("day", pattern="^(day|week|month)$"),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_crud.get_demand_trends(
        db, start_date, end_date, product_id, category, region, group_by
    )


@router.get("/supply-demand-comparison", response_model=list[SupplyDemandComparison])
async def supply_demand_comparison(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_crud.get_supply_demand_comparison(
        db, start_date, end_date, category
    )


@router.get("/price-trends", response_model=list[PriceTrendPoint])
async def price_trends(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    product_id: str | None = Query(None),
    group_by: str = Query("day", pattern="^(day|week|month)$"),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_crud.get_price_trends(
        db, start_date, end_date, product_id, group_by
    )


@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_crud.get_analytics_summary(db, start_date, end_date)
