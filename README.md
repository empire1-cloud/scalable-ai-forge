# Emergent // Architect

An emergent-intelligence systems architect: drop in any idea and get back a
complete, scalable system — core insight, system blueprint, leverage points,
roadmap, risks, monetization, and production-ready executable assets.

Built with **FastAPI + React + MongoDB**, powered by a multi-model AI pipeline.

**Live app:** [scalable-ai-forge.emergent.host](https://scalable-ai-forge.emergent.host)

---

## Features

- **Blueprint Generator** — one prompt in, a full structured system out, from
  **Claude Sonnet 5**. Pro/Team get it streamed token-by-token over SSE; Free
  gets the same real generation via a plain request/response call.
- **Hybrid Intelligence Core** (`/core`) — a multi-model orchestrator that routes
  each task to the right engine (Claude for strategy, GPT for code, Gemini for
  speed) with canon enforcement and drift monitoring. Returns strict JSON.
  Pro/Team only.
- **Blueprint Vault** — save, search, rename, open and delete blueprints per user.
- **Export** — copy JSON, download `.md` / `.json`.
- **Auth** — email/password with JWT.
- **Generation priority** — Free, Pro and Team each draw from their own
  concurrency ceiling (`backend/generation_gate.py`), so Pro/Team generation is
  never delayed by Free-tier load, and Team's ceiling is higher than Pro's.
- **Billing (Stripe)** — Free / Pro / Team subscriptions (monthly + yearly) and
  one-time blueprint credit packs, with feature gating.

## Plans & gating

| Plan  | Price            | Blueprints | Hybrid Core |
|-------|------------------|------------|-------------|
| Free  | $0               | 3 total    | ✗           |
| Pro   | $19/mo · $182/yr | Unlimited  | ✓           |
| Team  | $49/mo · $470/yr | Unlimited  | ✓           |

Free users who hit the limit can buy one-time credit packs (10 for $9, 50 for
$29) — each credit unlocks one extra blueprint.

---

## Tech stack

- **Frontend:** React, React Router, Tailwind CSS, shadcn/ui, native SSE.
- **Backend:** FastAPI, Motor (async MongoDB), JWT, bcrypt.
- **AI:** `emergentintegrations` bridging Claude Sonnet 4.5/5, GPT-5.2, Gemini 3 Flash.
- **Payments:** Stripe (claimable sandbox).

## Project layout

```
/app
├── backend/
│   ├── server.py        # Auth, blueprints, SSE streaming, quota gating
│   ├── core.py          # Hybrid Intelligence Core (multi-model orchestrator)
│   ├── payments.py      # Stripe checkout, webhook, entitlements, billing config
│   ├── setup_stripe.py  # Idempotent Stripe catalog (products + prices)
│   └── requirements.txt
└── frontend/
    └── src/
        ├── pages/       # Landing, AuthPage, Dashboard, Generator, BlueprintDetail,
        │                #   CorePage, Pricing, PaymentSuccess, PaymentCancel
        ├── components/  # Header + core/ pipeline components + shadcn ui
        ├── context/     # AuthContext
        └── lib/         # api.js (axios), stream.js (SSE)
```

## Environment

Backend (`backend/.env`):

```
MONGO_URL=...
DB_NAME=...
JWT_SECRET=...
EMERGENT_LLM_KEY=...
STRIPE_SECRET_KEY=...
STRIPE_PUBLISHABLE_KEY=...
STRIPE_ACCOUNT_ID=...
STRIPE_WEBHOOK_SECRET=...
STRIPE_MODE=test
```

Frontend (`frontend/.env`):

```
REACT_APP_BACKEND_URL=...
```

## Running locally

Services are supervisor-managed.

```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
python backend/setup_stripe.py   # (re)sync the Stripe catalog
```

## Key API endpoints

| Method | Path                              | Notes                          |
|--------|-----------------------------------|--------------------------------|
| POST   | `/api/auth/register` / `login`    | JWT auth                       |
| GET    | `/api/auth/me`                    | Current user (plan + credits)  |
| POST   | `/api/blueprints/stream`          | SSE token-by-token generation  |
| GET/PATCH/DELETE | `/api/blueprints/{id}`  | Vault CRUD                     |
| POST   | `/api/core/run`                   | Hybrid Core (Pro/Team only)    |
| GET    | `/api/billing/config`             | Public pricing config          |
| GET    | `/api/billing/me`                 | Usage + entitlement            |
| POST   | `/api/payments/checkout`          | Create Stripe Checkout session |
| GET    | `/api/payments/status/{id}`       | Poll payment status            |
| POST   | `/api/stripe/webhook`             | Stripe webhook (idempotent)    |

## Stripe

Uses a **claimable sandbox** — no account or keys required to test. Test card:
`4242 4242 4242 4242`, any future expiry, any CVC. Claim the account later to go
live; keys switch automatically on deploy after KYC.
