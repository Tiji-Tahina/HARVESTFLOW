# HarvesterFlow

Agritech marketplace backend connecting farmers, buyers, and logistics providers. Built with FastAPI and PostgreSQL (PostGIS). Includes a WhatsApp chatbot for farmers to submit harvest data via Meta Cloud API.

## Tech Stack

- **FastAPI** 0.115 — async web framework
- **SQLAlchemy 2.0** — async ORM with `Mapped`/`mapped_column` style
- **GeoAlchemy2** — PostGIS geography type support
- **asyncpg** — PostgreSQL async driver
- **Pydantic v2** — request/response validation
- **Alembic** — database migrations
- **Redis** — WhatsApp chatbot session management
- **httpx** — async HTTP client for WhatsApp API
- **React + Vite** — Buyer dashboard frontend

## Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env  # edit DATABASE_URL (requires PostGIS extension)
alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs`

## Architecture

```
app/
├── main.py              # FastAPI app, lifespan, router mounting
├── config.py            # pydantic-settings (DATABASE_URL, WhatsApp, Redis)
├── database.py          # async engine, session factory, Base, get_db
├── models/__init__.py   # SQLAlchemy ORM models (7 entities)
├── schemas/             # Pydantic schemas (Create, Update, Read per entity)
├── crud/                # DB operations + supply-demand matching queries
├── routers/             # FastAPI routers with validation
└── whatsapp/            # WhatsApp chatbot (Meta Cloud API)
    ├── router.py        # Webhook endpoints
    ├── webhook.py       # Message dispatcher
    ├── flow.py          # Conversation state machine
    ├── session.py       # Redis session store
    └── templates.py     # Message builders
```

## Models

| Entity | Key Fields | Relationships |
|---|---|---|
| **Farmer** | id, name, email, phone, location | 1:N → Listings, Orders |
| **Buyer** | id, name, email, phone, location, geo, preferred_categories | 1:N → Orders |
| **Product** | id, name, category, unit_of_measure, description | 1:N → Listings |
| **Listing** | id, farmer_id, product_id, price_per_unit, quantity_available, status, harvest_date, geo | N:1 → Farmer, Product; 1:N → Orders |
| **Order** | id, listing_id, farmer_id, buyer_id, quantity, total_price, status | N:1 → Listing, Farmer, Buyer; 0..1 → Shipment |
| **Transporter** | id, name, vehicle_type, capacity_kg, is_available, phone, geo | 1:N → Shipments |
| **Shipment** | id, order_id (unique), transporter_id, pickup/delivery locations, geo_pickup, geo_delivery, status, tracking_notes | N:1 → Order, Transporter |

### Status Enums

- **Listing**: `draft`, `active`, `sold_out`
- **Order**: `pending`, `confirmed`, `in_transit`, `delivered`, `cancelled`
- **Transporter**: `available`, `unavailable`, `in_transit`
- **Shipment**: `scheduled`, `picked_up`, `in_transit`, `delivered`, `failed`

## Endpoints (all under `/api/v1`)

| Method | Path | Description |
|---|---|---|
| GET | `/farmers/` | List farmers |
| GET | `/buyers/` | List buyers |
| POST | `/buyers/` | Create buyer |
| GET | `/products/` | List products |
| GET | `/listings/` | List listings |
| GET | `/orders/` | List orders |
| POST | `/orders/` | Create order (total_price auto-calculated) |
| GET | `/transporters/` | List transporters |
| GET | `/shipments/` | List shipments |
| GET | `/shipments/order/{order_id}` | Get shipment by order |
| POST | `/shipments/` | Create shipment |
| **GET** | `/matching/supply-demand` | Supply-demand summary by product |
| **GET** | `/matching/nearby-listings` | Active listings within radius (PostGIS) |
| **GET** | `/matching/available-transporters` | Available transporters with capacity filter |
| **POST** | `/matching/find-listings` | Scored buyer-to-listing matching with combination suggestions |

**Special logic**: `Order.total_price` is auto-calculated from `listing.price_per_unit × order.quantity` on creation.

## Supply-Demand Matching

All geo-matching uses PostGIS `ST_DWithin` for efficient radius searches:

- `GET /matching/supply-demand` — materialized view aggregating supply (active listings) vs demand (open orders) by product
- `GET /matching/nearby-listings?lat=&lon=&radius_km=50` — finds active listings near a location
- `GET /matching/available-transporters?lat=&lon=&radius_km=50&min_capacity_kg=` — finds nearby transporters with sufficient capacity
- `POST /matching/find-listings` — scores and ranks listings for a buyer based on distance, price, and quantity fulfillment:
  ```json
  {
    "buyer_id": "uuid",
    "product_id": "uuid (or product_category)",
    "quantity": 100,
    "max_distance_km": 200
  }
  ```
  Returns individual matches with score breakdowns plus combination suggestions (multiple listings that together fulfill the order). Scoring formula: `0.4 × distance_score + 0.4 × price_score + 0.2 × quantity_score`.

## WhatsApp Chatbot

Farmers submit harvest data via WhatsApp using a conversational flow powered by Meta Cloud API with Redis session management.

### Setup

```bash
# Add to .env
WHATSAPP_VERIFY_TOKEN=your_verify_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_ACCESS_TOKEN=your_access_token
REDIS_URL=redis://localhost:6379/1
```

Ensure Redis is running: `redis-server`

### Webhook

Configure Meta Cloud API webhook URL to `https://your-domain/api/v1/whatsapp/webhook`

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/whatsapp/webhook` | Meta verification |
| POST | `/api/v1/whatsapp/webhook` | Receives incoming messages |

### Conversation Flow

```
New:  → Enter name → Share location (GPS) → Welcome menu
All:  → Submit Harvest → Select product → Enter quantity → Enter price → Enter date → Share location → Confirm → Listing created
Cmds: → "menu" → Return to main menu | "help" → Show help
```

Sessions expire after 15 minutes of inactivity. After 3 failed attempts on any input, the session resets.

## Validation

- `EmailStr` on farmer/buyer email
- `gt=0` on prices and quantities
- `min_length=1` on names
- Status enums enforced in schemas and DB
- Latitude/longitude validated to valid ranges

## Scripts

```bash
.venv/bin/ruff check app/          # lint
.venv/bin/ruff format app/         # format
.venv/bin/pyright app/             # type check
```
