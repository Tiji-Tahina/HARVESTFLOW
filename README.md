# HarvesterFlow

Agritech marketplace backend built with FastAPI and PostgreSQL.

## Tech Stack

- **FastAPI** 0.115 — async web framework
- **SQLAlchemy 2.0** — async ORM with `Mapped`/`mapped_column` style
- **asyncpg** — PostgreSQL async driver
- **Pydantic v2** — request/response validation
- **Alembic** — database migrations

## Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env  # edit DATABASE_URL
alembic revision --autogenerate -m "init"
alembic upgrade head
uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs`

## Architecture

```
app/
├── main.py              # FastAPI app, lifespan, router mounting
├── config.py            # pydantic-settings (DATABASE_URL, etc.)
├── database.py          # async engine, session factory, Base, get_db
├── models/__init__.py   # SQLAlchemy ORM models (Farmer, Product, Listing, Order, Transporter)
├── schemas/             # Pydantic schemas (Create, Update, Read per entity)
├── crud/                # DB operations (get, list, create, update, delete)
└── routers/             # FastAPI routers with validation
```

## Models

| Entity | Key Fields | Relationships |
|---|---|---|
| **Farmer** | id, name, email, phone, location | 1:N → Listings, Orders |
| **Product** | id, name, category, unit_of_measure, description | 1:N → Listings |
| **Listing** | id, farmer_id, product_id, price_per_unit, quantity_available, status | N:1 → Farmer, Product; 1:N → Orders |
| **Order** | id, listing_id, farmer_id, transporter_id, quantity, total_price, status | N:1 → Listing, Farmer, Transporter |
| **Transporter** | id, name, vehicle_type, capacity_kg, is_available, phone | 1:N → Orders |

### Status Enums

- **Listing**: `draft`, `active`, `sold_out`
- **Order**: `pending`, `confirmed`, `in_transit`, `delivered`, `cancelled`
- **Transporter**: `available`, `unavailable`, `in_transit`

## Endpoints (all under `/api/v1`)

| Method | Path | Description |
|---|---|---|
| GET | `/farmers/` | List farmers (skip/limit) |
| GET | `/farmers/{id}` | Get farmer + listings |
| POST | `/farmers/` | Create farmer |
| PUT | `/farmers/{id}` | Update farmer |
| DELETE | `/farmers/{id}` | Delete farmer |

Same CRUD pattern for `/products/`, `/listings/`, `/orders/`, `/transporters/`

**Special logic**: `Order.total_price` is auto-calculated from `listing.price_per_unit × order.quantity` on creation.

## Validation

- `EmailStr` on farmer email
- `gt=0` on prices and quantities
- `min_length=1` on names
- Status enums enforced in schemas and DB

## Scripts

```bash
.venv/bin/ruff check app/          # lint
.venv/bin/ruff format app/         # format
.venv/bin/pyright app/             # type check
```
