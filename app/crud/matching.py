from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_supply_demand_summary(db: AsyncSession) -> list[dict]:
    result = await db.execute(text("SELECT * FROM supply_demand_summary"))
    rows = result.mappings().all()
    return [dict(row) for row in rows]


async def get_nearby_listings(
    db: AsyncSession,
    latitude: float,
    longitude: float,
    radius_meters: float,
    product_id: str | None = None,
) -> list[dict]:
    query = """
        SELECT
            l.id,
            l.price_per_unit,
            l.quantity_available,
            l.status,
            l.harvest_date,
            l.created_at,
            p.id AS product_id,
            p.name AS product_name,
            p.category,
            f.id AS farmer_id,
            f.name AS farmer_name,
            f.location AS farmer_location,
            ST_Distance(l.geo, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) AS distance_m
        FROM listings l
        JOIN products p ON p.id = l.product_id
        JOIN farmers f ON f.id = l.farmer_id
        WHERE l.status = 'active'
          AND l.geo IS NOT NULL
          AND ST_DWithin(
              l.geo,
              ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
              :radius
          )
    """
    params: dict = {"lon": longitude, "lat": latitude, "radius": radius_meters}
    if product_id:
        query += " AND l.product_id = :product_id"
        params["product_id"] = product_id

    query += " ORDER BY distance_m ASC"

    result = await db.execute(text(query), params)
    rows = result.mappings().all()
    return [dict(row) for row in rows]


async def get_available_transporters(
    db: AsyncSession,
    latitude: float,
    longitude: float,
    radius_meters: float,
    min_capacity_kg: float | None = None,
) -> list[dict]:
    query = """
        SELECT
            t.id,
            t.name,
            t.vehicle_type,
            t.capacity_kg,
            t.is_available,
            t.phone,
            ST_Distance(t.geo, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) AS distance_m
        FROM transporters t
        WHERE t.is_available = 'available'
          AND t.geo IS NOT NULL
          AND ST_DWithin(
              t.geo,
              ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
              :radius
          )
    """
    params = {"lon": longitude, "lat": latitude, "radius": radius_meters}
    if min_capacity_kg is not None:
        query += " AND t.capacity_kg >= :min_capacity"
        params["min_capacity"] = min_capacity_kg

    query += " ORDER BY distance_m ASC"

    result = await db.execute(text(query), params)
    rows = result.mappings().all()
    return [dict(row) for row in rows]
