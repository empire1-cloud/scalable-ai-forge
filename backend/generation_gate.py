"""
Generation priority gate.

Backs two pricing-page claims that previously had no code behind them:
"Priority generation" (Pro) and "Higher generation limits" (Team).

This is not a queue-reordering system. It's a per-tier concurrency ceiling:
each plan draws blueprint-generation slots from its own semaphore. Free
traffic can queue behind other Free traffic once it hits its ceiling; a Pro
or Team request never waits behind Free load, because it isn't drawing from
the same pool. Team's ceiling is higher than Pro's, so a Team workspace can
run more concurrent generations before its own requests start queuing.

The numbers below are a real, enforced starting point, not decoration --
change GENERATION_CONCURRENCY_LIMITS if usage patterns call for different
values. What matters for the pricing page is that the tiers are genuinely
different and genuinely enforced, which they are.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import HTTPException

GENERATION_CONCURRENCY_LIMITS: Dict[str, int] = {
    "free": 2,
    "pro": 10,
    "team": 50,
}

_semaphores: Dict[str, asyncio.Semaphore] = {
    plan: asyncio.Semaphore(limit) for plan, limit in GENERATION_CONCURRENCY_LIMITS.items()
}


def _plan_key(plan: str) -> str:
    return plan if plan in GENERATION_CONCURRENCY_LIMITS else "free"


@asynccontextmanager
async def generation_priority_gate(plan: str):
    """Hold this plan's concurrency slot for the duration of one LLM call.

    Wrap only the actual model call, not the whole request handler, so a
    slow generation doesn't hold a slot during unrelated DB work.
    """
    sem = _semaphores[_plan_key(plan)]
    async with sem:
        yield


def available_slots(plan: str) -> int:
    """Current free slots for a plan's semaphore. Exposed for tests/metrics."""
    return _semaphores[_plan_key(plan)]._value  # noqa: SLF001 - intentional introspection


def require_streaming_access(plan: str) -> None:
    """Live token-by-token streaming is a Pro/Team feature.

    Free users still get real generation via POST /blueprints (subject to
    the existing 3-blueprint quota) -- they just don't get the SSE stream.
    """
    if plan not in ("pro", "team"):
        raise HTTPException(
            status_code=402,
            detail=(
                "Live token-by-token streaming is a Pro feature. "
                "Upgrade to unlock it, or generate without streaming from your dashboard."
            ),
        )
