"""Provider-direct LLM client — drop-in replacement for `emergentintegrations.llm.chat`.

Same surface the app already uses (LlmChat / UserMessage / TextDelta / StreamDone,
`.with_model()`, `.with_params()`, `send_message()`, `stream_message()`), but it
calls Anthropic, OpenAI and Google directly with YOUR keys instead of routing
through Emergent's universal key (which bills Emergent credits and only installs
inside Emergent).

Env vars:
  ANTHROPIC_API_KEY   required (primary provider)
  OPENAI_API_KEY      optional — if missing, "openai" calls fall back to Anthropic
  GEMINI_API_KEY      optional — if missing, "gemini" calls fall back to Anthropic
  LLM_FALLBACK_MODEL  Anthropic model used for fallbacks (default below)
  ANTHROPIC_MODEL_OVERRIDE  optional — force every Anthropic call onto one model id
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import AsyncIterator, Optional, Union

log = logging.getLogger("llm_client")

DEFAULT_FALLBACK_MODEL = "claude-sonnet-4-5-20250929"


@dataclass
class UserMessage:
    text: str


@dataclass
class TextDelta:
    content: str


@dataclass
class StreamDone:
    pass


StreamEvent = Union[TextDelta, StreamDone]


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


class LlmChat:
    def __init__(self, api_key: Optional[str] = None, session_id: Optional[str] = None, system_message: str = ""):
        # api_key is accepted for signature compatibility; an explicit non-empty
        # key is used for Anthropic only. Other providers read their own env var.
        self._explicit_key = (api_key or "").strip()
        self.session_id = session_id
        self.system_message = system_message or ""
        self.provider = "anthropic"
        self.model = DEFAULT_FALLBACK_MODEL
        self.max_tokens = 4096

    def with_model(self, provider: str, model: str) -> "LlmChat":
        self.provider = (provider or "anthropic").lower()
        self.model = model
        return self

    def with_params(self, max_tokens: Optional[int] = None, **_ignored) -> "LlmChat":
        if max_tokens:
            self.max_tokens = int(max_tokens)
        return self

    # ------------------------------------------------------------------ routing
    def _resolve(self) -> tuple[str, str]:
        provider, model = self.provider, self.model
        if provider == "openai" and not _env("OPENAI_API_KEY"):
            log.warning("OPENAI_API_KEY not set; routing %s to Anthropic fallback", model)
            provider, model = "anthropic", _env("LLM_FALLBACK_MODEL") or DEFAULT_FALLBACK_MODEL
        elif provider in ("gemini", "google") and not _env("GEMINI_API_KEY"):
            log.warning("GEMINI_API_KEY not set; routing %s to Anthropic fallback", model)
            provider, model = "anthropic", _env("LLM_FALLBACK_MODEL") or DEFAULT_FALLBACK_MODEL
        if provider == "anthropic" and _env("ANTHROPIC_MODEL_OVERRIDE"):
            model = _env("ANTHROPIC_MODEL_OVERRIDE")
        return provider, model

    # ------------------------------------------------------------------ public
    async def send_message(self, message: UserMessage) -> str:
        parts = []
        async for ev in self.stream_message(message):
            if isinstance(ev, TextDelta):
                parts.append(ev.content)
        return "".join(parts)

    async def stream_message(self, message: UserMessage) -> AsyncIterator[StreamEvent]:
        provider, model = self._resolve()
        text = message.text
        if provider == "anthropic":
            gen = self._stream_anthropic(model, text)
        elif provider == "openai":
            gen = self._stream_openai(model, text)
        elif provider in ("gemini", "google"):
            gen = self._stream_gemini(model, text)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        async for chunk in gen:
            if chunk:
                yield TextDelta(content=chunk)
        yield StreamDone()

    # ------------------------------------------------------------------ providers
    async def _stream_anthropic(self, model: str, text: str) -> AsyncIterator[str]:
        from anthropic import AsyncAnthropic

        key = self._explicit_key if self._explicit_key.startswith("sk-ant-") else _env("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        client = AsyncAnthropic(api_key=key)
        kwargs = dict(model=model, max_tokens=self.max_tokens, messages=[{"role": "user", "content": text}])
        if self.system_message:
            kwargs["system"] = self.system_message
        async with client.messages.stream(**kwargs) as stream:
            async for chunk in stream.text_stream:
                yield chunk

    async def _stream_openai(self, model: str, text: str) -> AsyncIterator[str]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=_env("OPENAI_API_KEY"))
        messages = []
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        messages.append({"role": "user", "content": text})
        stream = await client.chat.completions.create(
            model=model, messages=messages, max_completion_tokens=self.max_tokens, stream=True
        )
        async for event in stream:
            if event.choices and event.choices[0].delta and event.choices[0].delta.content:
                yield event.choices[0].delta.content

    async def _stream_gemini(self, model: str, text: str) -> AsyncIterator[str]:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=_env("GEMINI_API_KEY"))
        config = types.GenerateContentConfig(
            system_instruction=self.system_message or None, max_output_tokens=self.max_tokens
        )
        stream = await client.aio.models.generate_content_stream(model=model, contents=text, config=config)
        async for chunk in stream:
            if getattr(chunk, "text", None):
                yield chunk.text
