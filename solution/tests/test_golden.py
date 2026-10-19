"""Golden cases from the product brief §13 that the phase 1 demo can exercise without an LLM.

    cd solution && ../.venv/bin/python -m pytest -q
"""
from datetime import date

import pytest

from aai import queries as q
from aai.graph import Graph
from aai.ingest import load
from aai.memory import promoter, write_action, write_completion
from aai.roster import Roster
from aai.tasks import NotAuthorized, TaskStore

MAR, EMAIL, JAN = "INT-2026-03-QBR-CR", "INT-2026-02-EMAIL-CR", "INT-2026-01-QBR-CR"
D19, D20, D23, D27 = date(2026, 3, 19), date(2026, 3, 20), date(2026, 3, 23), date(2026, 3, 27)


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("aai")
    roster = Roster()
    g = Graph(tmp / "graph.lbug", fresh=True)
    store = TaskStore(tmp / "tasks.sqlite", roster, fresh=True)
    first = load(g, store)
    w = {"g": g, "store": store, "roster": roster, "first": first, "second": load(g, store)["counts"]}
    w["promote"] = promoter(g, first["interactions"])
    return w


@pytest.fixture(scope="module")
def covered(world):
    """Jordan goes on leave after saving the March QBR; Priya covers and validates it."""
    s, promote = world["store"], world["promote"]
    s.mark_unavailable("REP-JORDAN", D19, "leave")
    world["before_coverage_queue"] = s.queue("TEAM-CR", D19)
    with pytest.raises(NotAuthorized):
        s.resolve_review("REP-PRIYA", MAR, D19, {}, promote)
    s.activate_coverage("REP-LEE", "TEAM-CR", "REP-JORDAN", "REP-PRIYA", D19)
    world["after_notification"] = s.assignment(f"ASG:review:{MAR}:REP-PRIYA")
    with pytest.raises(NotAuthorized):
        s.resolve_review("REP-PRIYA", MAR, D19, {}, promote)
    s.acknowledge("REP-PRIYA", f"ASG:review:{MAR}:REP-PRIYA", D20)
    s.acknowledge("REP-PRIYA", f"ASG:review:{MAR}:REP-PRIYA", D20)
    s.resolve_review("REP-PRIYA", MAR, D20, {c["id"]: "confirm" for c in s.candidates(MAR, "candidate")}, promote)
    return world


def test_duplicate_imports_do_not_duplicate_facts(world):
    assert world["first"]["counts"] == world["second"]


def test_similar_names_are_not_merged_and_history_is_kept(world):
    (match,) = world["first"]["identity"]
    assert match["decision"].startswith("kept separate") and not match["same_crd"]
    p = q.profile(world["g"], world["roster"], "REP-PRIYA", "ADV-001", D20, D20)
    assert [a["name"] for a in p["affiliations"]] == ["Harbor Point Financial", "Cedar Ridge Advisory"]
    assert p["current_firms"] == ["Cedar Ridge Advisory"]


def test_exam_passed_registration_unknown_shows_gap(world):
    p = q.profile(world["g"], world["roster"], "REP-PRIYA", "ADV-001", D20, D20)
    assert any(x["exam"] == "Series 65" for x in p["qualifications"])
    assert p["registrations"] == [] and "unknown" in p["gaps"][0]


def test_aum_and_aua_are_not_totalled(world):
    obs = q.assets(world["g"], world["roster"], "REP-PRIYA", "FIRM-001", D20)
    result = q.combine_assets(obs)
    assert not result["allowed"] and any("metric types" in r for r in result["reasons"])


def test_missing_capability_is_unknown(world):
    assert q.capability(world["g"], "SVC-B", "integration")["status"] == "unknown"
    assert q.capability(world["g"], "SVC-B", "consolidated")["status"] == "documented"


def test_repeated_quote_is_not_independent_confirmation(world):
    (cand,) = world["store"].candidates(EMAIL)
    assert cand["status"] == "repetition" and cand["quotes"].startswith(JAN)


def test_extraction_with_no_new_candidates_stays_pending(world):
    assert world["store"].review_item(EMAIL)["status"] == "pending review"


def test_unauthorized_firm_is_excluded(world):
    with pytest.raises(q.OutOfScope):
        q.profile(world["g"], world["roster"], "REP-PRIYA", "ADV-002", D20, D20)
    with pytest.raises(q.OutOfScope):
        q.intents(world["g"], world["roster"], "REP-PRIYA", "FIRM-002", D20, D20)


def test_absent_author_leaves_work_unowned_but_visible(covered):
    rows = {r["item"]: r for r in covered["before_coverage_queue"]}
    assert rows[MAR]["owner"] == "UNOWNED" and rows[MAR]["status"] == "pending review"


def test_notification_alone_does_not_complete_handoff(covered):
    assert covered["after_notification"]["status"] == "offered"


def test_retrying_handoff_does_not_duplicate(covered):
    ids = [a["id"] for a in covered["store"].assignments()]
    assert len(ids) == len(set(ids)) == 2


def test_as_of_answer_excludes_facts_learned_later(covered):
    g, r = covered["g"], covered["roster"]
    before = q.product_state(g, r, "REP-PRIYA", "FIRM-001", "SVC-B", D20, D19)
    after = q.product_state(g, r, "REP-PRIYA", "FIRM-001", "SVC-B", D20, D20)
    assert before["state"] == "evaluating" and after["state"] == "paused"
    assert [i["intent"] for i in q.intents(g, r, "REP-PRIYA", "FIRM-001", D20, D19)] == ["exploring or comparing"]


def test_pausing_service_b_leaves_other_products_unchanged(covered):
    g, r = covered["g"], covered["roster"]
    for product in ("CUST-A", "SVC-A"):
        assert q.product_state(g, r, "REP-PRIYA", "FIRM-001", product, D20, D20)["state"] == "using"


def test_crm_disagreement_raises_discrepancy(covered):
    s = q.product_state(covered["g"], covered["roster"], "REP-PRIYA", "FIRM-001", "SVC-B", D20, D20)
    assert s["discrepancies"] == ["qbr says paused; crm still says evaluating"]


def test_advisor_reported_dissatisfaction_is_attributed_to_the_advisor(covered):
    exp = q.experience(covered["g"], covered["roster"], "REP-PRIYA", "FIRM-001", D20, D20)
    investor = [e for e in exp if e["affected"] == "investor group"]
    assert investor and all(e["reportedBy"] == "Maya Chen" and e["evidence"] == "testimony" for e in investor)


def test_missing_follow_up_result_stays_open(covered):
    (c,) = q.commitments(covered["g"], covered["roster"], "REP-PRIYA", "FIRM-001", D20)
    assert c["status"] == "open"


def test_actions_cite_sources_and_never_promote_paused_product(covered):
    proposals = q.propose_actions(covered["g"], covered["roster"], "REP-PRIYA", "FIRM-001", MAR, D20)
    assert all(p["sources"] and p["addresses"] for p in proposals)
    svc_b = [p for p in proposals if p["product"] == "SVC-B"]
    assert svc_b and all("comparison" not in p["title"].lower() for p in svc_b)
    assert svc_b[0]["requires"] == ["PRQ-001"] and svc_b[0]["fulfils"] == ["CAND-01-4"]
    covered["proposals"] = proposals


def test_backup_missing_deadline_escalates_to_lead(covered):
    s = covered["store"]
    assert s.escalate_overdue(D23) == [f"ASG:review:{EMAIL}:REP-PRIYA"]
    assert s.review_item(EMAIL)["status"] == "pending review"
    with pytest.raises(ValueError):
        s.resolve_review("REP-LEE", EMAIL, D23, {}, covered["promote"])
    item = s.resolve_review("REP-LEE", EMAIL, D23, {}, covered["promote"], no_action_reason="repeats January")
    assert item["status"] == "no action needed"


def test_covering_rep_closes_action_only_with_evidence(covered):
    s, g = covered["store"], covered["g"]
    proposals = q.propose_actions(g, covered["roster"], "REP-PRIYA", "FIRM-001", MAR, D20)
    for p in proposals:
        s.approve_action("REP-PRIYA", p, D20, write_action(g))
    aid = proposals[0]["id"]
    with pytest.raises(ValueError):
        s.complete_action("REP-PRIYA", aid, D27, "", write_completion(g))
    assert s.action(aid)["status"] == "approved"
    done = s.complete_action("REP-PRIYA", aid, D27, "SR-4471", write_completion(g))
    assert done["status"] == "completed"
    assert g.one("MATCH (a:Action {id: $id})-[:evidencedBy]->(s:SourceRecord) RETURN s.sourceRecordId AS e", id=aid)["e"] == "SR-4471"


def test_records_survive_author_absence(covered):
    g = covered["g"]
    assert g.one("MATCH (i:Interaction {id: $id})-[:authoredBy]->(r:Rep) RETURN r.id AS r", id=MAR)["r"] == "REP-JORDAN"
