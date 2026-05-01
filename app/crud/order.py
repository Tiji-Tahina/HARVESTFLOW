from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import listing as listing_crud
from app.models import Order
from app.schemas.order import OrderCreate, OrderUpdate


async def get_orders(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Order]:
    result = await db.execute(select(Order).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_order(db: AsyncSession, order_id: UUID) -> Order | None:
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.listing),
            selectinload(Order.farmer),
            selectinload(Order.transporter),
        )
        .where(Order.id == order_id)
    )
    return result.scalar_one_or_none()


async def create_order(db: AsyncSession, order: OrderCreate) -> Order:
    db_listing = await listing_crud.get_listing(db, order.listing_id)
    if not db_listing:
        raise ValueError("Listing not found")

    total_price = Decimal(str(db_listing.price_per_unit)) * Decimal(str(order.quantity))

    db_order = Order(
        listing_id=order.listing_id,
        farmer_id=order.farmer_id,
        transporter_id=order.transporter_id,
        quantity=order.quantity,
        total_price=total_price,
    )
    db.add(db_order)
    await db.flush()
    await db.refresh(db_order)
    return db_order


async def update_order(db: AsyncSession, order_id: UUID, order: OrderUpdate) -> Order | None:
    db_order = await get_order(db, order_id)
    if not db_order:
        return None
    update_data = order.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_order, key, value)
    await db.flush()
    await db.refresh(db_order)
    return db_order


async def delete_order(db: AsyncSession, order_id: UUID) -> bool:
    db_order = await get_order(db, order_id)
    if not db_order:
        return False
    await db.delete(db_order)
    await db.flush()
    return True
