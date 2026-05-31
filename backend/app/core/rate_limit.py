"""
CodeGuard AI - Rate Limiting Configuration
SlowAPI-based request rate limiting with secure IP extraction.

Trust model for X-Forwarded-For:
  We trust the rightmost (last) IP because it is set by the most
  immediately preceding trusted proxy. In a deployment behind a single
  reverse proxy (nginx, Cloudflare, AWS ALB), that rightmost value is
  the true client IP. Earlier/leftmost entries are client-supplied and
  can be spoofed — they MUST NOT be used for rate-limiting.
"""

import uuid

from fastapi import Request, Response
from slowapi import Limiter
from app.core.config import settings

_RATE_LIMIT_COOKIE = "x-rate-id"


def get_client_ip(request: Request) -> str:
    """Extract a unique client identifier for rate limiting.

    Resolution order:
      1. Rightmost IP from X-Forwarded-For (trusted proxy header)
      2. Direct connection host (request.client.host)
      3. Persistent cookie (x-rate-id) for anonymous clients
      4. Per-request UUID fallback — set as cookie for subsequent requests
    """
    # 1. Trusted reverse-proxy header
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        ips = [ip.strip() for ip in forwarded.split(",") if ip.strip()]
        if ips:
            return ips[-1]

    # 2. Direct connection host
    if request.client and request.client.host:
        return request.client.host

    # 3. Persistent cookie for anonymous clients
    rate_id = request.cookies.get(_RATE_LIMIT_COOKIE)
    if rate_id:
        return rate_id

    # 4. Generate a persistent ID and set it as a cookie so
    #    subsequent requests from the same client are bucketed together.
    rate_id = str(uuid.uuid4())
    # Store on request state so middleware can set the cookie on the response
    request.state._new_rate_id = rate_id
    return rate_id


def set_rate_limit_cookie(request: Request, response: Response) -> Response:
    """Middleware to set the rate-limit ID cookie if a new one was generated."""
    new_id = getattr(request.state, "_new_rate_id", None)
    if new_id:
        response.set_cookie(
            _RATE_LIMIT_COOKIE,
            new_id,
            max_age=86400 * 30,  # 30 days
            httponly=True,
            samesite="lax",
        )
    return response


limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW_SECONDS}seconds"],
    enabled=True,
)