"""
Route-level wiring tests for the streaming plan gate and the generation
priority gate.

Uses an isolated, disposable test database (a fresh DB_NAME on the local
Mongo instance, dropped at the end of the module) and a stubbed
`emergentintegrations` module -- no real LLM call is made and no Stripe call
is made anywhere in this file.
"""
import json
import os
import sys
import types
import uuid
from contextlib import asynccontextmanager

import pytest
from pymongo import MongoClient

# ---------------------------------------------------------------------------
# Stub emergentintegrations before `server`/`core` import it. Same technique
# used elsewhere in this codebase's sibling projects for offline test runs.
# ---------------------------------------------------------------------------
FAKE_BLUEPRINT_JSON = json.dumps(
    {
        "title": "Test System",
        "tagline": "A test blueprint",
        "core_insight": "test insight",
        "system_blueprint": {"architecture": "x", "components": [], "tech_stack": {}, "data_models": []},
        "leverage_point": {"the_move": "x", "why_it_works": "x", "impact_effort": {"impact": "10", "effort": "1"}},
        "roadmap": [],
        "risks": [],
        "monetization": {"model": "x", "pricing_tiers": [], "unit_economics": "x", "growth_loops": []},
        "executable_output": {"summary": "x", "artifacts": []},
    }
)


class _FakeTextDelta:
    def __init__(self, content):
        self.content = content


class _FakeStreamDone:
    pass


class _FakeLlmChat:
    """Stands in for emergentintegrations.llm.chat.LlmChat. Never touches the network."""

    def __init__(self, *a, **k):
        pass

    def with_model(self, *a, **k):
        return self

    def with_params(self, *a, **k):
        return self

    async def send_message(self, *a, **k):
        return FAKE_BLUEPRINT_JSON

    async def stream_message(self, *a, **k):
        for chunk in (FAKE_BLUEPRINT_JSON[:20], FAKE_BLUEPRINT_JSON[20:]):
            yield _FakeTextDelta(chunk)
        yield _FakeStreamDone()


def _stub_emergentintegrations():
    for name in ("emergentintegrations", "emergentintegrations.llm", "emergentintegrations.llm.chat"):
        sys.modules.setdefault(name, types.ModuleType(name))
    chat_mod = sys.modules["emergentintegrations.llm.chat"]
    chat_mod.LlmChat = _FakeLlmChat
    chat_mod.UserMessage = lambda text: types.SimpleNamespace(text=text)
    chat_mod.TextDelta = _FakeTextDelta
    chat_mod.StreamDone = _FakeStreamDone


_stub_emergentintegrations()

# ---------------------------------------------------------------------------
# Isolated env + disposable test database, set before importing `server`.
# ---------------------------------------------------------------------------
TEST_DB_NAME = f"scalable_ai_forge_test_{uuid.uuid4().hex[:8]}"
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ["DB_NAME"] = TEST_DB_NAME
os.environ.setdefault("JWT_SECRET", "test-secret-not-real")
os.environ.setdefault("EMERGENT_LLM_KEY", "test-key-not-real-never-called")
os.environ.setdefault("CORS_ORIGINS", "*")

from fastapi.testclient import TestClient  # noqa: E402

import generation_gate  # noqa: E402
import server as server_module  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(server_module.app) as c:
        yield c
    MongoClient(os.environ["MONGO_URL"]).drop_database(TEST_DB_NAME)


def _register(client, plan="free"):
    email = f"test-{uuid.uuid4().hex[:10]}@architect-gate-tests.io"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123", "name": "Test User"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    if plan != "free":
        mongo = MongoClient(os.environ["MONGO_URL"])[TEST_DB_NAME]
        mongo.users.update_one({"id": data["user"]["id"]}, {"$set": {"plan": plan}})
    return data["token"]


IDEA = {"idea": "A marketplace for something real and specific enough to pass validation"}


# ---------------------------------------------------------------------------
# Streaming gate: matches "Live token-by-token streaming" as a Pro/Team line item
# ---------------------------------------------------------------------------
def test_free_user_blocked_from_streaming_with_upgrade_message(client):
    token = _register(client, "free")
    r = client.post(
        "/api/blueprints/stream",
        headers={"Authorization": f"Bearer {token}"},
        json=IDEA,
    )
    assert r.status_code == 402, r.text
    detail = r.json()["detail"].lower()
    assert "stream" in detail
    assert "pro" in detail


def test_free_user_can_still_generate_without_streaming(client):
    """Free tier keeps real generation -- it only loses the SSE stream."""
    token = _register(client, "free")
    r = client.post(
        "/api/blueprints",
        headers={"Authorization": f"Bearer {token}"},
        json=IDEA,
    )
    assert r.status_code == 200, r.text
    assert r.json()["content"]["title"] == "Test System"


def test_pro_user_can_stream(client):
    token = _register(client, "pro")
    r = client.post(
        "/api/blueprints/stream",
        headers={"Authorization": f"Bearer {token}"},
        json=IDEA,
    )
    assert r.status_code == 200, r.text
    assert '"type": "token"' in r.text
    assert '"type": "done"' in r.text


def test_team_user_can_stream(client):
    token = _register(client, "team")
    r = client.post(
        "/api/blueprints/stream",
        headers={"Authorization": f"Bearer {token}"},
        json=IDEA,
    )
    assert r.status_code == 200, r.text


# ---------------------------------------------------------------------------
# Priority generation / higher generation limits: prove the route actually
# goes through the per-plan concurrency gate with the caller's real plan.
# ---------------------------------------------------------------------------
def test_blueprint_route_uses_the_generation_gate_with_the_caller_plan(client, monkeypatch):
    seen = []
    original = generation_gate.generation_priority_gate

    @asynccontextmanager
    async def spy(plan):
        seen.append(plan)
        async with original(plan):
            yield

    monkeypatch.setattr(server_module, "generation_priority_gate", spy)

    token_free = _register(client, "free")
    r1 = client.post("/api/blueprints", headers={"Authorization": f"Bearer {token_free}"}, json=IDEA)
    assert r1.status_code == 200, r1.text

    token_pro = _register(client, "pro")
    r2 = client.post("/api/blueprints", headers={"Authorization": f"Bearer {token_pro}"}, json=IDEA)
    assert r2.status_code == 200, r2.text

    assert "free" in seen
    assert "pro" in seen


def test_stream_route_uses_the_generation_gate_with_the_caller_plan(client, monkeypatch):
    seen = []
    original = generation_gate.generation_priority_gate

    @asynccontextmanager
    async def spy(plan):
        seen.append(plan)
        async with original(plan):
            yield

    monkeypatch.setattr(server_module, "generation_priority_gate", spy)

    token_team = _register(client, "team")
    r = client.post("/api/blueprints/stream", headers={"Authorization": f"Bearer {token_team}"}, json=IDEA)
    assert r.status_code == 200, r.text
    assert "team" in seen
