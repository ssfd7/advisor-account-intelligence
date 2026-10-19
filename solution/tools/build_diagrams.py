"""Generate the architecture and design diagrams in solution/diagrams/.

    .venv/bin/python solution/tools/build_diagrams.py
    .venv/bin/python solution/tools/render.py solution-design memory-architecture

Regenerating overwrites manual edits to these two Draw.io files.
"""
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "diagrams"

FILL = {"source": "#FFF2CC", "step": "#E5EFFA", "memory": "#E4F1E3", "agent": "#EEE5F4", "work": "#FCE4D6",
        "neutral": "#F2F2F2", "white": "#FFFFFF", "code": "#FBE5EC"}
GROUP_FILL = {"source": "#FFFBEE", "step": "#F3F8FD", "memory": "#F4FAF0", "agent": "#F8F4FB", "work": "#FDF6F1",
              "neutral": "#FAFAFA"}
EDGE = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#555555;strokeWidth=1.2;fontSize=12;"
        "fontColor=#333333;labelBackgroundColor=#FFFFFF;endArrow=classic;endSize=7;jumpStyle=arc;jumpSize=8;")
STRAIGHT = EDGE.replace("edgeStyle=orthogonalEdgeStyle;rounded=1;", "edgeStyle=none;rounded=0;")


class Page:
    def __init__(self, mxfile, name, width, height, title, subtitle):
        d = ET.SubElement(mxfile, "diagram", {"id": name.lower().replace(" ", "-"), "name": name})
        m = ET.SubElement(d, "mxGraphModel", {"dx": "1400", "dy": "900", "grid": "1", "gridSize": "10", "guides": "1",
                                              "tooltips": "1", "connect": "1", "arrows": "1", "fold": "1", "page": "1",
                                              "pageScale": "1", "pageWidth": str(width), "pageHeight": str(height),
                                              "background": "#FFFFFF", "math": "0", "shadow": "0",
                                              "lineJumpsEnabled": "1"})
        self.root = ET.SubElement(m, "root")
        ET.SubElement(self.root, "mxCell", {"id": "0"})
        ET.SubElement(self.root, "mxCell", {"id": "1", "parent": "0"})
        self.n = 0
        self.text("title", title, 25, 14, width - 50, 34, 24, bold=True)
        if subtitle:
            self.text("subtitle", subtitle, 25, 50, width - 50, 26, 13, color="#444444")

    def _cell(self, cid, value, style, geo, vertex=True, src=None, tgt=None, points=None):
        attrs = {"id": cid, "value": value, "style": style, "parent": "1"}
        if vertex:
            attrs["vertex"] = "1"
        else:
            attrs.update(edge="1", source=src, target=tgt)
        c = ET.SubElement(self.root, "mxCell", attrs)
        g = ET.SubElement(c, "mxGeometry", {k: str(v) for k, v in geo.items()})
        g.set("as", "geometry")
        if points:
            arr = ET.SubElement(g, "Array", {"as": "points"})
            for x, y in points:
                ET.SubElement(arr, "mxPoint", {"x": str(x), "y": str(y)})
        return cid

    def text(self, cid, value, x, y, w, h, size=13, bold=False, color="#222222", align="left"):
        style = (f"text;html=1;align={align};verticalAlign=middle;whiteSpace=wrap;fontSize={size};fontColor={color};"
                 f"strokeColor=none;fillColor=none;" + ("fontStyle=1;" if bold else ""))
        return self._cell(cid, escape(value), style, {"x": x, "y": y, "width": w, "height": h})

    def group(self, cid, title, x, y, w, h, kind="neutral", dashed=False):
        style = ("rounded=1;arcSize=3;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacingLeft=12;spacingTop=6;"
                 f"fillColor={GROUP_FILL[kind]};strokeColor=#888888;strokeWidth=1;fontSize=14;fontColor=#222222;"
                 + ("dashed=1;dashPattern=6 4;" if dashed else ""))
        return self._cell(cid, f"<b>{escape(title)}</b>", style, {"x": x, "y": y, "width": w, "height": h})

    def box(self, cid, title, x, y, w, h, kind="step", sub=None, desc=None, dashed=False, center=False, size=13):
        html = f"<b>{escape(title)}</b>"
        if sub:
            html += f'<br><font color="#555555" style="font-size:12px">{escape(sub)}</font>'
        if desc:
            html += f'<div style="margin-top:5px">{escape(desc).replace(chr(10), "<br>")}</div>'
        style = (f"rounded=1;arcSize=8;whiteSpace=wrap;html=1;align={'center' if center else 'left'};"
                 f"verticalAlign={'middle' if center else 'top'};spacing=8;fillColor={FILL[kind]};strokeColor=#666666;"
                 f"strokeWidth=1;fontSize={size};fontColor=#222222;" + ("dashed=1;dashPattern=6 4;" if dashed else ""))
        return self._cell(cid, html, style, {"x": x, "y": y, "width": w, "height": h})

    def ellipse(self, cid, label, x, y, w, h, kind="neutral"):
        style = (f"ellipse;whiteSpace=wrap;html=1;fillColor={FILL[kind]};strokeColor=#666666;fontSize=12;"
                 "fontColor=#222222;")
        return self._cell(cid, escape(label), style, {"x": x, "y": y, "width": w, "height": h})

    def lane(self, cid, title, x, y, w, h, kind):
        style = (f"swimlane;horizontal=0;html=1;startSize=36;fillColor={FILL[kind]};swimlaneFillColor={GROUP_FILL.get(kind, '#FFFFFF')};"
                 "strokeColor=#888888;fontSize=14;fontStyle=1;fontColor=#222222;")
        return self._cell(cid, escape(title), style, {"x": x, "y": y, "width": w, "height": h})

    def arrow(self, src, tgt, label="", dashed=False, straight=False, exit=None, entry=None, points=None, curved=False, pos=None):
        self.n += 1
        style = STRAIGHT if straight else EDGE
        if curved:
            style = STRAIGHT + "curved=1;"
        if dashed:
            style += "dashed=1;dashPattern=6 4;"
        if exit:
            style += f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
        if entry:
            style += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
        return self._cell(f"a{self.n}", escape(label).replace("\n", "<br>"), style, {"relative": "1", **({"x": pos} if pos is not None else {})}, vertex=False, src=src, tgt=tgt,
                          points=points)


def solution_design():
    mx = ET.Element("mxfile", {"host": "app.diagrams.net"})

    # ------------------------------------------------------------ solution architecture
    p = Page(mx, "Solution architecture", 1600, 1190, "Advisor Account Intelligence: phase 1 solution architecture",
             "Synthetic file feeds, one assistant, mock task store. Read each arrow as source, label, target.")
    p.group("g-src", "Source files (synthetic)", 25, 90, 1550, 150, "source")
    src = [("src-profile", "Profile export · CSV", "Snowflake export", "Identities, affiliations, qualifications, registrations, asset observations"),
           ("src-qbr", "QBR notes · Markdown", "Salesforce export", "Experience, intent, alternatives, commitments"),
           ("src-email", "Email and activity · Markdown", "Salesforce export", "Follow-up notes; may quote earlier QBRs"),
           ("src-catalog", "Product catalog", "structured files", "Offerings, capabilities, prerequisites, versions"),
           ("src-tax", "Intent taxonomy", "versioned file", "Approved concepts, definitions, examples"),
           ("src-click", "Clickstream · CSV", "phase 2, optional", "Dated usage summaries per offering")]
    for i, (cid, t, s, d) in enumerate(src):
        p.box(cid, t, 40 + i * 255, 125, 235, 100, "source", s, d, dashed=cid == "src-click")
    p.group("g-ing", "Ingestion pipeline", 25, 290, 1550, 150, "step")
    steps = [("ing-1", "1 · Preserve source files", "Raw copies with import version"),
             ("ing-2", "2 · Validate identifiers and dates", "Reject or flag malformed records"),
             ("ing-3", "3 · Reconcile identities", "Never merge on name similarity alone"),
             ("ing-4", "4 · Extract candidates", "LLM: experience, intent, commitments with source spans"),
             ("ing-5", "5 · Review and validate", "Reviewer confirms or corrects in the review app"),
             ("ing-6", "6 · Load with provenance", "Idempotent; valid and recorded time")]
    for i, (cid, t, d) in enumerate(steps):
        p.box(cid, t, 40 + i * 255, 325, 235, 95, "step", None, d)
        if i:
            p.arrow(steps[i - 1][0], cid, straight=True)
    p.arrow("g-src", "ing-1", "", exit=(0.08, 1), entry=(0.5, 0))
    p.group("g-mem", "Memory and knowledge", 25, 490, 1550, 190, "memory")
    p.box("store", "Source store", 40, 530, 300, 130, "memory", "raw files and spans", "Citations in briefs resolve to exact source spans here")
    p.box("graph", "Knowledge graph · LadybugDB", 400, 530, 420, 130, "memory", "semantic and episodic memory",
          "Identities, product relationships and state records, interactions, intents, actions. Bitemporal and access-scoped.")
    p.box("onto", "Ontology and governance", 900, 530, 280, 130, "memory", "solution/model",
          "Classes, relationships, code lists and stewards. Defines the graph schema.")
    p.box("proc", "Procedure and taxonomy versions", 1220, 530, 340, 130, "memory", "procedural memory",
          "Approved QBR and follow-up steps (Markdown plus step list) and the active taxonomy version")
    p.arrow("ing-1", "store", "raw copies", exit=(0.5, 1), entry=(0.5, 0))
    p.arrow("ing-6", "graph", "load", exit=(0.5, 1), entry=(0.75, 0))
    p.arrow("onto", "graph", "schema", straight=True)
    p.group("g-ast", "Assistant", 25, 730, 1550, 170, "agent")
    p.box("ctx", "Context builder", 40, 770, 340, 110, "agent", None,
          "Access-scoped retrieval, as-of filter, graph traversal; bundle of at most 12k tokens")
    p.box("agent", "QBR assistant", 450, 770, 320, 110, "agent", "one agent in phase 1",
          "Follows the procedure; drafts the brief and up to three actions")
    p.box("verify", "Evidence verifier", 840, 770, 300, 110, "agent", None,
          "Checks citations, prerequisites, metric scope and access before anything is proposed")
    p.box("eval", "Evaluation harness", 1220, 770, 340, 110, "neutral", "golden cases",
          "Held-out periods and memory metrics; run on every model, prompt or procedure change")
    p.arrow("store", "ctx", "spans", exit=(0.5, 1), entry=(0.25, 0))
    p.arrow("graph", "ctx", "facts and history", exit=(0.2, 1), entry=(0.75, 0))
    p.arrow("proc", "agent", "procedure", exit=(0.5, 1), entry=(0.75, 0))
    p.arrow("ctx", "agent", "bundle", straight=True)
    p.arrow("agent", "verify", "draft", straight=True)
    p.group("g-work", "Work and review", 25, 950, 1550, 190, "work")
    p.box("ui", "Review app", 40, 1000, 380, 110, "work", "RM, covering rep, analyst, compliance",
          "Brief review, takeaway validation (pipeline step 5), action approval")
    p.box("queue", "Team queue and task store", 500, 1000, 380, 110, "work", "mock in phase 1",
          "Unreviewed QBRs, actions, assignments, coverage, completion evidence")
    p.box("roster", "Roster and coverage settings", 960, 1000, 270, 110, "work", None,
          "Manual availability; no HR or calendar integration")
    p.box("lead", "Team lead view", 1290, 1000, 270, 110, "work", None, "Overdue and unowned items; escalation")
    p.arrow("verify", "ui", "proposed brief and actions", exit=(0.5, 1), entry=(0.5, 0))
    p.arrow("ui", "queue", "approved", straight=True)
    p.arrow("roster", "queue", "coverage", straight=True)
    p.arrow("queue", "lead", "overdue, unowned", exit=(0.5, 1), entry=(0.5, 1), points=[(690, 1130), (1425, 1130)])
    p.arrow("queue", "graph", "outcomes", dashed=True, exit=(0.9, 0), entry=(0.9, 1),
            points=[(842, 960), (1180, 960), (1180, 705), (778, 705)], pos=0.35)

    # ------------------------------------------------------------ product state transitions
    p = Page(mx, "Product state transitions", 1500, 710, "Product relationship state transitions",
             "One product relationship. Labels name the evidence that can make the change. Business rules: brief §8.")
    p.ellipse("start", "new", 60, 145, 70, 70)
    p.box("evaluating", "evaluating", 250, 140, 220, 80, "memory", center=True, size=15)
    p.box("using", "using", 680, 140, 220, 80, "memory", center=True, size=15)
    p.box("expanding", "expanding", 1110, 140, 220, 80, "memory", center=True, size=15)
    p.box("paused", "paused", 250, 440, 220, 80, "neutral", center=True, size=15)
    p.box("rejected", "rejected", 680, 440, 220, 80, "code", center=True, size=15)
    p.box("discontinued", "discontinued", 1110, 440, 220, 80, "code", center=True, size=15)
    p.arrow("start", "evaluating", "confirmed intent\nor CRM opportunity", straight=True)
    p.arrow("evaluating", "using", "operational record only", straight=True)
    p.arrow("using", "expanding", "operational record, or\nconfirmed intent with scope", straight=True)
    p.arrow("evaluating", "paused", "confirmed QBR\nor CRM update", straight=True, exit=(0.25, 1), entry=(0.25, 0), pos=-0.45)
    p.arrow("paused", "evaluating", "new confirmed intent\nor explicit request", straight=True, exit=(0.75, 0), entry=(0.75, 1), pos=-0.45)
    p.arrow("evaluating", "rejected", "confirmed statement\nwith reason", straight=True, exit=(1, 1), entry=(0, 0.3), pos=-0.45)
    p.arrow("paused", "rejected", "confirmed statement\nwith reason", straight=True)
    p.arrow("rejected", "evaluating", "new evidence;\nreason stays visible", dashed=True, straight=True, exit=(0.5, 0), entry=(1, 0.5), pos=-0.45)
    p.arrow("using", "discontinued", "operational record", straight=True, exit=(1, 0.8), entry=(0.3, 0))
    p.box("rules", "Rules", 60, 580, 1270, 100, "white", None,
          "Testimony-driven changes are proposed until a reviewer confirms them. If the CRM disagrees with a confirmed QBR statement, "
          "both are shown and a Discrepancy is raised. Each change is dated, cites its source and affects only this product "
          "relationship: never the platform relationship or other products. Intent or clickstream alone never moves a relationship to using.")

    # ------------------------------------------------------------ QBR continuity workflow
    p = Page(mx, "QBR continuity workflow", 2240, 900, "QBR continuity: absence before review",
             "The decisive demonstration (brief §15). Jordan saves a note and becomes unavailable; Priya completes the follow-up without contacting Jordan.")
    lanes = [("l-orig", "Originating rep · Jordan", "source"), ("l-sys", "Team queue · system", "step"),
             ("l-cover", "Covering rep · Priya", "agent"), ("l-lead", "Team lead", "work")]
    for i, (cid, t, k) in enumerate(lanes):
        p.lane(cid, t, 25, 90 + i * 170, 2190, 170, k)
    Y = {cid: 90 + i * 170 + 45 for i, (cid, _, _) in enumerate(lanes)}
    W, H = 190, 80
    def step(cid, title, col, lane, desc=None, kind="white", dashed=False):
        p.box(cid, title, 90 + col * 230, Y[lane], W, H, kind, None, desc, dashed=dashed, size=12)
    step("w1", "Save QBR note", 0, "l-orig", "Salesforce-style note")
    step("w2", "Create review item", 1, "l-sys", "Team, deadline, status pending")
    step("w3", "Extract candidate takeaways", 2, "l-sys", "May fail or find none; stays pending")
    p.ellipse("w-away", "Unavailable", 90 + 3 * 230 + 25, Y["l-orig"] + 5, 140, 70)
    step("w4", "Activate coverage", 3, "l-lead", "Priya covers Jordan")
    step("w5", "Offer reassignment", 4, "l-sys", "With source context and history")
    step("w6", "Acknowledge ownership", 5, "l-cover", "Handoff complete only now")
    step("w7", "Validate takeaways", 6, "l-cover", "Confirm, correct, or no action needed")
    step("w8", "Approve and execute", 7, "l-cover", "Actions with owner and due date")
    step("w9", "Close with evidence", 8, "l-sys", "Completion evidence required")
    step("w-esc", "Escalation", 4, "l-lead", "Not acknowledged by deadline", kind="code")
    p.arrow("w1", "w2", "saved", exit=(0.5, 1), entry=(0, 0.5))
    p.arrow("w2", "w3", "", straight=True)
    p.arrow("w1", "w-away", "then", straight=True, dashed=True)
    p.arrow("w-away", "w4", "reported", exit=(0.5, 1), entry=(0.5, 0), pos=-0.7)
    p.arrow("w3", "w5", "candidates", straight=True, pos=-0.55)
    p.arrow("w4", "w5", "coverage", exit=(0.8, 0), entry=(0.2, 1), pos=-0.6)
    p.arrow("w5", "w6", "")
    p.arrow("w6", "w7", "", straight=True)
    p.arrow("w7", "w8", "", straight=True)
    p.arrow("w8", "w9", "evidence")
    p.arrow("w5", "w-esc", "no acknowledgment\nby deadline", dashed=True, straight=True, exit=(0.8, 1), entry=(0.8, 0), pos=0.3)
    p.box("w-rules", "Rules", 90, 790, 2120, 80, "white", None,
          "Notification alone never completes a handoff. A QBR whose extraction fails or yields nothing stays pending until a reviewer "
          "resolves it. Assignment records keep created_by separate from assigned_to, so revoking Jordan's access removes retrieval rights, not records.")

    ET.indent(mx)
    ET.ElementTree(mx).write(OUT / "solution-design.drawio", encoding="utf-8", xml_declaration=True)


def memory_architecture():
    mx = ET.Element("mxfile", {"host": "app.diagrams.net"})

    # ------------------------------------------------------------ memory types and scopes
    p = Page(mx, "Memory types and scopes", 1600, 800, "Memory types and federated scopes",
             "Left: what is remembered and how it moves between types. Right: who can retrieve it. Details: memory-architecture.md §2–3.")
    p.group("g-types", "Memory types", 25, 90, 900, 640, "memory")
    p.box("working", "Working memory", 50, 140, 400, 120, "agent", "session and task store",
          "Draft brief, unresolved candidates, context bundle. Expires on approval, disposition or timeout.")
    p.box("episodic", "Episodic memory", 50, 340, 400, 120, "step", "graph and source spans",
          "QBRs, experience observations, intents, product decisions, action outcomes. Durable.")
    p.box("semantic", "Semantic memory", 50, 540, 400, 140, "memory", "graph",
          "Confirmed identities, affiliations, product relationships and states, capabilities, current intent. Versioned; superseded, never overwritten.")
    p.box("procedural", "Procedural memory", 500, 140, 400, 120, "code", "versioned Markdown",
          "Approved QBR-preparation and follow-up procedure; intent taxonomy version.")
    p.box("assoc", "Associative recall", 500, 400, 400, 180, "neutral", "typed graph traversal",
          "From the subject, follow addresses, targets, considersAlternative and supersedes links. Embedding search proposes candidate spans; graph links confirm them.")
    p.arrow("working", "episodic", "extraction and reviewer validation", straight=True)
    p.arrow("episodic", "semantic", "validated promotion", straight=True)
    p.arrow("procedural", "working", "governs", straight=True)
    p.arrow("assoc", "episodic", "traverses", straight=True, exit=(0, 0.3), entry=(1, 0.5))
    p.arrow("assoc", "semantic", "traverses", straight=True, exit=(0, 0.8), entry=(1, 0.4))
    p.group("g-scopes", "Memory scopes (federated)", 950, 90, 625, 640, "neutral")
    p.box("s-org", "Organization", 970, 135, 585, 525, "white", "procedures, taxonomy, catalog")
    p.box("s-team", "Team", 1000, 200, 525, 330, "work", "QBRs, takeaways, actions, coverage")
    p.box("s-rel", "Relationship (firm or advisor)", 1030, 265, 465, 175, "source",
          "profile, product relationships, experience, intent, assets")
    p.box("s-session", "Session", 1060, 335, 405, 80, "agent", "working memory for one brief")
    p.box("s-role", "Role-restricted", 1000, 550, 525, 90, "code", "asset definitions, compliance review notes")
    p.text("scope-note", "Derived summaries, caches, embeddings and handoff payloads inherit the most restrictive scope of their inputs. "
           "Access is enforced at retrieval and traversal, before anything reaches model context.", 25, 740, 1550, 44, 13, color="#444444")

    # ------------------------------------------------------------ write path
    p = Page(mx, "Write path and promotion", 1640, 640, "Memory write path and promotion",
             "Nothing reaches semantic memory without provenance and validation. Details: memory-architecture.md §4–6.")
    chain = [("p1", "Source preserved", "import version recorded"), ("p2", "Identifiers and dates validated", None),
             ("p3", "Identity reconciled", "no merge on similar names"), ("p4", "Candidate extracted", "working → episodic"),
             ("p5", "Reviewer validation", "confirm, correct or reject"), ("p6", "Promoted with provenance", "semantic; valid and recorded time"),
             ("p7", "Affected recommendations revalidated", None)]
    for i, (cid, t, s) in enumerate(chain):
        p.box(cid, t, 30 + i * 230, 120, 200, 100, "memory" if cid == "p6" else "step", s, center=True)
        if i:
            p.arrow(chain[i - 1][0], cid, straight=True)
    outcomes = [("o1", "Same subject and target", "supersedes the earlier fact; earlier fact kept with dates"),
                ("o2", "Repeats an earlier span", "quotes link to the original; not new evidence"),
                ("o3", "Conflicts with an authoritative field", "Discrepancy raised; field unchanged"),
                ("o4", "Rejected", "kept as a disputed candidate with reason")]
    for i, (cid, t, d) in enumerate(outcomes):
        p.box(cid, t, 240 + i * 300, 330, 270, 110, "neutral", None, d)
        p.arrow("p5", cid, "", exit=(0.5, 1), entry=(0.5, 0))
    p.text("wp-note", "Re-importing the same source version creates no new facts. As-of queries return facts valid at the date and recorded on or before it.",
           30, 480, 1580, 40, 13, color="#444444")

    # ------------------------------------------------------------ context assembly
    p = Page(mx, "Context assembly", 1620, 660, "Context assembly for one brief",
             "Bounded, cited, access-scoped. Details: memory-architecture.md §8.")
    p.box("c-req", "Request", 30, 270, 210, 110, "source", None, "Subject, review date, requesting user")
    p.box("c-acc", "Access filter", 290, 270, 210, 110, "work", None, "Restrict to the user's scopes before retrieval")
    p.box("c-pin", "Pinned facts", 560, 110, 230, 110, "memory", None, "Identity, product relationships with current state, open commitments and actions")
    p.box("c-span", "Span retrieval", 560, 270, 230, 110, "step", None, "Statement-level QBR spans and catalog entries for target products")
    p.box("c-trav", "Graph traversal", 560, 430, 230, 110, "memory", None, "Linked experience, intent and supersession history")
    p.box("c-asof", "As-of filter", 850, 270, 210, 110, "neutral", None, "Valid at D and recorded by D")
    p.box("c-bundle", "Context bundle", 1110, 270, 210, 110, "agent", None, "At most 12k tokens; every item cited")
    p.box("c-agent", "QBR assistant", 1370, 270, 210, 110, "agent", None, "Drafts brief and actions")
    p.box("c-excl", "Excluded and reported", 1110, 470, 470, 90, "code", None,
          "Unauthorized records (never shown), superseded facts unless history is requested, incompatible metrics")
    p.arrow("c-req", "c-acc", straight=True)
    p.arrow("c-acc", "c-pin", exit=(0.5, 0), entry=(0, 0.5))
    p.arrow("c-acc", "c-span", straight=True)
    p.arrow("c-acc", "c-trav", exit=(0.5, 1), entry=(0, 0.5))
    p.arrow("c-pin", "c-asof", exit=(1, 0.5), entry=(0.3, 0))
    p.arrow("c-span", "c-asof", straight=True)
    p.arrow("c-trav", "c-asof", exit=(1, 0.5), entry=(0.3, 1))
    p.arrow("c-asof", "c-bundle", straight=True)
    p.arrow("c-bundle", "c-agent", straight=True)
    p.arrow("c-asof", "c-excl", "", dashed=True, exit=(0.7, 1), entry=(0, 0.5))

    # ------------------------------------------------------------ agent handoff contract
    p = Page(mx, "Agent handoff contract", 1600, 900, "Phase 3: specialist agents and the evidence contract",
             "Specialists are kept only if measured quality or operational benefit justifies their cost. Details: memory-architecture.md §7.")
    p.box("h-orch", "Orchestrating assistant", 620, 110, 360, 90, "agent", None, "Owns the brief; dispatches bounded tasks")
    p.box("h-prof", "Profile and metric checker", 80, 320, 360, 100, "agent", None, "Identity, qualifications versus registration, AUM/AUA scope")
    p.box("h-prod", "Product comparison", 620, 320, 360, 100, "agent", None, "Catalog-grounded comparison; unknown stays unknown")
    p.box("h-exp", "Experience and intent follow-up", 1160, 320, 360, 100, "agent", None, "Service issues, intent changes, open commitments")
    p.arrow("h-orch", "h-prof", "task + contract", exit=(0, 0.5), entry=(0.5, 0))
    p.arrow("h-orch", "h-prod", "task + contract", straight=True)
    p.arrow("h-orch", "h-exp", "task + contract", exit=(1, 0.3), entry=(0.5, 0))
    p.box("h-mem", "Shared memory", 80, 520, 360, 110, "memory", "graph and source store",
          "Specialists read within their scopes; writes go through validation")
    p.arrow("h-mem", "h-prof", "scoped read", straight=True)
    contract = ("task_id · procedure_version · taxonomy_version\nsubject · product_targets\nevidence_refs (node IDs and spans, not copied text)\n"
                "claims with verification_state\naccess_scope (most restrictive of inputs)\nowner · acknowledged_at · deadline")
    p.box("h-contract", "Evidence contract", 520, 500, 560, 200, "white", "carried by every handoff, agent or human", contract)
    p.box("h-rep", "Covering rep", 1160, 520, 360, 110, "work", None, "Receives the same contract; acknowledges before owning the work")
    p.arrow("h-orch", "h-rep", "same contract", exit=(1, 0.8), entry=(0.5, 0), points=[(1560, 182), (1560, 470), (1340, 470)], pos=0.4)
    p.text("h-note", "A handoff is incomplete until the receiver acknowledges it. Claims cite evidence references rather than restating facts, "
           "so the receiver can verify them against shared memory.", 80, 740, 1440, 44, 13, color="#444444")

    ET.indent(mx)
    ET.ElementTree(mx).write(OUT / "memory-architecture.drawio", encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    solution_design()
    memory_architecture()
    print("wrote", OUT)
