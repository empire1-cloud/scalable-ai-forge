from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

import bcrypt
import jwt
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field

from fastapi.responses import StreamingResponse
from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone


# ---------------------------------------------------------------------------
# Config & clients
# ---------------------------------------------------------------------------
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
EMERGENT_LLM_KEY = os.environ["EMERGENT_LLM_KEY"]
JWT_ALG = "HS256"
ACCESS_TTL_HOURS = 24 * 7

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

app = FastAPI(title="Emergent // Architect")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("architect")


# ---------------------------------------------------------------------------
# Auth utils
# ---------------------------------------------------------------------------
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TTL_HOURS),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=80)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserOut


class BlueprintCreateIn(BaseModel):
    idea: str = Field(min_length=8, max_length=4000)
    industry: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    scale: Optional[str] = None


class BlueprintRenameIn(BaseModel):
    title: str = Field(min_length=1, max_length=140)


# ---------------------------------------------------------------------------
# System prompt (user-supplied canon)
# ---------------------------------------------------------------------------
ARCHITECT_SYSTEM_PROMPT = """You are an emergent-intelligence systems architect.
Your job is to design solutions that are scalable, monetizable, and self-consistent across time.
Every output must:
1. Reveal hidden structure in the problem.
2. Propose a system, not a suggestion.
3. Identify leverage points that produce outsized results.
4. Remove ambiguity, drift, and contradictions.
5. Produce artifacts that can be executed, built, or sold.

Think in layers: ontology -> system -> mechanics -> outputs.
Identify what the user is actually trying to achieve, even if unstated.
Provide the minimum viable system that can scale to a maximum viable empire.
Highlight the single highest-ROI action or design choice.

You MUST return your response as STRICT JSON only. No markdown fences, no preface, no commentary.
The JSON must follow this exact schema:

{
  "title": "short 3-6 word title of the system",
  "tagline": "one-line pitch",
  "core_insight": "the hidden structural truth of the problem, 3-6 sentences",
  "system_blueprint": {
    "architecture": "prose description of the architecture",
    "components": [{"name": "...", "role": "...", "tech": "..."}],
    "tech_stack": {"frontend": "...", "backend": "...", "database": "...", "infra": "...", "ai": "..."},
    "data_models": [{"name": "...", "fields": [{"name":"...","type":"...","note":"..."}]}]
  },
  "leverage_point": {
    "the_move": "the ONE highest-ROI move",
    "why_it_works": "mechanism of outsized advantage",
    "impact_effort": {"impact": "10", "effort": "3"}
  },
  "roadmap": [{"phase": "Phase 1: ...", "weeks": "0-2", "deliverables": ["...","..."]}],
  "risks": [{"risk": "...", "severity": "High|Medium|Low", "mitigation": "..."}],
  "monetization": {
    "model": "SaaS / marketplace / etc",
    "pricing_tiers": [{"name":"Starter","price":"$0","includes":["..."]}],
    "unit_economics": "CAC/LTV notes",
    "growth_loops": ["..."]
  },
  "executable_output": {
    "summary": "what the user can ship today",
    "artifacts": [
      {"kind": "code|schema|prompt|api_spec|sql", "language": "python|typescript|sql|json|markdown", "filename": "...", "content": "..."}
    ]
  }
}

Rules:
- Return ONLY valid JSON. No prose outside JSON.
- Provide at least 3 components, 3 data models, 4 roadmap phases, 3 risks, 2 pricing tiers, and 2 executable artifacts (at least one real, runnable code snippet).
- Keep each artifact "content" under 120 lines of code. Focus on the most valuable, runnable core, not exhaustive scaffolding.
- Executable artifact "content" MUST contain real code / real schema, not placeholders.
- Be specific, opinionated, and non-generic. Never say "depends on the use case".
"""


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@api.post("/auth/register", response_model=AuthResponse)
async def register(body: RegisterIn):
    email = body.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    uid = str(uuid.uuid4())
    doc = {
        "id": uid,
        "email": email,
        "name": body.name.strip(),
        "password_hash": hash_password(body.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(doc)
    token = create_access_token(uid, email)
    return AuthResponse(
        token=token,
        user=UserOut(id=uid, email=email, name=doc["name"], created_at=doc["created_at"]),
    )


@api.post("/auth/login", response_model=AuthResponse)
async def login(body: LoginIn):
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"], email)
    return AuthResponse(
        token=token,
        user=UserOut(id=user["id"], email=user["email"], name=user["name"], created_at=user["created_at"]),
    )


@api.get("/auth/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user)):
    return UserOut(id=user["id"], email=user["email"], name=user["name"], created_at=user["created_at"])


# ---------------------------------------------------------------------------
# Blueprints
# ---------------------------------------------------------------------------
def _serialize_blueprint(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


def _build_chat_and_prompt(body: BlueprintCreateIn):
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"bp-{uuid.uuid4()}",
        system_message=ARCHITECT_SYSTEM_PROMPT,
    ).with_model("anthropic", "claude-sonnet-5").with_params(max_tokens=16000)

    constraints = []
    if body.industry:
        constraints.append(f"Industry: {body.industry}")
    if body.budget:
        constraints.append(f"Capital budget: {body.budget}")
    if body.timeline:
        constraints.append(f"Timeline: {body.timeline}")
    if body.scale:
        constraints.append(f"Target scale: {body.scale}")
    constraint_str = "\n".join(constraints) if constraints else "No explicit constraints."

    prompt = (
        f"IDEA:\n{body.idea}\n\n"
        f"CONSTRAINTS:\n{constraint_str}\n\n"
        "Produce the full JSON blueprint per the schema. Return ONLY JSON."
    )
    return chat, prompt


def _parse_llm_json(raw) -> dict:
    text = raw if isinstance(raw, str) else str(raw)
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text[: -3]
        text = text.strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        log.error("LLM returned invalid JSON: %s\n---\n%s", e, text[:1000])
        raise HTTPException(status_code=502, detail="AI returned invalid JSON. Try again.")


async def generate_blueprint_with_llm(body: BlueprintCreateIn) -> dict:
    chat, prompt = _build_chat_and_prompt(body)
    raw = await chat.send_message(UserMessage(text=prompt))
    return _parse_llm_json(raw)


def _blueprint_doc(body: BlueprintCreateIn, content: dict, user_id: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    title = content.get("title") or (body.idea[:60] + ("..." if len(body.idea) > 60 else ""))
    return {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title,
        "idea": body.idea,
        "industry": body.industry,
        "budget": body.budget,
        "timeline": body.timeline,
        "scale": body.scale,
        "content": content,
        "created_at": now,
        "updated_at": now,
    }


@api.post("/blueprints")
async def create_blueprint(body: BlueprintCreateIn, user: dict = Depends(get_current_user)):
    content = await generate_blueprint_with_llm(body)
    doc = _blueprint_doc(body, content, user["id"])
    await db.blueprints.insert_one(doc)
    return _serialize_blueprint(doc)


@api.post("/blueprints/stream")
async def stream_blueprint(body: BlueprintCreateIn, user: dict = Depends(get_current_user)):
    chat, prompt = _build_chat_and_prompt(body)

    def sse(obj: dict) -> str:
        return f"data: {json.dumps(obj)}\n\n"

    async def gen():
        chunks = []
        try:
            async for ev in chat.stream_message(UserMessage(text=prompt)):
                if isinstance(ev, TextDelta):
                    chunks.append(ev.content)
                    yield sse({"type": "token", "content": ev.content})
                elif isinstance(ev, StreamDone):
                    break
            content = _parse_llm_json("".join(chunks))
            doc = _blueprint_doc(body, content, user["id"])
            await db.blueprints.insert_one(doc)
            yield sse({"type": "done", "blueprint": _serialize_blueprint(doc)})
        except HTTPException as e:
            yield sse({"type": "error", "detail": e.detail})
        except Exception as e:
            log.exception("Streaming generation failed")
            yield sse({"type": "error", "detail": f"Generation failed: {str(e)[:200]}"})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@api.get("/blueprints")
async def list_blueprints(user: dict = Depends(get_current_user)):
    cursor = db.blueprints.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1)
    items = await cursor.to_list(500)
    # Return trimmed summary
    return [
        {
            "id": b["id"],
            "title": b["title"],
            "idea": b["idea"],
            "industry": b.get("industry"),
            "created_at": b["created_at"],
            "tagline": (b.get("content") or {}).get("tagline"),
            "core_insight_snippet": ((b.get("content") or {}).get("core_insight") or "")[:180],
            "tech_stack": ((b.get("content") or {}).get("system_blueprint") or {}).get("tech_stack"),
        }
        for b in items
    ]


@api.get("/blueprints/{bp_id}")
async def get_blueprint(bp_id: str, user: dict = Depends(get_current_user)):
    doc = await db.blueprints.find_one({"id": bp_id, "user_id": user["id"]}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return doc


@api.patch("/blueprints/{bp_id}")
async def rename_blueprint(bp_id: str, body: BlueprintRenameIn, user: dict = Depends(get_current_user)):
    result = await db.blueprints.update_one(
        {"id": bp_id, "user_id": user["id"]},
        {"$set": {"title": body.title.strip(), "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return {"ok": True}


@api.delete("/blueprints/{bp_id}")
async def delete_blueprint(bp_id: str, user: dict = Depends(get_current_user)):
    result = await db.blueprints.delete_one({"id": bp_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@api.get("/")
async def root():
    return {"service": "emergent-architect", "status": "online"}


app.include_router(api)

from core import make_router as make_core_router  # noqa: E402

app.include_router(make_core_router(db, EMERGENT_LLM_KEY, get_current_user))

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.blueprints.create_index("id", unique=True)
    await db.blueprints.create_index("user_id")
    await db.core_runs.create_index("id", unique=True)
    await db.core_runs.create_index("user_id")
    await db.core_metrics.create_index([("engine", 1), ("created_at", -1)])
    log.info("Indexes ensured")


@app.on_event("shutdown")
async def shutdown():
    client.close()
