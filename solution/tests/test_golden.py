"""Golden cases for the pivot: concept detection, the SME gate, hydration into a procedure run, and continuity.

    cd solution && ../.venv/bin/python -m pytest -q
"""
from datetime import date

import pytest

from aai import queries as q
from aai.bundle import check
from aai.detect import detect
from aai.graph import Graph
from aai.ingest import load
from aai.memory import write_action, write_completion
from aai.pipeline import approve
from aai.roster import Roster
from aai.tasks import NotAuthorized, TaskStore

MAR, EMAIL, JAN, NF = "INT-2026-03-QBR-CR", "INT-2026-02-EMAIL-CR", "INT-2026-01-QBR-CR", "INT-2026-03-QBR-NF"
D19, D20, D23, D27 = date(2026, 3, 19), date(2026, 3, 20), date(2026, 3, 23), date(2026, 3, 27)


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("aai")
    roster = Roster()
    g = Graph(tmp / "graph.lbug", fresh=True)
    store = TaskStore(tmp / "tasks.sqlite", roster, fresh=True)
    first = load(g, store)
    w = {"g": g, "store": store, "roster": roster, "first": first, "second": load(g, store)["counts"]}
    w["approve"] = lambda rep, iid, at, decisions, reason=None: approve(
        g, store, roster, first["interactions"], first["bodies"], first["firm_names"], rep, iid, at, decisions, reason)
    return w


@pytest.fixture(scope="module")
def approved(world):
    """Jordan goes on leave after saving the March QBR; the SME approves it; Priya covers the follow-up."""
    s, g = world["store"], world["g"]
    s.mark_unavailable("REP-JORDAN", D19, "leave")
    world["queue_19"] = s.queue("TEAM-CR", D19)
    decisions = {c["id"]: "confirm" for c in s.candidates(MAR, "candidate")}
    for rep in ("REP-PRIYA", "REP-LEE"):
        with pytest.raises(NotAuthorized):
            world["approve"](rep, MAR, D20, decisions)
    world["approve"]("REP-DANA", MAR, D20, decisions)
    world["queue_20"] = s.queue("TEAM-CR", D20)
    world["offers"] = s.activate_coverage("REP-LEE", "TEAM-CR", "REP-JORDAN", "REP-PRIYA", D20)
    world["march"] = [a["id"] for a in s.actions() if a["interaction_id"] == MAR]
    with pytest.raises(NotAuthorized):
        s.approve_action("REP-PRIYA", world["march"][0], D20, write_action(g))
    for o in world["offers"]:
        s.acknowledge("REP-PRIYA", o["id"], D20)
        s.acknowledge("REP-PRIYA", o["id"], D20)
    for aid in world["march"]:
        s.approve_action("REP-PRIYA", aid, D20, write_action(g))
    return world


# ------------------------------------------------------------ 1. the firm knows what advisors tell it

def test_loose_and_specific_product_mentions_link_to_the_catalog(world):
    links = {m.phrase: m.target for m in detect(world["first"]["bodies"][MAR])["mentions"]}
    assert links == {"CPX UMA": "CPX-UMA", "CMP": "CMP", "Crestline custody": "CCC"}
    nf = {m.phrase: (m.target, m.method) for m in detect(world["first"]["bodies"][NF])["mentions"]}
    assert nf["UMA"] == ("CPX-UMA", "alias") and nf["separate accounts"] == (None, "unresolved")


def test_asset_figure_is_read_with_metric_and_scope(world):
    (a,) = detect(world["first"]["bodies"][MAR])["assets"]
    assert (a.metric, a.value, a.scope) == ("reported AUM", 320e6, "across all custodians")


def test_duplicate_imports_do_not_duplicate_facts(world):
    assert world["first"]["counts"] == world["second"]


def test_similar_names_are_not_merged_and_history_is_kept(world):
    (match,) = world["first"]["identity"]
    assert match["decision"].startswith("kept separate") and not match["same_crd"]
    p = q.profile(world["g"], world["roster"], "REP-PRIYA", "ADV-001", D20, D20)
    assert [a["name"] for a in p["affiliations"]] == ["Harbor Point Financial", "Cedar Ridge Advisory"]


def test_repeated_quote_is_not_independent_confirmation(world):
    (cand,) = world["store"].candidates(EMAIL)
    assert cand["status"] == "repetition" and cand["quotes"].startswith(JAN)


# ------------------------------------------------------------ 2. experts stay in control

def test_note_is_stored_and_queued_before_review(world):
    assert world["g"].one("MATCH (i:Interaction {id: $id}) RETURN i.id AS id", id=MAR)
    assert world["store"].review_item(MAR)["status"] == "pending review"


def test_nothing_from_the_note_is_in_memory_before_approval(world):
    g = world["g"]
    assert not g.one("MATCH (n:Intent {id: 'CAND-03-1'}) RETURN n.id AS id")
    assert not g.one("MATCH (o:AssetObservation {id: $id}) RETURN o.id AS id", id=f"DET-{MAR}-A1")
    assert not g.one("MATCH (s:SemanticQBR {id: $id}) RETURN s.id AS id", id=f"SQBR:{MAR}")


def test_review_waits_for_the_sme_not_the_author(approved):
    rows = {r["item"]: r for r in approved["queue_19"]}
    assert rows[MAR]["owner"] == "REP-DANA"


def test_only_an_sme_approves_findings(approved):
    item = approved["store"].review_item(MAR)
    assert item["status"] == "reviewed" and item["resolved_by"] == "REP-DANA"


def test_rejected_finding_keeps_its_reason(tmp_path):
    roster = Roster()
    g, s = Graph(tmp_path / "g.lbug", fresh=True), TaskStore(tmp_path / "t.sqlite", roster, fresh=True)
    r = load(g, s)
    decisions = {c["id"]: "confirm" for c in s.candidates(MAR, "candidate")} | {f"DET-{MAR}-A1": "figure is approximate; ask for the ADV"}
    approve(g, s, roster, r["interactions"], r["bodies"], r["firm_names"], "REP-DANA", MAR, D20, decisions)
    (c,) = [c for c in s.candidates(MAR) if c["id"] == f"DET-{MAR}-A1"]
    assert c["status"] == "rejected" and c["reason"].startswith("figure is approximate")
    assert not g.one("MATCH (o:AssetObservation {id: $id}) RETURN o.id AS id", id=f"DET-{MAR}-A1")


def test_as_of_answer_excludes_facts_learned_later(approved):
    g, r = approved["g"], approved["roster"]
    before = q.product_state(g, r, "REP-PRIYA", "FIRM-001", "CPX-UMA", D20, D19)
    after = q.product_state(g, r, "REP-PRIYA", "FIRM-001", "CPX-UMA", D20, D20)
    assert before["state"] == "evaluating" and after["state"] == "paused"


def test_pausing_one_product_leaves_others_unchanged(approved):
    for product in ("CCC", "CMP"):
        assert q.product_state(approved["g"], approved["roster"], "REP-PRIYA", "FIRM-001", product, D20, D20)["state"] == "using"


def test_crm_disagreement_raises_discrepancy(approved):
    s = q.product_state(approved["g"], approved["roster"], "REP-PRIYA", "FIRM-001", "CPX-UMA", D20, D20)
    assert s["discrepancies"] == ["qbr says paused; crm still says evaluating"]


def test_approval_hydrates_semantic_qbr_mentions_and_run(approved):
    g = approved["g"]
    links = g.run("""MATCH (:SemanticQBR {id: $s})-[:contains]->(m:ProductMention)-[:refersTo]->(o:ProductOffering)
                     RETURN m.phrase AS phrase, o.id AS product ORDER BY phrase""", s=f"SQBR:{MAR}")
    assert {(x["phrase"], x["product"]) for x in links} == {("CPX UMA", "CPX-UMA"), ("CMP", "CMP"), ("Crestline custody", "CCC")}
    steps = g.run("""MATCH (a:Action)-[:partOfRun]->(:ProcedureRun {id: $r})-[:startedBy]->(:SemanticQBR {id: $s})
                     RETURN a.id AS id""", r=f"RUN:{MAR}", s=f"SQBR:{MAR}")
    assert {x["id"] for x in steps} == set(approved["march"])


# ------------------------------------------------------------ 3. no promise falls through the cracks

def test_absent_owner_leaves_steps_unowned_but_visible(approved):
    actions = [r for r in approved["queue_20"] if r["type"] == "action"]
    assert actions and all(r["owner"] == "UNOWNED" for r in actions)


def test_notification_alone_does_not_complete_handoff(approved):
    assert all(o["status"] == "offered" for o in approved["offers"])


def test_retrying_handoff_does_not_duplicate(approved):
    ids = [a["id"] for a in approved["store"].assignments()]
    assert len(ids) == len(set(ids)) == len(approved["offers"])


def test_missing_follow_up_result_stays_open(approved):
    (c,) = q.commitments(approved["g"], approved["roster"], "REP-PRIYA", "FIRM-001", D20)
    assert c["status"] == "open"


def test_overdue_review_escalates_and_lead_can_only_dispose(approved):
    s = approved["store"]
    assert EMAIL in s.escalate_overdue(D23)
    with pytest.raises(ValueError):
        approved["approve"]("REP-LEE", EMAIL, D23, {})
    assert approved["approve"]("REP-LEE", EMAIL, D23, {}, "repeats January")["status"] == "no action needed"


def test_covering_rep_closes_action_only_with_evidence(approved):
    s, g = approved["store"], approved["g"]
    aid = approved["march"][0]
    with pytest.raises(ValueError):
        s.complete_action("REP-PRIYA", aid, D27, "", write_completion(g))
    assert s.complete_action("REP-PRIYA", aid, D27, "SR-4471", write_completion(g))["status"] == "completed"
    assert g.one("MATCH (a:Action {id: $id})-[:evidencedBy]->(s:SourceRecord) RETURN s.sourceRecordId AS e", id=aid)["e"] == "SR-4471"


def test_dismissal_keeps_its_reason(world):
    dismissed = world["store"].actions("dismissed")
    assert dismissed and all(a["note"] for a in dismissed)


def test_records_survive_author_absence(approved):
    assert approved["g"].one("MATCH (i:Interaction {id: $id})-[:authoredBy]->(r:Rep) RETURN r.id AS r", id=MAR)["r"] == "REP-JORDAN"


# ------------------------------------------------------------ 5. we stop saying the wrong thing

def test_postponed_product_is_not_pitched(approved):
    (held,) = approved["store"].actions("on hold")
    assert held["id"] == "ACT:CAND-01-3" and "postponing" in held["note"]
    titles = [approved["store"].action(a)["title"] for a in approved["march"]]
    assert not any("comparison" in t.lower() for t in titles)


def test_stated_aum_is_not_merged_with_reported_figures(approved):
    obs = q.assets(approved["g"], approved["roster"], "REP-PRIYA", "FIRM-001", D20)
    assert {o["methodology"] for o in obs if o["reporter"] == "ADV-001"} == {"stated by the advisor in a QBR"}
    assert not q.combine_assets(obs)["allowed"]


def test_exam_passed_registration_unknown_shows_gap(world):
    p = q.profile(world["g"], world["roster"], "REP-PRIYA", "ADV-001", D20, D20)
    assert any(x["exam"] == "Series 65" for x in p["qualifications"])
    assert p["registrations"] == [] and "unknown" in p["gaps"][0]


def test_missing_capability_is_unknown(world):
    assert q.capability(world["g"], "CPX-UMA", "integration")["status"] == "unknown"
    assert q.capability(world["g"], "CPX-UMA", "consolidated")["status"] == "documented"


def test_unauthorized_firm_is_excluded(world):
    with pytest.raises(q.OutOfScope):
        q.profile(world["g"], world["roster"], "REP-PRIYA", "ADV-002", D20, D20)


# ------------------------------------------------------------ procedural memory

def test_okf_bundle_is_consistent():
    assert check() == []
