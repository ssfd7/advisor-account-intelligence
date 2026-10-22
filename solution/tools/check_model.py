"""Structural checks for the Draw.io model and its Turtle counterpart (AGENTS.md "Review before delivery").

    .venv/bin/python solution/tools/check_model.py
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from rdflib import OWL, RDF, RDFS, Graph, Namespace

MODEL = Path(__file__).resolve().parents[1] / "model"
AAI = Namespace("https://w3id.org/aai/ontology#")
failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


pages = {}
for d in ET.parse(MODEL / "aai-model.drawio").getroot().findall("diagram"):
    cells = list(d.iter("mxCell"))
    ids = [c.get("id") for c in cells]
    check(len(ids) == len(set(ids)), f"{d.get('name')}: duplicate cell ids")
    by_id = {c.get("id"): c for c in cells}
    concepts = {c.get("id"): c.get("value") for c in cells if "ellipse" in (c.get("style") or "")}
    rels = set()
    for c in cells:
        if c.get("edge"):
            s, t, v = c.get("source"), c.get("target"), c.get("value")
            check(s in concepts and t in concepts, f"{d.get('name')}: edge {c.get('id')} has a missing endpoint")
            check(bool(v) and "/" not in v, f"{d.get('name')}: edge {c.get('id')} needs exactly one name")
            if v == "subclassOf":
                st = c.get("style")
                check("dashed=1" in st and "endArrow=block" in st and "endFill=0" in st,
                      f"{d.get('name')}: subclassOf {c.get('id')} style")
            rels.add((concepts.get(s), v, concepts.get(t)))
    check(any(c.get("id") == "right-panel" for c in cells), f"{d.get('name')}: no right-side panel")
    check(any(c.get("id") == "legend-heading" for c in cells), f"{d.get('name')}: no legend")
    examples = [c for c in cells if (c.get("id") or "").startswith("example-")]
    if d.get("name").startswith("00"):
        check(not examples, "overview must not carry examples")
    for e in examples:
        check(all(line.startswith("[") and line.endswith("]") for line in e.get("value").split("\n")),
              f"{d.get('name')}: example {e.get('id')} not bracketed")
    pages[d.get("name")] = (set(concepts.values()), rels)

names = list(pages)
overview = pages[names[0]]
union_c = set().union(*(pages[n][0] for n in names[1:]))
union_r = set().union(*(pages[n][1] for n in names[1:]))
check(overview[0] == union_c, f"overview concepts differ from union: {overview[0] ^ union_c}")
check(overview[1] == union_r, f"overview relationships differ from union: {overview[1] ^ union_r}")

g = Graph()
g.parse(MODEL / "aai-model.ttl")
labels = {str(o): s for s, o in g.subject_objects(RDFS.label)}
classes = {str(g.value(c, RDFS.label)) for c in g.subjects(RDF.type, OWL.Class) if str(c).startswith(str(AAI))}
check(classes == overview[0], f"Turtle classes differ from overview: {classes ^ overview[0]}")
props = {str(g.value(p, RDFS.label)) for p in g.subjects(RDF.type, OWL.ObjectProperty) if str(p).startswith(str(AAI))}
diagram_props = {r for _, r, _ in overview[1] if r != "subclassOf"}
check(props == diagram_props, f"Turtle object properties differ from diagram: {props ^ diagram_props}")
subs = {(str(g.value(s, RDFS.label)), str(g.value(o, RDFS.label))) for s, o in g.subject_objects(RDFS.subClassOf)
        if str(o).startswith(str(AAI))}
diagram_subs = {(s, t) for s, r, t in overview[1] if r == "subclassOf"}
check(subs == diagram_subs, f"Turtle subclass axioms differ from diagram: {subs ^ diagram_subs}")
terms = [s for s in set(g.subjects(RDF.type, None)) if str(s).startswith(str(AAI))
         and (s, RDF.type, OWL.Class) in g or (s, RDF.type, OWL.ObjectProperty) in g or (s, RDF.type, OWL.DatatypeProperty) in g]
missing = [s for s in terms if str(s).startswith(str(AAI)) and (s, AAI.steward, None) not in g]
check(not missing, f"terms without steward: {missing}")
undefined = [s for s in terms if str(s).startswith(str(AAI)) and (s, Namespace("http://www.w3.org/2004/02/skos/core#").definition, None) not in g]
check(not undefined, f"terms without definition: {undefined}")

print(f"{len(names)} pages; overview {len(overview[0])} concepts, {len(overview[1])} connectors; "
      f"Turtle {len(g)} triples, {len(classes)} classes, {len(props)} object properties")
if failures:
    print("FAILED:\n- " + "\n- ".join(failures))
    sys.exit(1)
print("All structural checks passed.")
