import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

W_DISTANCE = 0.4
W_PRICE = 0.4
W_QUANTITY = 0.2


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


async def match_buyer_to_listings(
    db: AsyncSession,
    buyer_id: uuid.UUID,
    quantity: float,
    max_distance_km: float,
    product_id: uuid.UUID | None = None,
    product_category: str | None = None,
) -> dict:
    buyer_query = """
        SELECT id, ST_X(geo::geometry) AS lon, ST_Y(geo::geometry) AS lat
        FROM buyers
        WHERE id = :buyer_id
    """
    buyer_result = await db.execute(text(buyer_query), {"buyer_id": str(buyer_id)})
    buyer_row = buyer_result.mappings().one_or_none()

    if not buyer_row or buyer_row["lon"] is None or buyer_row["lat"] is None:
        return {
            "individual_matches": [],
            "combination_matches": [],
            "requested_quantity": quantity,
            "total_candidates": 0,
        }

    product_filter = ""
    if product_id:
        product_filter = "AND l.product_id = :product_id"
    elif product_category:
        product_filter = "AND p.category = :product_category"

    listing_query = f"""
        SELECT
            l.id,
            l.farmer_id,
            l.product_id,
            l.price_per_unit,
            l.quantity_available,
            f.name AS farmer_name,
            p.name AS product_name,
            ST_Distance(
                l.geo,
                ST_SetSRID(ST_MakePoint(:buyer_lon, :buyer_lat), 4326)
            ) / 1000 AS distance_km
        FROM listings l
        JOIN farmers f ON f.id = l.farmer_id
        JOIN products p ON p.id = l.product_id
        WHERE l.status = 'active'
          AND l.geo IS NOT NULL
          AND l.quantity_available > 0
          {product_filter}
    """

    params = {
        "buyer_lon": buyer_row["lon"],
        "buyer_lat": buyer_row["lat"],
    }
    if product_id:
        params["product_id"] = str(product_id)
    elif product_category:
        params["product_category"] = product_category

    result = await db.execute(text(listing_query), params)
    rows = result.mappings().all()

    candidates = [dict(row) for row in rows if dict(row)["distance_km"] <= max_distance_km]

    if not candidates:
        return {
            "individual_matches": [],
            "combination_matches": [],
            "requested_quantity": quantity,
            "total_candidates": 0,
        }

    max_distance = max(c["distance_km"] for c in candidates) or 1
    max_price = max(c["price_per_unit"] for c in candidates) or 1

    scored = []
    for c in candidates:
        dist_score = 1 - (c["distance_km"] / max_distance)
        price_score = 1 - (c["price_per_unit"] / max_price)
        qty_score = min(c["quantity_available"] / quantity, 1.0)
        total_score = W_DISTANCE * dist_score + W_PRICE * price_score + W_QUANTITY * qty_score
        c["score_breakdown"] = {
            "distance_score": round(dist_score, 4),
            "price_score": round(price_score, 4),
            "quantity_score": round(qty_score, 4),
            "total_score": round(total_score, 4),
        }
        scored.append(c)

    scored.sort(key=lambda x: x["score_breakdown"]["total_score"], reverse=True)

    individual_matches = [
        {
            "listing_id": s["id"],
            "farmer_id": s["farmer_id"],
            "farmer_name": s["farmer_name"],
            "product_id": s["product_id"],
            "product_name": s["product_name"],
            "price_per_unit": float(s["price_per_unit"]),
            "quantity_available": float(s["quantity_available"]),
            "distance_km": round(s["distance_km"], 2),
            "score_breakdown": s["score_breakdown"],
        }
        for s in scored
    ]

    combination_matches = _build_combinations(scored, quantity)

    return {
        "individual_matches": individual_matches,
        "combination_matches": combination_matches,
        "requested_quantity": quantity,
        "total_candidates": len(candidates),
    }


def _build_combinations(scored: list[dict], requested_quantity: float) -> list[dict]:
    combinations = []
    accumulated_qty = 0
    combo_listings = []
    combo_weighted_price_sum = 0

    for item in scored:
        accumulated_qty += item["quantity_available"]
        combo_listings.append(item)
        combo_weighted_price_sum += item["price_per_unit"] * item["quantity_available"]

        if accumulated_qty >= requested_quantity or len(combo_listings) == len(scored):
            combinations.append(
                _make_combo(len(combinations) + 1, combo_listings, requested_quantity)
            )

            if accumulated_qty >= requested_quantity:
                break

    if not combinations and len(scored) <= 3:
        combinations.append(_make_combo(1, scored, requested_quantity))
    elif not combinations and scored:
        top3 = scored[:3]
        combinations.append(_make_combo(1, top3, requested_quantity))

    return combinations


def _make_combo(combo_id: int, items: list[dict], requested_quantity: float) -> dict:
    total_qty = sum(i["quantity_available"] for i in items)
    avg_distance = sum(i["distance_km"] for i in items) / len(items)
    weighted_price_sum = sum(i["price_per_unit"] * i["quantity_available"] for i in items)
    weighted_avg_price = weighted_price_sum / total_qty if total_qty > 0 else 0
    fulfillment_pct = min(total_qty / requested_quantity * 100, 100)

    return {
        "combination_id": combo_id,
        "listings": [
            {
                "listing_id": i["id"],
                "farmer_id": i["farmer_id"],
                "farmer_name": i["farmer_name"],
                "product_id": i["product_id"],
                "product_name": i["product_name"],
                "price_per_unit": float(i["price_per_unit"]),
                "quantity_available": float(i["quantity_available"]),
                "distance_km": round(i["distance_km"], 2),
                "score_breakdown": i["score_breakdown"],
            }
            for i in items
        ],
        "total_quantity": round(total_qty, 2),
        "avg_distance_km": round(avg_distance, 2),
        "weighted_avg_price": round(weighted_avg_price, 4),
        "fulfillment_pct": round(fulfillment_pct, 2),
    }


async def dispatch_order(
    db: AsyncSession,
    order_id: uuid.UUID,
    search_radius_m: float = 50000,
) -> dict:
    from app.crud import order as order_crud, shipment as shipment_crud
    from app.schemas.shipment import ShipmentCreate

    order = await order_crud.get_order(db, order_id)
    if not order:
        raise ValueError("Order not found")
    if order.shipment:
        raise ValueError("Order already has a shipment")

    listing = order.listing
    if not listing or not listing.geo:
        raise ValueError("Listing has no location data")

    pickup_query = text(
        "SELECT ST_Y(geo::geometry) AS lat, ST_X(geo::geometry) AS lon "
        "FROM listings WHERE id = :lid"
    )
    pickup_lat_result = await db.execute(
        pickup_query,
        {"lid": str(listing.id)},
    )
    pickup = pickup_lat_result.mappings().one_or_none()
    if not pickup:
        raise ValueError("Could not determine pickup location")

    transporters = await get_available_transporters(
        db, pickup["lat"], pickup["lon"], search_radius_m, min_capacity_kg=float(order.quantity)
    )

    if not transporters:
        raise ValueError("No available transporters found within radius")

    nearest = transporters[0]

    shipment_in = ShipmentCreate(
        order_id=str(order_id),
        transporter_id=nearest["id"],
        pickup_location=listing.farmer.location or "Pickup location",
        delivery_location=order.buyer.location or "Delivery location",
        pickup_latitude=pickup["lat"],
        pickup_longitude=pickup["lon"],
        delivery_latitude=None,
        delivery_longitude=None,
    )

    shipment = await shipment_crud.create_shipment(db, shipment_in)

    await db.execute(
        text("UPDATE orders SET status = 'confirmed' WHERE id = :oid"),
        {"oid": str(order_id)},
    )
    await db.execute(
        text("UPDATE transporters SET is_available = 'in_transit' WHERE id = :tid"),
        {"tid": nearest["id"]},
    )
    await db.flush()

    return {
        "shipment_id": str(shipment.id),
        "transporter_id": nearest["id"],
        "transporter_name": nearest["name"],
        "distance_m": nearest["distance_m"],
        "status": "dispatched",
    }
