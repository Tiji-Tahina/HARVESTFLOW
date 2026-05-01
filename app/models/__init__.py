import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text
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
    transporter_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("transporters.id"), nullable=True
    )
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
    transporter: Mapped["Transporter"] = relationship(back_populates="orders")


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
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    orders: Mapped[list["Order"]] = relationship(back_populates="transporter")
