# HarvesterFlow — Project Graph (Token-Efficient Reference)

## File Tree
```
app/
├── __init__.py
├── main.py          → FastAPI app, lifespan, 5 routers @ /api/v1
├── config.py        → Settings(DATABASE_URL, APP_NAME, DEBUG)
├── database.py      → engine, async_session, class Base(DeclarativeBase), get_db()
├── models/__init__.py
├── schemas/{farmer,product,listing,order,transporter}.py
├── crud/{farmer,product,listing,order,transporter}.py
└── routers/{farmers,products,listings,orders,transporters}.py
alembic/env.py, alembic.ini, script.py.mako
```

## Models (app/models/__init__.py)
```
class Farmer(Base):
    id(UUID PK), name(Str 100), email(Str 255 unique idx), phone(Str 20?), location(Str 255?)
    created_at, updated_at
    → listings, orders

class Product(Base):
    id(UUID PK), name(Str 100 idx), category(Str 100 idx), unit_of_measure(Str 20), description(Text?)
    created_at
    → listings

class Listing(Base):
    id(UUID PK), farmer_id(FK farmers), product_id(FK products)
    price_per_unit(10,2), quantity_available(10,2)
    status[enum: draft|active|sold_out] → default draft
    created_at, updated_at
    ← farmer, ← product → orders

class Order(Base):
    id(UUID PK), listing_id(FK listings), farmer_id(FK farmers), transporter_id(FK transporters?)
    quantity(10,2), total_price(10,2), status[enum: pending|confirmed|in_transit|delivered|cancelled]
    created_at, updated_at
    ← listing, ← farmer, ← transporter

class Transporter(Base):
    id(UUID PK), name(Str 100), vehicle_type(Str 50), capacity_kg(10,2)
    is_available[enum: available|unavailable|in_transit] → default available
    phone(Str 20?), created_at, updated_at
    → orders
```

## Schemas Pattern (per entity in app/schemas/)
```
EntityBase(BaseModel)     → name/fields with Field(..., constraints)
EntityCreate(EntityBase)  → pass (or extra required)
EntityUpdate(BaseModel)   → optional fields with Field(None, ...)
EntityRead(EntityBase)    → + id, timestamps, model_config = from_attributes
EntityDetail(EntityRead)  → + nested relation dicts (only for listing, order)
```

## CRUD Pattern (per entity in app/crud/)
```python
async def get_entities(db, skip=0, limit=100)  → select().offset().limit()
async def get_entity(db, id)                    → select().where(id==), scalar_one_or_none()
async def create_entity(db, entity)             → Model(**entity.model_dump()), flush, refresh
async def update_entity(db, id, entity)         → get, setattrs from model_dump(exclude_unset), flush, refresh
async def delete_entity(db, id)                 → get, delete, flush → bool
```

## Router Pattern (per entity in app/routers/)
```python
router = APIRouter(prefix="/entities", tags=["entities"])
GET  "/"      → list(skip, limit)
GET  "/{id}"  → get(id), 404 if None
POST "/"      → create(schema), 201
PUT  "/{id}"  → update(id, schema), 404 if None
DEL  "/{id}"  → delete(id), 204, 404 if None
```

## Key Logic
- `Order.total_price` = `listing.price_per_unit * order.quantity` (Decimal arithmetic, set in CRUD not schema)
- `get_db()` → yields session, commit on success, rollback on error
- Lifespan → `Base.metadata.create_all` via engine.begin()
- Alembic env.py strips `+asyncpg` for offline migrations

## Enums
| Field | Values |
|---|---|
| Listing.status | draft, active, sold_out |
| Order.status | pending, confirmed, in_transit, delivered, cancelled |
| Transporter.is_available | available, unavailable, in_transit |

## Validation
- `EmailStr` → requires `email-validator` package
- `Field(..., gt=0)` → prices, quantities, capacity_kg
- `Field(..., min_length=1, max_length=N)` → names
- UUID v4 primary keys via `PG_UUID(as_uuid=True)`

## Commands
```
dev:    .venv/bin/uvicorn app.main:app --reload
lint:   .venv/bin/ruff check app/
format: .venv/bin/ruff format app/
types:  .venv/bin/pyright app/
migrate:.venv/bin/alembic revision --autogenerate -m "msg" && upgrade head
```
