# HarvesterFlow — Agent Guide

## Project Overview

Agritech marketplace backend connecting farmers, buyers, and logistics. FastAPI + async SQLAlchemy + PostgreSQL (PostGIS).

## File Structure (all under `/home/tsinjo/Documents/1. Projects/HarvestFlow`)

```
.venv/                         # virtual environment
app/
├── __init__.py
├── main.py                    # FastAPI app, lifespan creates tables, mounts 11 routers at /api/v1
├── config.py                  # Settings via pydantic-settings, reads .env
├── database.py                # async engine, async_session factory, Base class, get_db dependency
├── models/__init__.py         # ALL 8 ORM models: Farmer, Buyer, Product, Listing, Order, Transporter, Shipment, PriceHistory
├── schemas/                   # one file per entity + matching.py, price_history.py, analytics.py
├── crud/                      # one file per entity + matching.py, price_history.py, analytics.py
├── routers/                   # one file per entity + matching.py, price_history.py, analytics.py
└── whatsapp/                  # WhatsApp chatbot (Meta Cloud API integration)
    ├── router.py              # Webhook endpoints (GET verify, POST handle)
    ├── webhook.py             # Incoming message dispatcher
    ├── flow.py                # State machine for conversation states
    ├── session.py             # Redis session manager with TTL
    └── templates.py           # WhatsApp message formatting helpers
frontend/                      # React buyer dashboard (Vite + React Router)
    ├── src/
    │   ├── App.jsx           # Main app with routing
    │   ├── main.jsx          # Entry point
    │   ├── pages/            # Listings, PlaceOrder
    │   ├── services/api.js   # API calls to backend
    │   └── styles/App.css   # Styles
    ├── package.json
    └── vite.config.js       # Proxy to backend
alembic/                       # migrations (autogenerate configured)
alembic.ini
requirements.txt
pyproject.toml                 # ruff + pyright config
```

## Key Conventions

1. **Models**: All in `app/models/__init__.py` using SQLAlchemy 2.0 `Mapped`/`mapped_column` syntax
2. **Geo columns**: Use `Geography("POINT", srid=4326)` from `geoalchemy2` for spatial queries
3. **Schemas**: Per entity — `*Create`, `*Update`, `*Read` (+ `*Detail` for listings/orders/shipments with nested relations)
4. **Geo in schemas**: Use `latitude`/`longitude` float fields (validated ge=-90..90, ge=-180..180); CRUD converts to PostGIS `ST_SetSRID(ST_MakePoint(lon, lat), 4326)`
5. **CRUD**: Async functions — `get_*`, `*_by_id`, `create_*`, `update_*`, `delete_*`. Always use `db.flush()` then `db.refresh()`.
6. **Routers**: Each has prefix `/{resource}s`, tag for grouping. List endpoint uses `skip`/`limit` query params.
7. **DB**: `get_db()` yields session, commits on success, rolls back on error. Lifespan calls `Base.metadata.create_all`.
8. **Validation**: Pydantic v2 — `Field(..., gt=0)` for positives, `EmailStr` for emails, `Enum` for statuses.
9. **Order total_price**: Computed in CRUD from `listing.price_per_unit × order.quantity`, NOT accepted from client.

## Model Relationships

```
Buyer 1 ── N Order 1 ── 1 Listing N ── 1 Product
                       N ── 1 Farmer

Order 1 ── 0..1 Shipment N ── 1 Transporter

PriceHistory N ── 1 Product
PriceHistory 1 ── 1 Order
```

## Status Enums

| Enum | Values |
|---|---|
| listing_status | draft, active, sold_out |
| order_status | pending, confirmed, in_transit, delivered, cancelled |
| transporter_status | available, unavailable, in_transit |
| shipment_status | scheduled, picked_up, in_transit, delivered, failed |

## Matching Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/matching/supply-demand` | Returns materialized view of supply vs demand by product |
| `GET /api/v1/matching/nearby-listings` | Finds active listings within radius using PostGIS ST_DWithin |
| `GET /api/v1/matching/available-transporters` | Finds available transporters near a location with capacity filter |
| `POST /api/v1/matching/find-listings` | Scores buyer-to-listing matches: `0.4×distance + 0.4×price + 0.2×quantity`. Returns ranked individual matches and combination suggestions that together fulfill the requested quantity. Accepts `buyer_id`, `product_id`/`product_category`, `quantity`, `max_distance_km`. |
| `POST /api/v1/matching/dispatch` | Assigns nearest available transporter to order using PostGIS ST_DWithin |

## Price History & Analytics

### Price History Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/price-history/` | Record a transaction price |
| `GET /api/v1/price-history/` | List price history (filter by product, region, date range) |
| `GET /api/v1/price-history/averages` | Get average prices per product per region over time |

### Analytics Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/analytics/supply-trends` | Supply trends over time (group by day/week/month) |
| `GET /api/v1/analytics/demand-trends` | Demand trends over time |
| `GET /api/v1/analytics/supply-demand-comparison` | Surplus/deficit by product & region |
| `GET /api/v1/analytics/price-trends` | Price trends from transaction history |
| `GET /api/v1/analytics/summary` | Overview with top products and trends |

### Analytics Features

- **Supply Trends**: Tracks listing quantities over time, grouped by day/week/month
- **Demand Trends**: Tracks order quantities over time with regional breakdown
- **Supply-Demand Comparison**: Identifies surplus/deficit regions for each product
- **Price Trends**: Moving averages and price volatility from transaction history
- **Auto-recording**: `record_order_price()` auto-records prices when orders are confirmed

## WhatsApp Chatbot

Meta Cloud API integration at `/api/v1/whatsapp/webhook` for farmers to submit harvest data.

### States

| State | Trigger | Next |
|---|---|---|
| `ONBOARD_NAME` | Text reply (name) | `ONBOARD_LOCATION` |
| `ONBOARD_LOCATION` | WhatsApp location share | `WELCOME` (creates Farmer) |
| `WELCOME` | "menu" or first message | Interactive list menu |
| `SUBMIT_PRODUCT` | Button selection or text | `SUBMIT_QUANTITY` |
| `SUBMIT_QUANTITY` | Number | `SUBMIT_PRICE` |
| `SUBMIT_PRICE` | Number | `SUBMIT_HARVEST_DATE` |
| `SUBMIT_HARVEST_DATE` | Date or "today" | `SUBMIT_LOCATION` |
| `SUBMIT_LOCATION` | WhatsApp location share | Summary + confirm |
| Confirm | Yes → creates Listing, No → back to product | — |

### Redis Keys

- `wa:session:{phone}` — session payload with state + harvest_data (TTL 900s)
- `wa:phone:{phone}` — farmer_id lookup for returning users (TTL 9000s)

### Session Payload

```json
{
  "phone": "+263771234567",
  "state": "SUBMIT_QUANTITY",
  "harvest_data": {"product_id": "...", "product_name": "Maize", "quantity": 500},
  "farmer_id": "uuid-or-null",
  "attempts": 0
}
```

### Error Handling

- 3 invalid attempts on any numeric/date input → session cleared, user must reply "menu"
- Commands "menu" and "help" work from any state
- Unknown messages get a reminder; after 3 attempts session resets

## Commands

```bash
# Dev server
.venv/bin/uvicorn app.main:app --reload

# Migrations
.venv/bin/alembic revision --autogenerate -m "description"
.venv/bin/alembic upgrade head

# Lint / format / typecheck
.venv/bin/ruff check app/
.venv/bin/ruff format app/
.venv/bin/pyright app/

# Redis (required for WhatsApp chatbot)
redis-server
```

## Common Pitfalls

- `DeclarativeBase` must be subclassed: `class Base(DeclarativeBase): pass` — not called like `DeclarativeBase()`
- `email-validator` package required for `EmailStr` in Pydantic
- Use `selectinload` in CRUD for eager-loading relationships
- All IDs are UUID v4 (PostgreSQL `uuid` type via `PG_UUID(as_uuid=True)`)
- Alembic `env.py` strips `+asyncpg` from URL for offline mode (sync driver needed)
- PostGIS extension must be enabled: `CREATE EXTENSION postgis` (migration handles this)
- Geo columns use `func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)` — note lon comes first
- Matching queries use raw SQL via `text()` for PostGIS functions
