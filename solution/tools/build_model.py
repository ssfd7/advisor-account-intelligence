"""Generate the Draw.io model and Turtle ontology from model_spec.py.

    .venv/bin/python solution/tools/build_model.py

Writes solution/model/aai-model.drawio, aai-model.ttl (with steward and status per term). Layout is a deterministic
Fruchterman–Reingold pass (networkx spring_layout) per page, best of a seed search by crossing and clearance score,
followed by overlap and node-to-edge clearance relaxation. Re-running overwrites manual edits to the diagram.
"""
import math
import xml.etree.ElementTree as ET
from collections import defaultdict
from html import escape
from pathlib import Path

import networkx as nx

from model_spec import (ATTRIBUTES, CODE_LISTS, CONCEPTS, DATE, EXAMPLES, GROUPS, NS, PAGES, QUESTIONS,
                        RELATIONSHIPS, STEWARDS, VERSION)

OUT = Path(__file__).resolve().parents[1] / "model"
R = 60                      # concept circle radius
NOTE_W, LINE_H = 200, 20    # example note geometry
LEFT, TOP, RIGHT = 70, 120, 1930
PANEL_X, PANEL_W, PAGE_W = 2010, 430, 2480

NODE_STYLE = ("shape=ellipse;perimeter=ellipsePerimeter;whiteSpace=wrap;html=0;aspect=fixed;fillColor={fill};"
              "strokeColor=#666666;strokeWidth=1;fontSize=14;fontColor=#222222;spacing=8;")
EDGE_BASE = ("edgeStyle=none;html=1;rounded=0;strokeColor=#666666;strokeWidth=1.2;fontSize=14;fontColor=#333333;"
             "labelBackgroundColor=#FFFFFF;jumpStyle=arc;jumpSize=8;")
REL_STYLE = EDGE_BASE + "endArrow=classic;endSize=8;"
SUB_STYLE = EDGE_BASE + "dashed=1;endArrow=block;endFill=0;endSize=10;startArrow=none;"
NOTE_STYLE = ("shape=label;html=0;whiteSpace=wrap;fillColor=none;strokeColor=none;fontSize=13;fontStyle=1;"
              "fontColor=#444444;align=center;verticalAlign=top;spacing=0;")
TEXT_STYLE = "shape=label;html=0;fillColor=none;strokeColor=none;align=left;verticalAlign=top;whiteSpace=wrap;fontColor=#333333;spacing=10;"


# ---------------------------------------------------------------- layout

def seg_intersect(a, b, c, d):
    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])
    return (ccw(a, c, d) * ccw(b, c, d) < 0) and (ccw(a, b, c) * ccw(a, b, d) < 0)


def point_seg(p, a, b):
    ax, ay = a; bx, by = b
    L = (bx - ax) ** 2 + (by - ay) ** 2 or 1
    t = max(0, min(1, ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / L))
    q = (ax + t * (bx - ax), ay + t * (by - ay))
    return math.dist(p, q), q


def note_h(n):
    return LINE_H * n + 6


def footprint(cid, pos, examples):
    """Bounding box of a concept with its example note."""
    x, y = pos
    h = R
    if cid in examples:
        h = R + 4 + note_h(len(examples[cid]))
    w = max(R, NOTE_W / 2) if cid in examples else R
    return x - w, y - R, x + w, y + h


def edge_geometry(pos, edges, examples=None):
    """Per edge: polyline from source to target centre, label centre, and waypoints for curved parallels."""
    pairs = defaultdict(list)
    for e in edges:
        pairs[frozenset((e[0], e[2]))].append(e)
    out = []
    for s, rel, t in edges:
        if s == t:
            out.append(None)
            continue
        group = pairs[frozenset((s, t))]
        a, b = pos[s], pos[t]
        if len(group) > 1:
            k = group.index((s, rel, t))
            offset = (k - (len(group) - 1) / 2) * 90
            (x1, y1), (x2, y2) = sorted([a, b])
            L = math.dist((x1, y1), (x2, y2)) or 1
            w = ((x1 + x2) / 2 - (y2 - y1) / L * offset, (y1 + y2) / 2 + (x2 - x1) / L * offset)
            out.append(([(a, w), (w, b)], w, [w], ""))
        else:
            out.append(([(a, b)], ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 12), None, ""))
    segs = [seg for g in out if g for seg in g[0]]
    for i, (s, rel, t) in enumerate(edges):
        if s != t:
            continue
        best = None
        for side in LOOP_SIDES:
            if side == "down" and examples and s in examples:
                continue
            g = loop_geometry(pos[s], side)
            box = loop_box(pos[s], side)
            hits = sum(1 for a, b in segs if seg_hits_rect(a, b, box))
            hits += sum(2 for n, p in pos.items() if n != s and rect_overlap(box, (p[0] - R, p[1] - R, p[0] + R, p[1] + R)))
            if examples:
                hits += sum(2 for n in examples if n in pos and n != s and rect_overlap(box, note_rect(n, pos, examples)))
            if best is None or hits < best[0]:
                best = (hits, g)
        out[i] = best[1]
    return out


LOOP_SIDES = ["up", "left", "right", "down"]


def loop_geometry(p, side):
    x, y = p
    d = R + 85
    if side == "up":
        pts, lab, st = [(x - 55, y - d), (x + 55, y - d)], (x, y - d), "exitX=0.3;exitY=0.04;entryX=0.7;entryY=0.04;"
    elif side == "down":
        pts, lab, st = [(x + 55, y + d), (x - 55, y + d)], (x, y + d), "exitX=0.7;exitY=0.96;entryX=0.3;entryY=0.96;"
    elif side == "left":
        pts, lab, st = [(x - d, y + 55), (x - d, y - 55)], (x - d, y), "exitX=0.04;exitY=0.7;entryX=0.04;entryY=0.3;"
    else:
        pts, lab, st = [(x + d, y - 55), (x + d, y + 55)], (x + d, y), "exitX=0.96;exitY=0.3;entryX=0.96;entryY=0.7;"
    poly = [(p, pts[0]), (pts[0], pts[1]), (pts[1], p)]
    return poly, lab, pts, st + "exitDx=0;exitDy=0;entryDx=0;entryDy=0;"


def loop_box(p, side):
    x, y = p
    d = R + 100
    return {"up": (x - 75, y - d, x + 75, y - R), "down": (x - 75, y + R, x + 75, y + d),
            "left": (x - d, y - 75, x - R, y + 75), "right": (x + R, y - 75, x + d, y + 75)}[side]


def label_box(name, c):
    w = 7.6 * len(name) + 12
    return c[0] - w / 2, c[1] - 11, c[0] + w / 2, c[1] + 11


def rect_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def seg_hits_rect(p, q, r, pad=4):
    x0, y0, x1, y1 = r[0] - pad, r[1] - pad, r[2] + pad, r[3] + pad
    for i in range(25):
        f = i / 24
        x, y = p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f
        if x0 <= x <= x1 and y0 <= y <= y1:
            return True
    return False


def note_rect(cid, pos, examples):
    x, y = pos[cid]
    return x - NOTE_W / 2 + 15, y + R + 4, x + NOTE_W / 2 - 15, y + R + 4 + note_h(len(examples[cid]))


def score(pos, edges, examples):
    geo = edge_geometry(pos, edges, examples)
    segs = []
    for (s, _, t), (poly, _, _, _) in zip(edges, geo):
        for a, b in poly:
            segs.append((a, b, s, t))
    crossings = sum(1 for i, (a, b, s1, t1) in enumerate(segs) for (c, d, s2, t2) in segs[i + 1:]
                    if len({s1, t1, s2, t2}) == 4 and seg_intersect(a, b, c, d))
    near = 0
    for n, p in pos.items():
        for a, b, s, t in segs:
            if n not in (s, t):
                d, _ = point_seg(p, a, b)
                if d < R + 30:
                    near += 1
    notes = {n: note_rect(n, pos, examples) for n in examples if n in pos}
    note_hits = sum(1 for a, b, s, t in segs for n, r in notes.items() if seg_hits_rect(a, b, r))
    labels = [label_box(rel, c) for (_, rel, _), (_, c, _, _) in zip(edges, geo)]
    label_hits = sum(1 for i, a in enumerate(labels) for b in labels[i + 1:] if rect_overlap(a, b))
    circles = [(p[0] - R, p[1] - R, p[0] + R, p[1] + R) for p in pos.values()]
    label_hits += sum(1 for lb in labels for r in circles + list(notes.values()) if rect_overlap(lb, r))
    return crossings * 10 + near * 6 + note_hits * 25 + label_hits * 10


def relax(pos, edges, examples, bottom, iterations=400):
    pos = {k: list(v) for k, v in pos.items()}
    ids = list(pos)
    segs = [(s, t) for s, _, t in edges if s != t]
    for _ in range(iterations):
        moved = False
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                ax0, ay0, ax1, ay1 = footprint(a, pos[a], examples)
                bx0, by0, bx1, by1 = footprint(b, pos[b], examples)
                m = 60
                ox = min(ax1, bx1) - max(ax0, bx0) + m
                oy = min(ay1, by1) - max(ay0, by0) + m
                if ox > 0 and oy > 0:
                    dx, dy = pos[b][0] - pos[a][0], pos[b][1] - pos[a][1]
                    if ox < oy:
                        s = (ox / 2 + 1) * (1 if dx >= 0 else -1)
                        pos[a][0] -= s; pos[b][0] += s
                    else:
                        s = (oy / 2 + 1) * (1 if dy >= 0 else -1)
                        pos[a][1] -= s; pos[b][1] += s
                    moved = True
        for n in ids:
            for s, t in segs:
                if n in (s, t):
                    continue
                d, q = point_seg(pos[n], pos[s], pos[t])
                if d < R + 35:
                    vx, vy = pos[n][0] - q[0], pos[n][1] - q[1]
                    L = math.hypot(vx, vy) or 1
                    push = (R + 36 - d) / 2
                    pos[n][0] += vx / L * push; pos[n][1] += vy / L * push
                    moved = True
        for n in ids:
            pos[n][0] = min(max(pos[n][0], LEFT + R + 40), RIGHT - R - 40)
            pos[n][1] = min(max(pos[n][1], TOP + R + 20), bottom - R - 80)
        if not moved:
            break
    return {k: (round(v[0]), round(v[1])) for k, v in pos.items()}


def layout(nodes, edges, examples, height, seed_base, seeds=250):
    G = nx.Graph()
    G.add_nodes_from(nodes)
    for s, _, t in edges:
        if s != t:
            G.add_edge(s, t)
    best = None
    w, h = RIGHT - LEFT - 2 * R - 120, height - TOP - 2 * R - 160
    for k in range(seeds):
        seed = seed_base + k
        raw = nx.spring_layout(G, seed=seed, k=2.2 / math.sqrt(len(nodes)), iterations=300)
        xs = [p[0] for p in raw.values()]; ys = [p[1] for p in raw.values()]
        sx = w / ((max(xs) - min(xs)) or 1); sy = h / ((max(ys) - min(ys)) or 1)
        pos = {n: (LEFT + R + 60 + (p[0] - min(xs)) * sx, TOP + R + 40 + (p[1] - min(ys)) * sy) for n, p in raw.items()}
        pos = relax(pos, edges, examples, height)
        sc = score(pos, edges, examples)
        if best is None or sc < best[0]:
            best = (sc, seed, pos)
    return best


# ---------------------------------------------------------------- drawio

def cell(container, **attrs):
    geo = attrs.pop("geometry", None)
    points = attrs.pop("points", None)
    c = ET.SubElement(container, "mxCell", {k: str(v) for k, v in attrs.items()})
    if geo is not None:
        g = ET.SubElement(c, "mxGeometry", {k: str(v) for k, v in geo.items()})
        g.set("as", "geometry")
        if points:
            arr = ET.SubElement(g, "Array", {"as": "points"})
            for x, y in points:
                ET.SubElement(arr, "mxPoint", {"x": str(round(x)), "y": str(round(y))})
    return c


def cq_height(text):
    return 24 * (math.ceil(len(text) / 44) + 1) + 18


def panel(root, page_name, cqs, overview, groups_used, height):
    y0 = 110
    items = []
    y = y0 + 20
    items.append(("cq-heading", "Competency questions", y, 40, 21, True)); y += 52
    for q in cqs:
        txt = f"{q}\n{QUESTIONS[q]}"
        h = cq_height(QUESTIONS[q])
        items.append((f"cq-{q}", txt, y, h, 17, False)); y += h
    y += 14
    items.append(("legend-heading", "Legend", y, 40, 21, True)); y += 52
    legend_y = y
    gl = [g for g in GROUPS if g in groups_used]
    rows = math.ceil(len(gl) / 2)
    y += rows * 48 + 8
    note = ("Solid arrow: relationship\nDashed + hollow triangle: subclassOf\nRounded jump: crossing, not a junction\n"
            + ("Synthetic data examples appear on the detail pages" if overview else "[Bold bracketed text]: synthetic data examples"))
    items.append(("notation", note, y, 125, 15, False)); y += 130
    cell(root, id="right-panel", value="", style="shape=rectangle;rounded=1;fillColor=#F8FAFC;strokeColor=#D9E1E8;",
         vertex="1", parent="1", geometry={"x": PANEL_X, "y": y0, "width": PANEL_W, "height": y - y0 + 10})
    for cid, txt, yy, h, fs, bold in items:
        cell(root, id=cid, value=txt, style=TEXT_STYLE + f"fontSize={fs};" + ("fontStyle=1;" if bold else ""),
             vertex="1", parent="1", geometry={"x": PANEL_X + 20, "y": yy, "width": PANEL_W - 45, "height": h})
    for i, g in enumerate(gl):
        label, fill = GROUPS[g]
        cell(root, id=f"legend-{g}", value=label,
             style=f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor=#999999;fontSize=12;fontColor=#333333;",
             vertex="1", parent="1",
             geometry={"x": PANEL_X + 30 + (i % 2) * 190, "y": legend_y + (i // 2) * 48, "width": 175, "height": 32})
    return y + 20


def page_xml(mxfile, idx, name, cqs, edges, examples, overview):
    nodes = sorted({s for s, _, _ in edges} | {t for _, _, t in edges}, key=list(CONCEPTS).index)
    height = max(1400, int(260 * math.sqrt(len(nodes)) * 1.55)) if not overview else 2500
    sc, seed, pos = layout(nodes, edges, examples, height, 100 * (idx + 1), seeds=120 if overview else 500)
    d = ET.SubElement(mxfile, "diagram", {"id": f"page-{idx:02d}", "name": name})
    model = ET.SubElement(d, "mxGraphModel", {"dx": "1536", "dy": "702", "grid": "1", "gridSize": "10", "guides": "1",
                                               "tooltips": "1", "connect": "1", "arrows": "1", "fold": "1", "page": "1",
                                               "pageScale": "1", "pageWidth": str(PAGE_W), "pageHeight": str(height),
                                               "background": "#FFFFFF", "math": "0", "shadow": "0",
                                               "lineJumpsEnabled": "1"})
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    cell(root, id="title", value=f"{name} — draft v{VERSION}",
         style="shape=label;fillColor=none;strokeColor=none;html=1;align=left;fontSize=24;fontStyle=1;fontColor=#222222;",
         vertex="1", parent="1", geometry={"x": 40, "y": 20, "width": 1700, "height": 40})
    for n in nodes:
        label, _, group, _ = CONCEPTS[n]
        x, y = pos[n]
        cell(root, id=n, value=label, style=NODE_STYLE.format(fill=GROUPS[group][1]), vertex="1", parent="1",
             geometry={"x": x - R, "y": y - R, "width": 2 * R, "height": 2 * R})
        if n in examples:
            lines = examples[n]
            cell(root, id=f"example-{n}", value="\n".join(f"[{e}]" for e in lines), style=NOTE_STYLE, vertex="1",
                 parent="1", geometry={"x": x - NOTE_W / 2, "y": y + R + 4, "width": NOTE_W, "height": note_h(len(lines))})
    for i, ((s, rel, t), (_, _, points, loop)) in enumerate(zip(edges, edge_geometry(pos, edges, examples))):
        style = SUB_STYLE if rel == "subclassOf" else REL_STYLE
        geo = {"relative": "1"}
        if s == t:
            style += "curved=1;" + loop
        elif points:
            style += "curved=1;"
        else:
            style += "curved=0;"
            geo["y"] = "-12"
        cell(root, id=f"e{i}", value=rel, style=style, edge="1", parent="1", source=s, target=t,
             geometry=geo, points=points)
    groups_used = {CONCEPTS[n][2] for n in nodes}
    panel(root, name, cqs, overview, groups_used, height)
    return name, seed, sc, len(nodes), len(edges)


def build_drawio():
    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net"})
    overview_edges = []
    for _, _, edges in PAGES:
        for e in edges:
            if e not in overview_edges:
                overview_edges.append(e)
    report = [page_xml(mxfile, 0, "00 Model overview", list(QUESTIONS), overview_edges, {}, True)]
    for i, (name, cqs, edges) in enumerate(PAGES, 1):
        report.append(page_xml(mxfile, i, name, cqs, edges, EXAMPLES.get(name, {}), False))
    ET.indent(mxfile)
    path = OUT / "aai-model.drawio"
    ET.ElementTree(mxfile).write(path, encoding="utf-8", xml_declaration=True)
    return report


# ---------------------------------------------------------------- turtle

def lit(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"@en'


def camel(s):
    parts = [p for p in s.replace("-", " ").split() if p]
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:]) if parts else s


def union(names):
    names = sorted(set(names))
    return names[0] if len(names) == 1 else "[ a owl:Class ; owl:unionOf ( " + " ".join(names) + " ) ]"


def build_turtle():
    cls = {k: f"aai:{v[1]}" for k, v in CONCEPTS.items()}
    all_edges = [e for _, _, es in PAGES for e in es]
    lines = [
        f"@prefix aai:     <{NS}> .",
        "@prefix owl:     <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        "@prefix skos:    <http://www.w3.org/2004/02/skos/core#> .",
        "@prefix prov:    <http://www.w3.org/ns/prov#> .",
        "@prefix vann:    <http://purl.org/vocab/vann/> .",
        "",
        "#################################################################",
        "# Ontology header",
        "#################################################################",
        "",
        f"<{NS[:-1]}> a owl:Ontology ;",
        f"    dcterms:title {lit('Advisor Account Intelligence ontology')} ;",
        f"    dcterms:description {lit('Structural semantic model of advisors, firms, platforms, product relationships, QBR interactions, experience, intent and team-owned follow-up work. Formal counterpart of aai-model.drawio.')} ;",
        f'    dcterms:created "{DATE}"^^xsd:date ;',
        f'    dcterms:modified "{DATE}"^^xsd:date ;',
        f'    owl:versionInfo "{VERSION}" ;',
        f"    owl:versionIRI <{NS[:-1]}/{VERSION}> ;",
        '    vann:preferredNamespacePrefix "aai" ;',
        f'    vann:preferredNamespaceUri "{NS}" .',
        "",
        "#################################################################",
        "# Reused external terms (declared, not imported)",
        "#################################################################",
        "",
        "skos:Concept a owl:Class .",
        "skos:ConceptScheme a owl:Class .",
        "prov:Entity a owl:Class .",
        "skos:inScheme a owl:ObjectProperty .",
        "skos:definition a owl:AnnotationProperty .",
        "skos:prefLabel a owl:AnnotationProperty .",
        "dcterms:title a owl:AnnotationProperty .",
        "dcterms:description a owl:AnnotationProperty .",
        "dcterms:created a owl:AnnotationProperty .",
        "dcterms:modified a owl:AnnotationProperty .",
        "vann:preferredNamespacePrefix a owl:AnnotationProperty .",
        "vann:preferredNamespaceUri a owl:AnnotationProperty .",
        "",
        "aai:steward a owl:AnnotationProperty ;",
        f"    rdfs:label {lit('steward')} ;",
        f"    skos:definition {lit('The team accountable for the meaning of a term and for approving changes to it.')} .",
        "",
        "aai:termStatus a owl:AnnotationProperty ;",
        f"    rdfs:label {lit('termStatus')} ;",
        f"    skos:definition {lit('Where a term stands in its lifecycle: proposed, reviewed or released.')} .",
        "",
        "#################################################################",
        "# Classes",
        "#################################################################",
        "",
    ]
    supers = defaultdict(list)
    for s, r, t in all_edges:
        if r == "subclassOf" and cls[t] not in supers[s]:
            supers[s].append(cls[t])
    extra_super = {"productState": "skos:Concept", "metricType": "skos:Concept", "affectedGroup": "skos:Concept",
                   "intentConcept": "skos:Concept", "taxonomyVersion": "skos:ConceptScheme",
                   "sourceRecord": "prov:Entity", "span": "prov:Entity"}
    for k, (label, name, group, definition) in CONCEPTS.items():
        lines.append(f"aai:{name} a owl:Class ;")
        for sp in supers[k]:
            lines.append(f"    rdfs:subClassOf {sp} ;")
        if k in extra_super:
            lines.append(f"    rdfs:subClassOf {extra_super[k]} ;")
        lines.append(f"    rdfs:label {lit(label)} ;")
        lines.append(f"    skos:definition {lit(definition)} .")
        lines.append("")
    lines += ["aai:Advisor owl:disjointWith aai:Firm .", "aai:Rep owl:disjointWith aai:Party .", ""]
    lines += ["#################################################################",
              "# Object properties (relationships on the diagram)",
              "#################################################################", ""]
    doms, rngs = defaultdict(list), defaultdict(list)
    for s, r, t in all_edges:
        if r != "subclassOf":
            doms[r].append(cls[s]); rngs[r].append(cls[t])
    functional = {"ofAdvisor", "heldBy", "ofParty", "withPlatform", "forProduct", "stateOf", "hasState", "partOf",
                  "hasMetricType", "classifiedAs", "inTaxonomy", "arisesFrom", "assignedTo", "coversFor", "coveredBy",
                  "createdBy", "authoredBy", "interprets", "foundIn", "follows", "startedBy"}
    for r in RELATIONSHIPS:
        if r not in doms:
            continue
        lines.append(f"aai:{r} a owl:ObjectProperty{' , owl:FunctionalProperty' if r in functional else ''} ;")
        lines.append(f"    rdfs:label {lit(r)} ;")
        lines.append(f"    rdfs:domain {union(doms[r])} ;")
        lines.append(f"    rdfs:range {union(rngs[r])} ;")
        lines.append(f"    skos:definition {lit(RELATIONSHIPS[r])} .")
        lines.append("")
    lines += ["#################################################################",
              "# Data properties (attributes; not on the diagram)",
              "#################################################################", ""]
    for a, (ds, xt, definition) in ATTRIBUTES.items():
        lines.append(f"aai:{a} a owl:DatatypeProperty ;")
        lines.append(f"    rdfs:label {lit(a)} ;")
        lines.append(f"    rdfs:domain {union([cls[d] for d in ds])} ;")
        lines.append(f"    rdfs:range xsd:{xt} ;")
        lines.append(f"    skos:definition {lit(definition)} .")
        lines.append("")
    lines += ["#################################################################",
              "# Code lists",
              "#################################################################", ""]
    for k, members in CODE_LISTS.items():
        scheme = f"aai:{CONCEPTS[k][1]}Scheme"
        if k == "intentConcept":
            scheme = "aai:IntentTaxonomyV1"
            lines.append(f"{scheme} a aai:TaxonomyVersion ;")
            lines.append(f"    skos:prefLabel {lit('Intent taxonomy, seed version 1')} .")
        else:
            lines.append(f"{scheme} a skos:ConceptScheme ;")
            lines.append(f"    skos:prefLabel {lit(CONCEPTS[k][0] + ' codes')} .")
        lines.append("")
        for m in members:
            lines.append(f"aai:{CONCEPTS[k][1]}_{camel(m)} a {cls[k]} ;")
            lines.append(f"    skos:prefLabel {lit(m)} ;")
            if k == "intentConcept":
                lines.append(f'    aai:conceptId "INT-{members.index(m) + 1:02d}" ;')
                lines.append(f"    aai:inTaxonomy {scheme} ;")
            lines.append(f"    skos:inScheme {scheme} .")
            lines.append("")
    gov = ["#################################################################",
           "# Steward and lifecycle status (all terms proposed in v" + VERSION + ")",
           "#################################################################", ""]
    for k, (_, name, group, _) in CONCEPTS.items():
        gov.append(f'aai:{name} aai:steward "{STEWARDS[group]}" ; aai:termStatus "proposed" .')
    for r in RELATIONSHIPS:
        if r in doms:
            gov.append(f'aai:{r} aai:steward "Data stewardship" ; aai:termStatus "proposed" .')
    for a in ATTRIBUTES:
        gov.append(f'aai:{a} aai:steward "Data stewardship" ; aai:termStatus "proposed" .')
    (OUT / "aai-model.ttl").write_text("\n".join(lines + gov) + "\n")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, seed, sc, n, e in build_drawio():
        print(f"{name}: {n} concepts, {e} connectors, seed {seed}, score {sc}")
    build_turtle()
    print("wrote", OUT)
