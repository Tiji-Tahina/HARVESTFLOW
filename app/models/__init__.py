import uuid
from datetime import date, datetime

from geoalchemy2 import Geography
from sqlalchemy import ARRAY, Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Farmer(Base):
    __tablename__ = "farmers"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    listings: Mapped[list["Listing"]] = relationship(back_populates="farmer")
    orders: Mapped[list["Order"]] = relationship(back_populates="farmer")


class Buyer(Base):
    __tablename__ = "buyers"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    geo = mapped_column(Geography("POINT", srid=4326), nullable=True)
    preferred_categories: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    orders: Mapped[list["Order"]] = relationship(back_populates="buyer")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    unit_of_measure: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    listings: Mapped[list["Listing"]] = relationship(back_populates="product")


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farmers.id"))
    product_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("products.id"))
    price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity_available: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(
        Enum("draft", "active", "sold_out", name="listing_status"), default="draft"
    )
    harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    geo = mapped_column(Geography("POINT", srid=4326), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    farmer: Mapped["Farmer"] = relationship(back_populates="listings")
    product: Mapped["Product"] = relationship(back_populates="listings")
    orders: Mapped[list["Order"]] = relationship(back_populates="listing")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("listings.id"))
    farmer_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farmers.id"))
    buyer_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("buyers.id"))
    quantity: Mapped[float] = mapped_column(Numeric(10, 2))
    total_price: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "confirmed",
            "in_transit",
            "delivered",
            "cancelled",
            name="order_status",
        ),
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    listing: Mapped["Listing"] = relationship(back_populates="orders")
    farmer: Mapped["Farmer"] = relationship(back_populates="orders")
    buyer: Mapped["Buyer"] = relationship(back_populates="orders")
    shipment: Mapped["Shipment | None"] = relationship(back_populates="order", uselist=False)


class Transporter(Base):
    __tablename__ = "transporters"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100))
    vehicle_type: Mapped[str] = mapped_column(String(50))
    capacity_kg: Mapped[float] = mapped_column(Numeric(10, 2))
    is_available: Mapped[str] = mapped_column(
        Enum("available", "unavailable", "in_transit", name="transporter_status"),
        default="available",
    )
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    geo = mapped_column(Geography("POINT", srid=4326), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    shipments: Mapped[list["Shipment"]] = relationship(back_populates="transporter")


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("orders.id"), unique=True
    )
    transporter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("transporters.id")
    )
    pickup_location: Mapped[str] = mapped_column(String(255))
    delivery_location: Mapped[str] = mapped_column(String(255))
    geo_pickup = mapped_column(Geography("POINT", srid=4326), nullable=True)
    geo_delivery = mapped_column(Geography("POINT", srid=4326), nullable=True)
    estimated_delivery: Mapped[datetime | None] = mapped_column(nullable=True)
    actual_delivery: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "scheduled",
            "picked_up",
            "in_transit",
            "delivered",
            "failed",
            name="shipment_status",
        ),
        default="scheduled",
    )
    tracking_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    order: Mapped["Order"] = relationship(back_populates="shipment")
    transporter: Mapped["Transporter"] = relationship(back_populates="shipments")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("products.id")
    )
    region: Mapped[str] = mapped_column(String(100), index=True)
    price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity: Mapped[float] = mapped_column(Numeric(10, 2))
    transaction_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    order_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("orders.id")
    )

    product: Mapped["Product"] = relationship()
    order: Mapped["Order"] = relationship()
