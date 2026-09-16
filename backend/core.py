import re
import json
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

log = logging.getLogger("core")

ENGINES = {
    "strategy": {
        "name": "Strategy Engine",
        "provider": "anthropic",
        "model": "claude-sonnet-4-5-20250929",
        "tier": "claude",
        "role": "Structured strategies, business reasoning, positioning, plans of intent.",
        "schema": {
            "objective": "string",
            "situation": "string",
            "strategic_pillars": [{"name": "string", "rationale": "string", "actions": ["string"]}],
            "leverage_point": "string",
            "risks": [{"risk": "string", "mitigation": "string"}],
            "success_metrics": ["string"],
            "time_horizon": "string",
        },
    },
    "plan_builder": {
        "name": "Plan Builder Engine",
        "provider": "anthropic",
        "model": "claude-sonnet-4-5-20250929",
        "tier": "claude",
        "role": "Converts goals into sequenced, actionable execution plans.",
        "schema": {
            "goal": "string",
            "phases": [
                {
                    "name": "string",
                    "duration": "string",
                    "tasks": [{"task": "string", "owner_role": "string", "output": "string"}],
                    "milestone": "string",
                }
            ],
            "dependencies": ["string"],
            "critical_path": ["string"],
        },
    },
    "analysis": {
        "name": "Analysis Engine",
        "provider": "anthropic",
        "model": "claude-sonnet-4-5-20250929",
        "tier": "claude",
        "role": "Deep diagnostic and evaluative analysis: root causes, patterns, evidence.",
        "schema": {
            "subject": "string",
            "findings": [{"finding": "string", "evidence": "string", "severity": "High|Medium|Low"}],
            "root_causes": ["string"],
            "patterns": ["string"],
            "recommendations": ["string"],
            "confidence": "0.0-1.0",
        },
    },
    "code": {
        "name": "Code Engine",
        "provider": "openai",
        "model": "gpt-5.2",
        "tier": "gpt",
        "role": "Coding, logic, algorithms, technical implementation.",
        "schema": {
            "solution_summary": "string",
            "language": "string",
            "files": [{"filename": "string", "content": "string"}],
            "usage": "string",
            "tests": ["string"],
            "notes": ["string"],
        },
    },
    "fast": {
        "name": "Fast Engine",
        "provider": "gemini",
        "model": "gemini-3-flash-preview",
        "tier": "gemini",
        "role": "Fast answers, summaries, lookups, quick transformations.",
        "schema": {"answer": "string", "key_points": ["string"], "assumptions": ["string"]},
    },
}

ROUTER_MODEL = ("gemini", "gemini-3-flash-preview")

CANON_RULES = [
    "No disclaimers",
    "No model identity",
    "No filler language",
    "Direct, operator-grade tone",
    "Always return clean JSON",
]

CANON_PATTERNS = [
    (r"\b(as an ai|as a language model|i am an ai|i'm an ai|i am claude|i am chatgpt|i'm chatgpt|as claude|as gpt|as gemini)\b[^.\n]*[.\n]?", "model_identity"),
    (r"\b(i cannot guarantee|please consult|this is not (financial|legal|medical) advice|consult a professional|disclaimer:)[^.\n]*[.\n]?", "disclaimer"),
    (r"^(certainly|sure|absolutely|great question|of course)[!,.:]?\s*", "filler"),
    (r"\b(i hope this helps|let me know if|feel free to)[^.\n]*[.\n]?", "filler"),
]

DRIFT_THRESHOLDS = {"token_ratio": 0.6, "min_history": 3}


class CoreRunIn(BaseModel):
    task: str = Field(min_length=4, max_length=8000)
    engine_override: Optional[str] = None


def make_router(db, api_key: str, auth_dep) -> APIRouter:
    router = APIRouter(prefix="/api/core")

    # ---------------- helpers ----------------
    def now_iso():
        return datetime.now(timezone.utc).isoformat()

    def error_payload(err_type: str, message: str, stage: str, run_id: Optional[str] = None):
        body = {"error": True, "type": err_type, "message": message, "stage": stage}
        if run_id:
            body["run_id"] = run_id
        return body

    def parse_json(text: str) -> dict:
        t = text.strip()
        if t.startswith("```"):
            t = t.split("\n", 1)[1] if "\n" in t else t
            if t.endswith("```"):
                t = t[:-3]
            t = t.strip()
        if not t.startswith("{"):
            s, e = t.find("{"), t.rfind("}")
            if s != -1 and e != -1:
                t = t[s : e + 1]
        return json.loads(t)

    async def call_model(provider: str, model: str, system: str, prompt: str, max_tokens: int) -> str:
        chat = (
            LlmChat(api_key=api_key, session_id=f"core-{uuid.uuid4()}", system_message=system)
            .with_model(provider, model)
            .with_params(max_tokens=max_tokens)
        )
        chunks = []
        async for ev in chat.stream_message(UserMessage(text=prompt)):
            if isinstance(ev, TextDelta):
                chunks.append(ev.content)
            elif isinstance(ev, StreamDone):
                break
        return "".join(chunks)

    # ---------------- 1. routing engine ----------------
    def heuristic_route(task: str) -> str:
        t = task.lower()
        if re.search(r"\b(code|function|script|api|bug|debug|sql|regex|algorithm|implement|refactor|typescript|python|class)\b", t):
            return "code"
        if re.search(r"\b(analy[sz]e|diagnos|evaluate|audit|root cause|why is|assess|compare)\b", t):
            return "analysis"
        if re.search(r"\b(plan|roadmap|steps|timeline|schedule|milestone|execute|sprint)\b", t):
            return "plan_builder"
        if re.search(r"\b(summari[sz]e|tl;dr|define|what is|quick|lookup|list|translate)\b", t):
            return "fast"
        return "strategy"

    async def route(task: str) -> dict:
        system = (
            "You are the Routing Engine of a multi-model pipeline. Classify the task into exactly one engine.\n"
            "Engines: strategy (business/strategy/planning of intent/reasoning), plan_builder (execution plans, sequenced steps), "
            "analysis (deep diagnostic/evaluative analysis), code (coding/logic/technical), fast (quick answers, summaries, lookups).\n"
            'Return ONLY JSON: {"engine": "strategy|plan_builder|analysis|code|fast", "confidence": 0.0-1.0, "rationale": "one sentence"}'
        )
        raw = ""
        try:
            raw = await call_model(ROUTER_MODEL[0], ROUTER_MODEL[1], system, f"TASK:\n{task}", 300)
            try:
                data = parse_json(raw)
            except json.JSONDecodeError:
                m = re.search(r'"engine"\s*:\s*"(\w+)"', raw)
                if not m:
                    raise
                data = {"engine": m.group(1), "confidence": 0.7, "rationale": "Recovered from malformed router JSON."}
            engine = data.get("engine")
            if engine not in ENGINES:
                raise ValueError("unknown engine")
            return {
                "engine": engine,
                "confidence": float(data.get("confidence", 0.7)),
                "rationale": data.get("rationale", ""),
                "router_model": ROUTER_MODEL[1],
                "method": "llm",
            }
        except Exception as e:
            log.warning("Router LLM failed, using heuristic: %s | raw=%s", e, raw[:300])
            return {
                "engine": heuristic_route(task),
                "confidence": 0.5,
                "rationale": "Heuristic fallback classification.",
                "router_model": ROUTER_MODEL[1],
                "method": "heuristic",
            }

    # ---------------- 2. engine execution ----------------
    async def run_engine(engine_key: str, task: str) -> dict:
        eng = ENGINES[engine_key]
        system = (
            f"You are the {eng['name']} inside the Hybrid Intelligence Core. Role: {eng['role']}\n"
            "CANON RULES: " + "; ".join(CANON_RULES) + ".\n"
            "Never mention which model you are. No preface, no disclaimers, no filler. Operator-grade, direct.\n"
            "Return ONLY strict JSON matching this schema (no markdown fences):\n"
            + json.dumps(eng["schema"], indent=2)
        )
        raw = await call_model(eng["provider"], eng["model"], system, f"TASK:\n{task}", 6000)
        return parse_json(raw)

    # ---------------- 3. canon enforcer ----------------
    def enforce_canon(output: dict) -> tuple[dict, dict]:
        violations = []

        def clean(val, path):
            if isinstance(val, str):
                cleaned = val
                for pat, kind in CANON_PATTERNS:
                    if re.search(pat, cleaned, flags=re.I | re.M):
                        violations.append({"rule": kind, "path": path})
                        cleaned = re.sub(pat, "", cleaned, flags=re.I | re.M)
                return re.sub(r"\s{3,}", " ", cleaned).strip() if cleaned != val else val
            if isinstance(val, list):
                return [clean(v, f"{path}[{i}]") for i, v in enumerate(val)]
            if isinstance(val, dict):
                return {k: clean(v, f"{path}.{k}" if path else k) for k, v in val.items()}
            return val

        normalized = clean(output, "")
        return normalized, {"compliant": len(violations) == 0, "violations": violations, "rules": CANON_RULES}

    # ---------------- 4. drift monitor ----------------
    def measure(output: dict, canon: dict) -> dict:
        text = json.dumps(output)
        return {
            "token_estimate": max(1, len(text) // 4),
            "top_level_keys": sorted(output.keys()),
            "depth": _depth(output),
            "canon_violations": len(canon["violations"]),
            "compliance": 1.0 if canon["compliant"] else max(0.0, 1 - 0.2 * len(canon["violations"])),
        }

    def _depth(o, d=0):
        if isinstance(o, dict):
            return max([_depth(v, d + 1) for v in o.values()] + [d + 1])
        if isinstance(o, list):
            return max([_depth(v, d + 1) for v in o] + [d + 1])
        return d

    async def monitor_drift(engine_key: str, metrics: dict) -> dict:
        history = await db.core_metrics.find({"engine": engine_key}, {"_id": 0}).sort("created_at", -1).to_list(50)
        flags = []
        baseline = None
        if len(history) >= DRIFT_THRESHOLDS["min_history"]:
            avg_tokens = sum(h["metrics"]["token_estimate"] for h in history) / len(history)
            avg_compliance = sum(h["metrics"]["compliance"] for h in history) / len(history)
            baseline = {"avg_tokens": round(avg_tokens), "avg_compliance": round(avg_compliance, 3), "samples": len(history)}
            ratio = abs(metrics["token_estimate"] - avg_tokens) / max(avg_tokens, 1)
            if ratio > DRIFT_THRESHOLDS["token_ratio"]:
                flags.append({"type": "token_drift", "detail": f"Output size deviates {round(ratio*100)}% from baseline."})
            expected_keys = sorted(ENGINES[engine_key]["schema"].keys())
            if metrics["top_level_keys"] != expected_keys:
                flags.append({"type": "structure_drift", "detail": "Top-level keys differ from canonical schema."})
            if metrics["compliance"] < avg_compliance - 0.15:
                flags.append({"type": "tone_drift", "detail": "Canon compliance below rolling baseline."})
        else:
            expected_keys = sorted(ENGINES[engine_key]["schema"].keys())
            if metrics["top_level_keys"] != expected_keys:
                flags.append({"type": "structure_drift", "detail": "Top-level keys differ from canonical schema."})
        await db.core_metrics.insert_one({"id": str(uuid.uuid4()), "engine": engine_key, "metrics": metrics, "flags": flags, "created_at": now_iso()})
        return {"flags": flags, "metrics": metrics, "baseline": baseline, "stable": len(flags) == 0}

    # ---------------- orchestrator ----------------
    @router.post("/run")
    async def run(body: CoreRunIn, user: dict = Depends(auth_dep)):
        if user.get("plan", "free") not in ("pro", "team"):
            return JSONResponse(
                error_payload("access_denied", "The Hybrid Intelligence Core is a Pro feature. Upgrade to unlock multi-model orchestration.", "orchestrator"),
                status_code=402,
            )
        run_id = str(uuid.uuid4())
        t0 = time.time()
        stages = []
        task = body.task.strip()

        async def persist(doc_extra: dict):
            doc = {"id": run_id, "user_id": user["id"], "task": task, "created_at": now_iso(), "latency_ms": int((time.time() - t0) * 1000), "stages": stages, **doc_extra}
            await db.core_runs.insert_one(doc)

        # routing
        try:
            if body.engine_override:
                if body.engine_override not in ENGINES:
                    err = error_payload("routing_error", f"Unknown engine '{body.engine_override}'.", "routing", run_id)
                    await persist({"error": err})
                    return JSONResponse(err, status_code=400)
                routing = {"engine": body.engine_override, "confidence": 1.0, "rationale": "Manual override.", "router_model": None, "method": "override"}
            else:
                routing = await route(task)
            stages.append({"stage": "routing", "ok": True, "engine": routing["engine"]})
        except Exception as e:
            err = error_payload("routing_error", str(e)[:200], "routing", run_id)
            await persist({"error": err})
            return JSONResponse(err, status_code=502)

        engine_key = routing["engine"]
        eng = ENGINES[engine_key]

        # generation
        try:
            output = await run_engine(engine_key, task)
            stages.append({"stage": "strategy", "ok": True, "engine": engine_key, "model": eng["model"]})
        except json.JSONDecodeError:
            err = error_payload("generation_error", f"{eng['name']} returned non-JSON output.", "strategy", run_id)
            await persist({"error": err, "engine": engine_key, "routing": routing})
            return JSONResponse(err, status_code=502)
        except Exception as e:
            err = error_payload("generation_error", str(e)[:200], "strategy", run_id)
            await persist({"error": err, "engine": engine_key, "routing": routing})
            return JSONResponse(err, status_code=502)

        # canon
        try:
            output, canon = enforce_canon(output)
            stages.append({"stage": "canon", "ok": True, "violations": len(canon["violations"])})
        except Exception as e:
            err = error_payload("canon_error", str(e)[:200], "canon", run_id)
            await persist({"error": err, "engine": engine_key, "routing": routing})
            return JSONResponse(err, status_code=500)

        # drift
        try:
            drift = await monitor_drift(engine_key, measure(output, canon))
            stages.append({"stage": "drift", "ok": True, "flags": len(drift["flags"])})
        except Exception as e:
            err = error_payload("drift_error", str(e)[:200], "drift", run_id)
            await persist({"error": err, "engine": engine_key, "routing": routing})
            return JSONResponse(err, status_code=500)

        result = {
            "error": False,
            "run_id": run_id,
            "engine": engine_key,
            "engine_name": eng["name"],
            "model": eng["model"],
            "provider": eng["provider"],
            "routing": routing,
            "output": output,
            "canon": canon,
            "drift": drift,
            "latency_ms": int((time.time() - t0) * 1000),
        }
        await persist({k: v for k, v in result.items() if k not in ("run_id", "latency_ms")})
        return result

    @router.get("/runs")
    async def list_runs(user: dict = Depends(auth_dep)):
        items = await db.core_runs.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
        return [
            {
                "id": r["id"],
                "task": r["task"][:140],
                "engine": r.get("engine"),
                "model": r.get("model"),
                "error": bool(r.get("error")),
                "latency_ms": r.get("latency_ms"),
                "drift_flags": len((r.get("drift") or {}).get("flags", [])),
                "created_at": r["created_at"],
            }
            for r in items
        ]

    @router.get("/runs/{run_id}")
    async def get_run(run_id: str, user: dict = Depends(auth_dep)):
        doc = await db.core_runs.find_one({"id": run_id, "user_id": user["id"]}, {"_id": 0})
        if not doc:
            return JSONResponse(error_payload("system_error", "Run not found.", "orchestrator"), status_code=404)
        return doc

    @router.get("/metrics")
    async def metrics(user: dict = Depends(auth_dep)):
        out = {}
        for key in ENGINES:
            hist = await db.core_metrics.find({"engine": key}, {"_id": 0}).sort("created_at", -1).to_list(50)
            if not hist:
                out[key] = {"samples": 0}
                continue
            out[key] = {
                "samples": len(hist),
                "avg_tokens": round(sum(h["metrics"]["token_estimate"] for h in hist) / len(hist)),
                "avg_compliance": round(sum(h["metrics"]["compliance"] for h in hist) / len(hist), 3),
                "drift_events": sum(len(h["flags"]) for h in hist),
                "last_run": hist[0]["created_at"],
            }
        return out

    @router.get("/playbook")
    async def playbook():
        return {
            "name": "Hybrid Intelligence Core",
            "version": "1.0",
            "pipeline": ["routing", "engine_execution", "canon_enforcer", "drift_monitor", "error_handler"],
            "routing_logic": [
                {"signal": "Strategy, planning, business, reasoning", "engine": "strategy", "tier": "claude", "model": ENGINES["strategy"]["model"]},
                {"signal": "Execution planning", "engine": "plan_builder", "tier": "claude", "model": ENGINES["plan_builder"]["model"]},
                {"signal": "Deep analysis", "engine": "analysis", "tier": "claude", "model": ENGINES["analysis"]["model"]},
                {"signal": "Coding, logic, technical tasks", "engine": "code", "tier": "gpt", "model": ENGINES["code"]["model"]},
                {"signal": "Fast answers, summaries, lookups", "engine": "fast", "tier": "gemini", "model": ENGINES["fast"]["model"]},
            ],
            "router": {"model": ROUTER_MODEL[1], "fallback": "keyword heuristic"},
            "engines": {k: {"name": v["name"], "provider": v["provider"], "model": v["model"], "role": v["role"], "schema": v["schema"]} for k, v in ENGINES.items()},
            "canon_rules": CANON_RULES,
            "formatting_standards": ["Strict JSON, no fences", "Schema per engine", "snake_case keys", "No prose outside JSON"],
            "drift_prevention": {
                "tracked": ["token_estimate", "top_level_keys", "depth", "canon_violations", "compliance"],
                "policy": "Flag deviations, never modify output",
                "thresholds": DRIFT_THRESHOLDS,
                "storage": "core_metrics collection (rolling 50 per engine)",
            },
            "error_format": {"error": True, "type": "routing_error | generation_error | canon_error | drift_error | system_error", "message": "string", "stage": "routing | strategy | canon | drift | orchestrator"},
        }

    return router

