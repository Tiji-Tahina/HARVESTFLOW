import json
from datetime import datetime, timezone

import redis

from app.config import settings

_session_store = None


def get_redis() -> redis.Redis:  # type: ignore[no-any-return]
    global _session_store
    if _session_store is None:
        _session_store = redis.from_url(settings.redis_url, decode_responses=True)
    return _session_store


SESSION_TTL = 900
SESSION_PREFIX = "wa:session:"
FARMER_PHONE_PREFIX = "wa:phone:"


class Session:
    def __init__(self, phone: str):
        self.phone = phone
        self._key = f"{SESSION_PREFIX}{phone}"
        self.r = get_redis()

    def get(self) -> dict | None:
        raw = self.r.get(self._key)
        if raw is None:
            return None
        return json.loads(raw)  # type: ignore[reportArgumentType]

    def set(self, state: str, data: dict | None = None, farmer_id: str | None = None):
        payload = {
            "phone": self.phone,
            "state": state,
            "harvest_data": data or {},
            "farmer_id": farmer_id,
            "attempts": 0,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.r.setex(self._key, SESSION_TTL, json.dumps(payload))

    def update_harvest(self, updates: dict):
        raw = self.r.get(self._key)
        if raw is None:
            return
        payload = json.loads(raw)  # type: ignore[reportArgumentType]
        payload["harvest_data"].update(updates)
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.r.setex(self._key, SESSION_TTL, json.dumps(payload))

    def set_state(self, state: str):
        raw = self.r.get(self._key)
        if raw is None:
            return
        payload = json.loads(raw)  # type: ignore[reportArgumentType]
        payload["state"] = state
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.r.setex(self._key, SESSION_TTL, json.dumps(payload))

    def inc_attempts(self) -> int:
        raw = self.r.get(self._key)
        if raw is None:
            return 0
        payload = json.loads(raw)  # type: ignore[reportArgumentType]
        payload["attempts"] = payload.get("attempts", 0) + 1
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.r.setex(self._key, SESSION_TTL, json.dumps(payload))
        return payload["attempts"]

    def clear(self):
        self.r.delete(self._key)

    def exists(self) -> bool:
        return self.r.exists(self._key) == 1

    @property
    def state(self) -> str | None:
        s = self.get()
        return s.get("state") if s else None

    @property
    def farmer_id(self) -> str | None:
        s = self.get()
        return s.get("farmer_id") if s else None

    @property
    def harvest_data(self) -> dict:
        s = self.get()
        return s.get("harvest_data", {}) if s else {}


def link_farmer_phone(phone: str, farmer_id: str):
    get_redis().setex(f"{FARMER_PHONE_PREFIX}{phone}", SESSION_TTL * 10, farmer_id)


def lookup_farmer_id(phone: str) -> str | None:
    return get_redis().get(f"{FARMER_PHONE_PREFIX}{phone}")  # type: ignore[reportReturnType]
