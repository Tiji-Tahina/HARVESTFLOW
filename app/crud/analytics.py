from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_supply_trends(
    db: AsyncSession,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    product_id: str | None = None,
    category: str | None = None,
    region: str | None = None,
    group_by: str = "day",
) -> list[dict]:
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    date_format = {"day": "YYYY-MM-DD", "week": "YYYY-WW", "month": "YYYY-MM"}[group_by]

    query = text(
        f"""
        SELECT
            TO_CHAR(l.created_at, '{date_format}') AS date,
            l.product_id,
            p.name AS product_name,
            p.category,
            f.location AS region,
            SUM(l.quantity_available) AS total_quantity,
            COUNT(*) AS listing_count,
            AVG(l.price_per_unit) AS avg_price
        FROM listings l
        JOIN products p ON p.id = l.product_id
        JOIN farmers f ON f.id = l.farmer_id
        WHERE l.created_at BETWEEN :start_date AND :end_date
          AND l.status IN ('active', 'sold_out')
        """
        + (" AND l.product_id = :product_id" if product_id else "")
        + (" AND p.category = :category" if category else "")
        + (" AND f.location = :region" if region else "")
        + """
        GROUP BY date, l.product_id, p.name, p.category, f.location
        ORDER BY date ASC, total_quantity DESC
        """
    )

    params = {"start_date": start_date, "end_date": end_date}
    if product_id:
        params["product_id"] = product_id
    if category:
        params["category"] = category
    if region:
        params["region"] = region

    result = await db.execute(query, params)
    return [dict(row) for row in result.mappings().all()]


async def get_demand_trends(
    db: AsyncSession,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    product_id: str | None = None,
    category: str | None = None,
    region: str | None = None,
    group_by: str = "day",
) -> list[dict]:
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    date_format = {"day": "YYYY-MM-DD", "week": "YYYY-WW", "month": "YYYY-MM"}[group_by]

    query = text(
        f"""
        SELECT
            TO_CHAR(o.created_at, '{date_format}') AS date,
            l.product_id,
            p.name AS product_name,
            p.category,
            b.location AS region,
            SUM(o.quantity) AS total_quantity,
            COUNT(*) AS order_count,
            AVG(l.price_per_unit) AS avg_price
        FROM orders o
        JOIN listings l ON l.id = o.listing_id
        JOIN products p ON p.id = l.product_id
        JOIN buyers b ON b.id = o.buyer_id
        WHERE o.created_at BETWEEN :start_date AND :end_date
          AND o.status IN ('confirmed', 'in_transit', 'delivered')
        """
        + (" AND l.product_id = :product_id" if product_id else "")
        + (" AND p.category = :category" if category else "")
        + (" AND b.location = :region" if region else "")
        + """
        GROUP BY date, l.product_id, p.name, p.category, b.location
        ORDER BY date ASC, total_quantity DESC
        """
    )

    params = {"start_date": start_date, "end_date": end_date}
    if product_id:
        params["product_id"] = product_id
    if category:
        params["category"] = category
    if region:
        params["region"] = region

    result = await db.execute(query, params)
    return [dict(row) for row in result.mappings().all()]


async def get_supply_demand_comparison(
    db: AsyncSession,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    category: str | None = None,
) -> list[dict]:
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    query = text(
        """
        WITH supply AS (
            SELECT
                l.product_id,
                p.name AS product_name,
                p.category,
                f.location AS region,
                SUM(l.quantity_available) AS supply_quantity,
                COUNT(*) AS supply_count
            FROM listings l
            JOIN products p ON p.id = l.product_id
            JOIN farmers f ON f.id = l.farmer_id
            WHERE l.created_at BETWEEN :start_date AND :end_date
              AND l.status IN ('active', 'sold_out')
            """
        + (" AND p.category = :category" if category else "")
        + """
            GROUP BY l.product_id, p.name, p.category, f.location
        ),
        demand AS (
            SELECT
                l.product_id,
                p.name AS product_name,
                p.category,
                b.location AS region,
                SUM(o.quantity) AS demand_quantity,
                COUNT(*) AS demand_count
            FROM orders o
            JOIN listings l ON l.id = o.listing_id
            JOIN products p ON p.id = l.product_id
            JOIN buyers b ON b.id = o.buyer_id
            WHERE o.created_at BETWEEN :start_date AND :end_date
              AND o.status IN ('confirmed', 'in_transit', 'delivered')
            """
        + (" AND p.category = :category" if category else "")
        + """
            GROUP BY l.product_id, p.name, p.category, b.location
        )
        SELECT
            COALESCE(s.product_id, d.product_id) AS product_id,
            COALESCE(s.product_name, d.product_name) AS product_name,
            COALESCE(s.category, d.category) AS category,
            COALESCE(s.region, d.region) AS region,
            COALESCE(s.supply_quantity, 0) AS supply_quantity,
            COALESCE(d.demand_quantity, 0) AS demand_quantity,
            COALESCE(s.supply_count, 0) AS supply_count,
            COALESCE(d.demand_count, 0) AS demand_count,
            COALESCE(s.supply_quantity, 0) - COALESCE(d.demand_quantity, 0) AS surplus_deficit
        FROM supply s
        FULL OUTER JOIN demand d ON s.product_id = d.product_id AND s.region = d.region
        ORDER BY surplus_deficit DESC
        """
    )

    params = {"start_date": start_date, "end_date": end_date}
    if category:
        params["category"] = category

    result = await db.execute(query, params)
    rows = [dict(row) for row in result.mappings().all()]

    for row in rows:
        if row["surplus_deficit"] > 0:
            row["trend"] = "surplus"
        elif row["surplus_deficit"] < 0:
            row["trend"] = "deficit"
        else:
            row["trend"] = "balanced"

    return rows


async def get_price_trends(
    db: AsyncSession,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    product_id: str | None = None,
    group_by: str = "day",
) -> list[dict]:
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    date_format = {"day": "YYYY-MM-DD", "week": "YYYY-WW", "month": "YYYY-MM"}[group_by]

    query = text(
        f"""
        SELECT
            TO_CHAR(transaction_date, '{date_format}') AS date,
            product_id,
            product_name,
            AVG(price_per_unit) AS avg_price,
            MIN(price_per_unit) AS min_price,
            MAX(price_per_unit) AS max_price,
            COUNT(*) AS transaction_count
        FROM price_history ph
        JOIN products p ON p.id = ph.product_id
        WHERE ph.transaction_date BETWEEN :start_date AND :end_date
        """
        + (" AND ph.product_id = :product_id" if product_id else "")
        + """
        GROUP BY date, product_id, product_name
        ORDER BY date ASC, avg_price DESC
        """
    )

    params = {"start_date": start_date, "end_date": end_date}
    if product_id:
        params["product_id"] = product_id

    result = await db.execute(query, params)
    return [dict(row) for row in result.mappings().all()]


async def get_analytics_summary(
    db: AsyncSession,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    supply_query = text(
        """
        SELECT
            SUM(l.quantity_available) AS total_supply,
            COUNT(*) AS active_listings
        FROM listings l
        WHERE l.created_at BETWEEN :start_date AND :end_date
          AND l.status = 'active'
        """
    )

    demand_query = text(
        """
        SELECT
            SUM(o.quantity) AS total_demand,
            COUNT(*) AS completed_orders
        FROM orders o
        WHERE o.created_at BETWEEN :start_date AND :end_date
          AND o.status IN ('confirmed', 'in_transit', 'delivered')
        """
    )

    top_supply_query = text(
        """
        SELECT
            l.product_id,
            p.name AS product_name,
            SUM(l.quantity_available) AS total_quantity
        FROM listings l
        JOIN products p ON p.id = l.product_id
        WHERE l.created_at BETWEEN :start_date AND :end_date
          AND l.status = 'active'
        GROUP BY l.product_id, p.name
        ORDER BY total_quantity DESC
        LIMIT 5
        """
    )

    top_demand_query = text(
        """
        SELECT
            l.product_id,
            p.name AS product_name,
            SUM(o.quantity) AS total_quantity
        FROM orders o
        JOIN listings l ON l.id = o.listing_id
        JOIN products p ON p.id = l.product_id
        WHERE o.created_at BETWEEN :start_date AND :end_date
          AND o.status IN ('confirmed', 'in_transit', 'delivered')
        GROUP BY l.product_id, p.name
        ORDER BY total_quantity DESC
        LIMIT 5
        """
    )

    params = {"start_date": start_date, "end_date": end_date}

    supply_result = await db.execute(supply_query, params)
    demand_result = await db.execute(demand_query, params)
    top_supply = await db.execute(top_supply_query, params)
    top_demand = await db.execute(top_demand_query, params)

    supply_row = supply_result.mappings().one()
    demand_row = demand_result.mappings().one()

    return {
        "period_start": start_date,
        "period_end": end_date,
        "total_supply": float(supply_row["total_supply"] or 0),
        "total_demand": float(demand_row["total_demand"] or 0),
        "active_listings": supply_row["active_listings"],
        "completed_orders": demand_row["completed_orders"],
        "top_supplied_products": [dict(row) for row in top_supply.mappings().all()],
        "top_demanded_products": [dict(row) for row in top_demand.mappings().all()],
        "price_trends": await get_price_trends(db, start_date, end_date),
    }
