"""QBR note → concept detection → semantic QBR (OKF concept, draft) → SME approval (verified) → hydration.

- `draft` writes the semantic QBR into working memory (.data/semantic-qbr/): product mentions linked to the catalog,
  asset figures with the computations they allow, and candidate findings, each with its source sentence.
- `approve` is the one gate: the SME confirms or rejects each finding. Confirmed findings are promoted to memory;
  rejected ones keep the reviewer's reason. The file becomes `status: verified`.
- `hydrate` writes the semantic QBR and its mentions into the graph and starts a run of the bundle's follow-up
  procedure: proposed actions bound to findings, owned by the relationship owner, with due dates. Open actions that
  would pitch a product the advisor has since postponed or rejected are put on hold.
"""
from datetime import date
from pathlib import Path

import yaml

from . import DATA, SOLUTION, STATE
from . import queries as q
from .detect import detect, unlinked_findings
from .graph import Graph
from .memory import promoter, write_action
from .roster import Roster
from .tasks import TaskStore

BUNDLE = SOLUTION / "bundle"
PROCEDURE = BUNDLE / "procedures" / "qbr-understanding-and-follow-up.md"
DRAFTS = STATE / "semantic-qbr"
WRITES = {
    "experience": ["aai:ExperienceObservation", "aai:concerns", "aai:reportedBy", "aai:affects", "aai:hasSentiment", "aai:supportedBy", "aai:reviewComment"],
    "intent": ["aai:Intent", "aai:targets", "aai:considersAlternative", "aai:classifiedAs", "aai:supersedes",
               "aai:supportedBy", "aai:ProductStateRecord", "aai:reviewComment"],
    "commitment": ["aai:Commitment", "aai:madeBy", "aai:dueDate", "aai:reviewComment"],
    "commitment_status": ["aai:Commitment"],
    "asset": ["aai:AssetObservation", "aai:measures", "aai:reportedBy", "aai:supportedBy", "aai:evidenceType", "aai:reviewComment"],
}
STOPPED = ("postponing", "rejecting or discontinuing")


def procedure() -> dict:
    return yaml.safe_load(PROCEDURE.read_text().split("---\n", 2)[1])


def _names(data=DATA):
    """Display names for offering, platform and intent concept ids."""
    catalog = yaml.safe_load((data / "reference" / "catalog.yaml").read_text())
    taxonomy = yaml.safe_load((data / "reference" / "intents.yaml").read_text())
    return {o["id"]: o["name"] for o in catalog["offerings"] + catalog["platforms"]} | \
        {c["id"]: c["label"] for c in taxonomy["concepts"]}


def _rules(data=DATA):
    return yaml.safe_load((data / "reference" / "asset_definitions.yaml").read_text())["allowed_computations"]


def _span(body, start, end):
    return " ".join(body[start:end].split())


def render(store: TaskStore, roster: Roster, meta: dict, body: str, firm_name: str) -> str:
    """The semantic QBR as an OKF concept: frontmatter for the agent, readable sections for the SME."""
    iid, item, det, names = meta["interaction_id"], store.review_item(meta["interaction_id"]), detect(body), _names()
    team = roster.teams[meta["team"]]
    cands = store.candidates(iid)
    status = {"pending review": "draft", "awaiting expert": "partially verified", "reviewed": "verified",
              "no action needed": "verified"}[item["status"]]
    writes = ["aai:SemanticQBR", "aai:interprets", "aai:ProductMention", "aai:foundIn", "aai:refersTo"]
    for c in cands:
        writes += [w for w in WRITES[c["kind"]] if w not in writes]
    review = {"owner": team.sme, "deadline": item["deadline"]}
    if item["resolved_by"]:
        review |= {"decided_by": item["resolved_by"], "decided_at": item["resolved_at"], "outcome": item["status"]}
    waiting = [c for c in cands if c["status"] == "escalated"]
    if waiting:
        review["awaiting"] = [{"finding": c["id"], "expert": c["escalated_to"], "due": c["escalation_deadline"]} for c in waiting]
    front = {
        "type": "Semantic QBR",
        "title": f"Semantic QBR: {firm_name}, {meta['date']}",
        "description": f"What the {meta['type']} of {meta['date']} says about products, assets, intent and commitments, "
                       f"linked to the catalog and tied to the advisor's words.",
        "status": status,
        "interprets": iid,
        "sources": [{"id": iid, "resource": str(Path(meta["path"]).relative_to(SOLUTION))}],
        "catalog_version": det["catalog_version"],
        "procedure": {"resource": "/procedures/qbr-understanding-and-follow-up.md", "steps": [3, 4]},
        "review": review,
        "writes": writes,
        "supports": ["CQ1", "CQ3", "CQ4", "CQ6"],
    }
    out = ["---", yaml.safe_dump(front, sort_keys=False, allow_unicode=True).rstrip(), "---", ""]
    hints = unlinked_findings(cands, det["mentions"], body)
    for c in cands:
        if c["kind"] == "experience" and not c["payload"].get("sentiment"):
            hints[c["id"]] = (hints[c["id"]] + "; " if c["id"] in hints else "") + \
                "no sentiment recorded, so no follow-up will be proposed; re-extract or note it"
    described = {c["id"]: describe(c, names, roster) for c in cands}
    tips = {cid: f"{dict((c['id'], c['kind']) for c in cands)[cid].replace('_', ' ').capitalize()}: {w}. "
                 f"{d[0].upper() + d[1:]}." + (f" Hint: {hints[cid]}." if cid in hints else "") + " Click to review."
            for cid, (w, d) in described.items()}
    lead = (f"Draft until an SME approves it; only approved findings enter memory." if status == "draft" else
            f"Partly decided: approved findings are in memory; {len(waiting)} finding(s) await an expert." if waiting else
            f"Decided by {roster.reps.get(item['resolved_by'], item['resolved_by'])} on {item['resolved_at']}: {item['status']}"
            + (f" ({item['note']})." if item["note"] else "."))
    out += [f"{lead} Source: `{iid}`.", "", "# Note", "",
            "The note as saved. Each finding's sentence is in bold and links to the finding below; hover it to see "
            "what it says and its status.", "",
            *[f"> {line}" if line else ">" for line in marked(body, cands, tips).strip().splitlines()],
            "", "# Product mentions", "",
            "| Phrase | In the sentence | Linked to | How |", "|---|---|---|---|"]
    for m in det["mentions"]:
        target = f"{names[m.target]} (`{m.target}`)" if m.target else "**unresolved**: ask the advisor or SME"
        out.append(f"| {m.phrase} | {_span(body, *m.sentence)} | {target} | {m.method} |")
    out += ["", "# Asset figures", ""]
    if not det["assets"]:
        out.append("None stated.")
    for a in det["assets"]:
        out += [f"- **{a.text}** read as `{a.metric}`, scope \"{a.scope}\", stated by the advisor (testimony, not a reported figure).",
                *[f"  - Rule `{r['id']}`: {r['rule']}" for r in _rules()],
                f"  - Sentence: \"{_span(body, *a.sentence)}\""]
    out += ["", "# Findings", ""]
    for c in cands:
        what, decision = described[c["id"]]
        p = c["payload"]
        text = p.get("span") or (_span(body, *map(int, c["span_id"].split("#")[1].split("-"))) if c["span_id"] else "")
        out += [f'<a id="{_anchor(c["id"])}"></a>', "", f"## {c['id']} · {c['kind'].replace('_', ' ')}", "", f"> {text}", "",
                f"- Reads as: {what}", f"- Writes: {', '.join(WRITES[c['kind']])}", f"- Decision: {decision}"]
        if c["id"] in hints:
            out.append(f"- Hint for the SME: {hints[c['id']]}")
        out += ["", "[Back to the note](#note)", ""]
    return "\n".join(out)


def describe(c: dict, names: dict, roster: Roster) -> tuple:
    """What a finding says, and where its decision stands, in plain words."""
    p = c["payload"]
    what = {"experience": lambda: f"{p.get('sentiment') or 'sentiment not recorded'}, {p.get('affected')}: {p.get('summary')} "
                                  f"({names.get(p.get('product'), p.get('product'))})",
            "intent": lambda: f"{names.get(p.get('concept'), p.get('concept'))} → {names.get(p.get('target'), p.get('target'))}"
                              + (f"; proposes state `{p['proposes_state']}`" if p.get("proposes_state") else ""),
            "commitment": lambda: f"{p.get('summary')}, due {p.get('due')}",
            "commitment_status": lambda: f"{p.get('commitment')} is {p.get('status')}",
            "asset": lambda: f"{p.get('metric')} {p.get('value'):,.0f} {p.get('currency')}, {p.get('scope')}"}[c["kind"]]()
    name = lambda r: roster.reps.get(r, r)
    decision = {"candidate": lambda: "pending SME approval",
                "confirmed": lambda: f"approved by {name(c['decided_by'])} on {c['decided_at']}",
                "rejected": lambda: f"rejected by {name(c['decided_by'])}: {c['reason']}",
                "escalated": lambda: f"escalated by {name(c['escalated_by'])} to {name(c['escalated_to'])} "
                                     f"({roster.roles[c['escalated_to']]}), due {c['escalation_deadline']}",
                "repetition": lambda: f"repetition of `{c['quotes']}`; linked, not counted as new evidence"}[c["status"]]()
    if c.get("escalated_by"):
        decision = (f"escalated by {name(c['escalated_by'])}: \"{c['escalation_comment']}\"; " + decision
                    if c["status"] != "escalated" else decision + f"; \"{c['escalation_comment']}\"")
    if c.get("comment") and c["status"] != "rejected":
        decision += f"; comment: \"{c['comment']}\""
    return what, decision


def _anchor(cid: str) -> str:
    return cid.lower()


def _title(text: str) -> str:
    """Safe inside a Markdown link title."""
    return text.replace('"', "'").replace("`", "")


def marked(body: str, cands: list, tips: dict) -> str:
    """The note with each finding's span in bold, linked to its section below with a tooltip; overlapping spans keep the first."""
    spans = []
    for c in cands:
        if c["span_id"]:
            start, end = map(int, c["span_id"].split("#")[1].split("-"))
            if body[start:end].strip() and not any(start < e and s < end for s, e, _ in spans):
                spans.append((start, end, c["id"]))
    out, pos = [], 0
    for start, end, cid in sorted(spans):
        text = body[start:end]
        lead, core, trail = text[:len(text) - len(text.lstrip())], text.strip(), text[len(text.rstrip()):]
        out += [body[pos:start], f'{lead}**[{core}](#{_anchor(cid)} "{_title(tips[cid])}")** `{cid}`{trail}']
        pos = end
    return "".join(out + [body[pos:]])


def draft(store, roster, meta, body, firm_name) -> Path:
    path = DRAFTS / f"{meta['interaction_id']}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(store, roster, meta, body, firm_name))
    return path


def add_asset_candidates(g: Graph, store: TaskStore, meta: dict, body: str):
    """Asset figures from concept detection become candidate findings, each supported by its sentence."""
    iid = meta["interaction_id"]
    for n, a in enumerate(detect(body)["assets"], 1):
        s, e = a.sentence
        span_id = f"{iid}#{s}-{e}"
        g.node("SourceSpan", span_id, spanText=body[s:e], startOffset=s, endOffset=e)
        g.link("SourceSpan", span_id, "partOf", "Interaction", iid)
        store.add_candidate(f"DET-{iid}-A{n}", iid, "asset",
                            {"metric": a.metric, "value": a.value, "currency": a.currency, "scope": a.scope,
                             "speaker": meta["advisor"], "span": body[s:e].strip()}, span_id)


def approve(g: Graph, store: TaskStore, roster: Roster, interactions: dict, bodies: dict, firm_names: dict,
            rep: str, iid: str, at: date, decisions: dict, no_action_reason: str = None) -> dict:
    """The SME gate. Promote what the SME confirms, keep reasons for what they reject, then hydrate."""
    if store.review_item(iid)["status"] not in ("pending review", "awaiting expert"):
        return store.review_item(iid)
    item = store.resolve_review(rep, iid, at, decisions, promoter(g, interactions), no_action_reason)
    meta = interactions[iid]
    hydrate(g, store, roster, meta, bodies[iid], rep, at, start_run=item["confirmed_now"] > 0)
    draft(store, roster, meta, bodies[iid], firm_names[meta["firm"]])
    return item


def hydrate(g: Graph, store: TaskStore, roster: Roster, meta: dict, body: str, approver: str, at: date, start_run=True):
    iid, team = meta["interaction_id"], roster.teams[meta["team"]]
    sq = f"SQBR:{iid}"
    g.node("SemanticQBR", sq, approvalStatus="partially verified" if store.review_item(iid)["status"] == "awaiting expert" else "verified", dueDate=date.fromisoformat(store.review_item(iid)["deadline"]),
           recordedAt=at, path=str((DRAFTS / f"{iid}.md").relative_to(SOLUTION)))
    g.link("SemanticQBR", sq, "interprets", "Interaction", iid)
    g.link("SemanticQBR", sq, "approvedBy", "Rep", approver)
    for m in detect(body)["mentions"]:
        mid, span_id = f"{iid}@{m.start}", f"{iid}#{m.sentence[0]}-{m.sentence[1]}"
        g.node("ProductMention", mid, phrase=m.phrase, linkMethod=m.method)
        g.node("SourceSpan", span_id, spanText=body[m.sentence[0]:m.sentence[1]], startOffset=m.sentence[0], endOffset=m.sentence[1])
        g.link("SourceSpan", span_id, "partOf", "Interaction", iid)
        g.link("SemanticQBR", sq, "contains", "ProductMention", mid)
        g.link("ProductMention", mid, "foundIn", "SourceSpan", span_id)
        if m.target_kind == "offering":
            g.link("ProductMention", mid, "refersTo", "ProductOffering", m.target)
    if not start_run:
        return None
    proc = procedure()
    g.node("Procedure", proc["id"], name=proc["title"], procedureVersion=str(proc["version"]))
    run = f"RUN:{iid}"
    g.node("ProcedureRun", run, startedAt=at)
    g.link("ProcedureRun", run, "follows", "Procedure", proc["id"])
    g.link("ProcedureRun", run, "startedBy", "SemanticQBR", sq)
    store.start_run(run, proc["id"], str(proc["version"]), iid, at)
    for p in q.propose_actions(g, roster, team.owner, meta["firm"], iid, at):
        store.propose_action(p, run, at)
    hold_stale_actions(g, store, roster, meta["firm"], team, at)
    return run


def hold_stale_actions(g, store, roster, firm, team, at):
    """An open action that would promote a product the advisor has since postponed or rejected goes on hold."""
    current = {i["targetId"]: i for i in q.intents(g, roster, team.owner, firm, at, at)}
    for a in store.actions():
        p = yaml.safe_load(a["payload"])
        intent = current.get(p["product"])
        if a["team"] == team.id and a["status"] in ("proposed", "approved") and p.get("promotes") and intent \
                and intent["intent"] in STOPPED and intent["id"] not in [x[1] for x in p["addresses"]]:
            store.hold_action(a["id"], at, f"advisor is now {intent['intent']} {intent['target']} ({intent['id']}); "
                                           f"do not pitch it until the blocker is resolved")


def follow_up(g, store, rep, iid, at, approve_kinds, dismiss_reason=None):
    """Historical follow-up decisions from the fixtures: approve actions on the given finding kinds, dismiss the rest."""
    kinds = {"ExperienceObservation": "experience", "Intent": "intent"}
    for a in store.actions():
        if a["interaction_id"] != iid or a["status"] != "proposed":
            continue
        addressed = {kinds[x[0]] for x in yaml.safe_load(a["payload"])["addresses"]}
        if addressed & set(approve_kinds):
            store.approve_action(rep, a["id"], at, write_action(g))
        elif dismiss_reason:
            store.dismiss_action(rep, a["id"], at, dismiss_reason)
