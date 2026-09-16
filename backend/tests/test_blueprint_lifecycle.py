"""
End-to-end blueprint lifecycle tests: timestamp correctness and the new
funding_readiness/provenance fields round-tripping through the real
create -> store -> list -> rename path.

Uses an isolated, disposable test database (dropped at the end of the
module) and a stubbed `emergentintegrations` -- no real LLM call, no real
Stripe call anywhere in this file.
"""
import json
import os
import sys
import types
import uuid
from datetime import datetime, timezone

import pytest
from pymongo import MongoClient


# ---------------------------------------------------------------------------
# Stub emergentintegrations before `server` imports it.
# ---------------------------------------------------------------------------
WELL_FORMED_BLUEPRINT = {
    "title": "Test System",
    "tagline": "A test blueprint",
    "core_insight": "test insight",
    "system_blueprint": {"architecture": "x", "components": [], "tech_stack": {}, "data_models": []},
    "leverage_point": {"the_move": "x", "why_it_works": "x", "impact_effort": {"impact": "10", "effort": "1"}},
    "roadmap": [],
    "risks": [],
    "monetization": {"model": "x", "pricing_tiers": [], "unit_economics": "x", "growth_loops": []},
    "funding_readiness": {
        "dimensions": {
            "technical_readiness": {"status": "prototype", "evidence": "x", "gap": "no production deploy yet"},
            "market_evidence": {"status": "none", "evidence": "", "gap": "no customer conversations yet"},
            "revenue_evidence": {"status": "none", "evidence": "", "gap": "pre-revenue"},
            "defensibility": {"status": "weak", "evidence": "x", "gap": "no moat established"},
            "capital_requirements": {"estimate": "$50k", "runway_needed": "6mo", "gap": "unvalidated estimate"},
            "deployment_readiness": {"status": "idea", "evidence": "", "gap": "nothing shipped"},
            "founder_execution_evidence": {"status": "unknown", "evidence": "", "gap": "no track record given"},
        },
        "overall_gaps": ["No market evidence yet"],
        "note": "Not a funding recommendation.",
    },
    "executable_output": {"summary": "x", "artifacts": []},
    "provenance": {
        "core_insight": "Derived",
        "system_blueprint": "Proposed",
        "leverage_point": "Proposed",
        "roadmap": "Proposed",
        "risks": [],
        "monetization": "Proposed",
        "funding_readiness": "Unverified",
        "executable_output": "Generated",
    },
}

HALLUCINATED_DATE_BLUEPRINT = {**WELL_FORMED_BLUEPRINT, "created_at": "1999-01-01T00:00:00+00:00"}


class _StubChat:
    response = json.dumps(WELL_FORMED_BLUEPRINT)

    def __init__(self, *a, **k):
        pass

    def with_model(self, *a, **k):
        return self

    def with_params(self, *a, **k):
        return self

    async def send_message(self, *a, **k):
        return _StubChat.response


def _stub_emergentintegrations():
    for name in ("emergentintegrations", "emergentintegrations.llm", "emergentintegrations.llm.chat"):
        sys.modules.setdefault(name, types.ModuleType(name))
    chat_mod = sys.modules["emergentintegrations.llm.chat"]
    chat_mod.LlmChat = _StubChat
    chat_mod.UserMessage = lambda text: types.SimpleNamespace(text=text)
    chat_mod.TextDelta = type("TextDelta", (), {})
    chat_mod.StreamDone = type("StreamDone", (), {})


_stub_emergentintegrations()

TEST_DB_NAME = f"scalable_ai_forge_lifecycle_test_{uuid.uuid4().hex[:8]}"
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ["DB_NAME"] = TEST_DB_NAME
os.environ.setdefault("JWT_SECRET", "test-secret-not-real")
os.environ.setdefault("EMERGENT_LLM_KEY", "test-key-not-real-never-called")
os.environ.setdefault("CORS_ORIGINS", "*")

from fastapi.testclient import TestClient  # noqa: E402

import server as server_module  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _patch_llm_chat_class():
    """Guarantee server.py's LlmChat name resolves to our stub regardless of
    which test file's sys.modules stub happened to load first on this xdist
    worker (several sibling test files stub `emergentintegrations` at import
    time; only the first one to run actually controls what `server.py`'s
    own `from ... import LlmChat` bound, since Python caches the module).
    Patching the name inside server's own namespace sidesteps that entirely.
    """
    original = server_module.LlmChat
    server_module.LlmChat = _StubChat
    yield
    server_module.LlmChat = original


@pytest.fixture(scope="module")
def client():
    with TestClient(server_module.app) as c:
        yield c
    MongoClient(os.environ["MONGO_URL"]).drop_database(TEST_DB_NAME)


def _register(client):
    email = f"test-{uuid.uuid4().hex[:10]}@architect-lifecycle-tests.io"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "testpass123", "name": "Test User"},
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


IDEA = {"idea": "A marketplace for something real and specific enough to pass validation"}


# ---------------------------------------------------------------------------
# Timestamp correctness, end to end
# ---------------------------------------------------------------------------
def test_new_blueprint_gets_a_current_server_set_timestamp(client, monkeypatch):
    _StubChat.response = json.dumps(WELL_FORMED_BLUEPRINT)
    token = _register(client)

    r = client.post("/api/blueprints", headers={"Authorization": f"Bearer {token}"}, json=IDEA)
    assert r.status_code == 200, r.text
    doc = r.json()

    created = datetime.fromisoformat(doc["created_at"])
    updated = datetime.fromisoformat(doc["updated_at"])
    assert created.year == datetime.now(timezone.utc).year
    assert doc["created_at"] == doc["updated_at"]


def test_a_hallucinated_date_inside_llm_content_never_reaches_created_at(client):
    """The regression this pass guards against: even if the model free-associates
    a date field into its JSON, it must not leak into the real timestamp or
    even survive inside stored content."""
    _StubChat.response = json.dumps(HALLUCINATED_DATE_BLUEPRINT)
    token = _register(client)

    r = client.post("/api/blueprints", headers={"Authorization": f"Bearer {token}"}, json=IDEA)
    assert r.status_code == 200, r.text
    doc = r.json()

    assert doc["created_at"] != "1999-01-01T00:00:00+00:00"
    assert datetime.fromisoformat(doc["created_at"]).year == datetime.now(timezone.utc).year
    assert "created_at" not in doc["content"]


def test_rename_updates_updated_at_but_never_created_at(client):
    _StubChat.response = json.dumps(WELL_FORMED_BLUEPRINT)
    token = _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post("/api/blueprints", headers=headers, json=IDEA).json()
    bp_id = created["id"]
    original_created_at = created["created_at"]

    rename = client.patch(f"/api/blueprints/{bp_id}", headers=headers, json={"title": "Renamed"})
    assert rename.status_code == 200, rename.text

    fetched = client.get(f"/api/blueprints/{bp_id}", headers=headers).json()
    assert fetched["title"] == "Renamed"
    assert fetched["created_at"] == original_created_at
    assert fetched["updated_at"] != original_created_at
    assert datetime.fromisoformat(fetched["updated_at"]) > datetime.fromisoformat(original_created_at)


def test_list_blueprints_shows_correct_created_at_per_card(client):
    """Direct regression guard for the reported bug: what Dashboard.jsx reads
    (GET /api/blueprints -> b.created_at) must be today's date."""
    _StubChat.response = json.dumps(WELL_FORMED_BLUEPRINT)
    token = _register(client)
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/blueprints", headers=headers, json=IDEA)

    listed = client.get("/api/blueprints", headers=headers).json()
    assert len(listed) >= 1
    for item in listed:
        assert datetime.fromisoformat(item["created_at"]).year == datetime.now(timezone.utc).year


# ---------------------------------------------------------------------------
# funding_readiness / provenance round-trip
# ---------------------------------------------------------------------------
def test_funding_readiness_and_provenance_round_trip_into_stored_blueprint(client):
    _StubChat.response = json.dumps(WELL_FORMED_BLUEPRINT)
    token = _register(client)

    r = client.post("/api/blueprints", headers={"Authorization": f"Bearer {token}"}, json=IDEA)
    assert r.status_code == 200, r.text
    content = r.json()["content"]

    assert content["funding_readiness"]["dimensions"].keys() == WELL_FORMED_BLUEPRINT["funding_readiness"]["dimensions"].keys()
    assert content["provenance"] == WELL_FORMED_BLUEPRINT["provenance"]
