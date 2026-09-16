"""
Prompt/schema tests for the fundable -> funding-readiness reframe and
provenance tagging. Pure string/content assertions on ARCHITECT_SYSTEM_PROMPT
-- no LLM call, since what the model actually returns can't be tested
without one; what CAN be tested and matters just as much is that the
instruction we're sending it is the one we intend to send.
"""
import json
import re
import sys
import types


def _stub_llm():
    for name in ("emergentintegrations", "emergentintegrations.llm", "emergentintegrations.llm.chat"):
        sys.modules.setdefault(name, types.ModuleType(name))
    chat = sys.modules["emergentintegrations.llm.chat"]
    if not hasattr(chat, "LlmChat"):
        class _Stub:
            def __init__(self, *a, **k):
                pass

            def with_model(self, *a, **k):
                return self

            def with_params(self, *a, **k):
                return self

        chat.LlmChat = _Stub
        chat.UserMessage = _Stub
        chat.TextDelta = _Stub
        chat.StreamDone = _Stub


_stub_llm()

import os  # noqa: E402

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "scalable_ai_forge_prompt_schema_test")
os.environ.setdefault("JWT_SECRET", "test-secret-not-real")
os.environ.setdefault("EMERGENT_LLM_KEY", "test-key-not-real-never-called")

from server import ARCHITECT_SYSTEM_PROMPT  # noqa: E402

# Pull the embedded JSON schema block out of the prompt so we can parse it
# structurally instead of doing fragile substring matching on the whole
# prompt text.
_SCHEMA_MATCH = re.search(r"\{.*\}", ARCHITECT_SYSTEM_PROMPT, re.DOTALL)
SCHEMA_TEXT = _SCHEMA_MATCH.group(0)
SCHEMA = json.loads(SCHEMA_TEXT)


FUNDING_READINESS_DIMENSIONS = {
    "technical_readiness",
    "market_evidence",
    "revenue_evidence",
    "defensibility",
    "capital_requirements",
    "deployment_readiness",
    "founder_execution_evidence",
}

PROVENANCE_TAGS = {"Fact", "Derived", "Proposed", "Unverified", "Generated"}


# ---------------------------------------------------------------------------
# funding_readiness reframe
# ---------------------------------------------------------------------------
def test_schema_has_no_binary_fundable_verdict_field():
    schema_keys = set(SCHEMA.keys()) | set(SCHEMA.get("funding_readiness", {}).keys())
    banned = {"fundable", "is_fundable", "fundability", "funded"}
    assert not (schema_keys & banned), f"binary fundability field(s) present: {schema_keys & banned}"


def test_schema_has_funding_readiness_section_with_all_seven_dimensions():
    assert "funding_readiness" in SCHEMA
    dimensions = SCHEMA["funding_readiness"]["dimensions"]
    assert set(dimensions.keys()) == FUNDING_READINESS_DIMENSIONS


def test_every_funding_readiness_dimension_asks_for_evidence_and_a_gap():
    for name, shape in SCHEMA["funding_readiness"]["dimensions"].items():
        assert "gap" in shape, f"{name} schema doesn't ask for a gap"


def test_funding_readiness_has_an_overall_gaps_list_and_a_disclaimer_note():
    fr = SCHEMA["funding_readiness"]
    assert "overall_gaps" in fr
    assert isinstance(fr["overall_gaps"], list)
    assert "note" in fr


def test_prompt_explicitly_instructs_against_a_fundable_verdict():
    lowered = ARCHITECT_SYSTEM_PROMPT.lower()
    assert "never output the words" in lowered or "never assert that a business" in lowered
    assert "fundable" in lowered  # present only inside the prohibition, checked below


def test_the_only_use_of_fundable_in_the_prompt_is_the_prohibition_itself():
    """The word may appear while telling the model not to use it; it must not
    appear anywhere that reads as the system itself making the claim.

    Checked over paragraphs (blank-line-separated blocks), not physical
    lines -- the prohibition sentence itself wraps across multiple lines in
    the source.
    """
    paragraphs = re.split(r"\n\s*\n", ARCHITECT_SYSTEM_PROMPT)
    paragraphs_with_fundable = [p for p in paragraphs if "fundable" in p.lower()]
    assert paragraphs_with_fundable, "expected at least the prohibition paragraph"
    for paragraph in paragraphs_with_fundable:
        collapsed = " ".join(paragraph.split())
        assert re.search(r"never|not a|cannot|no basis", collapsed, re.IGNORECASE), (
            f"paragraph mentions 'fundable' without clearly prohibiting it: {collapsed!r}"
        )


# ---------------------------------------------------------------------------
# provenance tagging
# ---------------------------------------------------------------------------
def test_schema_has_a_provenance_section():
    assert "provenance" in SCHEMA


def test_provenance_covers_every_major_claim_bearing_section():
    provenance = SCHEMA["provenance"]
    expected_sections = {
        "core_insight", "system_blueprint", "leverage_point", "roadmap",
        "risks", "monetization", "funding_readiness", "executable_output",
    }
    assert expected_sections <= set(provenance.keys())


def test_provenance_example_values_use_only_the_five_allowed_tags():
    provenance = SCHEMA["provenance"]
    for section, value in provenance.items():
        values = value if isinstance(value, list) else [value]
        for tag in values:
            assert tag in PROVENANCE_TAGS, f"{section} uses an unlisted provenance tag: {tag!r}"


def test_risks_provenance_is_an_array_matching_the_per_item_nature_of_risks():
    assert isinstance(SCHEMA["provenance"]["risks"], list)


def test_prompt_defines_all_five_provenance_tags_with_meanings():
    prompt_lower = ARCHITECT_SYSTEM_PROMPT.lower()
    for tag in PROVENANCE_TAGS:
        assert f'"{tag.lower()}"' in prompt_lower, f"provenance tag {tag!r} is not defined in the prompt rules"


def test_prompt_requires_every_dimension_to_be_filled_even_with_no_evidence():
    assert "never omit a dimension" in ARCHITECT_SYSTEM_PROMPT.lower()
