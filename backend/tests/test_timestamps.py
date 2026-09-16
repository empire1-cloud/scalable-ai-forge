"""
Unit tests for timestamps.py -- no Mongo, no LLM, no network.

Root cause of the stale-Vault-date bug: nothing was hardcoded and nothing
came from the LLM even before this change (verified directly against
server.py) -- the gap was that nothing *guaranteed* that stayed true, and
nothing would notice a clock that returned an implausible value. These tests
prove the guarantees this module adds.
"""
import logging
from datetime import datetime, timezone

import pytest

import timestamps


def test_now_iso_returns_a_valid_current_year_timestamp():
    value = timestamps.now_iso()
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None
    assert parsed.year == datetime.now(timezone.utc).year


def test_now_iso_logs_loudly_but_still_returns_a_value_when_clock_looks_wrong(monkeypatch, caplog):
    class _FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2020, 1, 1, tzinfo=tz)

    monkeypatch.setattr(timestamps, "datetime", _FakeDatetime)

    with caplog.at_level(logging.ERROR, logger="architect.timestamps"):
        value = timestamps.now_iso()

    assert value.startswith("2020-01-01")
    assert any("implausible" in record.message for record in caplog.records)


def test_now_iso_is_silent_for_a_plausible_clock(caplog):
    with caplog.at_level(logging.ERROR, logger="architect.timestamps"):
        timestamps.now_iso()
    assert not caplog.records


@pytest.mark.parametrize(
    "hallucinated_key",
    ["created_at", "CREATED_AT", "createdAt", "updated_at", "date", "timestamp", "generated_at"],
)
def test_strip_llm_supplied_timestamp_fields_removes_every_alias(hallucinated_key):
    content = {"title": "x", hallucinated_key: "1999-01-01T00:00:00+00:00", "summary": "real content"}
    cleaned = timestamps.strip_llm_supplied_timestamp_fields(content)
    assert hallucinated_key not in cleaned
    assert cleaned["title"] == "x"
    assert cleaned["summary"] == "real content"


def test_strip_llm_supplied_timestamp_fields_does_not_mutate_input():
    content = {"title": "x", "created_at": "1999-01-01"}
    timestamps.strip_llm_supplied_timestamp_fields(content)
    assert "created_at" in content  # original dict untouched


def test_strip_llm_supplied_timestamp_fields_is_a_noop_when_nothing_to_strip():
    content = {"title": "x", "summary": "y", "steps": ["a", "b"]}
    assert timestamps.strip_llm_supplied_timestamp_fields(content) == content


@pytest.mark.parametrize("forbidden_key", ["created_at", "id", "_id", "user_id"])
def test_apply_safe_update_strips_immutable_fields(forbidden_key):
    proposed = {"title": "New Title", forbidden_key: "attacker-supplied-value"}
    safe = timestamps.apply_safe_update(proposed)
    assert forbidden_key not in safe
    assert safe["title"] == "New Title"


def test_apply_safe_update_always_injects_a_fresh_updated_at():
    safe = timestamps.apply_safe_update({"title": "x"})
    assert "updated_at" in safe
    parsed = datetime.fromisoformat(safe["updated_at"])
    assert parsed.year == datetime.now(timezone.utc).year


def test_apply_safe_update_overrides_a_caller_supplied_updated_at():
    """Even a well-intentioned caller can't backdate updated_at."""
    safe = timestamps.apply_safe_update({"title": "x", "updated_at": "1999-01-01T00:00:00+00:00"})
    assert safe["updated_at"] != "1999-01-01T00:00:00+00:00"
