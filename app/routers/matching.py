from fastapi import APIRouter, Depends, Query

from app.crud import matching as matching_crud
from app.database import get_db

router = APIRouter(prefix="/matching", tags=["matching"])


@router.get("/supply-demand")
async def get_supply_demand_summary(db=Depends(get_db)):
    return await matching_crud.get_supply_demand_summary(db)


@router.get("/nearby-listings")
async def get_nearby_listings(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(50, gt=0, le=500),
    product_id: str | None = None,
    db=Depends(get_db),
):
    return await matching_crud.get_nearby_listings(
        db, latitude, longitude, radius_km * 1000, product_id
    )


@router.get("/available-transporters")
async def get_available_transporters(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(50, gt=0, le=500),
    min_capacity_kg: float | None = None,
    db=Depends(get_db),
):
    return await matching_crud.get_available_transporters(
        db, latitude, longitude, radius_km * 1000, min_capacity_kg
    )
