"""Screen 1 for presenting the accelerator: the same QBR note, before and after.

    cd solution && ../.venv/bin/streamlit run app.py

Four beats, advanced by the presenter: (1) the note as the CRM holds it, and a CRM search that finds nothing;
(2) Claude reads the note live against the firm's catalog, and concept detection links products and asset figures;
(3) the SME approves, escalating one figure to the data steward, and the side panel shows what the firm now knows;
(4) the same search, now answered from memory. Everything runs the real pipeline; nothing is mocked.
"""
import html
import shutil
import time
import uuid
from datetime import date, timedelta
from pathlib import Path

import streamlit as st
import yaml

from aai import DATA, STATE
from aai import queries as q
from aai.detect import detect
from aai.graph import Graph
from aai.ingest import load, parse_interaction
from aai.memory import write_action
from aai.pipeline import approve
from aai.roster import Roster
from aai.tasks import TaskStore

MAR = "INT-2026-03-QBR-CR"
NOTE = DATA / "salesforce" / "interactions" / f"{MAR}.md"
LIVE = DATA / "salesforce" / "extractions-live"   # git-ignored: fixtures plus this session's reading of the March note
APP = STATE / "app"
REPLAY = APP / "last-live.yaml"
VIEWER = "REP-HEAD"
D19, D20, D21 = date(2026, 3, 19), date(2026, 3, 20), date(2026, 3, 21)
PRIOR = [{"id": "CAND-01-4", "summary": "Specialist session on reporting and integration", "due": "2026-02-28"}]
BEATS = ["Today", "Understand this note", "SME approves", "Ask the firm"]

CSS = """
<style>
.block-container {padding-top: 2.2rem; max-width: 1400px}
header[data-testid='stHeader'] {display: none}
.stButton button[kind='primary'] {background: #2e2e38; border-color: #2e2e38; color: #ffe600; font-weight: 600}
.beats {font-size: 15px; color: #8a94a6; padding-top: 8px} .beats b {color: #16325c; border-bottom: 3px solid #ffe600}
.gap {height: 10px}
.crm {border: 1px solid #d8dde6; border-radius: 6px; background: #fff; font-family: -apple-system, 'Segoe UI', sans-serif}
.crm-head {background: #f3f6f9; border-bottom: 1px solid #d8dde6; padding: 12px 18px; border-radius: 6px 6px 0 0}
.crm-type {font-size: 12px; color: #54698d; text-transform: uppercase; letter-spacing: .04em}
.crm-title {font-size: 20px; font-weight: 600; color: #16325c; margin-top: 2px}
.crm-fields {display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px 18px; padding: 12px 18px; border-bottom: 1px solid #eef1f6}
.crm-fields div span {display: block; font-size: 11px; color: #54698d}
.crm-fields div b {font-weight: 500; color: #16325c; font-size: 14px}
.crm-body {padding: 16px 18px 20px; font-size: 16px; line-height: 1.9; color: #16325c}
.crm-label {font-size: 11px; color: #54698d; margin-bottom: 4px}
.read .plain {color: #8a94a6}
.f {border-radius: 3px; padding: 1px 2px; animation: reveal .7s ease both; cursor: help}
.f-intent {background: #fff1b8} .f-exp-negative {background: #ffd9d6} .f-exp-positive {background: #d7f2dc}
.f-exp-neutral, .f-exp-mixed, .f-exp-unknown {background: #e7ebf0} .f-commitment {background: #dbe8fb} .f-asset {background: #ece4f7}
.m {border-bottom: 2px solid #2e844a; cursor: help; font-weight: 600}
.m-ambiguous {border-bottom: 2px dashed #dd7a01} .m-unresolved {border-bottom: 2px dotted #ba0517}
.pill {display: inline-block; font-size: 11.5px; line-height: 1.5; padding: 0 8px; margin: 0 4px; border-radius: 10px;
       vertical-align: 2px; font-weight: 600; animation: reveal .7s ease both; white-space: nowrap}
.p-intent {background: #f5d76e; color: #4a3b00} .p-exp-negative {background: #ea5d52; color: #fff} .p-exp-positive {background: #2e844a; color: #fff}
.p-exp-neutral, .p-exp-mixed, .p-exp-unknown {background: #8a94a6; color: #fff} .p-commitment {background: #0b5cab; color: #fff}
.p-asset {background: #7f56d9; color: #fff} .p-chip {background: #e3f3e8; color: #1e6b37; font-weight: 500}
.p-ambiguous {background: #fde9c9; color: #8c4b02; font-weight: 500}
.ok {color: #2e844a; font-weight: 600}
@keyframes reveal {from {opacity: 0; transform: translateY(3px)} to {opacity: 1; transform: none}}
.search {border: 1px solid #d8dde6; border-radius: 6px; padding: 10px 14px; background: #fff; margin-bottom: 12px; font-size: 14px}
.search .q {font-weight: 600; color: #16325c} .zero {color: #ba0517; font-weight: 600}
.panel {border: 1px solid #d8dde6; border-top: 4px solid #ffe600; border-radius: 6px; background: #fff; padding: 14px 16px;
        font-family: -apple-system, 'Segoe UI', sans-serif; animation: reveal .7s ease both}
.panel h4 {margin: 0 0 4px; color: #16325c; font-size: 15px} .panel .sub {color: #54698d; font-size: 12px; margin-bottom: 10px}
.panel h5 {margin: 12px 0 4px; font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: #54698d}
.panel li {font-size: 13.5px; margin-bottom: 3px; color: #16325c} .panel ul {padding-left: 18px; margin: 0}
.dont li::marker {content: "✕  "; color: #ba0517}
.warn {color: #8c4b02; font-size: 12.5px}
</style>
"""


def esc(s):
    return html.escape(str(s), quote=True)


def names():
    cat = yaml.safe_load((DATA / "reference" / "catalog.yaml").read_text())
    return {o["id"]: o["name"] for o in cat["offerings"] + cat["platforms"]}


def crm_search(text):
    """What a CRM text search over activity notes finds: the literal words, nothing more."""
    hits = []
    for p in sorted((DATA / "salesforce" / "interactions").glob("*.md")):
        meta, body = parse_interaction(p)
        if text.lower() in body.lower():
            hits.append(meta["interaction_id"])
    return hits


# ------------------------------------------------------------------------------------------------ reading the note

def read_live():
    from aai.llm import extract_note, load_env
    load_env()
    started = time.time()
    doc = extract_note(NOTE, PRIOR)
    doc["seconds"] = round(time.time() - started, 1)
    APP.mkdir(parents=True, exist_ok=True)
    REPLAY.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
    return doc


def read_replay():
    source = REPLAY if REPLAY.exists() else DATA / "salesforce" / "extractions-llm" / f"{MAR}.yaml"
    doc = yaml.safe_load(source.read_text())
    doc["seconds"] = None
    return doc


def tooltip_for(c, nm):
    k = c["kind"]
    if k == "intent":
        return f"Intent: {c.get('concept')} → {nm.get(c.get('target'), c.get('target'))}. Reason: {c.get('reason')}. Proposes: {c.get('proposes_state') or 'no state change'}."
    if k == "experience":
        return f"Experience ({c.get('sentiment') or 'sentiment not recorded'}) with {nm.get(c.get('product'), c.get('product'))}, affecting the {c.get('affected')}. {c.get('summary')}. Testimony, not a measured outcome."
    if k == "commitment_status":
        return f"Update on an earlier promise ({c.get('commitment')}): still {c.get('status')}."
    if k == "commitment":
        return f"Commitment by {c.get('made_by')}: {c.get('summary')}, due {c.get('due')}."
    return f"Asset figure: {c.get('metric')} {c.get('value'):,.0f} {c.get('currency')}, {c.get('scope')}. The advisor's statement, not a reported figure."


def pill_for(c, nm, status=None):
    k, prod = c["kind"], nm.get(c.get("product") or c.get("target"), c.get("product") or c.get("target"))
    short = {"CPX Unified Managed Account": "CPX UMA", "Crestline Model Portfolios": "CMP", "Crestline Custody and Clearing": "Custody"}
    prod = short.get(prod, prod)
    if k == "intent":
        cls, label = "intent", f"Intent · {c.get('concept')} · {prod}" + (" · blocker: integration" if c.get("blocker") or "integration" in (c.get("reason") or "") else "")
    elif k == "experience":
        s = c.get("sentiment") or "unknown"
        cls, label = f"exp-{s}", f"{s.capitalize()} · {prod} · {c.get('affected')}"
    elif k in ("commitment", "commitment_status"):
        cls, label = "commitment", "Promise still open" if c.get("status", "open") == "open" else "Promise kept"
    else:
        cls, label = "asset", f"Her statement · {c.get('metric')} ${c.get('value') / 1e6:,.0f}M · not merged"
    if status:
        label += f" · {status}"
    return cls, label


def annotate(body, findings, mentions, nm, statuses):
    """The note with findings highlighted and labelled, and product mentions linked to the catalog. Hover shows why."""
    spans = []
    for c in findings:
        start = body.find(c["span"])
        if start >= 0:
            spans.append((start, start + len(c["span"]), c))
    cuts = sorted({0, len(body)} | {x for s, e, _ in spans for x in (s, e)} | {x for m in mentions for x in (m.start, m.end)})
    out = []
    for a, b in zip(cuts, cuts[1:]):
        text = esc(body[a:b])
        f = next((c for s, e, c in spans if s <= a and b <= e), None)
        m = next((m for m in mentions if m.start <= a and b <= m.end), None)
        if m:
            if m.method == "ambiguous":
                tip = f"Probably {nm[m.target]}, but 'their' may mean a competitor's product. The SME decides."
            elif m.target:
                tip = f"Linked to the Crestline catalog: {nm[m.target]} ({m.target}), by {m.method}."
            else:
                tip = "A kind of product with no match in the catalog: left unresolved for the SME."
            text = f'<span class="m m-{m.method}" title="{esc(tip)}">{text}</span>'
        if f:
            cls = pill_for(f, nm)[0]
            text = f'<span class="f f-{cls}" title="{esc(tooltip_for(f, nm))}">{text}</span>'
        elif not m:
            text = f'<span class="plain">{text}</span>'
        out.append(text)
        for s, e, c in spans:
            if e == b:
                cls, label = pill_for(c, nm, statuses.get(c["id"]))
                out.append(f'<span class="pill p-{cls}" title="{esc(tooltip_for(c, nm))}">{esc(label)}</span>')
        for mm in mentions:
            if mm.end == b and mm.target and mm.method == "ambiguous":
                out.append(f'<span class="pill p-ambiguous">ours or a competitor\'s?</span>')
            elif mm.end == b and mm.target and not any(s <= mm.start and mm.end <= e for s, e, _ in spans):
                out.append(f'<span class="pill p-chip">→ {esc(nm[mm.target])}</span>')
    return "".join(out).replace("\n\n", '<div class="gap"></div>').replace("\n", " ")


# ------------------------------------------------------------------------------------------------ memory

def build_memory(doc):
    """The real pipeline on the fixtures plus this reading of the March note: load, SME approval, escalation, coverage."""
    if LIVE.exists():
        shutil.rmtree(LIVE)
    shutil.copytree(DATA / "salesforce" / "extractions", LIVE)
    (LIVE / f"{MAR}.yaml").write_text(yaml.safe_dump({k: v for k, v in doc.items() if k != "seconds"}, sort_keys=False))
    roster = Roster()
    run_dir = APP / uuid.uuid4().hex[:8]  # one graph per build: sessions never share an open database
    g, s = Graph(run_dir / "graph.lbug", fresh=True), TaskStore(run_dir / "tasks.sqlite", roster, fresh=True)
    r = load(g, s, extractions=LIVE.name)
    s.mark_unavailable("REP-JORDAN", D19, "leave")
    run = lambda rep, at, d: approve(g, s, roster, r["interactions"], r["bodies"], r["firm_names"], rep, MAR, at, d)
    asset = f"DET-{MAR}-A1"
    decisions = {c["id"]: "confirm" for c in s.candidates(MAR, "candidate")}
    decisions[asset] = {"decision": "escalate", "to": "REP-RIA",
                        "comment": "Stated $320M differs from the firm's reported $300M; decide whether it enters memory as her statement"}
    run("REP-DANA", D20, decisions)
    run("REP-RIA", D21, {asset: {"decision": "confirm", "comment": "Accept as her statement: testimony, never merged with reported AUM"}})
    for a in s.activate_coverage("REP-LEE", "TEAM-CR", "REP-JORDAN", "REP-PRIYA", D21):
        s.acknowledge("REP-PRIYA", a["id"], D21)
    for a in s.actions("proposed"):
        if a["interaction_id"] == MAR:
            s.approve_action("REP-PRIYA", a["id"], D21, write_action(g))
    return {"g": g, "s": s, "roster": roster}


def panel(mem, nm):
    g, s, roster = mem["g"], mem["s"], mem["roster"]
    states = [q.product_state(g, roster, VIEWER, "FIRM-001", p, D21, D21) for p in ("CCC", "CMP", "CPX-UMA")]
    knows = "".join(f"<li><b>{esc(nm[x['product']])}</b>: {x['state']}"
                    + (f' <span class="warn">⚠ the CRM {esc(x["discrepancies"][0].split("; ")[1].removeprefix("crm "))}</span>' if x["discrepancies"] else "")
                    + "</li>" for x in states)
    obs = q.assets(g, roster, VIEWER, "FIRM-001", D21)
    gap = q.profile(g, roster, VIEWER, "ADV-001", D21, D21)["gaps"]
    dont = [f"Pitch {esc(a['title'].split(' of ')[1].split(' against')[0])}: on hold, she is postponing it" for a in s.actions("on hold")]
    dont.append(f"Quote a total AUM: {len(obs)} figures with different meanings ($300M reported, $180M AUA, $320M her statement)")
    if gap:
        dont.append("Say she is registered: exams passed, registration unknown")
    owe = "".join(f"<li>{esc(c['summary'])}: {c['status']}, owner Priya (covering Jordan)</li>"
                  for c in q.commitments(g, roster, VIEWER, "FIRM-001", D21) if c["status"] == "open")
    nxt = "".join(f"<li>{esc(a['title'].split(';')[0])}: owner Priya, due {a['due']}</li>"
                  for a in s.actions("approved") if a["interaction_id"] == MAR)
    cands = [c for c in s.candidates(MAR) if c["status"] in ("confirmed", "rejected")]
    escalated = [c for c in cands if c["escalated_by"]]
    sme = (f"{len(cands)} findings decided: {len(cands) - len(escalated)} approved by Dana Ortiz (SME) on 20 March; "
           f"{len(escalated)} escalated to Ria Patel (data steward), who accepted it on 21 March.")
    return f"""<div class="panel"><h4>Account intelligence · Maya Chen, Cedar Ridge</h4>
    <div class="sub">What the firm now knows, after expert approval</div>
    <h5>Uses and considers</h5><ul>{knows}</ul>
    <h5>Don't say</h5><ul class="dont">{"".join(f"<li>{d}</li>" for d in dont)}</ul>
    <h5>We owe her</h5><ul>{owe or "<li>nothing open</li>"}</ul>
    <h5>Next steps, owned</h5><ul>{nxt}</ul>
    <h5>Expert control</h5><ul><li>{esc(sme)}</li></ul></div>"""


# ------------------------------------------------------------------------------------------------ page

st.set_page_config(page_title="Account Intelligence · QBR", layout="wide", initial_sidebar_state="collapsed")
st.markdown(CSS, unsafe_allow_html=True)
ss = st.session_state
if "beat" not in ss:  # deep link: ?beat=2 opens at that beat; ?replay=1 starts with the live toggle off
    ss.beat = min(int(st.query_params.get("beat", 0)), len(BEATS) - 1)

with st.sidebar:
    st.markdown("**Presenter**")
    live = st.toggle("Claude reads the note live", value=st.query_params.get("replay") != "1",
                     help="Off: replay the last live reading, instantly")
    st.caption(f"Viewing as Morgan Hale, head of relationship management. Note: {MAR}.")
    if st.button("Reset to the start", width="stretch"):
        for k in list(ss.keys()):
            del ss[k]
        st.rerun()

nm = names()
meta, body = parse_interaction(NOTE)
cols = st.columns([5, 1.2])
with cols[0]:
    st.markdown('<div class="beats">' + "  →  ".join(f"<b>{i + 1}. {b}</b>" if i == ss.beat else f"{i + 1}. {b}"
                                                     for i, b in enumerate(BEATS)) + "</div>", unsafe_allow_html=True)
with cols[1]:
    if ss.beat < len(BEATS) - 1 and st.button(f"Next: {BEATS[ss.beat + 1]}", type="primary", width="stretch"):
        ss.beat += 1
        st.rerun()

query = "CPX Unified Managed Account"
left, right = st.columns([2.1, 1])
with left:
    if ss.beat >= 1 and "doc" not in ss:
        with st.status("Reading the note against Crestline's catalog, intents and sentiments…", expanded=True) as status:
            try:
                ss.doc = read_live() if live else read_replay()
                how = f"Claude ({ss.doc['extractor']}) read it in {ss.doc['seconds']} s" if ss.doc["seconds"] else "Replayed the last live reading"
                status.update(label=how, state="complete", expanded=False)
            except Exception as e:  # keep the room moving: fall back to the last reading
                ss.doc = read_replay()
                status.update(label=f"Live call failed ({type(e).__name__}); replayed the last reading", state="error", expanded=False)
    if ss.beat >= 2 and "mem" not in ss:
        with st.spinner("SME approval, escalation and follow-up…"):
            ss.mem = build_memory(ss.doc)

    if ss.beat < 3:
        hits = crm_search(query)
        st.markdown(f'<div class="search">CRM search: <span class="q">"{query}"</span> → '
                    f'<span class="zero">{len(hits)} results</span> in activity notes</div>', unsafe_allow_html=True)
    else:
        found = q.who_mentions(ss.mem["g"], ss.mem["roster"], VIEWER, query, D21,
                               yaml.safe_load((DATA / "reference" / "catalog.yaml").read_text()))
        st.markdown(f'<div class="search">Ask the firm: <span class="q">"{query}"</span> → '
                    f'<span class="ok">{len(found["rows"])} advisors</span>, from approved memory</div>', unsafe_allow_html=True)
        st.dataframe([{"Advisor": r["advisor"], "Firm": r["firm"], "Intent": r["intent"], "Why": r["reason"], "Since": str(r["since"]),
                       "State": r["state"] + (f" (CRM disagrees)" if r["discrepancy"] else "")} for r in found["rows"]],
                     hide_index=True, width="stretch")

    statuses = {}
    if "mem" in ss:
        for c in ss.mem["s"].candidates(MAR):
            statuses[c["id"]] = ("✓ approved, escalated first" if c["escalated_by"] else "✓ approved") if c["status"] == "confirmed" else c["status"]
    if ss.beat == 0:
        note_html = esc(body.strip()).replace("\n\n", '<div class="gap"></div>')
    else:
        det = detect(body)
        findings = list(ss.doc["candidates"])
        findings += [{"id": f"DET-{MAR}-A1", "kind": "asset", "span": body[a.sentence[0]:a.sentence[1]].strip(), "metric": a.metric,
                      "value": a.value, "currency": a.currency, "scope": a.scope} for a in det["assets"]]
        note_html = annotate(body.strip(), findings, det["mentions"], nm, statuses)
    st.markdown(f"""<div class="crm {'read' if ss.beat else ''}">
      <div class="crm-head"><div class="crm-type">Activity · Quarterly business review</div>
        <div class="crm-title">QBR with Maya Chen</div></div>
      <div class="crm-fields"><div><span>Account</span><b>Cedar Ridge Advisory</b></div>
        <div><span>Contact</span><b>Maya Chen</b></div><div><span>Date</span><b>{meta['date']}</b></div>
        <div><span>Assigned to</span><b>Jordan{' (on leave)' if ss.beat else ''}</b></div></div>
      <div class="crm-body"><div class="crm-label">Description</div>{note_html}</div></div>""", unsafe_allow_html=True)
    if ss.beat >= 1 and ss.doc.get("reviewer_notes"):
        with st.expander("What the reader flagged for the SME"):
            for n in ss.doc["reviewer_notes"]:
                st.markdown(f"- {n}")

with right:
    if "mem" in ss:
        st.markdown(panel(ss.mem, nm), unsafe_allow_html=True)
    elif ss.beat == 1:
        st.markdown('<div class="panel"><h4>Waiting for the SME</h4><div class="sub">Nothing enters the firm\'s memory '
                    'until an expert approves it. Hover any highlight to see what was read and why.</div></div>',
                    unsafe_allow_html=True)
