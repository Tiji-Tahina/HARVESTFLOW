from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transporter
from app.schemas.transporter import TransporterCreate, TransporterUpdate


async def get_transporters(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Transporter]:
    result = await db.execute(select(Transporter).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_transporter(db: AsyncSession, transporter_id: UUID) -> Transporter | None:
    result = await db.execute(select(Transporter).where(Transporter.id == transporter_id))
    return result.scalar_one_or_none()


async def create_transporter(db: AsyncSession, transporter: TransporterCreate) -> Transporter:
    db_transporter = Transporter(**transporter.model_dump())
    db.add(db_transporter)
    await db.flush()
    await db.refresh(db_transporter)
    return db_transporter


async def update_transporter(
    db: AsyncSession, transporter_id: UUID, transporter: TransporterUpdate
) -> Transporter | None:
    db_transporter = await get_transporter(db, transporter_id)
    if not db_transporter:
        return None
    update_data = transporter.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transporter, key, value)
    await db.flush()
    await db.refresh(db_transporter)
    return db_transporter


async def delete_transporter(db: AsyncSession, transporter_id: UUID) -> bool:
    db_transporter = await get_transporter(db, transporter_id)
    if not db_transporter:
        return False
    await db.delete(db_transporter)
    await db.flush()
    return True
