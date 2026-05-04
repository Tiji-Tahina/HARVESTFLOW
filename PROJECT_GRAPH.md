# HarvesterFlow — Project Graph (Token-Efficient Reference)

## File Tree
```
app/
├── __init__.py
├── main.py          → FastAPI app, lifespan, 9 routers @ /api/v1
├── config.py        → Settings(DATABASE_URL, APP_NAME, DEBUG, WhatsApp, Redis)
├── database.py      → engine, async_session, class Base(DeclarativeBase), get_db()
├── models/__init__.py
├── schemas/{farmer,buyer,product,listing,order,transporter,shipment,matching}.py
├── crud/{farmer,buyer,product,listing,order,transporter,shipment,matching}.py
├── routers/{farmers,buyers,products,listings,orders,transporters,shipments,matching}.py
└── whatsapp/
    ├── router.py     → GET/POST /webhook (Meta verification + message handling)
    ├── webhook.py    → dispatch_message() → routes by state + msg type
    ├── flow.py       → state machine handlers (onboard, submit harvest, confirm)
    ├── session.py    → Redis session store (TTL 900s), farmer phone lookup
    └── templates.py  → text_msg, list_msg, button_msg, harvest_summary
alembic/env.py, alembic.ini, script.py.mako
alembic/versions/001_add_buyer_shipment_geo.py
```

## Models (app/models/__init__.py)
```
class Farmer(Base):
    id(UUID PK), name, email(unique idx), phone?, location?
    created_at, updated_at
    → listings, orders

class Buyer(Base):
    id(UUID PK), name, email(unique idx), phone?, location?, geo(Geography POINT), preferred_categories(ARRAY?)
    created_at, updated_at
    → orders

class Product(Base):
    id(UUID PK), name(idx), category(idx), unit_of_measure, description?
    created_at
    → listings

class Listing(Base):
    id(UUID PK), farmer_id(FK), product_id(FK)
    price_per_unit(10,2), quantity_available(10,2)
    status[enum: draft|active|sold_out] → default draft
    harvest_date?, geo(Geography POINT)
    created_at, updated_at
    ← farmer, ← product → orders

class Order(Base):
    id(UUID PK), listing_id(FK), farmer_id(FK), buyer_id(FK)
    quantity(10,2), total_price(10,2)
    status[enum: pending|confirmed|in_transit|delivered|cancelled]
    created_at, updated_at
    ← listing, ← farmer, ← buyer → shipment

class Transporter(Base):
    id(UUID PK), name, vehicle_type, capacity_kg(10,2)
    is_available[enum: available|unavailable|in_transit] → default available
    phone?, geo(Geography POINT)
    created_at, updated_at
    → shipments

class Shipment(Base):
    id(UUID PK), order_id(FK unique), transporter_id(FK)
    pickup_location, delivery_location
    geo_pickup(Geography POINT), geo_delivery(Geography POINT)
    estimated_delivery?, actual_delivery?
    status[enum: scheduled|picked_up|in_transit|delivered|failed] → default scheduled
    tracking_notes?
    created_at, updated_at
    ← order, ← transporter
```

## Schemas Pattern (per entity in app/schemas/)
```
EntityBase(BaseModel)     → fields with Field(..., constraints)
EntityCreate(EntityBase)  → pass (or extra required)
EntityUpdate(BaseModel)   → optional fields with Field(None, ...)
EntityRead(EntityBase)    → + id, timestamps, model_config = from_attributes
EntityDetail(EntityRead)  → + nested relation dicts (listing, order, shipment, buyer)
```
**Geo handling**: Schema uses `latitude`/`longitude` floats (ge=-90..90, ge=-180..180). CRUD converts via `func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)`.

## CRUD Pattern (per entity in app/crud/)
```python
async def get_entities(db, skip=0, limit=100)  → select().offset().limit()
async def get_entity(db, id)                    → select().where(id==), scalar_one_or_none()
async def create_entity(db, entity)             → Model(**entity.model_dump(exclude geo fields)), set geo, flush, refresh
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
- Geo matching uses raw SQL via `text()` with PostGIS functions

## Matching CRUD (app/crud/matching.py)
```python
async def get_supply_demand_summary(db)    → SELECT * FROM supply_demand_summary (materialized view)
async def get_nearby_listings(db, lat, lon, radius_m, product_id?) → ST_DWithin on listings.geo
async def get_available_transporters(db, lat, lon, radius_m, min_capacity?) → ST_DWithin on transporters.geo
async def match_buyer_to_listings(db, buyer_id, quantity, max_distance_km, product_id?, product_category?)
  → Fetches buyer geo, queries active listings, scores by 0.4*dist + 0.4*price + 0.2*qty
  → Returns individual matches + greedy combination suggestions
```

## Matching Endpoints
```
GET  /api/v1/matching/supply-demand
GET  /api/v1/matching/nearby-listings?latitude=&longitude=&radius_km=50&product_id=
GET  /api/v1/matching/available-transporters?latitude=&longitude=&radius_km=50&min_capacity_kg=
POST /api/v1/matching/find-listings
  → body: {buyer_id, product_id|product_category, quantity, max_distance_km}
  → returns: {individual_matches: [...], combination_matches: [...], total_candidates}
```

## WhatsApp Endpoints
```
GET  /api/v1/whatsapp/webhook?hub.mode=&hub.verify_token=&hub.challenge  → verify (returns challenge)
POST /api/v1/whatsapp/webhook                                             → receive messages
```

## WhatsApp Chatbot (app/whatsapp/)

```
Message Flow:
  POST /webhook → parse WhatsApp payload → extract phone, msg_type, text/location/interactive
    → Session(phone) lookup → current_state
    → dispatch_message(phone, msg_type, text, location, interactive_reply, db)
      → state handler → returns response dict → _send_to_whatsapp() → Meta Cloud API

States: ONBOARD_NAME → ONBOARD_LOCATION → WELCOME → SUBMIT_PRODUCT → SUBMIT_QUANTITY →
        SUBMIT_PRICE → SUBMIT_HARVEST_DATE → SUBMIT_LOCATION → CONFIRM_SUMMARY → [creates Listing]

Session (Redis): wa:session:{phone} = {state, harvest_data, farmer_id, attempts} (TTL 900s)
Farmer lookup: wa:phone:{phone} = farmer_id (TTL 9000s)
```

## Enums
| Field | Values |
|---|---|
| Listing.status | draft, active, sold_out |
| Order.status | pending, confirmed, in_transit, delivered, cancelled |
| Transporter.is_available | available, unavailable, in_transit |
| Shipment.status | scheduled, picked_up, in_transit, delivered, failed |

## Validation
- `EmailStr` → requires `email-validator` package
- `Field(..., gt=0)` → prices, quantities, capacity_kg
- `Field(..., min_length=1, max_length=N)` → names
- `Field(..., ge=-90, le=90)` → latitude
- `Field(..., ge=-180, le=180)` → longitude
- UUID v4 primary keys via `PG_UUID(as_uuid=True)`

## DB Indexes & Optimization
```
idx_listings_active_product    → (status, product_id) WHERE status='active'
idx_transporters_available     → (is_available, capacity_kg) WHERE is_available='available'
idx_orders_buyer_status        → (buyer_id, status)
ix_buyers_email                → email (unique)
supply_demand_summary          → materialized view + idx on product_id
```

## Commands
```
dev:    .venv/bin/uvicorn app.main:app --reload
lint:   .venv/bin/ruff check app/
format: .venv/bin/ruff format app/
types:  .venv/bin/pyright app/
migrate:.venv/bin/alembic revision --autogenerate -m "msg" && upgrade head
redis:  redis-server  # required for WhatsApp chatbot
```
