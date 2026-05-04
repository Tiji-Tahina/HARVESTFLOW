from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.whatsapp.session import Session, lookup_farmer_id
from app.whatsapp.templates import text_msg


async def dispatch_message(
    to_phone: str,
    msg_type: str,
    text: str | None = None,
    location: dict | None = None,
    interactive_reply: dict | None = None,
    db: AsyncSession | None = None,
) -> dict:
    session = Session(to_phone)
    current_state = session.state
    access_token = settings.whatsapp_access_token
    phone_id = settings.whatsapp_phone_number_id

    if current_state is None:
        return await _handle_new_user(to_phone, session, access_token, phone_id)

    if text and text.strip().lower() == "menu":
        from app.whatsapp.flow import handle_menu

        return await handle_menu(session, to_phone, access_token, phone_id, None)

    if text and text.strip().lower() == "help":
        from app.whatsapp.flow import handle_help

        return await handle_help(session)

    handler_map = {
        "ONBOARD_NAME": _handle_onboard_name,
        "ONBOARD_LOCATION": _handle_onboard_location,
        "WELCOME": _handle_welcome,
        "SUBMIT_PRODUCT": _handle_submit_product,
        "SUBMIT_PRODUCT_MANUAL": _handle_submit_product_manual,
        "SUBMIT_QUANTITY": _handle_submit_quantity,
        "SUBMIT_PRICE": _handle_submit_price,
        "SUBMIT_HARVEST_DATE": _handle_submit_harvest_date,
        "SUBMIT_LOCATION": _handle_submit_location,
        "CONFIRM_SUMMARY": _handle_confirm_summary,
    }

    handler = handler_map.get(current_state)
    if handler is None:
        from app.whatsapp.flow import handle_unknown

        return await handle_unknown(session)

    if (
        msg_type == "location"
        and location
        and current_state in ("ONBOARD_LOCATION", "SUBMIT_LOCATION")
    ):
        return await handler(
            location["latitude"],
            location["longitude"],
            session,
            to_phone,
            access_token,
            phone_id,
            db,
        )

    if msg_type == "interactive" and interactive_reply:
        reply_id = interactive_reply.get("id", "")
        if reply_id.startswith("prod_"):
            product_id = reply_id.replace("prod_", "")
            from app.whatsapp.flow import handle_product_selected

            return await handle_product_selected(product_id, session, db)
        if reply_id == "opt_1":
            from app.whatsapp.flow import handle_submit_product

            return await handle_submit_product(session, to_phone, access_token, phone_id, db)
        if reply_id == "opt_2":
            from app.whatsapp.flow import handle_my_listings

            return await handle_my_listings(session, db)
        if reply_id == "opt_3":
            from app.whatsapp.flow import handle_help

            return await handle_help(session)
        if reply_id in ("confirm_yes", "yes"):
            from app.whatsapp.flow import handle_confirm_yes

            return await handle_confirm_yes(session, to_phone, access_token, phone_id, db)
        if reply_id in ("confirm_no", "no"):
            from app.whatsapp.flow import handle_confirm_no

            return await handle_confirm_no(session)

    if text is not None and current_state not in ("ONBOARD_LOCATION", "SUBMIT_LOCATION"):
        return await handler(text, session, db)

    if text is None and current_state not in ("ONBOARD_LOCATION", "SUBMIT_LOCATION"):
        from app.whatsapp.flow import handle_unknown

        return await handle_unknown(session)

    return text_msg("Please follow the prompts or reply 'menu' for options.")


async def _handle_new_user(
    to_phone: str, session: Session, access_token: str, phone_id: str
) -> dict:
    farmer_id = lookup_farmer_id(to_phone)
    if farmer_id:
        from app.whatsapp.flow import handle_welcome

        session.set("WELCOME", farmer_id=farmer_id)
        return await handle_welcome(session, to_phone, access_token, phone_id, None)
    from app.whatsapp.flow import handle_new_user

    return await handle_new_user(session, to_phone, access_token, phone_id, None)


async def _handle_onboard_name(text: str, session: Session, db: AsyncSession | None = None) -> dict:
    from app.whatsapp.flow import handle_onboard_name

    return await handle_onboard_name(text, session, None, None, None, None)


async def _handle_onboard_location(
    lat: float,
    lon: float,
    session: Session,
    to_phone: str,
    access_token: str,
    phone_id: str,
    db: AsyncSession | None = None,
) -> dict:
    from app.whatsapp.flow import handle_onboard_location

    return await handle_onboard_location(
        lat, lon, session, to_phone, access_token, phone_id, None, db
    )


async def _handle_welcome(text: str, session: Session, db: AsyncSession | None = None) -> dict:
    from app.whatsapp.flow import handle_welcome

    return await handle_welcome(session, None, None, None, None)


async def _handle_submit_product(
    text: str, session: Session, db: AsyncSession | None = None
) -> dict:
    from app.whatsapp.flow import handle_submit_product

    return await handle_submit_product(session, None, None, None, None, db)


async def _handle_submit_product_manual(
    text: str, session: Session, db: AsyncSession | None = None
) -> dict:
    if not text or not text.strip():
        session.inc_attempts()
        return text_msg("Please type a product name.")
    product_name = text.strip()
    if db is None:
        session.update_harvest({"product_name": product_name})
        session.set_state("SUBMIT_QUANTITY")
        return text_msg(
            f"New product '{product_name}' noted.\n\nHow many units do you have? (e.g., 500)"
        )
    from sqlalchemy import select

    from app.models import Product

    result = await db.execute(select(Product).where(Product.name.ilike(product_name)).limit(1))
    product = result.scalar_one_or_none()
    if product:
        from app.whatsapp.flow import handle_product_selected

        return await handle_product_selected(str(product.id), session, db)
    session.update_harvest({"product_name": product_name})
    session.set_state("SUBMIT_QUANTITY")
    return text_msg(
        f"New product '{product_name}' noted.\n\nHow many units do you have? (e.g., 500)"
    )


async def _handle_submit_quantity(
    text: str, session: Session, db: AsyncSession | None = None
) -> dict:
    from app.whatsapp.flow import handle_submit_quantity

    return await handle_submit_quantity(text, session)


async def _handle_submit_price(text: str, session: Session, db: AsyncSession | None = None) -> dict:
    from app.whatsapp.flow import handle_submit_price

    return await handle_submit_price(text, session)


async def _handle_submit_harvest_date(
    text: str, session: Session, db: AsyncSession | None = None
) -> dict:
    from app.whatsapp.flow import handle_submit_harvest_date

    return await handle_submit_harvest_date(text, session)


async def _handle_submit_location(
    lat: float,
    lon: float,
    session: Session,
    to_phone: str,
    access_token: str,
    phone_id: str,
    db: AsyncSession | None = None,
) -> dict:
    from app.whatsapp.flow import handle_submit_location

    return await handle_submit_location(lat, lon, session, to_phone, access_token, phone_id, None)


async def _handle_confirm_summary(
    text: str, session: Session, db: AsyncSession | None = None
) -> dict:
    if text and text.strip().lower() in ("yes", "confirm"):
        from app.whatsapp.flow import handle_confirm_yes

        return await handle_confirm_yes(session, None, None, None, db)
    from app.whatsapp.flow import handle_confirm_no

    return await handle_confirm_no(session)
