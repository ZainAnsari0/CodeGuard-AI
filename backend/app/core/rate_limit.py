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

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

_RATE_LIMIT_COOKIE = "x-rate-id"


def get_client_ip(request: Request) -> str:
    """Extract a unique client identifier for rate limiting.

    Resolution order:
      1. Rightmost IP from X-Forwarded-For (trusted proxy header)
      2. Direct connection host (request.client.host)
      3. Persistent cookie (x-rate-id) for anonymous clients
      4. Per-request UUID fallback — avoids collapsing all
         unidentified traffic into a single shared bucket
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

    # 4. Per-request fallback — each unidentified request gets its own
    #    unique identifier so no shared bucket throttles everyone.
    return str(uuid.uuid4())


limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW_SECONDS}seconds"],
    enabled=True,
)