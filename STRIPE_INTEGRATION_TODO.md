# Stripe Integration TODO

This file lists what is still left to set up for the Stripe Checkout integration. Check here first.

**Scenario:** The code already created a Checkout Session (Scenario A). The only change was to the parameters of the existing `stripe.checkout.Session.create(...)` call in `create_checkout`. No new files, routes or refactors were added.

## Values to Replace

None of the checkout parameters use placeholder values. `mode`, `success_url`, `cancel_url` and `line_items` already had real values in your code, so they were left as they were.

**Files containing placeholders:**
- None among the Checkout Session parameters.

| Field | Current Value | What to Set |
|-------|--------------|-------------|
| mode | `"subscription" if price.recurring else "payment"` | Already correct. It is set from the Stripe Price the user picks. No change needed. |
| success_url | `{origin_url}/payment/success?session_id={CHECKOUT_SESSION_ID}` | Already real. Keep the `{CHECKOUT_SESSION_ID}` template. |
| cancel_url | `{origin_url}/payment/cancel` | Already real. |
| line_items[].price | Looked up at runtime with `stripe.Price.list(lookup_keys=[...])` | Already real. The prices come from `backend/setup_stripe.py` (lookup keys `pro_monthly`, `pro_yearly`, `team_monthly`, `team_yearly`, `credits_10`, `credits_50`). |

### Check these before going live

1. **Stripe SDK version isn't pinned.** `backend/requirements.txt` has no `stripe` line, so the SDK is pulled in by another package (probably `emergentintegrations`). `ui_mode` is set to `hosted_page`, which needs a newer SDK and API version. Older SDKs use `hosted` instead.
   - Pin `stripe` in `backend/requirements.txt`.
   - Create one test session to confirm the API accepts `ui_mode="hosted_page"`, `integration_identifier` and `origin_context`.
   - If the API rejects `hosted_page`, change it to `hosted`.
   - Local check: the parameters were only verified against a mocked `Session.create`. No real Stripe call has been made yet.
2. **Fallback secret key in code.** `backend/payments.py` and `backend/setup_stripe.py` fall back to `"sk_test_emergent"` when `STRIPE_SECRET_KEY` is missing. Set the real key in your environment, and think about failing loudly instead of using the fallback.
3. **Tax and Managed Payments were turned off.** The old call tried `managed_payments={"enabled": True}` first. If that failed, it retried with `automatic_tax` enabled and `billing_address_collection="required"`. Checkout Studio now sets `automatic_tax` to off and `billing_address_collection` to `auto`, and `managed_payments` isn't one of its settings, so that parameter and the retry logic were removed.
   - If you need Stripe to collect tax or act as merchant of record, change these settings in Checkout Studio.
4. **`metadata` was kept.** It isn't a Checkout Studio setting, but it holds real data (`user_id`, `lookup_key`) that you need to match payments in the Dashboard. Fulfillment itself doesn't depend on it: it looks up `payment_transactions` by `session_id`.

## Configured Parameters

These parameters come from Checkout Studio and are already set.

**Files containing these parameters:**
- [backend/payments.py](backend/payments.py)

| Parameter | Value |
|-----------|-------|
| ui_mode | hosted_page |
| billing_address_collection | auto |
| phone_number_collection | `{"enabled": false}` |
| automatic_tax | `{"enabled": false}` |
| allow_promotion_codes | false |
| payment_method_collection | always (only sent when `mode` is `subscription`) |
| submit_type | auto |
| integration_identifier | hosted_web_0001 |
| origin_context | web |

**Removed** (not part of the Checkout Studio settings): `managed_payments`, plus the retry path that set `automatic_tax={"enabled": True}` and `billing_address_collection="required"`.

## Setup

Set these environment variables in `backend/.env`. `.env` files are already gitignored.

```
STRIPE_SECRET_KEY=sk_test_...        # https://dashboard.stripe.com/test/apikeys
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...      # https://dashboard.stripe.com/workbench/webhooks
```

- The frontend doesn't use Stripe.js. It only redirects to `checkout_url`, so it doesn't need a publishable key. (The frontend is Create React App, not Vite, so the `VITE_` prefix rule doesn't apply.)
- Install dependencies with `pip install -r backend/requirements.txt`, then pin `stripe` (see item 1 above).
- Sync the catalog with `python backend/setup_stripe.py`.
- Point a webhook endpoint at `POST /api/stripe/webhook` and subscribe it to these events:
  - `checkout.session.completed`
  - `checkout.session.async_payment_succeeded`
  - `checkout.session.async_payment_failed`
  - `checkout.session.expired`
  - `charge.refunded`

## Project structure

No new files were created except this one. The only modified file is `backend/payments.py`, and only the `create_checkout` call changed.

## How it works

1. The frontend calls `POST /api/payments/checkout` with `lookup_key`, `origin_url` and `quantity`. The user must be logged in.
2. The backend looks up the Price by its lookup key. It sets `mode` from `price.recurring` and creates a hosted Checkout Session with the parameters above.
3. The backend saves a `payment_transactions` record and returns `checkout_url`. The browser then redirects to the Stripe-hosted page.
4. After payment, Stripe sends the user to `/payment/success?session_id=...`. The page polls `GET /api/payments/status/{session_id}`.
5. The webhook, or the status poll as a backup, marks the transaction as paid. `grant_entitlement` then sets the user's plan or adds credits, and only does so once per transaction.

## Testing

- Use test mode keys (`sk_test_...`).
- Test cards (any future expiry date, any CVC):
  - `4242 4242 4242 4242`: succeeds
  - `4000 0025 0000 3155`: requires 3D Secure authentication
  - `4000 0000 0000 9995`: declined (insufficient funds)
- Forward webhooks to your machine with `stripe listen --forward-to localhost:8001/api/stripe/webhook`.
- Existing tests: `backend/tests/test_billing.py`. It needs the backend running at `BASE_URL`.

## Next steps

- Pin the Stripe SDK and confirm `hosted_page` works (item 1 above).
- Decide on tax collection. Right now it is off in Checkout Studio.
- Handle `customer.subscription.updated` and `customer.subscription.deleted` so plans are downgraded when a subscription is canceled. The webhook doesn't handle these events yet.
- Save `customer_id` on the user so they can manage billing in the Customer Portal.

## Resources

- https://support.stripe.com
- https://docs.stripe.com/mcp
