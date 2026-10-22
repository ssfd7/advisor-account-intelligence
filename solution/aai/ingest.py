"""Load the synthetic fixtures into graph memory and the task store (pipeline steps 1–6).

Every write is a MERGE on a stable identifier, so re-importing the same files adds nothing. Identities are matched on
registry identifiers (CRD, SEC file number), never on name similarity; similar names are reported for a data steward.
"""
import csv
import difflib
import hashlib
from datetime import date
from pathlib import Path

import yaml

from . import DATA
from .graph import Graph
from .memory import add_state, product_relationship
from .pipeline import add_asset_candidates, approve, draft, follow_up
from .tasks import TaskStore

CRM_STAGE = {"discovery": "evaluating", "pilot ready": "evaluating", "won": "using", "lost": "rejected"}


def d(value):
    return date.fromisoformat(value) if value else None


def version(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def rows(path: Path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def source(g: Graph, system: str, table: str, key: str, ver: str) -> str:
    sid = f"{system}:{table}:{key}"
    g.node("SourceRecord", sid, sourceSystem=system, sourceRecordId=key, importVersion=ver)
    return sid


def party_label(pid: str) -> str:
    return "Advisor" if pid.startswith("ADV-") else "Firm" if pid.startswith("FIRM-") else "Platform"


def parse_interaction(path: Path):
    text = path.read_text()
    _, front, body = text.split("---\n", 2)
    meta = yaml.safe_load(front)
    meta["date"], meta["recorded_at"] = d(str(meta["date"])), d(str(meta["recorded_at"]))
    meta["version"], meta["path"] = version(path), str(path)
    return meta, body


def load(g: Graph, store: TaskStore, data: Path = DATA, extractions: str = "extractions") -> dict:
    """`extractions` names the folder of candidate takeaways: the fixtures, or `extractions-llm` from aai.llm."""
    sf, crm, ref = data / "snowflake", data / "salesforce", data / "reference"
    report = {"identity": []}

    # Reference: catalog, taxonomy, roster
    cat_path = ref / "catalog.yaml"
    catalog, cv = yaml.safe_load(cat_path.read_text()), version(cat_path)
    for p in catalog["platforms"]:
        g.node("Platform", p["id"], name=p["name"])
    for o in catalog["offerings"]:
        g.node("ProductOffering", o["id"], name=o["name"], productCategory=o["category"], alias=", ".join(o.get("aliases", [])),
               catalogVersion=catalog["catalog_version"], validFrom=o["valid_from"])
        g.link("Platform", o["platform"], "offers", "ProductOffering", o["id"])
        for c in o.get("capabilities", []):
            g.node("Capability", c["id"], name=c["name"], catalogVersion=catalog["catalog_version"], validFrom=c["valid_from"])
            g.link("ProductOffering", o["id"], "hasCapability", "Capability", c["id"])
            g.link("Capability", c["id"], "evidencedBy", "SourceRecord", source(g, "catalog", "capability", c["id"], cv))
        for q in o.get("prerequisites", []):
            g.node("Prerequisite", q["id"], name=q["name"])
            g.link("ProductOffering", o["id"], "hasPrerequisite", "Prerequisite", q["id"])
    taxonomy = yaml.safe_load((ref / "taxonomy.yaml").read_text())
    concept_ids = {}
    for c in taxonomy["concepts"]:
        g.node("IntentConcept", c["id"], label=c["label"], taxonomyVersion=taxonomy["version"])
        concept_ids[c["label"]] = c["id"]
    for rid, name in store.roster.reps.items():
        g.node("Rep", rid, name=name)
    for t in store.roster.teams.values():
        g.node("Team", t.id, name=t.name)
        g.link("Team", t.id, "ledBy", "Rep", t.lead)
        for m in t.members:
            g.link("Rep", m, "memberOf", "Team", t.id)

    # Profiles (Snowflake export)
    ver = {p.name: version(p) for p in sf.glob("*.csv")}
    advisors = rows(sf / "advisors.csv")
    for a in advisors:
        g.node("Advisor", a["advisor_id"], name=a["full_name"], crd=a["crd"], sourceRef=f"snowflake:advisors:{a['advisor_id']}")
    for i, a in enumerate(advisors):
        for b in advisors[i + 1:]:
            ratio = difflib.SequenceMatcher(None, a["full_name"].lower(), b["full_name"].lower()).ratio()
            if ratio >= 0.8:
                report["identity"].append({"a": a["advisor_id"], "b": b["advisor_id"], "names": (a["full_name"], b["full_name"]),
                                           "similarity": round(ratio, 2), "same_crd": a["crd"] == b["crd"],
                                           "decision": "merged" if a["crd"] == b["crd"] else "kept separate; steward review suggested"})
    firm_names = {}
    for f in rows(sf / "firms.csv"):
        firm_names[f["firm_id"]] = f["legal_name"]
        g.node("Firm", f["firm_id"], name=f["legal_name"], secFileNumber=f["sec_file_number"], sourceRef=f"snowflake:firms:{f['firm_id']}")
    for r in rows(sf / "affiliations.csv"):
        g.node("Affiliation", r["affiliation_id"], role=r["role"], validFrom=d(r["valid_from"]), validTo=d(r["valid_to"]),
               recordedAt=d(r["recorded_at"]))
        g.link("Affiliation", r["affiliation_id"], "ofAdvisor", "Advisor", r["advisor_id"])
        g.link("Affiliation", r["affiliation_id"], "withFirm", "Firm", r["firm_id"])
        g.link("Affiliation", r["affiliation_id"], "evidencedBy", "SourceRecord",
               source(g, "snowflake", "affiliations", r["affiliation_id"], ver["affiliations.csv"]))
    for r in rows(sf / "qualifications.csv"):
        g.node("Qualification", r["qualification_id"], examName=r["exam_name"], result=r["result"],
               resultDate=d(r["result_date"]), recordedAt=d(r["recorded_at"]))
        g.link("Qualification", r["qualification_id"], "heldBy", "Advisor", r["advisor_id"])
        g.link("Qualification", r["qualification_id"], "evidencedBy", "SourceRecord",
               source(g, "snowflake", "qualifications", r["qualification_id"], ver["qualifications.csv"]))
    for r in rows(sf / "registrations.csv"):
        g.node("Registration", r["registration_id"], registrationType=r["registration_type"], registrationStatus=r["status"],
               statusDate=d(r["status_date"]), recordedAt=d(r["recorded_at"]))
        g.link("Registration", r["registration_id"], "registers", party_label(r["party_id"]), r["party_id"])
        if r["with_firm_id"]:
            g.link("Registration", r["registration_id"], "withFirm", "Firm", r["with_firm_id"])
        g.link("Registration", r["registration_id"], "evidencedBy", "SourceRecord",
               source(g, "snowflake", "registrations", r["registration_id"], ver["registrations.csv"]))
    for r in rows(sf / "platform_relationships.csv"):
        rid = r["platform_relationship_id"]
        g.node("PlatformRelationship", rid, status=r["status"], validFrom=d(r["valid_from"]), validTo=d(r["valid_to"]),
               recordedAt=d(r["recorded_at"]))
        g.link("PlatformRelationship", rid, "ofParty", party_label(r["party_id"]), r["party_id"])
        g.link("PlatformRelationship", rid, "withPlatform", "Platform", r["platform_id"])
        g.link("PlatformRelationship", rid, "evidencedBy", "SourceRecord",
               source(g, "snowflake", "platform_relationships", rid, ver["platform_relationships.csv"]))
    for r in rows(sf / "product_holdings.csv"):
        pr = product_relationship(g, r["party_id"], party_label(r["party_id"]), r["product_id"])
        add_state(g, f"PSR:{r['holding_id']}", pr, r["status"], "operational", d(r["valid_from"]), d(r["recorded_at"]),
                  (f"snowflake:product_holdings:{r['holding_id']}", "snowflake", r["holding_id"], ver["product_holdings.csv"]))
    for r in rows(sf / "asset_observations.csv"):
        oid = r["observation_id"]
        g.node("AssetObservation", oid, metricType=r["metric_type"], metricValue=float(r["value"]), currency=r["currency"],
               scope=r["scope"], asOfDate=d(r["as_of_date"]), methodology=r["methodology"], evidenceType="reported",
               recordedAt=d(r["recorded_at"]))
        g.link("AssetObservation", oid, "measures", party_label(r["measured_party"]), r["measured_party"])
        g.link("AssetObservation", oid, "reportedBy", party_label(r["reporting_entity"]), r["reporting_entity"])
        if r["product_id"]:
            g.link("AssetObservation", oid, "measures", "ProductOffering", r["product_id"])
        g.link("AssetObservation", oid, "evidencedBy", "SourceRecord",
               source(g, "snowflake", "asset_observations", oid, ver["asset_observations.csv"]))

    # Interactions (Salesforce export), candidate takeaways and historical reviews, in date order
    interactions = {}
    bodies = {}
    for path in sorted((crm / "interactions").glob("*.md")):
        meta, body = parse_interaction(path)
        interactions[meta["interaction_id"]], bodies[meta["interaction_id"]] = meta, body
    for iid, meta in sorted(interactions.items(), key=lambda kv: kv[1]["date"]):
        g.node("Interaction", iid, kind=meta["type"], interactionDate=meta["date"], recordedAt=meta["recorded_at"], path=meta["path"])
        g.link("Interaction", iid, "withParty", "Firm", meta["firm"])
        g.link("Interaction", iid, "withParty", "Advisor", meta["advisor"])
        g.link("Interaction", iid, "authoredBy", "Rep", meta["author"])
        g.link("Interaction", iid, "ownedByTeam", "Team", meta["team"])
        store.save_interaction(iid, meta["team"], meta["author"], meta["recorded_at"])
        ext_path = crm / extractions / f"{iid}.yaml"
        if not ext_path.exists():  # extraction failed: the review item stays pending, with detection only
            add_asset_candidates(g, store, meta, bodies[iid])
            draft(store, store.roster, meta, bodies[iid], firm_names[meta["firm"]])
            continue
        ext = yaml.safe_load(ext_path.read_text())
        for c in ext.get("candidates") or []:
            start = bodies[iid].find(c["span"])
            if start < 0:  # not verbatim: never enters memory, stays visible to the reviewer
                store.add_candidate(c["id"], iid, c["kind"], {k: v for k, v in c.items() if k not in ("id", "kind")},
                                    None, rejected="span not found verbatim in the note")
                continue
            span_id = f"{iid}#{start}-{start + len(c['span'])}"
            g.node("SourceSpan", span_id, spanText=c["span"], startOffset=start, endOffset=start + len(c["span"]))
            g.link("SourceSpan", span_id, "partOf", "Interaction", iid)
            quoted = None
            for other, om in interactions.items():  # a repetition of an earlier statement is linked, not counted
                pos = bodies[other].find(c["span"])
                if other != iid and om["firm"] == meta["firm"] and om["date"] < meta["date"] and pos >= 0:
                    quoted = f"{other}#{pos}-{pos + len(c['span'])}"
                    g.node("SourceSpan", quoted, spanText=c["span"], startOffset=pos, endOffset=pos + len(c["span"]))
                    g.link("SourceSpan", quoted, "partOf", "Interaction", other)
                    g.link("SourceSpan", span_id, "quotes", "SourceSpan", quoted)
                    break
            payload = {k: v for k, v in c.items() if k not in ("id", "kind", "span")}
            if payload.get("concept"):
                payload["concept"] = concept_ids[payload["concept"]]
            store.add_candidate(c["id"], iid, c["kind"], payload, span_id, quoted)
        add_asset_candidates(g, store, meta, bodies[iid])
        review = ext.get("review")
        if review:  # historical SME approval and follow-up decisions recorded in the fixtures
            decisions = {c["id"]: "confirm" for c in store.candidates(iid, "candidate")}
            approve(g, store, store.roster, interactions, bodies, firm_names, review["by"], iid, d(str(review["at"])), decisions)
            if ext.get("follow_up"):
                f = ext["follow_up"]
                follow_up(g, store, f["by"], iid, d(str(f["at"])), f["approve"], f.get("dismiss_reason"))
        else:
            draft(store, store.roster, meta, bodies[iid], firm_names[meta["firm"]])

    # CRM opportunity stages, after the interactions they followed
    cv = version(crm / "crm_opportunities.csv")
    for r in rows(crm / "crm_opportunities.csv"):
        pr = product_relationship(g, r["party_id"], party_label(r["party_id"]), r["product_id"])
        add_state(g, f"PSR:{r['opportunity_id']}", pr, CRM_STAGE[r["stage"]], "crm", d(r["stage_date"]), d(r["recorded_at"]),
                  (f"salesforce:opportunity:{r['opportunity_id']}", "salesforce", r["opportunity_id"], cv))

    report["interactions"], report["bodies"], report["firm_names"] = interactions, bodies, firm_names
    report["counts"] = g.counts()
    return report
