from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import (
    analytics,
    buyers,
    farmers,
    listings,
    matching,
    orders,
    price_history,
    products,
    shipments,
    transporters,
)
from app.whatsapp.router import router as whatsapp_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.include_router(farmers.router, prefix="/api/v1")
app.include_router(buyers.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(listings.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(transporters.router, prefix="/api/v1")
app.include_router(shipments.router, prefix="/api/v1")
app.include_router(matching.router, prefix="/api/v1")
app.include_router(price_history.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(whatsapp_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name}
