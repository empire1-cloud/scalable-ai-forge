"""
Server-authoritative timestamps for blueprints (and any other resource that
wants them).

Root cause of the stale-date bug (Vault cards showing 2020 while it's 2026):
`_blueprint_doc()` and `rename_blueprint()` already only ever wrote
`datetime.now(timezone.utc).isoformat()` -- never a hardcoded value, never
something read from the LLM's JSON, never something a client could supply.
Every write site and the frontend's `new Date(b.created_at)` render path were
all individually correct. What was missing was a *guarantee*: nothing
enforced that they would always stay that way, and nothing would notice if
`datetime.now()` itself ever returned an implausible value (the realistic
failure mode for an ephemeral/restored dev container: a system clock that
hasn't finished syncing, or was frozen at snapshot time, momentarily reports
a stale wall-clock date -- `datetime.now()` faithfully returns exactly that).
A blueprint written at such a moment would silently persist a real, validly
formatted, wrong date -- which is what a "2020" Vault card actually is: not
a parsing bug, a bad write.

This module makes the invariants explicit and enforced:
  - `now_iso()` is the one function anything should call for a server
    timestamp. It logs loudly (does not block the request -- a clock glitch
    should not turn into a 500) if the wall clock looks implausible.
  - `strip_llm_supplied_timestamp_fields()` removes any date/time-shaped key
    an LLM response might contain before that content is ever stored, so a
    hallucinated date can never be mistaken for -- or silently override --
    the real one.
  - `apply_safe_update()` is the one function anything should call to build
    a MongoDB `$set` payload for an existing resource. It strips
    `created_at`/`id`/`_id`/`user_id` from whatever fields are proposed (so
    `created_at` cannot be touched by any future update path, accidentally
    or otherwise) and always injects a fresh `updated_at`.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterable

log = logging.getLogger("architect.timestamps")

# This app's git history starts 2026-09-15. Nothing it creates today can
# predate that. A generous floor (not "today") avoids false alarms from
# clock skew of a few hours/days while still catching the class of bug this
# fixes (a clock that is off by literal years).
MIN_PLAUSIBLE_YEAR = 2025

# Never let content the LLM produced masquerade as -- or silently overwrite
# -- a server-set timestamp. Covers common casings/aliases defensively.
_TIMESTAMP_LIKE_KEYS = {
    "created_at", "createdat", "created", "updated_at", "updatedat", "updated",
    "date", "timestamp", "generated_at", "generatedat",
}

# Fields nothing is ever allowed to move into a blueprint's $set payload,
# regardless of what the caller proposes.
_IMMUTABLE_UPDATE_FIELDS = {"created_at", "id", "_id", "user_id"}


def now_iso() -> str:
    """The one source of truth for a server-generated timestamp.

    Never raises and never blocks the caller on a clock problem -- it logs
    at ERROR level (visible in ops/monitoring immediately, unlike a bad date
    quietly sitting in a Vault card) and returns the real value regardless,
    since there is no more-trustworthy time source available in-process to
    substitute it with.
    """
    now = datetime.now(timezone.utc)
    if now.year < MIN_PLAUSIBLE_YEAR:
        log.error(
            "System clock looks implausible: datetime.now(timezone.utc) returned %s "
            "(year < %s). A timestamp written right now would be wrong. This is the "
            "root cause class behind stale Vault dates -- check the host/container clock.",
            now.isoformat(), MIN_PLAUSIBLE_YEAR,
        )
    return now.isoformat()


def strip_llm_supplied_timestamp_fields(content: Dict[str, Any]) -> Dict[str, Any]:
    """Remove any date/time-shaped top-level key from LLM-generated content.

    Defensive: the current prompt schema does not ask for a date field, and
    `_blueprint_doc()` never reads one from `content` for `created_at`. This
    makes that guarantee structural instead of incidental, so a future
    prompt change (or a model that free-associates an extra field) can never
    introduce a value that gets confused with the real, server-set
    timestamp. Does not mutate the input.
    """
    return {k: v for k, v in content.items() if k.lower() not in _TIMESTAMP_LIKE_KEYS}


def apply_safe_update(proposed_fields: Dict[str, Any]) -> Dict[str, Any]:
    """Build a MongoDB `$set` payload that can never touch created_at/id/user_id.

    Always includes a fresh `updated_at`. Use this for every future
    "modify an existing blueprint" endpoint, not just rename, so the
    immutability guarantee holds regardless of how many mutation endpoints
    this app grows.
    """
    safe = {k: v for k, v in proposed_fields.items() if k not in _IMMUTABLE_UPDATE_FIELDS}
    safe["updated_at"] = now_iso()
    return safe
