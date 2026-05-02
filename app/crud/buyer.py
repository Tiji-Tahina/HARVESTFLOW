from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Buyer
from app.schemas.buyer import BuyerCreate, BuyerUpdate


async def get_buyers(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Buyer]:
    result = await db.execute(select(Buyer).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_buyer(db: AsyncSession, buyer_id: UUID) -> Buyer | None:
    result = await db.execute(select(Buyer).where(Buyer.id == buyer_id))
    return result.scalar_one_or_none()


async def create_buyer(db: AsyncSession, buyer: BuyerCreate) -> Buyer:
    data = buyer.model_dump(exclude={"latitude", "longitude"})
    if buyer.latitude is not None and buyer.longitude is not None:
        data["geo"] = func.ST_SetSRID(func.ST_MakePoint(buyer.longitude, buyer.latitude), 4326)
    db_buyer = Buyer(**data)
    db.add(db_buyer)
    await db.flush()
    await db.refresh(db_buyer)
    return db_buyer


async def update_buyer(db: AsyncSession, buyer_id: UUID, buyer: BuyerUpdate) -> Buyer | None:
    db_buyer = await get_buyer(db, buyer_id)
    if not db_buyer:
        return None
    update_data = buyer.model_dump(exclude_unset=True, exclude={"latitude", "longitude"})
    if buyer.latitude is not None and buyer.longitude is not None:
        update_data["geo"] = func.ST_SetSRID(
            func.ST_MakePoint(buyer.longitude, buyer.latitude), 4326
        )
    for key, value in update_data.items():
        setattr(db_buyer, key, value)
    await db.flush()
    await db.refresh(db_buyer)
    return db_buyer


async def delete_buyer(db: AsyncSession, buyer_id: UUID) -> bool:
    db_buyer = await get_buyer(db, buyer_id)
    if not db_buyer:
        return False
    await db.delete(db_buyer)
    await db.flush()
    return True
