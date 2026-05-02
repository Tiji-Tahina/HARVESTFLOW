from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Shipment
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate


async def get_shipments(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Shipment]:
    result = await db.execute(
        select(Shipment)
        .options(selectinload(Shipment.order), selectinload(Shipment.transporter))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_shipment(db: AsyncSession, shipment_id: UUID) -> Shipment | None:
    result = await db.execute(
        select(Shipment)
        .options(selectinload(Shipment.order), selectinload(Shipment.transporter))
        .where(Shipment.id == shipment_id)
    )
    return result.scalar_one_or_none()


async def get_shipment_by_order_id(db: AsyncSession, order_id: UUID) -> Shipment | None:
    result = await db.execute(
        select(Shipment)
        .options(selectinload(Shipment.order), selectinload(Shipment.transporter))
        .where(Shipment.order_id == order_id)
    )
    return result.scalar_one_or_none()


async def create_shipment(db: AsyncSession, shipment: ShipmentCreate) -> Shipment:
    data = shipment.model_dump(
        exclude={
            "pickup_latitude",
            "pickup_longitude",
            "delivery_latitude",
            "delivery_longitude",
        }
    )
    if shipment.pickup_latitude is not None and shipment.pickup_longitude is not None:
        data["geo_pickup"] = func.ST_SetSRID(
            func.ST_MakePoint(shipment.pickup_longitude, shipment.pickup_latitude), 4326
        )
    if shipment.delivery_latitude is not None and shipment.delivery_longitude is not None:
        data["geo_delivery"] = func.ST_SetSRID(
            func.ST_MakePoint(shipment.delivery_longitude, shipment.delivery_latitude), 4326
        )
    db_shipment = Shipment(**data)
    db.add(db_shipment)
    await db.flush()
    await db.refresh(db_shipment)
    return db_shipment


async def update_shipment(
    db: AsyncSession, shipment_id: UUID, shipment: ShipmentUpdate
) -> Shipment | None:
    db_shipment = await get_shipment(db, shipment_id)
    if not db_shipment:
        return None
    update_data = shipment.model_dump(
        exclude_unset=True,
        exclude={"pickup_latitude", "pickup_longitude", "delivery_latitude", "delivery_longitude"},
    )
    for key, value in update_data.items():
        setattr(db_shipment, key, value)
    await db.flush()
    await db.refresh(db_shipment)
    return db_shipment


async def delete_shipment(db: AsyncSession, shipment_id: UUID) -> bool:
    db_shipment = await get_shipment(db, shipment_id)
    if not db_shipment:
        return False
    await db.delete(db_shipment)
    await db.flush()
    return True
