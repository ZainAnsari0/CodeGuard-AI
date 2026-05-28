"""
CodeGuard AI - Guest Demo Endpoint
Serves pre-computed scan results for unauthenticated demo access.
Rate-limited to prevent abuse.
"""

from fastapi import APIRouter, Request

from app.core.rate_limit import limiter
from app.data.demo_scan_results import DEMO_SCAN_RESULTS

router = APIRouter()


@router.get("/demo", response_model=dict)
@limiter.limit("10/minute")
async def get_demo_results(request: Request):
    """Get pre-computed demo scan results (no auth required, rate-limited)."""
    return {
        "success": True,
        "message": "Demo scan results",
        "data": DEMO_SCAN_RESULTS,
    }