"""Narrated phase 1 scenario: absence before review, as-of memory, and evidence-backed follow-up.

    cd solution && ../.venv/bin/python -m aai.demo

Rebuilds solution/.data/ from the fixtures each time. No LLM is called: candidate takeaways come from fixture files
standing in for extraction, and actions are proposed by rules standing in for the assistant.
"""
from datetime import date

from . import GRAPH_DB, TASK_DB
from . import queries as q
from .graph import Graph
from .ingest import load
from .memory import promoter, write_action, write_completion
from .roster import Roster
from .tasks import NotAuthorized, TaskStore

MAR = "INT-2026-03-QBR-CR"
EMAIL = "INT-2026-02-EMAIL-CR"


def section(title):
    print(f"\n{'=' * 100}\n{title}\n{'=' * 100}")


def table(rows, cols):
    if not rows:
        print("  (none)")
        return
    def cell(v):
        return "-" if v in (None, [], "") else ", ".join(map(str, v)) if isinstance(v, list) else str(v)
    widths = {c: max(len(c), *(len(cell(r.get(c))) for r in rows)) for c in cols}
    print("  " + "  ".join(c.ljust(widths[c]) for c in cols))
    for r in rows:
        print("  " + "  ".join(cell(r.get(c)).ljust(widths[c]) for c in cols))


def state_line(g, roster, user, product, valid_at, known_at):
    s = q.product_state(g, roster, user, "FIRM-001", product, valid_at, known_at)
    extra = f"   DISCREPANCY: {'; '.join(s['discrepancies'])}" if s["discrepancies"] else ""
    print(f"  {product:7} {s['state']:11} (source: {s['source']}, since {s['since']}){extra}")


def expect_refusal(label, fn):
    try:
        fn()
        print(f"  !! {label}: NOT refused")
    except (NotAuthorized, ValueError, q.OutOfScope) as e:
        print(f"  refused - {label}: {e}")


def main():
    roster = Roster()
    g = Graph(GRAPH_DB, fresh=True)
    store = TaskStore(TASK_DB, roster, fresh=True)

    section("1. Ingest synthetic Snowflake and Salesforce exports into graph memory")
    report = load(g, store)
    print(f"  first import:  {report['counts']}")
    print(f"  second import: {load(g, store)['counts']}   (same files, nothing added)")
    for m in report["identity"]:
        print(f"  identity: {m['names'][0]} ({m['a']}) vs {m['names'][1]} ({m['b']}): name similarity {m['similarity']}, "
              f"same CRD: {m['same_crd']} -> {m['decision']}")
    interactions = report["interactions"]
    promote = promoter(g, interactions)

    section("2. CQ1 profile of Maya Chen, as seen by Priya (Cedar Ridge team), 20 March 2026")
    p = q.profile(g, roster, "REP-PRIYA", "ADV-001", date(2026, 3, 20), date(2026, 3, 20))
    print(f"  {p['advisor']['name']} (CRD {p['advisor']['crd']}), current firm: {', '.join(p['current_firms'])}")
    table(p["affiliations"], ["name", "role", "validFrom", "validTo"])
    table(p["qualifications"], ["exam", "result", "date"])
    for gap in p["gaps"]:
        print(f"  GAP: {gap}")

    section("3. CQ3 asset observations for Cedar Ridge")
    obs = q.assets(g, roster, "REP-PRIYA", "FIRM-001", date(2026, 3, 20))
    table(obs, ["id", "metric", "value", "currency", "scope", "asOf", "reporter"])
    combined = q.combine_assets(obs)
    print(f"  total or share allowed: {combined['allowed']}")
    for r in combined.get("reasons", []):
        print(f"    - {r}")
    print("  product-level assets for Managed Portfolio Service A: unknown (no observation at product scope)")

    section("4. 18 March: Jordan saves the March QBR; 19 March: Jordan goes on leave")
    store.mark_unavailable("REP-JORDAN", date(2026, 3, 19), "leave")
    table(store.queue("TEAM-CR", date(2026, 3, 19)), ["item", "type", "status", "owner", "due", "overdue", "handoff"])
    print("  candidates waiting in the March QBR:")
    table([{"id": c["id"], "kind": c["kind"], "status": c["status"]} for c in store.candidates(MAR)], ["id", "kind", "status"])
    print("  candidates in the February email:")
    table([{"id": c["id"], "kind": c["kind"], "status": c["status"], "quotes": c["quotes"]} for c in store.candidates(EMAIL)],
          ["id", "kind", "status", "quotes"])
    expect_refusal("Priya reviews without an assignment",
                   lambda: store.resolve_review("REP-PRIYA", MAR, date(2026, 3, 19), {}, promote))

    section("5. Team lead activates coverage; notification alone does not hand over the work")
    for a in store.activate_coverage("REP-LEE", "TEAM-CR", "REP-JORDAN", "REP-PRIYA", date(2026, 3, 19)):
        print(f"  offered: {a['id']}  status={a['status']}  deadline={a['deadline']}")
    expect_refusal("Priya reviews after notification, before acknowledging",
                   lambda: store.resolve_review("REP-PRIYA", MAR, date(2026, 3, 19), {}, promote))
    a1 = store.acknowledge("REP-PRIYA", f"ASG:review:{MAR}:REP-PRIYA", date(2026, 3, 20))
    a2 = store.acknowledge("REP-PRIYA", f"ASG:review:{MAR}:REP-PRIYA", date(2026, 3, 20))
    print(f"  Priya acknowledges the March QBR: {a1['status']} at {a1['acknowledged_at']}; retried: {a2['status']}, "
          f"assignments in store: {len(store.assignments())}")
    print("  Priya does not acknowledge the February email review.")

    section("6. CQ2 as-of memory, before Priya's review: what did we know on 19 March?")
    for prod in ("CUST-A", "SVC-A", "SVC-B"):
        state_line(g, roster, "REP-PRIYA", prod, date(2026, 3, 20), date(2026, 3, 19))

    section("7. Priya validates the March takeaways (covering rep with acknowledged assignment)")
    item = store.resolve_review("REP-PRIYA", MAR, date(2026, 3, 20),
                                {c["id"]: "confirm" for c in store.candidates(MAR, "candidate")}, promote)
    print(f"  review item: {item['status']} by {item['resolved_by']} on {item['resolved_at']}")

    section("8. CQ2 / CQ4 after the review, 20 March")
    for prod in ("CUST-A", "SVC-A", "SVC-B"):
        state_line(g, roster, "REP-PRIYA", prod, date(2026, 3, 20), date(2026, 3, 20))
    print("  experience reported for products (advisor testimony, not direct investor statements):")
    exp = q.experience(g, roster, "REP-PRIYA", "FIRM-001", date(2026, 3, 20), date(2026, 3, 20))
    table(exp, ["date", "product", "summary", "affected", "reportedBy", "evidence", "repeated_in"])
    independent = {e["interaction"] for e in exp if "Service A" in e["product"] and "nvestor" in e["summary"]}
    print(f"  independent interactions reporting investor statement problems: {len(independent)} "
          f"({', '.join(sorted(independent))}); the February email only repeats January")
    print("  current intent per product:")
    table(q.intents(g, roster, "REP-PRIYA", "FIRM-001", date(2026, 3, 20), date(2026, 3, 20)),
          ["date", "target", "intent", "reason", "alternatives"])
    print("  as known before the March review:")
    table(q.intents(g, roster, "REP-PRIYA", "FIRM-001", date(2026, 3, 20), date(2026, 3, 19)), ["date", "target", "intent"])
    print("  commitments:")
    table(q.commitments(g, roster, "REP-PRIYA", "FIRM-001", date(2026, 3, 20)), ["id", "summary", "due", "status", "madeBy"])

    section("9. CQ5 proposed actions, checked and approved")
    print(f"  catalog check, Service B portfolio-accounting integration: {q.capability(g, 'SVC-B', 'integration')['status']}")
    proposals = q.propose_actions(g, roster, "REP-PRIYA", "FIRM-001", MAR, date(2026, 3, 20))
    for pr in proposals:
        print(f"  - {pr['id']}: {pr['title']}\n      product {pr['product']}; addresses {pr['addresses']}; sources {pr['sources']}; "
              f"requires {pr['requires'] or '-'}; fulfils {pr['fulfils'] or '-'}; due {pr['due']}")
    for pr in proposals:
        store.approve_action("REP-PRIYA", pr, date(2026, 3, 20), write_action(g))
    store.approve_action("REP-PRIYA", proposals[0], date(2026, 3, 20), write_action(g))
    print(f"  approved {len(proposals)} actions (one approval retried; actions in store: "
          f"{len(store._rows('SELECT id FROM actions'))})")

    section("10. 23 March: the unacknowledged email review escalates; the lead resolves it")
    print(f"  escalated: {store.escalate_overdue(date(2026, 3, 23))}")
    item = store.resolve_review("REP-LEE", EMAIL, date(2026, 3, 23), {}, promote,
                                no_action_reason="Only repeats the January QBR; no new takeaways")
    print(f"  {EMAIL}: {item['status']} by {item['resolved_by']}: {item['note']}")

    section("11. 27 March: completion requires evidence")
    service = next(p for p in proposals if p["id"].startswith("ACT:CAND-03-2"))
    expect_refusal("close without evidence",
                   lambda: store.complete_action("REP-PRIYA", service["id"], date(2026, 3, 27), "", write_completion(g)))
    done = store.complete_action("REP-PRIYA", service["id"], date(2026, 3, 27),
                                 "SR-4471 opened with Platform A statement team; explainer sent to Cedar Ridge", write_completion(g))
    print(f"  {done['id']}: {done['status']} with evidence '{done['evidence']}'")
    print("  CQ6 team queue on 27 March:")
    table(store.queue("TEAM-CR", date(2026, 3, 27)), ["item", "type", "status", "owner", "due", "overdue", "handoff"])

    section("12. Access scope")
    expect_refusal("Priya asks about May Chen (Northfield)",
                   lambda: q.profile(g, roster, "REP-PRIYA", "ADV-002", date(2026, 3, 20), date(2026, 3, 20)))
    s = q.product_state(g, roster, "REP-OMAR", "FIRM-002", "SVC-B", date(2026, 3, 20), date(2026, 3, 20))
    print(f"  Omar (Northfield team) sees Northfield's Service B state: {s['state']} (source {s['source']})")

    section("Event log")
    for e in store.events():
        print(f"  {e['at']}  {e['actor']:10}  {e['event']:24}  {e['detail']}")


if __name__ == "__main__":
    main()
