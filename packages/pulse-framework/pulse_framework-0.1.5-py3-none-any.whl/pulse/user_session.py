from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Literal, Optional

from fastapi import Response

from pulse.context import PulseContext
from pulse.cookies import SetCookie
from pulse.reactive import Effect
from pulse.reactive_extensions import ReactiveDict, reactive

if TYPE_CHECKING:
    from pulse.app import App

Session = ReactiveDict[str, Any]

logger = logging.getLogger(__name__)


class UserSession:
    sid: str
    data: Session

    def __init__(self, sid: str, data: dict[str, Any], handling_request=False) -> None:
        self.sid = sid
        self.data = reactive(data)
        self._scheduled_cookie_refresh = False
        self._handling_request = handling_request
        self._queued_cookies: dict[str, SetCookie] = {}
        self._effect = Effect(self.save, name=f"save_session:{self.sid}")

    async def save(self):
        app = PulseContext.get().app
        if isinstance(app.session_store, CookieSessionStore):
            self._refresh_session_cookie(app)
        else:
            await app.session_store.save(self.sid, self.data)

    def _refresh_session_cookie(self, app: "App"):
        assert isinstance(app.session_store, CookieSessionStore)
        signed_cookie = app.session_store.encode(self.sid, self.data)
        self.set_cookie(
            name=app.cookie.name,
            value=signed_cookie,
            domain=app.cookie.domain,
            secure=app.cookie.secure,
            samesite=app.cookie.samesite,
            max_age_seconds=app.cookie.max_age_seconds,
        )

    def dispose(self):
        self._effect.dispose()

    def handling_request(self):
        self._handling_request = True

    def handle_response(self, res: Response):
        for cookie in self._queued_cookies.values():
            cookie.set_on_fastapi(res, cookie.value)
        self._queued_cookies.clear()
        self._scheduled_cookie_refresh = False
        self._handling_request = False

    def set_cookie(
        self,
        name: str,
        value: str,
        domain: Optional[str] = None,
        secure: bool = True,
        samesite: Literal["lax", "strict", "none"] = "lax",
        max_age_seconds: int = 7 * 24 * 3600,
    ):
        cookie = SetCookie(
            name=name,
            value=value,
            domain=domain,
            secure=secure,
            samesite=samesite,
            max_age_seconds=max_age_seconds,
        )
        self._queued_cookies[name] = cookie
        if self._handling_request:
            # cookies will be set at the end of the reuqest
            return
        # Otherwise, schedule a cookie refresh for this user
        if not self._scheduled_cookie_refresh:
            ctx = PulseContext.get()
            ctx.app.refresh_cookies(self.sid)


class SessionStore(ABC):
    """Abstract base for server-backed session stores (DB, cache, memory).

    Implementations persist session state on the server and place only a stable
    identifier in the cookie. Override methods to integrate with your backend.
    """

    async def init(self) -> None:
        """Optional async initializer, invoked when the app starts.

        Override in implementations that need to establish connections or
        perform startup work. Default is a no-op.
        """
        return None

    async def close(self) -> None:
        """Optional async cleanup, invoked when the app shuts down.

        Override in implementations that need to tear down connections or
        perform cleanup. Default is a no-op.
        """
        return None

    @abstractmethod
    async def get(self, sid: str) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    async def create(self, sid: str) -> dict[str, Any]: ...

    @abstractmethod
    async def delete(self, sid: str) -> None: ...

    @abstractmethod
    async def save(self, sid: str, session: dict[str, Any]) -> None: ...


class InMemorySessionStore(SessionStore):
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    async def get(self, sid: str) -> Optional[dict[str, Any]]:
        return self._sessions.get(sid)

    async def create(self, sid: str) -> dict[str, Any]:
        session: Session = ReactiveDict()
        self._sessions[sid] = session
        return session

    async def save(self, sid: str, session: dict[str, Any]):
        # Should not matter as the session ReactiveDict is normally mutated directly
        self._sessions[sid] = session

    async def delete(self, sid: str) -> None:
        self._sessions.pop(sid, None)


class CookieSessionStore:
    """Persist session in a signed cookie (Flask-like default).

    The cookie stores a compact JSON of the session and is signed using
    HMAC-SHA256 to prevent tampering. Keep the session small (<4KB).
    """

    def __init__(
        self,
        secret: Optional[str] = None,
        *,
        salt: str = "pulse.session",
        digestmod: str = "sha256",
        max_cookie_bytes: int = 3800,
    ) -> None:
        if not secret:
            secret = (
                os.environ.get("PULSE_SECRET") or os.environ.get("SECRET_KEY") or ""
            )
            if not secret:
                mode = os.environ.get("PULSE_MODE", "dev").lower()
                if mode == "prod":
                    # In CI/production, require an explicit secret
                    raise RuntimeError(
                        "PULSE_SECRET must be set when using CookieSessionStore in production.\nCookieSessionStore is the default way of storing sessions in Pulse. Providing a secret is necessary to not invalidate all sessions on reload."
                    )
                # In dev, use an ephemeral secret silently
                secret = secrets.token_urlsafe(32)
        self._secret = secret.encode("utf-8")
        self._salt = salt.encode("utf-8")
        self._digest = getattr(hashlib, digestmod)
        self._max_cookie_bytes = max_cookie_bytes

    def encode(self, sid: str, session: dict[str, Any]) -> str:
        # Encode the entire session into the cookie
        try:
            # Convert to a plain dict for JSON serialization
            data = {"sid": sid, "data": dict(session)}
            payload = json.dumps(data, separators=(",", ":"))
            signed = self._sign(payload)
            if len(signed) > self._max_cookie_bytes:
                # If too large, fall back to an empty session to avoid breaking cookies
                return self.encode(sid, {})
            return signed
        except Exception:
            # Best effort: fallback to an empty session if it's not serializable
            return self.encode(sid, {})

    def decode(self, cookie: str) -> tuple[str, Session]:
        """Decode a signed session cookie.

        Returns a tuple of (session_id, session_data). If the cookie is invalid,
        returns a new session ID and empty session.
        """
        if not cookie:
            return new_sid(), ReactiveDict()

        payload = self._unsign(cookie)
        if not payload:
            return new_sid(), ReactiveDict()

        try:
            data = json.loads(payload)
            return data["sid"], ReactiveDict(data["data"])
        except Exception:
            return new_sid(), ReactiveDict()

    # --- signing helpers ---
    def _mac(self, payload: bytes) -> bytes:
        return hmac.new(
            self._secret + b"|" + self._salt, payload, self._digest
        ).digest()

    def _sign(self, payload: str) -> str:
        raw = payload.encode("utf-8")
        mac = self._mac(raw)
        b64 = base64.urlsafe_b64encode(raw).rstrip(b"=")
        sig = base64.urlsafe_b64encode(mac).rstrip(b"=")
        return f"v1.{b64.decode('ascii')}.{sig.decode('ascii')}"

    def _unsign(self, token: str) -> Optional[str]:
        try:
            if not token.startswith("v1."):
                return None
            _, b64, sig = token.split(".", 2)

            # Pad base64
            def _pad(s: str) -> bytes:
                return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

            raw = _pad(b64)
            mac = _pad(sig)
            expected = self._mac(raw)
            if not hmac.compare_digest(mac, expected):
                return None
            return raw.decode("utf-8")
        except Exception:
            return None


def new_sid() -> str:
    return uuid.uuid4().hex
