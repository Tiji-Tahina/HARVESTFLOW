# HarvesterFlow — Agent Guide

## Project Overview

Agritech marketplace backend. FastAPI + async SQLAlchemy + PostgreSQL.

## File Structure (all under `/home/tsinjo/Documents/1. Projects/HarvestFlow`)

```
.venv/                         # virtual environment
app/
├── __init__.py
├── main.py                    # FastAPI app, lifespan creates tables, mounts 5 routers at /api/v1
├── config.py                  # Settings via pydantic-settings, reads .env
├── database.py                # async engine, async_session factory, Base class, get_db dependency
├── models/__init__.py         # ALL 5 ORM models defined here (not split): Farmer, Product, Listing, Order, Transporter
├── schemas/                   # one file per entity: farmer.py, product.py, listing.py, order.py, transporter.py
├── crud/                      # one file per entity with async CRUD functions
└── routers/                   # one file per entity with FastAPI APIRouter
alembic/                       # migrations (autogenerate configured)
alembic.ini
requirements.txt
pyproject.toml                 # ruff + pyright config
```

## Key Conventions

1. **Models**: All in `app/models/__init__.py` using SQLAlchemy 2.0 `Mapped`/`mapped_column` syntax
2. **Schemas**: Per entity — `*Create`, `*Update`, `*Read` (+ `*Detail` for listings/orders with nested relations)
3. **CRUD**: Async functions — `get_*`, `*_by_id`, `create_*`, `update_*`, `delete_*`. Always use `db.flush()` then `db.refresh()`.
4. **Routers**: Each has prefix `/{resource}s`, tag for grouping. List endpoint uses `skip`/`limit` query params.
5. **DB**: `get_db()` yields session, commits on success, rolls back on error. Lifespan calls `Base.metadata.create_all`.
6. **Validation**: Pydantic v2 — `Field(..., gt=0)` for positives, `EmailStr` for emails, `Enum` for statuses.
7. **Order total_price**: Computed in CRUD from `listing.price_per_unit × order.quantity`, NOT accepted from client.

## Model Relationships

```
Farmer 1 ── N Listing N ── 1 Product
Farmer 1 ── N Order N ── 1 Listing
Transporter 1 ── N Order N ── 1 Listing
```

## Status Enums

| Enum | Values |
|---|---|
| listing_status | draft, active, sold_out |
| order_status | pending, confirmed, in_transit, delivered, cancelled |
| transporter_status | available, unavailable, in_transit |

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
```

## Common Pitfalls

- `DeclarativeBase` must be subclassed: `class Base(DeclarativeBase): pass` — not called like `DeclarativeBase()`
- `email-validator` package required for `EmailStr` in Pydantic
- Use `selectinload` in CRUD for eager-loading relationships
- All IDs are UUID v4 (PostgreSQL `uuid` type via `PG_UUID(as_uuid=True)`)
- Alembic `env.py` strips `+asyncpg` from URL for offline mode (sync driver needed)
