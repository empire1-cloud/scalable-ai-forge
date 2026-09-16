"""
Unit tests for generation_gate.py -- no Mongo, no Stripe, no LLM, no network.

These directly verify the claims the pricing page makes:
- "Priority generation" (Pro) / "Higher generation limits" (Team) are real,
  distinct, enforced concurrency ceilings per plan, not a shared queue.
- "Live token-by-token streaming" is gated to Pro/Team.
"""
import asyncio

import pytest
from fastapi import HTTPException

from generation_gate import (
    GENERATION_CONCURRENCY_LIMITS,
    available_slots,
    generation_priority_gate,
    require_streaming_access,
)


def test_tier_limits_are_distinct_and_ordered():
    """Team > Pro > Free -- the pricing page's "higher" claims must hold in code."""
    assert GENERATION_CONCURRENCY_LIMITS["free"] < GENERATION_CONCURRENCY_LIMITS["pro"]
    assert GENERATION_CONCURRENCY_LIMITS["pro"] < GENERATION_CONCURRENCY_LIMITS["team"]


def test_free_tier_queues_once_its_ceiling_is_held():
    """A Free request beyond the ceiling must wait for a slot to free up."""
    limit = GENERATION_CONCURRENCY_LIMITS["free"]
    order = []

    async def scenario():
        holders_ready = [asyncio.Event() for _ in range(limit)]
        release = asyncio.Event()

        async def holder(i):
            async with generation_priority_gate("free"):
                holders_ready[i].set()
                await release.wait()
            order.append(f"holder-{i}-released")

        async def waiter():
            for ev in holders_ready:
                await ev.wait()
            # every Free slot is held; this call must block until one is released
            async with generation_priority_gate("free"):
                order.append("waiter-acquired")

        tasks = [asyncio.create_task(holder(i)) for i in range(limit)]
        waiter_task = asyncio.create_task(waiter())

        for ev in holders_ready:
            await ev.wait()
        await asyncio.sleep(0.05)
        assert not waiter_task.done(), "waiter must still be blocked while every Free slot is held"

        release.set()
        await asyncio.gather(*tasks, waiter_task)

    asyncio.run(scenario())
    assert order[-1] == "waiter-acquired"


def test_pro_never_waits_behind_free_load():
    """Holding every Free slot must not delay a Pro request -- separate pools."""

    async def scenario():
        free_limit = GENERATION_CONCURRENCY_LIMITS["free"]
        free_held = asyncio.Event()
        release_free = asyncio.Event()

        async def hold_all_free():
            async def one_holder(ready):
                async with generation_priority_gate("free"):
                    ready.set()
                    await release_free.wait()

            readies = [asyncio.Event() for _ in range(free_limit)]
            tasks = [asyncio.create_task(one_holder(r)) for r in readies]
            for r in readies:
                await r.wait()
            free_held.set()
            await asyncio.gather(*tasks)

        free_task = asyncio.create_task(hold_all_free())
        await free_held.wait()

        # Pro must acquire immediately even though Free is fully saturated.
        async with asyncio.timeout(1):
            async with generation_priority_gate("pro"):
                pro_acquired = True

        release_free.set()
        await free_task
        return pro_acquired

    assert asyncio.run(scenario()) is True


def test_available_slots_reflects_independent_pools():
    async def scenario():
        assert available_slots("free") == GENERATION_CONCURRENCY_LIMITS["free"]
        assert available_slots("pro") == GENERATION_CONCURRENCY_LIMITS["pro"]
        async with generation_priority_gate("free"):
            assert available_slots("free") == GENERATION_CONCURRENCY_LIMITS["free"] - 1
            # Pro's pool is untouched by Free usage.
            assert available_slots("pro") == GENERATION_CONCURRENCY_LIMITS["pro"]
        assert available_slots("free") == GENERATION_CONCURRENCY_LIMITS["free"]

    asyncio.run(scenario())


def test_unknown_plan_falls_back_to_free_pool():
    async def scenario():
        before = available_slots("free")
        async with generation_priority_gate("nonexistent_plan"):
            assert available_slots("free") == before - 1

    asyncio.run(scenario())


@pytest.mark.parametrize("plan", ["free", None, "", "nonexistent"])
def test_streaming_blocked_for_non_paid_plans(plan):
    with pytest.raises(HTTPException) as exc_info:
        require_streaming_access(plan)
    assert exc_info.value.status_code == 402
    assert "pro" in exc_info.value.detail.lower() or "upgrade" in exc_info.value.detail.lower()


@pytest.mark.parametrize("plan", ["pro", "team"])
def test_streaming_allowed_for_paid_plans(plan):
    require_streaming_access(plan)  # must not raise
