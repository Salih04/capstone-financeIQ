"""Tiny in-memory rate limiter (no Redis / external infra).

Fixed 60s sliding window per (scope, identity). Identity is the verified token
subject/email when a valid token is present, otherwise the client IP. Disabled
unless RATE_LIMIT_ENABLED=true, so it never affects local dev or normal app
navigation by default.

Single-process only — adequate for a single Render web service. Not shared across
replicas; that is acceptable for this deployment and documented.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from app.config import settings
from app.core.dependencies import optional_bearer_scheme
from app.core.security import decode_supabase_token, decode_token

_hits: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()
_WINDOW_SECONDS = 60.0


def _identity(request: Request, credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is not None:
        token = credentials.credentials
        try:
            sub = decode_token(token).get("sub")
            if sub is not None:
                return f"legacy:{sub}"
        except Exception:
            pass
        try:
            email = (decode_supabase_token(token).get("email") or "").strip().lower()
            if email:
                return f"email:{email}"
        except Exception:
            pass
    fwd = request.headers.get("x-forwarded-for")
    ip = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "unknown")
    return f"ip:{ip}"


def rate_limit(scope: str):
    """Dependency factory: throttle a route to N requests/min per identity."""

    def _dep(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
    ) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return
        limit = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        if limit <= 0:
            return
        key = f"{scope}:{_identity(request, credentials)}"
        now = time.monotonic()
        with _lock:
            dq = _hits[key]
            while dq and now - dq[0] > _WINDOW_SECONDS:
                dq.popleft()
            if len(dq) >= limit:
                retry = int(_WINDOW_SECONDS - (now - dq[0])) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please slow down and try again shortly.",
                    headers={"Retry-After": str(max(1, retry))},
                )
            dq.append(now)

    return _dep
