from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Farmer
from app.schemas.farmer import FarmerCreate, FarmerUpdate


async def get_farmers(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Farmer]:
    result = await db.execute(select(Farmer).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_farmer(db: AsyncSession, farmer_id: UUID) -> Farmer | None:
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Farmer).options(selectinload(Farmer.listings)).where(Farmer.id == farmer_id)
    )
    return result.scalar_one_or_none()


async def create_farmer(db: AsyncSession, farmer: FarmerCreate) -> Farmer:
    db_farmer = Farmer(**farmer.model_dump())
    db.add(db_farmer)
    await db.flush()
    await db.refresh(db_farmer)
    return db_farmer


async def update_farmer(db: AsyncSession, farmer_id: UUID, farmer: FarmerUpdate) -> Farmer | None:
    db_farmer = await get_farmer(db, farmer_id)
    if not db_farmer:
        return None
    update_data = farmer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_farmer, key, value)
    await db.flush()
    await db.refresh(db_farmer)
    return db_farmer


async def delete_farmer(db: AsyncSession, farmer_id: UUID) -> bool:
    db_farmer = await get_farmer(db, farmer_id)
    if not db_farmer:
        return False
    await db.delete(db_farmer)
    await db.flush()
    return True
