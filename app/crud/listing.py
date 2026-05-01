from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Listing
from app.schemas.listing import ListingCreate, ListingUpdate


async def get_listings(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Listing]:
    result = await db.execute(select(Listing).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_listing(db: AsyncSession, listing_id: UUID) -> Listing | None:
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Listing)
        .options(selectinload(Listing.farmer), selectinload(Listing.product))
        .where(Listing.id == listing_id)
    )
    return result.scalar_one_or_none()


async def create_listing(db: AsyncSession, listing: ListingCreate) -> Listing:
    db_listing = Listing(**listing.model_dump())
    db.add(db_listing)
    await db.flush()
    await db.refresh(db_listing)
    return db_listing


async def update_listing(
    db: AsyncSession, listing_id: UUID, listing: ListingUpdate
) -> Listing | None:
    db_listing = await get_listing(db, listing_id)
    if not db_listing:
        return None
    update_data = listing.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_listing, key, value)
    await db.flush()
    await db.refresh(db_listing)
    return db_listing


async def delete_listing(db: AsyncSession, listing_id: UUID) -> bool:
    db_listing = await get_listing(db, listing_id)
    if not db_listing:
        return False
    await db.delete(db_listing)
    await db.flush()
    return True
