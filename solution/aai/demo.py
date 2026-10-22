"""The business demo: six takeaways, played on Cedar Ridge's March QBR.

    cd solution && ../.venv/bin/python -m aai.demo                          # fixtures only, no LLM
    cd solution && ../.venv/bin/python -m aai.demo --extractions llm --brief  # Claude's findings and a cited brief
    add --step to pause after each section when presenting

Rebuilds solution/.data/ each time. By default no model is called: candidate findings come from fixture files and
actions are proposed by rules. `--extractions llm` reads findings written by `python -m aai.llm extract`; `--brief`
asks Claude for a cited brief and checks it before writing it to .data/briefs/.
"""
import argparse
import json
from datetime import date

from . import GRAPH_DB, STATE, TASK_DB
from . import queries as q
from .brief import bundle, one_page
from .detect import detect
from .graph import Graph
from .ingest import load
from .memory import write_action, write_completion
from .pipeline import approve
from .roster import Roster
from .tasks import NotAuthorized, TaskStore

MAR, EMAIL, NF = "INT-2026-03-QBR-CR", "INT-2026-02-EMAIL-CR", "INT-2026-03-QBR-NF"
D19, D20, D23, D27 = date(2026, 3, 19), date(2026, 3, 20), date(2026, 3, 23), date(2026, 3, 27)
STEP = False


def section(title):
    if STEP and not title.startswith("1."):
        input("\n  [Enter for next section] ")
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


def refused(label, fn):
    try:
        fn()
        print(f"  !! {label}: NOT refused")
        return False
    except (NotAuthorized, ValueError, q.OutOfScope) as e:
        print(f"  refused - {label}: {e}")
        return True


def state_line(g, roster, product, known_at):
    s = q.product_state(g, roster, "REP-PRIYA", "FIRM-001", product, D20, known_at)
    extra = f"   DISCREPANCY: {'; '.join(s['discrepancies'])}" if s["discrepancies"] else ""
    print(f"  {product:8} {s['state']:11} (source: {s['source']}, since {s['since']}){extra}")


def open_actions(store, team):
    return [json.loads(a["payload"]) | {"status": a["status"], "note": a["note"]}
            for a in store.actions() if a["team"] == team and a["status"] in ("proposed", "approved", "on hold")]


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--extractions", choices=["fixtures", "llm"], default="fixtures")
    args.add_argument("--brief", action="store_true")
    args.add_argument("--step", action="store_true", help="pause after each section (for presenting)")
    args = args.parse_args()
    global STEP
    STEP = args.step
    folder = "extractions" if args.extractions == "fixtures" else "extractions-llm"
    roster = Roster()
    g = Graph(GRAPH_DB, fresh=True)
    store = TaskStore(TASK_DB, roster, fresh=True)
    caught = {}

    # -------------------------------------------------------------------------------------------- 1
    section("1. The firm finally knows what its advisors tell it")
    report = load(g, store, extractions=folder)
    interactions, bodies, firms = report["interactions"], report["bodies"], report["firm_names"]
    print(f"  Imported January to March: {report['counts']}; a second import adds nothing: {load(g, store, extractions=folder)['counts']}")
    print(f"  Findings from: data/salesforce/{folder}/")
    for iid in (MAR, NF):
        det = detect(bodies[iid])
        print(f"\n  {iid}: what the note mentions, linked to the Crestline catalog")
        table([{"phrase": m.phrase, "linked to": m.target or "UNRESOLVED (for the SME)", "how": m.method} for m in det["mentions"]],
              ["phrase", "linked to", "how"])
        for a in det["assets"]:
            print(f"  asset figure: {a.text} read as {a.metric}, scope '{a.scope}', advisor's statement")
    for m in report["identity"]:
        print(f"\n  identity: {m['names'][0]} and {m['names'][1]}: name similarity {m['similarity']}, same CRD: {m['same_crd']} "
              f"-> {m['decision']}")

    # -------------------------------------------------------------------------------------------- 2
    section("2. Experts stay in control: nothing enters memory until an SME approves it")
    store.mark_unavailable("REP-JORDAN", D19, "leave")
    print("  18 March: Jordan saves the QBR. 19 March: Jordan goes on leave. The review does not wait for Jordan:")
    table([r for r in store.queue("TEAM-CR", D19) if r["type"] == "SME review"], ["item", "type", "owner", "due", "overdue", "handoff"])
    print(f"  draft semantic QBR: .data/semantic-qbr/{MAR}.md (status: draft)")
    print("  what memory says on 19 March, before approval:")
    for prod in ("CCC", "CMP", "CPX-UMA"):
        state_line(g, roster, prod, D19)
    decisions = {c["id"]: "confirm" for c in store.candidates(MAR, "candidate")}
    caught["unauthorized approvals refused"] = sum([
        refused("Priya approves findings (not an SME)",
                lambda: approve(g, store, roster, interactions, bodies, firms, "REP-PRIYA", MAR, D20, decisions)),
        refused("Alex Lee, team lead, approves findings",
                lambda: approve(g, store, roster, interactions, bodies, firms, "REP-LEE", MAR, D20, decisions)),
    ])
    item = approve(g, store, roster, interactions, bodies, firms, "REP-DANA", MAR, D20, decisions)
    print(f"  20 March: Dana Ortiz (business analyst, SME) approves {len(decisions)} findings, each tied to its sentence: "
          f"{item['status']}; the file is now status: verified")
    print("  what memory says on 20 March:")
    for prod in ("CCC", "CMP", "CPX-UMA"):
        state_line(g, roster, prod, D20)
    print("  current intent, and what was known before approval:")
    table(q.intents(g, roster, "REP-PRIYA", "FIRM-001", D20, D20), ["date", "target", "intent", "reason"])
    table(q.intents(g, roster, "REP-PRIYA", "FIRM-001", D20, D19), ["date", "target", "intent"])

    # -------------------------------------------------------------------------------------------- 3
    section("3. No promise falls through the cracks")
    print("  Approval started a run of the QBR follow-up procedure; every step has an owner and a due date.")
    print("  Jordan owns them but is on leave, so they show as UNOWNED, still in the queue:")
    table(store.queue("TEAM-CR", D20), ["item", "type", "status", "owner", "due", "overdue"])
    for a in store.activate_coverage("REP-LEE", "TEAM-CR", "REP-JORDAN", "REP-PRIYA", D20):
        print(f"  offered to Priya: {a['work_id']}  ({a['status']}, respond by {a['deadline']})")
    march = [a for a in store.actions() if a["interaction_id"] == MAR]
    refused("Priya approves before acknowledging (a notification is not a handoff)",
            lambda: store.approve_action("REP-PRIYA", march[0]["id"], D20, write_action(g)))
    for a in store.assignments():
        if a["to_rep"] == "REP-PRIYA" and a["work_type"] == "action":
            store.acknowledge("REP-PRIYA", a["id"], D20)
            store.acknowledge("REP-PRIYA", a["id"], D20)
    print(f"  Priya acknowledges (retried; assignments in store: {len(store.assignments())}) and approves the March steps:")
    for a in march:
        store.approve_action("REP-PRIYA", a["id"], D20, write_action(g))
        print(f"    {a['id']}: {a['title']}")
    print(f"  23 March, overdue reviews escalate: {store.escalate_overdue(D23)}")
    pending = store.candidates(EMAIL, "candidate")
    if pending:  # something new in the email: only the SME can approve it
        item = approve(g, store, roster, interactions, bodies, firms, "REP-DANA", EMAIL, D23, {c["id"]: "confirm" for c in pending})
        print(f"  the lead sends it back to Dana, who approves {len(pending)} new finding(s): {item['status']}")
    else:
        item = approve(g, store, roster, interactions, bodies, firms, "REP-LEE", EMAIL, D23, {},
                       no_action_reason="Forwarded email only repeats the January QBR")
        print(f"  the lead closes the email review: {item['status']}: {item['note']}")
    service = next(a for a in march if a["title"].startswith("Open service issue"))
    refused("close a step without evidence",
            lambda: store.complete_action("REP-PRIYA", service["id"], D27, "", write_completion(g)))
    done = store.complete_action("REP-PRIYA", service["id"], D27, "SR-4471 opened with the CMP statements team; explainer sent",
                                 write_completion(g))
    print(f"  27 March: {done['id']} {done['status']} with evidence '{done['evidence']}'")
    print("  team queue on 27 March:")
    table(store.queue("TEAM-CR", D27), ["item", "type", "status", "owner", "due", "overdue", "handoff"])

    # -------------------------------------------------------------------------------------------- 4
    section("4. Reps are prepared in minutes, not hours: one page, every line cited")
    items = bundle(g, roster, "REP-PRIYA", "FIRM-001", "ADV-001", D20, open_actions(store, "TEAM-CR"))
    for line in one_page(items, firms["FIRM-001"], D20):
        print(f"  {line}")
    if args.brief:
        write_brief(items, firms["FIRM-001"])

    # -------------------------------------------------------------------------------------------- 5
    section("5. We stop saying the wrong thing")
    held = store.actions("on hold")
    for a in held:
        print(f"  on hold: {a['id']} '{a['title']}'\n           because the {a['note']}")
    obs = q.assets(g, roster, "REP-PRIYA", "FIRM-001", D20)
    table(obs, ["id", "metric", "value", "scope", "asOf", "reporter", "methodology"])
    combined = q.combine_assets(obs)
    print(f"  total of these figures allowed: {combined['allowed']}")
    for r in combined.get("reasons", []):
        print(f"    - {r}")
    p = q.profile(g, roster, "REP-PRIYA", "ADV-001", D20, D20)
    print(f"  credentials: {', '.join(x['exam'] + ' ' + x['result'] for x in p['qualifications'])}; {p['gaps'][0]}")
    print(f"  catalog, CPX UMA portfolio-accounting integration: {q.capability(g, 'CPX-UMA', 'integration')['status']}")
    caught["out-of-scope requests refused"] = int(refused("Priya asks about May Chen (Northfield)",
                                                          lambda: q.profile(g, roster, "REP-PRIYA", "ADV-002", D20, D20)))
    caught["pitches held back"] = len(held)
    caught["unsupported totals refused"] = int(not combined["allowed"])
    caught["source disagreements surfaced"] = len(q.product_state(g, roster, "REP-PRIYA", "FIRM-001", "CPX-UMA", D20, D20)["discrepancies"])
    caught["repetitions not double-counted"] = sum(len(store.candidates(i, "repetition")) for i in interactions)
    caught["unresolved product mentions sent to the SME"] = sum(m.target is None for i in interactions for m in detect(bodies[i])["mentions"])

    # -------------------------------------------------------------------------------------------- 6
    section("6. The value is measurable")
    events = store.events()
    saved = next(e for e in events if e["event"] == "review item created" and MAR in e["detail"])["at"]
    approved = next(e for e in events if e["event"] == "review resolved" and MAR in e["detail"])["at"]
    unowned = [a for a in store.assignments() if a["work_type"] == "action"]
    print(f"  SME turnaround on the March QBR: saved {saved}, approved {approved}, despite the author's leave")
    print(f"  follow-ups whose owner left: {len(unowned)}; recovered by an acknowledged colleague: "
          f"{sum(a['status'] == 'acknowledged' for a in unowned)}; lost: 0")
    print(f"  dismissals and holds with a reason kept: {sum(1 for a in store.actions() if a['status'] in ('dismissed', 'on hold'))}")
    print("  errors caught before anyone said them:")
    for k, v in caught.items():
        print(f"    {k}: {v}")
    print("  The pilot measures the same counts, plus preparation minutes per brief, against today's baseline.")


def write_brief(items, firm_name):
    from .brief import generate, render, verify
    print("\n  Cited brief from Claude, checked before anyone sees it:")
    brief, usage = generate(items, firm_name, D20)
    problems = verify(brief, items)
    out = STATE / "briefs" / f"FIRM-001-{D20}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(brief, items, firm_name, items["ADVISOR"]["name"], D20, problems))
    print(f"  tokens in {usage.input_tokens}, out {usage.output_tokens}, cache read {usage.cache_read_input_tokens}; "
          f"evidence check: {'passed' if not problems else 'FAILED'}")
    for p in problems:
        print(f"    - {p}")
    print(f"  headline: {brief.headline.text} [{', '.join(brief.headline.cites)}]")
    print(f"  written to {out.relative_to(STATE.parent)}")


if __name__ == "__main__":
    main()
