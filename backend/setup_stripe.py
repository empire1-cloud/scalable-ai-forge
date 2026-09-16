"""Idempotent Stripe catalog setup for Emergent // Architect.

Products: Pro plan + Team plan (subscriptions, monthly + yearly) and
one-time credit packs. Run: `python setup_stripe.py`.
"""
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

import os
import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY") or "sk_test_emergent"

# SaaS tax code for subscriptions, general digital for credit packs.
CATALOG = [
    {
        "emergent_product_id": "pro_plan",
        "name": "Architect Pro",
        "tax_code": "txcd_10103001",
        "prices": [
            {"lookup_key": "pro_monthly", "amount": 1900, "currency": "usd", "interval": "month"},
            {"lookup_key": "pro_yearly", "amount": 18240, "currency": "usd", "interval": "year"},
        ],
    },
    {
        "emergent_product_id": "team_plan",
        "name": "Architect Team",
        "tax_code": "txcd_10103001",
        "prices": [
            {"lookup_key": "team_monthly", "amount": 4900, "currency": "usd", "interval": "month"},
            {"lookup_key": "team_yearly", "amount": 47040, "currency": "usd", "interval": "year"},
        ],
    },
    {
        "emergent_product_id": "credits_10",
        "name": "10 Blueprint Credits",
        "tax_code": "txcd_10000000",
        "prices": [
            {"lookup_key": "credits_10", "amount": 900, "currency": "usd"},
        ],
    },
    {
        "emergent_product_id": "credits_50",
        "name": "50 Blueprint Credits",
        "tax_code": "txcd_10000000",
        "prices": [
            {"lookup_key": "credits_50", "amount": 2900, "currency": "usd"},
        ],
    },
]


def get_or_create_product(entry):
    for p in stripe.Product.list(active=True).auto_paging_iter():
        if p.to_dict().get("metadata", {}).get("emergent_product_id") == entry["emergent_product_id"]:
            return p
    return stripe.Product.create(
        name=entry["name"],
        tax_code=entry.get("tax_code"),
        metadata={"managed_by": "emergent", "emergent_product_id": entry["emergent_product_id"]},
    )


def ensure_price(product, p):
    existing = stripe.Price.list(lookup_keys=[p["lookup_key"]], active=True, limit=1).data
    if existing and (existing[0].unit_amount != p["amount"] or existing[0].currency != p["currency"]):
        stripe.Price.modify(existing[0].id, active=False)
        existing = []
    if existing:
        return existing[0]
    kwargs = dict(
        product=product.id,
        unit_amount=p["amount"],
        currency=p["currency"],
        lookup_key=p["lookup_key"],
        transfer_lookup_key=True,
    )
    if p.get("interval"):
        kwargs["recurring"] = {"interval": p["interval"]}
    return stripe.Price.create(**kwargs)


def main():
    for entry in CATALOG:
        product = get_or_create_product(entry)
        for p in entry["prices"]:
            price = ensure_price(product, p)
            print(f"OK {p['lookup_key']} -> {price.id} ({p['amount']} {p['currency']})")
    print("Catalog ready.")


if __name__ == "__main__":
    main()
