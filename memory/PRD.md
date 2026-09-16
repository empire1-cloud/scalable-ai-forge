# Emergent // Architect — PRD

## Problem statement (verbatim)
Build me an AI that converts any idea into a complete, scalable system with blueprints, leverage points, and production‑ready assets.

## Vision
An emergent-intelligence systems architect: any idea in → complete scalable system out (Core Insight → System Blueprint → Leverage Point → Executable Output).

## Users
- Founders / operators drafting new products
- Solo builders needing architecture + code scaffolds
- Strategists mapping monetization + roadmap

## Core requirements
- Email/password auth (JWT)
- One-prompt blueprint generation via Claude Sonnet 5
- Structured JSON output with sections: Core Insight, System Blueprint (arch + stack + data models), Leverage Point, Roadmap, Risks, Monetization, Executable Output
- Save/list/view/delete blueprints per user
- Export: copy JSON, download .md, download .json

## Implemented (Feb 2026)
- FastAPI backend (`/api/auth/*`, `/api/blueprints/*`)
- Claude Sonnet 5 via emergentintegrations (Universal Key)
- Mongo indexes on users.email, blueprints.user_id
- Bcrypt password hashing + JWT
- React frontend: Landing, Auth (tabs), Dashboard (vault), Generator (multi-stage animated), Blueprint Detail (tabs + artifacts)
- Design: dark blueprint aesthetic, Outfit + Plus Jakarta Sans + JetBrains Mono
- Export: copy JSON, download .md, download .json
- SSE token-by-token streaming generation + Hybrid Intelligence Core (`/core`, multi-model)

## Implemented (June 2026) — Stripe billing + gating
- Stripe (claimable sandbox, Flow A) in `backend/payments.py`; catalog via `backend/setup_stripe.py`
- Plans: Free (3 blueprints, no Core), Pro $19/mo · $182.40/yr, Team $49/mo · $470.40/yr (both unlimited + Core)
- One-time credit packs: 10 credits/$9, 50 credits/$29 (1 credit = 1 extra blueprint)
- Feature gating: `check_blueprint_quota` (server.py) enforces free limit=3 → credits → 402; `/api/core/run` returns 402 access_denied for free
- User doc gains `plan`, `credits`; surfaced via `/api/auth/me` + `/api/billing/me`
- Endpoints: `/api/billing/config`, `/api/billing/me`, `/api/payments/checkout`, `/api/payments/status/{id}`, `/api/stripe/webhook`
- Frontend: `/pricing` (monthly/yearly toggle), `/payment/success` (polling), `/payment/cancel`, Header plan badge + Upgrade; 402 → redirect to /pricing
- Tax mode: SMP ("Stripe manages everything") — US sandbox, digital goods
- Backend tested: 12/12 pass (iteration_2.json). Frontend pricing smoke-tested.
- README.md written for repo

## Backlog
- P1: Streaming SSE generation (currently non-streaming for reliable JSON parsing)
- P1: Blueprint rename inline
- P2: Sharing (public link)
- P2: Version history / re-generate
- P2: Team workspaces

## Learnings
- `@emergentbase/visual-edits` babel plugin stack-overflows on a component that renders itself via JSX (`<Self />`). Use `createElement(Self, props)` for recursive components (see JsonTree.jsx).
