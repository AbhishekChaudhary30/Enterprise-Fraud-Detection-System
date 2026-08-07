"""Request security middleware and process-local rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from uuid import uuid4

from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RateLimiter:
    """Fixed-window in-memory limiter suitable for one application process."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        """Initialize request capacity and time window."""
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        """Return whether a request may proceed for the client key."""
        now = time.monotonic()
        with self._lock:
            window = self._requests[key]
            while window and window[0] <= now - self.window_seconds:
                window.popleft()
            if len(window) >= self.limit:
                return False
            window.append(now)
            return True


class SecurityMiddleware:
    """ASGI middleware adding request IDs, security headers, and rate limiting."""

    def __init__(self, app: ASGIApp, limiter: RateLimiter, request_id_header: str) -> None:
        """Initialize middleware dependencies."""
        self.app = app
        self.limiter = limiter
        self.request_id_header = request_id_header

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process HTTP requests and leave non-HTTP scopes untouched."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        request_id = headers.get(self.request_id_header.lower().encode(), b"").decode() or str(
            uuid4()
        )
        client = scope.get("client")
        client_key = client[0] if client else "unknown"
        if not self.limiter.allow(client_key):
            response = JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
            response.headers[self.request_id_header] = request_id
            await response(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers.extend(
                    [
                        (self.request_id_header.lower().encode(), request_id.encode()),
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"referrer-policy", b"no-referrer"),
                        (b"content-security-policy", b"default-src 'self'"),
                    ]
                )
                message["headers"] = response_headers
            await send(message)

        scope["state"] = {**scope.get("state", {}), "request_id": request_id}
        await self.app(scope, receive, send_with_headers)
