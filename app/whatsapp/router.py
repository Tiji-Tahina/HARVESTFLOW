import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.get("/webhook")
async def verify_webhook(
    request: Request,
):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    from app.config import settings

    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        return int(challenge) if challenge else 0
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")


@router.post("/webhook")
async def handle_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    if "entry" not in body:
        return JSONResponse(status_code=200, content={"status": "ignored"})

    for entry in body["entry"]:
        for change in entry.get("changes", []):
            if change.get("field") != "messages":
                continue
            value = change.get("value", {})
            for message in value.get("messages", []):
                from_phone = message.get("from")
                msg_type = message.get("type")
                text = None
                location = None
                interactive_reply = None

                if msg_type == "text":
                    text = message.get("text", {}).get("body")
                elif msg_type == "location":
                    loc_data = message.get("location", {})
                    location = {
                        "latitude": loc_data.get("latitude"),
                        "longitude": loc_data.get("longitude"),
                    }
                elif msg_type == "interactive":
                    reply = message.get("interactive", {}).get("button_reply", {}) or message.get(
                        "interactive", {}
                    ).get("list_reply", {})
                    interactive_reply = {"id": reply.get("id"), "title": reply.get("title")}

                from app.whatsapp.webhook import dispatch_message

                response = await dispatch_message(
                    to_phone=from_phone,
                    msg_type=msg_type,
                    text=text,
                    location=location,
                    interactive_reply=interactive_reply,
                    db=db,
                )
                await _send_to_whatsapp(from_phone, response)

    return JSONResponse(status_code=200, content={"status": "received"})


async def _send_to_whatsapp(to_phone: str, payload: dict):
    import httpx

    from app.config import settings

    url = f"https://graph.facebook.com/v17.0/{settings.whatsapp_phone_number_id}/messages"
    payload["to"] = to_phone
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                logger.error(f"WhatsApp API error: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")


def verify_signature(request: Request, payload: bytes, signature: str) -> bool:
    from app.config import settings

    expected = hmac.new(
        settings.whatsapp_access_token.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
