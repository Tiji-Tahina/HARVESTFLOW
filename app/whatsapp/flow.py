from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import farmer as farmer_crud
from app.crud import product as product_crud
from app.models import Listing
from app.schemas.farmer import FarmerCreate
from app.whatsapp.session import Session, link_farmer_phone
from app.whatsapp.templates import (
    harvest_summary,
    list_msg,
    menu_sections,
    product_sections,
    text_msg,
)

MAX_ATTEMPTS = 3
MENU_OPTIONS = [
    ("Submit Harvest", "Add new harvest data"),
    ("My Listings", "View your active listings"),
    ("Help", "How to use this bot"),
]


def _parse_date(raw: str) -> date | None:
    raw = raw.strip().lower()
    today = date.today()
    if raw == "today":
        return today
    if raw == "tomorrow":
        return today + timedelta(days=1)
    if raw == "yesterday":
        return today - timedelta(days=1)
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


async def _send_wa(to: str, payload: dict, access_token: str, phone_id: str, httpx_client):
    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    payload["to"] = to
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    await httpx_client.post(url, json=payload, headers=headers)


async def handle_new_user(
    session: Session,
    to_phone: str | None = None,
    access_token: str | None = None,
    phone_id: str | None = None,
    httpx_client=None,
) -> dict:
    msg = list_msg(
        header="Welcome to HarvestFlow",
        body="Hi! Let's get you set up to submit harvest data. What's your name?",
        footer="Reply with your full name",
        sections=[],
    )
    session.set("ONBOARD_NAME")
    return msg


async def handle_onboard_name(
    text: str,
    session: Session,
    to_phone: str | None = None,
    access_token: str | None = None,
    phone_id: str | None = None,
    httpx_client=None,
) -> dict:
    if not text.strip():
        session.inc_attempts()
        return text_msg("Please reply with your name.")
    session.update_harvest({"farmer_name": text.strip()})
    session.set_state("ONBOARD_LOCATION")
    return text_msg(
        f"Thanks, {text.strip()}! Now share your farm location:\n\n"
        "1. Tap the attachment icon (paperclip)\n"
        "2. Select Location\n"
        "3. Send your current location"
    )


async def handle_onboard_location(
    lat: float,
    lon: float,
    session: Session,
    to_phone: str | None = None,
    access_token: str | None = None,
    phone_id: str | None = None,
    httpx_client=None,
    db: AsyncSession | None = None,
) -> dict:
    if db is None or to_phone is None:
        return text_msg("Error: Database connection required.")
    name = session.harvest_data.get("farmer_name", "")
    farmer_create = FarmerCreate(
        name=name,
        email=f"{name.lower().replace(' ', '.')}@harvestflow.local",
        phone=to_phone,
        location=f"({lat}, {lon})",
    )
    farmer = await farmer_crud.create_farmer(db, farmer_create)
    await db.commit()
    link_farmer_phone(to_phone, str(farmer.id))
    session.set("WELCOME", farmer_id=str(farmer.id))
    return text_msg(
        f"Welcome aboard, {name}! Your account is ready.\n\n"
        "Reply 'menu' to see your options anytime."
    )


async def handle_welcome(
    session: Session,
    to_phone: str | None = None,
    access_token: str | None = None,
    phone_id: str | None = None,
    httpx_client=None,
) -> dict:
    sections = menu_sections(MENU_OPTIONS)
    return list_msg(
        header="HarvestFlow Menu",
        body="What would you like to do?",
        footer="Select an option",
        sections=sections,
    )


async def handle_menu(
    session: Session,
    to_phone: str | None = None,
    access_token: str | None = None,
    phone_id: str | None = None,
    httpx_client=None,
) -> dict:
    sections = menu_sections(MENU_OPTIONS)
    return list_msg(
        header="HarvestFlow Menu",
        body="What would you like to do?",
        footer="Select an option",
        sections=sections,
    )


async def handle_submit_product(
    session: Session,
    to_phone: str | None = None,
    access_token: str | None = None,
    phone_id: str | None = None,
    httpx_client=None,
    db: AsyncSession | None = None,
) -> dict:
    if db is None:
        return text_msg("Error: Database connection required.")
    products = await product_crud.get_products(db, limit=10)
    if not products:
        session.set("SUBMIT_PRODUCT_MANUAL")
        return text_msg("No products found. Please type the product name (e.g., Maize, Tomatoes).")
    product_list = [
        {
            "id": str(p.id),
            "name": p.name,
            "category": p.category,
            "unit_of_measure": p.unit_of_measure,
        }
        for p in products
    ]
    sections = product_sections(product_list)
    return list_msg(
        header="Select Product",
        body="Choose the crop you harvested:",
        footer="Don't see your product? Type its name",
        sections=sections,
    )


async def handle_product_selected(
    product_id: str, session: Session, db: AsyncSession | None = None
) -> dict:
    if db is None:
        return text_msg("Error: Database connection required.")
    product = await product_crud.get_product(db, UUID(product_id))
    if not product:
        return text_msg("Product not found. Please select again or type the product name.")
    session.update_harvest(
        {
            "product_id": str(product.id),
            "product_name": product.name,
            "unit_of_measure": product.unit_of_measure,
        }
    )
    session.set_state("SUBMIT_QUANTITY")
    return text_msg(
        f"Product: *{product.name}*\n\nHow many {product.unit_of_measure} do you have? (e.g., 500)"
    )


async def handle_submit_quantity(text: str, session: Session) -> dict:
    try:
        qty = float(text.strip())
        if qty <= 0:
            raise ValueError
    except (ValueError, TypeError):
        n = session.inc_attempts()
        if n >= MAX_ATTEMPTS:
            session.clear()
            return text_msg("Too many invalid attempts. Reply 'menu' to start over.")
        return text_msg("Please enter a valid number greater than 0.")
    session.update_harvest({"quantity": qty})
    session.set_state("SUBMIT_PRICE")
    unit = session.harvest_data.get("unit_of_measure", "unit")
    return text_msg(
        f"Quantity recorded: {qty} {unit}.\n\nWhat's the price per {unit}? (e.g., 25.00)"
    )


async def handle_submit_price(text: str, session: Session) -> dict:
    try:
        price = float(text.strip())
        if price <= 0:
            raise ValueError
    except (ValueError, TypeError):
        n = session.inc_attempts()
        if n >= MAX_ATTEMPTS:
            session.clear()
            return text_msg("Too many invalid attempts. Reply 'menu' to start over.")
        return text_msg("Please enter a valid price greater than 0.")
    session.update_harvest({"price_per_unit": price})
    session.set_state("SUBMIT_HARVEST_DATE")
    return text_msg(
        "When was this harvested?\n\n"
        "Reply with a date (YYYY-MM-DD) or type "
        "'today', 'yesterday', 'tomorrow'."
    )


async def handle_submit_harvest_date(text: str, session: Session) -> dict:
    d = _parse_date(text)
    if d is None:
        n = session.inc_attempts()
        if n >= MAX_ATTEMPTS:
            session.clear()
            return text_msg("Too many invalid attempts. Reply 'menu' to start over.")
        return text_msg("Please enter a valid date in YYYY-MM-DD format, or type 'today'.")
    session.update_harvest({"harvest_date": d.isoformat()})
    session.set_state("SUBMIT_LOCATION")
    return text_msg(
        "Now share your farm location for this harvest:\n\n"
        "1. Tap the attachment icon (paperclip)\n"
        "2. Select Location\n"
        "3. Send your location"
    )


async def handle_submit_location(
    lat: float,
    lon: float,
    session: Session,
    to_phone: str | None = None,
    access_token: str | None = None,
    phone_id: str | None = None,
    httpx_client=None,
) -> dict:
    session.update_harvest({"lat": lat, "lon": lon})
    hd = session.harvest_data
    location_str = f"({lat:.6f}, {lon:.6f})"
    return harvest_summary(
        product=hd.get("product_name", "Unknown"),
        quantity=hd.get("quantity", 0),
        price=hd.get("price_per_unit", 0),
        date=hd.get("harvest_date", ""),
        location=location_str,
    )


async def handle_confirm_yes(
    session: Session,
    to_phone: str | None = None,
    access_token: str | None = None,
    phone_id: str | None = None,
    httpx_client=None,
    db: AsyncSession | None = None,
) -> dict:
    hd = session.harvest_data
    farmer_id = session.farmer_id
    if not farmer_id:
        session.clear()
        return text_msg("Error: No farmer account found. Reply 'menu' to start over.")
    if db is None:
        session.clear()
        return text_msg("Error: Database connection required.")
    try:
        geo_point = func.ST_SetSRID(func.ST_MakePoint(hd["lon"], hd["lat"]), 4326)
        listing_obj = Listing(
            farmer_id=UUID(farmer_id),
            product_id=UUID(hd["product_id"]),
            price_per_unit=hd["price_per_unit"],
            quantity_available=hd["quantity"],
            harvest_date=date.fromisoformat(hd["harvest_date"]),
            geo=geo_point,
        )
        db.add(listing_obj)
        await db.flush()
        await db.refresh(listing_obj)
        await db.commit()
    except Exception:
        await db.rollback()
        session.clear()
        return text_msg(
            "Something went wrong while saving. Please try again. Reply 'menu' to start over."
        )

    session.clear()
    return text_msg(
        f"Harvest submitted successfully!\n\n"
        f"Listing ID: {listing_obj.id}\n"
        f"Product: {hd['product_name']}\n"
        f"Quantity: {hd['quantity']}\n\n"
        f"Reply 'menu' to submit another."
    )


async def handle_confirm_no(session: Session) -> dict:
    session.set_state("SUBMIT_PRODUCT")
    return text_msg("Let's start over. Select a product:")


async def handle_my_listings(session: Session, db: AsyncSession | None = None) -> dict:
    if db is None:
        return text_msg("Error: Database connection required.")
    farmer_id = session.farmer_id
    if not farmer_id:
        return text_msg("Error: No farmer account found.")
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Listing)
        .options(selectinload(Listing.product))
        .where(Listing.farmer_id == UUID(farmer_id))
        .order_by(Listing.created_at.desc())
        .limit(5)
    )
    listings = result.scalars().all()
    if not listings:
        return text_msg(
            "You don't have any listings yet. Reply 'menu' to submit your first harvest."
        )
    lines = ["Your recent listings:"]
    for i, listing in enumerate(listings, 1):
        u = listing.product.unit_of_measure
        lines.append(
            f"\n{i}. {listing.product.name} | {listing.quantity_available} {u} "
            f"@ ${listing.price_per_unit:.2f}/{u} | {listing.status}"
        )
    return text_msg("\n".join(lines))


async def handle_help(session: Session) -> dict:
    return text_msg(
        "HarvestFlow Bot Help:\n\n"
        "1. Submit Harvest - Add new harvest data\n"
        "2. My Listings - View your active listings\n\n"
        "Commands:\n"
        "• menu - Return to main menu\n"
        "• help - Show this help\n\n"
        "Tips:\n"
        "• Share your location via the paperclip icon\n"
        "• Dates can be 'today', 'yesterday', or YYYY-MM-DD"
    )


async def handle_unknown(session: Session) -> dict:
    n = session.inc_attempts()
    if n >= MAX_ATTEMPTS:
        session.clear()
        return text_msg("Too many unrecognized messages. Reply 'menu' to start over.")
    return text_msg(
        "I didn't understand that. Reply 'menu' to see your options, or 'help' for assistance."
    )
