"""
Backend tests for Hybrid Intelligence Core (/api/core/*) and blueprint DELETE.
Runs against public REACT_APP_BACKEND_URL. LLM calls are real — budget guarded.
"""
import os
import time
import json
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback: read frontend/.env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

DEMO_EMAIL = "demo@architect.io"
DEMO_PASSWORD = "demo1234"

LLM_TIMEOUT = 150

# Shared state across tests
STATE = {"token": None, "run_ids": {}}


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}, timeout=30)
    if r.status_code != 200:
        # try register
        r2 = requests.post(f"{BASE_URL}/api/auth/register", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD, "name": "Demo Architect"}, timeout=30)
        assert r2.status_code == 200, f"login+register failed: {r.status_code} {r.text} / {r2.status_code} {r2.text}"
        tok = r2.json()["token"]
    else:
        tok = r.json()["token"]
    STATE["token"] = tok
    return tok


@pytest.fixture(scope="session")
def h(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------- Auth guards ----------
def test_core_run_requires_auth():
    r = requests.post(f"{BASE_URL}/api/core/run", json={"task": "hello world test"}, timeout=15)
    assert r.status_code == 401


def test_core_runs_requires_auth():
    r = requests.get(f"{BASE_URL}/api/core/runs", timeout=15)
    assert r.status_code == 401


def test_core_metrics_requires_auth():
    r = requests.get(f"{BASE_URL}/api/core/metrics", timeout=15)
    assert r.status_code == 401


def test_playbook_public():
    r = requests.get(f"{BASE_URL}/api/core/playbook", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert "pipeline" in data
    assert "routing_logic" in data and len(data["routing_logic"]) == 5
    assert "engines" in data
    assert "canon_rules" in data and len(data["canon_rules"]) == 5
    assert "drift_prevention" in data
    assert "error_format" in data


# ---------- Validation ----------
def test_task_too_short(h):
    r = requests.post(f"{BASE_URL}/api/core/run", headers=h, json={"task": "hi"}, timeout=15)
    assert r.status_code == 422, r.text


def test_bogus_engine_override(h):
    r = requests.post(f"{BASE_URL}/api/core/run", headers=h, json={"task": "Do something useful please", "engine_override": "bogus"}, timeout=15)
    assert r.status_code == 400
    body = r.json()
    assert body.get("error") is True
    assert body.get("type") == "routing_error"
    assert body.get("stage") == "routing"
    assert "run_id" in body
    assert "message" in body


# ---------- Real LLM calls (budget: 3 total) ----------
def test_code_engine_auto_route(h):
    payload = {"task": "Write a Python function that reverses a linked list"}
    r = requests.post(f"{BASE_URL}/api/core/run", headers=h, json=payload, timeout=LLM_TIMEOUT)
    assert r.status_code == 200, f"code engine failed: {r.status_code} {r.text[:400]}"
    data = r.json()
    assert data["error"] is False
    assert data["engine"] == "code", f"expected code engine got {data['engine']}"
    assert data["model"] == "gpt-5.2"
    for k in ["solution_summary", "language", "files", "usage", "tests", "notes"]:
        assert k in data["output"], f"missing key {k}"
    assert isinstance(data["canon"]["compliant"], bool)
    assert "metrics" in data["drift"]
    assert data["run_id"] and data["latency_ms"] > 0
    STATE["run_ids"]["code"] = data["run_id"]


def test_fast_engine_override(h):
    payload = {"task": "Summarize what a CDN does in 3 bullets", "engine_override": "fast"}
    r = requests.post(f"{BASE_URL}/api/core/run", headers=h, json=payload, timeout=LLM_TIMEOUT)
    assert r.status_code == 200, f"fast engine failed: {r.status_code} {r.text[:400]}"
    data = r.json()
    assert data["engine"] == "fast"
    assert data["model"] == "gemini-3-flash-preview"
    assert data["routing"]["method"] == "override"
    for k in ["answer", "key_points", "assumptions"]:
        assert k in data["output"], f"missing key {k}"
    STATE["run_ids"]["fast"] = data["run_id"]


def test_plan_builder_override(h):
    payload = {
        "task": "Plan the launch of a small SaaS in 6 weeks",
        "engine_override": "plan_builder",
    }
    r = requests.post(f"{BASE_URL}/api/core/run", headers=h, json=payload, timeout=LLM_TIMEOUT)
    assert r.status_code == 200, f"plan_builder failed: {r.status_code} {r.text[:400]}"
    data = r.json()
    assert data["engine"] == "plan_builder"
    assert data["model"] == "claude-sonnet-4-5-20250929"
    for k in ["goal", "phases", "dependencies", "critical_path"]:
        assert k in data["output"], f"missing key {k}"
    STATE["run_ids"]["plan_builder"] = data["run_id"]


# ---------- Runs list / detail / metrics ----------
def test_list_runs(h):
    r = requests.get(f"{BASE_URL}/api/core/runs", headers=h, timeout=15)
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list) and len(items) >= 1
    # newest-first
    ts = [it["created_at"] for it in items]
    assert ts == sorted(ts, reverse=True)
    fields = {"id", "task", "engine", "model", "error", "latency_ms", "drift_flags", "created_at"}
    assert fields.issubset(items[0].keys())
    # error runs (bogus) should exist
    assert any(it.get("error") for it in items)


def test_get_run_detail(h):
    rid = STATE["run_ids"].get("code") or STATE["run_ids"].get("fast")
    if not rid:
        pytest.skip("no run id available")
    r = requests.get(f"{BASE_URL}/api/core/runs/{rid}", headers=h, timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d["id"] == rid
    assert "output" in d and "canon" in d and "drift" in d


def test_get_run_unknown(h):
    r = requests.get(f"{BASE_URL}/api/core/runs/{uuid.uuid4()}", headers=h, timeout=15)
    assert r.status_code == 404
    body = r.json()
    assert body.get("error") is True
    assert body.get("type") == "system_error"


def test_metrics(h):
    r = requests.get(f"{BASE_URL}/api/core/metrics", headers=h, timeout=15)
    assert r.status_code == 200
    data = r.json()
    for k in ["strategy", "plan_builder", "analysis", "code", "fast"]:
        assert k in data
        assert "samples" in data[k]


# ---------- Blueprint DELETE ----------
def test_delete_blueprint_nonexistent(h):
    r = requests.delete(f"{BASE_URL}/api/blueprints/{uuid.uuid4()}", headers=h, timeout=15)
    assert r.status_code == 404


def test_delete_existing_blueprint(h):
    # Instead of paying full generation, insert a synthetic blueprint via API is impossible.
    # We'll list existing; if any exist, delete the oldest test-like one? Safer: skip if none.
    r = requests.get(f"{BASE_URL}/api/blueprints", headers=h, timeout=15)
    if r.status_code != 200 or not r.json():
        pytest.skip("no existing blueprints to delete")
    bps = r.json()
    # pick one that looks like a test
    target = None
    for b in bps:
        if "test" in (b.get("idea") or "").lower() or "CSV" in (b.get("idea") or ""):
            target = b
            break
    if not target:
        pytest.skip("no test blueprint to safely delete; skipping to preserve user data")
    bp_id = target["id"]
    d = requests.delete(f"{BASE_URL}/api/blueprints/{bp_id}", headers=h, timeout=15)
    assert d.status_code == 200
    assert d.json() == {"ok": True}
    g = requests.get(f"{BASE_URL}/api/blueprints/{bp_id}", headers=h, timeout=15)
    assert g.status_code == 404
