"""Stripe payments + entitlements for Emergent // Architect (Flow A sandbox)."""
import os
import logging
from datetime import datetime, timezone
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

log = logging.getLogger("payments")

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY") or "sk_test_emergent"
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

FREE_BLUEPRINT_LIMIT = 3

# lookup_key -> entitlement mapping (server-side source of truth)
PLAN_BY_LOOKUP = {
    "pro_monthly": "pro",
    "pro_yearly": "pro",
    "team_monthly": "team",
    "team_yearly": "team",
}
CREDITS_BY_LOOKUP = {"credits_10": 10, "credits_50": 50}

# Public pricing config surfaced to the frontend.
BILLING_CONFIG = {
    "plans": [
        {
            "id": "free",
            "name": "Free",
            "tagline": "Draft your first systems",
            "monthly": 0,
            "yearly": 0,
            "features": [
                f"{FREE_BLUEPRINT_LIMIT} blueprints total",
                "Full blueprint schema + export",
                "Save & revisit in your vault",
            ],
            "limits": {"blueprints": FREE_BLUEPRINT_LIMIT, "core": False},
        },
        {
            "id": "pro",
            "name": "Pro",
            "tagline": "Ship unlimited systems",
            "monthly": 19,
            "yearly": 182.40,
            "lookup_monthly": "pro_monthly",
            "lookup_yearly": "pro_yearly",
            "features": [
                "Unlimited blueprints",
                "Hybrid Intelligence Core access",
                "Live token-by-token streaming",
                "Priority generation",
            ],
            "limits": {"blueprints": None, "core": True},
            "highlighted": True,
        },
        {
            "id": "team",
            "name": "Team",
            "tagline": "Scale across your org",
            "monthly": 49,
            "yearly": 470.40,
            "lookup_monthly": "team_monthly",
            "lookup_yearly": "team_yearly",
            "features": [
                "Everything in Pro",
                "Hybrid Core with full drift metrics",
                "Higher generation limits",
                "Priority support",
            ],
            "limits": {"blueprints": None, "core": True},
        },
    ],
    "credit_packs": [
        {"id": "credits_10", "name": "10 Credits", "lookup_key": "credits_10", "credits": 10, "price": 9},
        {"id": "credits_50", "name": "50 Credits", "lookup_key": "credits_50", "credits": 50, "price": 29},
    ],
}


class CheckoutRequest(BaseModel):
    lookup_key: str
    origin_url: str
    quantity: int = Field(1, ge=1, le=100)


def make_payments_router(db, auth_dep) -> APIRouter:
    router = APIRouter(prefix="/api")

    async def grant_entitlement(session_id: str):
        """Idempotently apply plan/credits for a paid transaction."""
        tx = await db.payment_transactions.find_one({"session_id": session_id})
        if not tx or tx.get("granted"):
            return
        lookup = tx.get("lookup_key")
        user_id = tx.get("user_id")
        if not user_id:
            return
        if lookup in PLAN_BY_LOOKUP:
            await db.users.update_one(
                {"id": user_id},
                {"$set": {"plan": PLAN_BY_LOOKUP[lookup], "plan_since": datetime.now(timezone.utc).isoformat()}},
            )
        elif lookup in CREDITS_BY_LOOKUP:
            await db.users.update_one(
                {"id": user_id}, {"$inc": {"credits": CREDITS_BY_LOOKUP[lookup] * tx.get("quantity", 1)}}
            )
        await db.payment_transactions.update_one({"session_id": session_id}, {"$set": {"granted": True}})

    @router.get("/billing/config")
    async def billing_config():
        return BILLING_CONFIG

    @router.get("/billing/me")
    async def billing_me(user: dict = Depends(auth_dep)):
        count = await db.blueprints.count_documents({"user_id": user["id"]})
        plan = user.get("plan", "free")
        return {
            "plan": plan,
            "credits": user.get("credits", 0),
            "blueprint_count": count,
            "free_limit": FREE_BLUEPRINT_LIMIT,
            "unlimited": plan in ("pro", "team"),
        }

    @router.post("/payments/checkout")
    async def create_checkout(req: CheckoutRequest, user: dict = Depends(auth_dep)):
        prices = stripe.Price.list(lookup_keys=[req.lookup_key], active=True, limit=1).data
        if not prices:
            raise HTTPException(500, f"Price not found: {req.lookup_key}")
        price = prices[0]
        kwargs = dict(
            ui_mode="hosted_page",
            line_items=[{"price": price.id, "quantity": req.quantity}],
            mode="subscription" if price.recurring else "payment",
            success_url=f"{req.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{req.origin_url}/payment/cancel",
            metadata={"user_id": user["id"], "lookup_key": req.lookup_key},
            billing_address_collection="auto",
            phone_number_collection={"enabled": False},
            automatic_tax={"enabled": False},
            allow_promotion_codes=False,
            submit_type="auto",
            integration_identifier="hosted_web_0001",
            origin_context="web",
        )
        if kwargs["mode"] == "subscription":
            kwargs["payment_method_collection"] = "always"
        session = stripe.checkout.Session.create(**kwargs)
        await db.payment_transactions.insert_one({
            "session_id": session.id,
            "user_id": user["id"],
            "lookup_key": req.lookup_key,
            "quantity": req.quantity,
            "amount": (price.unit_amount or 0) * req.quantity,
            "currency": price.currency,
            "status": "initiated",
            "payment_status": "pending",
            "granted": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"checkout_url": session.url, "session_id": session.id}

    @router.get("/payments/status/{session_id}")
    async def get_status(session_id: str):
        record = await db.payment_transactions.find_one({"session_id": session_id})
        if not record:
            raise HTTPException(404, "Transaction not found")
        if record.get("payment_status") != "paid":
            try:
                s = stripe.checkout.Session.retrieve(session_id)
                if s.payment_status == "paid" or s.status == "complete":
                    await db.payment_transactions.update_one(
                        {"session_id": session_id, "payment_status": {"$ne": "paid"}},
                        {"$set": {
                            "status": "completed",
                            "payment_status": "paid",
                            "stripe_subscription_id": s.subscription,
                            "stripe_payment_intent_id": s.payment_intent,
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        }},
                    )
                    await grant_entitlement(session_id)
                    record = await db.payment_transactions.find_one({"session_id": session_id})
            except stripe.error.StripeError:
                pass
        return {
            "session_id": record["session_id"],
            "status": record["status"],
            "payment_status": record["payment_status"],
        }

    @router.post("/stripe/webhook")
    async def stripe_webhook(request: Request):
        payload = await request.body()
        sig = request.headers.get("stripe-signature", "")
        try:
            event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
        except stripe.error.SignatureVerificationError:
            raise HTTPException(400, "Invalid signature")
        obj, t = event["data"]["object"], event["type"]
        if t == "checkout.session.completed":
            await db.payment_transactions.update_one(
                {"session_id": obj["id"], "payment_status": {"$ne": "paid"}},
                {"$set": {
                    "status": "completed",
                    "payment_status": obj.get("payment_status", "paid"),
                    "stripe_subscription_id": obj.get("subscription"),
                    "stripe_payment_intent_id": obj.get("payment_intent"),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }},
            )
            await grant_entitlement(obj["id"])
        elif t == "checkout.session.async_payment_succeeded":
            await db.payment_transactions.update_one(
                {"session_id": obj["id"]},
                {"$set": {"payment_status": "paid", "updated_at": datetime.now(timezone.utc).isoformat()}},
            )
            await grant_entitlement(obj["id"])
        elif t == "checkout.session.async_payment_failed":
            await db.payment_transactions.update_one(
                {"session_id": obj["id"]},
                {"$set": {"status": "failed", "payment_status": "failed", "updated_at": datetime.now(timezone.utc).isoformat()}},
            )
        elif t == "checkout.session.expired":
            await db.payment_transactions.update_one(
                {"session_id": obj["id"]},
                {"$set": {"status": "expired", "payment_status": "expired", "updated_at": datetime.now(timezone.utc).isoformat()}},
            )
        elif t == "charge.refunded":
            await db.payment_transactions.update_one(
                {"stripe_payment_intent_id": obj.get("payment_intent")},
                {"$set": {"status": "refunded", "payment_status": "refunded", "updated_at": datetime.now(timezone.utc).isoformat()}},
            )
        return {"status": "ok"}

    return router
