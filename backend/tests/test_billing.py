"""Backend tests for billing/Stripe (Flow A) and plan-based gating."""
import os
import uuid
import time
from datetime import datetime, timezone

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

STATE = {}


@pytest.fixture(scope="session")
def mongo():
    return MongoClient(MONGO_URL)[DB_NAME]


@pytest.fixture(scope="session")
def user(mongo):
    email = f"TEST_billing_{uuid.uuid4().hex[:8]}@architect.io"
    pw = "Testpass1234!"
    r = requests.post(f"{BASE_URL}/api/auth/register",
                      json={"email": email, "password": pw, "name": "Bill Tester"}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    STATE["email"] = email
    STATE["token"] = data["token"]
    STATE["user_id"] = data["user"]["id"]
    yield data
    # cleanup
    try:
        mongo.users.delete_one({"id": data["user"]["id"]})
        mongo.blueprints.delete_many({"user_id": data["user"]["id"]})
        mongo.payment_transactions.delete_many({"user_id": data["user"]["id"]})
    except Exception:
        pass


@pytest.fixture(scope="session")
def h(user):
    return {"Authorization": f"Bearer {user['token']}", "Content-Type": "application/json"}


# ---------- /api/billing/config ----------
def test_billing_config_shape():
    r = requests.get(f"{BASE_URL}/api/billing/config", timeout=15)
    assert r.status_code == 200
    data = r.json()
    plans = data.get("plans", [])
    packs = data.get("credit_packs", [])
    plan_ids = {p["id"] for p in plans}
    assert plan_ids == {"free", "pro", "team"}, plan_ids
    pro = next(p for p in plans if p["id"] == "pro")
    team = next(p for p in plans if p["id"] == "team")
    assert pro["monthly"] == 19
    assert team["monthly"] == 49
    assert pro.get("lookup_monthly") == "pro_monthly"
    assert pro.get("lookup_yearly") == "pro_yearly"
    assert team.get("lookup_monthly") == "team_monthly"
    assert team.get("lookup_yearly") == "team_yearly"
    pack_ids = {p["id"] for p in packs}
    assert pack_ids == {"credits_10", "credits_50"}
    p10 = next(p for p in packs if p["id"] == "credits_10")
    p50 = next(p for p in packs if p["id"] == "credits_50")
    assert p10["credits"] == 10 and p10["lookup_key"] == "credits_10"
    assert p50["credits"] == 50 and p50["lookup_key"] == "credits_50"


# ---------- Auth: fresh user shape ----------
def test_auth_me_fresh_user(h):
    r = requests.get(f"{BASE_URL}/api/auth/me", headers=h, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["plan"] == "free"
    assert data["credits"] == 0


def test_billing_me_fresh_user(h):
    r = requests.get(f"{BASE_URL}/api/billing/me", headers=h, timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["plan"] == "free"
    assert data["credits"] == 0
    assert data["blueprint_count"] == 0
    assert data["free_limit"] == 3
    assert data["unlimited"] is False


# ---------- Blueprint quota gating (402 at 4th) ----------
def test_blueprint_quota_402_after_limit(h, mongo, user):
    """Seed 3 blueprints directly into Mongo to skip Claude, then verify 4th create is blocked."""
    uid = user["user"]["id"]
    now = datetime.now(timezone.utc).isoformat()
    docs = [{
        "id": str(uuid.uuid4()),
        "user_id": uid,
        "idea": f"TEST seed blueprint {i}",
        "created_at": now,
        "content": {"title": "seed"},
    } for i in range(3)]
    mongo.blueprints.insert_many(docs)

    # verify billing_me reflects count
    r = requests.get(f"{BASE_URL}/api/billing/me", headers=h, timeout=15)
    assert r.status_code == 200
    assert r.json()["blueprint_count"] == 3

    # 4th blueprint => 402
    r = requests.post(f"{BASE_URL}/api/blueprints", headers=h,
                      json={"idea": "TEST fourth blueprint that should be gated"}, timeout=30)
    assert r.status_code == 402, f"expected 402, got {r.status_code} {r.text[:300]}"
    body = r.json()
    msg = (body.get("detail") or body.get("message") or "").lower()
    assert "upgrade" in msg or "credit" in msg or "free" in msg, msg


def test_blueprint_quota_bypassed_with_credits(h, mongo, user):
    """Grant 1 credit; POST should now not immediately 402 (may succeed or fail on LLM).
    We only care that it isn't a 402 here."""
    uid = user["user"]["id"]
    mongo.users.update_one({"id": uid}, {"$set": {"credits": 1}})
    # Do NOT actually complete an LLM call (slow). Use short timeout & tolerate errors.
    try:
        r = requests.post(f"{BASE_URL}/api/blueprints", headers=h,
                          json={"idea": "TEST short bypass ignore"}, timeout=5)
        # if it responds within 5s
        assert r.status_code != 402
    except requests.exceptions.ReadTimeout:
        # LLM in progress -> proves quota check passed
        pass
    finally:
        # reset credits so it doesn't affect other tests
        mongo.users.update_one({"id": uid}, {"$set": {"credits": 0}})


# ---------- Hybrid Core gating for free user ----------
def test_core_run_blocked_for_free(h):
    r = requests.post(f"{BASE_URL}/api/core/run", headers=h,
                      json={"task": "Write a hello world function please"}, timeout=15)
    assert r.status_code == 402, f"expected 402, got {r.status_code} {r.text[:200]}"
    body = r.json()
    # server may wrap in {"detail": {...}} or return dict directly
    payload = body.get("detail") if isinstance(body.get("detail"), dict) else body
    assert payload.get("type") == "access_denied", payload


# ---------- Stripe checkout ----------
ORIGIN = "https://scalable-ai-forge.preview.emergentagent.com"


def test_checkout_pro_monthly(h, mongo, user):
    r = requests.post(f"{BASE_URL}/api/payments/checkout", headers=h,
                      json={"lookup_key": "pro_monthly", "origin_url": ORIGIN}, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:400]}"
    data = r.json()
    assert "checkout_url" in data and data["checkout_url"].startswith("https://")
    assert "stripe.com" in data["checkout_url"] or "checkout.stripe" in data["checkout_url"]
    assert "session_id" in data and data["session_id"].startswith("cs_")
    STATE["sub_session"] = data["session_id"]

    tx = mongo.payment_transactions.find_one({"session_id": data["session_id"]})
    assert tx is not None
    assert tx["user_id"] == user["user"]["id"]
    assert tx["lookup_key"] == "pro_monthly"
    assert tx["payment_status"] == "pending"
    assert tx["granted"] is False


def test_checkout_credits_10(h, mongo):
    r = requests.post(f"{BASE_URL}/api/payments/checkout", headers=h,
                      json={"lookup_key": "credits_10", "origin_url": ORIGIN}, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:400]}"
    data = r.json()
    assert data["checkout_url"].startswith("https://")
    assert data["session_id"].startswith("cs_")
    STATE["pack_session"] = data["session_id"]

    tx = mongo.payment_transactions.find_one({"session_id": data["session_id"]})
    assert tx is not None
    assert tx["lookup_key"] == "credits_10"


def test_payment_status_unauth_pending():
    sid = STATE.get("sub_session")
    if not sid:
        pytest.skip("no session id from prior test")
    r = requests.get(f"{BASE_URL}/api/payments/status/{sid}", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["session_id"] == sid
    assert data["payment_status"] in ("pending", "unpaid", "no_payment_required")
    assert data["status"] in ("initiated", "open", "complete", "expired")


def test_payment_status_not_found():
    r = requests.get(f"{BASE_URL}/api/payments/status/cs_test_doesnotexist_{uuid.uuid4().hex}", timeout=15)
    assert r.status_code == 404


def test_checkout_bad_lookup_key(h):
    r = requests.post(f"{BASE_URL}/api/payments/checkout", headers=h,
                      json={"lookup_key": "nonexistent_key_xyz", "origin_url": ORIGIN}, timeout=15)
    assert r.status_code in (400, 500)


def test_checkout_requires_auth():
    r = requests.post(f"{BASE_URL}/api/payments/checkout",
                      json={"lookup_key": "pro_monthly", "origin_url": ORIGIN}, timeout=15)
    assert r.status_code == 401
