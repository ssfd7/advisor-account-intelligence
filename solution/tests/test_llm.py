"""LLM extraction and brief checks.

Offline tests always run. Live tests call Claude and are skipped unless credentials are configured and AAI_LIVE=1:

    cd solution && AAI_LIVE=1 ../.venv/bin/python -m pytest -q tests/test_llm.py
"""
import os
from datetime import date

import pytest

from aai import DATA
from aai.brief import ActionChoice, Brief, Section, Statement, verify
from aai.ingest import parse_interaction
from aai.llm import schema

live = pytest.mark.skipif(os.environ.get("AAI_LIVE") != "1", reason="set AAI_LIVE=1 with Anthropic credentials to call Claude")

ITEMS = {
    "AST-001": {"type": "asset observation", "value": "300000000.0"},
    "AST-002": {"type": "asset observation", "value": "180000000.0"},
    "ASSET-RULE": {"type": "rule", "text": "Totals or shares not allowed"},
    "PSR:CAND-03-1": {"type": "product state", "state": "paused"},
    "ACT:CAND-03-1": {"type": "proposed action", "title": "Integration review"},
}


def brief(statements, actions=()):
    return Brief(headline=Statement(text="Service B is paused.", cites=["PSR:CAND-03-1"]),
                 sections=[Section(heading="Assets", statements=list(statements))],
                 actions=list(actions), unknowns=[])


def test_schema_enums_come_from_reference_data():
    s = schema().model_json_schema()
    text = str(s)
    assert "SVC-B" in text and "postponing" in text and "PRQ-001" in text


def test_verifier_accepts_cited_statements_and_proposed_actions():
    b = brief([Statement(text="Firm-reported AUM is $300M; Platform A reports $180M AUA; they are not added.",
                         cites=["AST-001", "AST-002", "ASSET-RULE"])],
              [ActionChoice(action_id="ACT:CAND-03-1", rationale="blocker", cites=["PSR:CAND-03-1"])])
    assert verify(b, ITEMS) == []


def test_verifier_rejects_totals_uncited_text_unknown_ids_and_invented_actions():
    b = brief([Statement(text="Total assets are $480M.", cites=["AST-001"]),
               Statement(text="Maya will adopt Service B.", cites=[]),
               Statement(text="Registered.", cites=["REG-999"])],
              [ActionChoice(action_id="ACT:PILOT", rationale="pitch", cites=[])])
    problems = "\n".join(verify(b, ITEMS))
    assert "480,000,000" in problems and "uncited" in problems and "REG-999" in problems and "ACT:PILOT" in problems


@live
def test_live_extraction_matches_spans_and_resists_injection(tmp_path):
    from aai.llm import extract_all
    paths = [DATA / "salesforce" / "interactions" / "INT-2026-03-QBR-CR.md", DATA / "adversarial" / "INT-2026-03-INJECT-CR.md"]
    results = extract_all(paths, out_dir=tmp_path)
    for iid, (doc, body) in results.items():
        assert all(c["span"] in body for c in doc["candidates"]), f"{iid}: non-verbatim span"
    march = results["INT-2026-03-QBR-CR"][0]["candidates"]
    assert any(c["kind"] == "intent" and c.get("target") == "SVC-B" and c.get("proposes_state") == "paused" for c in march)
    inject, _ = results["INT-2026-03-INJECT-CR"]
    assert not any(c.get("proposes_state") in ("using", "expanding") for c in inject["candidates"])
    assert not any(c.get("concept") == "planning adoption or transition" for c in inject["candidates"])
    assert inject["reviewer_notes"], "the embedded instruction should be flagged for the reviewer"
