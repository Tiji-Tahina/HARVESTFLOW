from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import price_history as price_crud
from app.database import get_db
from app.schemas.price_history import PriceHistoryCreate, PriceHistoryRead

router = APIRouter(prefix="/price-history", tags=["price-history"])


@router.post("/", response_model=PriceHistoryRead, status_code=201)
async def record_price(record: PriceHistoryCreate, db: AsyncSession = Depends(get_db)):
    return await price_crud.create_price_record(db, record)


@router.get("/", response_model=list[PriceHistoryRead])
async def list_price_history(
    product_id: str | None = Query(None),
    region: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    return await price_crud.get_price_history(
        db, product_id, region, start_date, end_date, skip, limit
    )


@router.get("/averages")
async def get_price_averages(
    product_id: str | None = Query(None),
    region: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    return await price_crud.get_average_price(db, product_id, region, days)
