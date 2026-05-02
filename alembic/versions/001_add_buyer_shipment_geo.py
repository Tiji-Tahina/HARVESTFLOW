"""add postgis extension, buyer, shipment models and geo indexes

Revision ID: 001
Revises:
Create Date: 2026-05-02
"""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "buyers",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("geo", Geography("POINT", srid=4326), nullable=True),
        sa.Column(
            "preferred_categories", sa.dialects.postgresql.ARRAY(sa.String(100)), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_buyers_email", "buyers", ["email"], unique=True)

    op.create_table(
        "shipments",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "order_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "transporter_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transporters.id"),
            nullable=False,
        ),
        sa.Column("pickup_location", sa.String(255), nullable=False),
        sa.Column("delivery_location", sa.String(255), nullable=False),
        sa.Column("geo_pickup", Geography("POINT", srid=4326), nullable=True),
        sa.Column("geo_delivery", Geography("POINT", srid=4326), nullable=True),
        sa.Column("estimated_delivery", sa.DateTime(), nullable=True),
        sa.Column("actual_delivery", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "scheduled",
                "picked_up",
                "in_transit",
                "delivered",
                "failed",
                name="shipment_status",
            ),
            server_default="scheduled",
        ),
        sa.Column("tracking_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.add_column("listings", sa.Column("harvest_date", sa.Date(), nullable=True))
    op.add_column("listings", sa.Column("geo", Geography("POINT", srid=4326), nullable=True))

    op.add_column(
        "orders",
        sa.Column(
            "buyer_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("buyers.id"),
            nullable=True,
        ),
    )

    op.add_column("transporters", sa.Column("geo", Geography("POINT", srid=4326), nullable=True))

    op.create_index(
        "idx_listings_active_product",
        "listings",
        ["status", "product_id"],
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "idx_transporters_available",
        "transporters",
        ["is_available", "capacity_kg"],
        postgresql_where=sa.text("is_available = 'available'"),
    )
    op.create_index("idx_orders_buyer_status", "orders", ["buyer_id", "status"])

    op.execute(
        """
        CREATE MATERIALIZED VIEW supply_demand_summary AS
        SELECT
            p.id AS product_id,
            p.name AS product_name,
            p.category,
            COUNT(DISTINCT l.id) FILTER (WHERE l.status = 'active') AS active_listings,
            COALESCE(SUM(l.quantity_available) FILTER (WHERE l.status = 'active'), 0) AS total_supply,
            COALESCE(AVG(l.price_per_unit) FILTER (WHERE l.status = 'active'), 0) AS avg_price,
            COUNT(DISTINCT o.id) FILTER (WHERE o.status IN ('pending', 'confirmed')) AS open_orders,
            COALESCE(SUM(o.quantity) FILTER (WHERE o.status IN ('pending', 'confirmed')), 0) AS total_demand
        FROM products p
        LEFT JOIN listings l ON l.product_id = p.id
        LEFT JOIN orders o ON o.listing_id = l.id AND o.status != 'cancelled'
        GROUP BY p.id, p.name, p.category
        """
    )
    op.execute("CREATE INDEX idx_supply_demand_product ON supply_demand_summary (product_id)")


def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS supply_demand_summary")
    op.drop_index("idx_orders_buyer_status", table_name="orders")
    op.drop_index("idx_transporters_available", table_name="transporters")
    op.drop_index("idx_listings_active_product", table_name="listings")
    op.drop_column("transporters", "geo")
    op.drop_column("orders", "buyer_id")
    op.drop_column("listings", "geo")
    op.drop_column("listings", "harvest_date")
    op.drop_table("shipments")
    op.drop_index("ix_buyers_email", table_name="buyers")
    op.drop_table("buyers")
    op.execute("DROP EXTENSION IF EXISTS postgis")
