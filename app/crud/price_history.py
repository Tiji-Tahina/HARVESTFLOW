from datetime import datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PriceHistory
from app.schemas.price_history import PriceHistoryCreate


async def create_price_record(db: AsyncSession, record: PriceHistoryCreate) -> PriceHistory:
    data = record.model_dump()
    db_record = PriceHistory(**data)
    db.add(db_record)
    await db.flush()
    await db.refresh(db_record)
    return db_record


async def get_price_history(
    db: AsyncSession,
    product_id: str | None = None,
    region: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[PriceHistory]:
    query = select(PriceHistory)
    if product_id:
        query = query.where(PriceHistory.product_id == product_id)
    if region:
        query = query.where(PriceHistory.region == region)
    if start_date:
        query = query.where(PriceHistory.transaction_date >= start_date)
    if end_date:
        query = query.where(PriceHistory.transaction_date <= end_date)
    query = query.order_by(PriceHistory.transaction_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_average_price(
    db: AsyncSession,
    product_id: str | None = None,
    region: str | None = None,
    days: int = 30,
) -> list[dict]:
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = text(
        """
        SELECT
            ph.product_id,
            p.name AS product_name,
            ph.region,
            AVG(ph.price_per_unit) AS avg_price,
            MIN(ph.price_per_unit) AS min_price,
            MAX(ph.price_per_unit) AS max_price,
            SUM(ph.quantity) AS total_quantity,
            COUNT(*) AS transaction_count,
            :start_date AS period_start,
            :end_date AS period_end
        FROM price_history ph
        JOIN products p ON p.id = ph.product_id
        WHERE ph.transaction_date BETWEEN :start_date AND :end_date
        """
        + (" AND ph.product_id = :product_id" if product_id else "")
        + (" AND ph.region = :region" if region else "")
        + """
        GROUP BY ph.product_id, p.name, ph.region
        ORDER BY ph.region, avg_price ASC
        """
    )

    params = {"start_date": start_date, "end_date": end_date}
    if product_id:
        params["product_id"] = product_id
    if region:
        params["region"] = region

    result = await db.execute(query, params)
    return [dict(row) for row in result.mappings().all()]


async def record_order_price(db: AsyncSession, order_id: str) -> PriceHistory | None:
    from app.crud import order as order_crud

    order = await order_crud.get_order(db, order_id)
    if not order or not order.listing:
        return None

    if order.status not in ("confirmed", "in_transit", "delivered"):
        return None

    existing = await db.execute(
        select(PriceHistory).where(PriceHistory.order_id == order_id)
    )
    if existing.scalar_one_or_none():
        return None

    region = order.farmer.location or "Unknown"
    record = PriceHistoryCreate(
        product_id=str(order.listing.product_id),
        region=region,
        price_per_unit=float(order.listing.price_per_unit),
        quantity=float(order.quantity),
        order_id=order_id,
    )
    return await create_price_record(db, record)
