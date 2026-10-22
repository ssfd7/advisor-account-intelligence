"""Promotion of validated takeaways into graph memory (architecture.md §3).

- valid time is when the statement was made; recorded time is when a reviewer confirmed it;
- supersession is scoped to the same speaker and product target;
- a confirmed state that disagrees with the CRM raises a Discrepancy; neither record is overwritten.
"""
from datetime import date

from .graph import Graph


def product_relationship(g: Graph, party: str, party_label: str, product: str) -> str:
    pr = f"PR:{party}:{product}"
    g.node("ProductRelationship", pr)
    g.link(party_label, party, "hasProductRelationship", "ProductRelationship", pr)
    g.link("ProductRelationship", pr, "forProduct", "ProductOffering", product)
    return pr


def add_state(g: Graph, sid: str, pr: str, state: str, source_type: str, valid_from: date, recorded_at: date,
              source: tuple = None, at: date = None):
    """Write a dated state record, link it to the record it supersedes and raise discrepancies with other sources."""
    if g.one("MATCH (s:ProductStateRecord {id: $id}) RETURN s.id AS id", id=sid):
        return
    previous = g.one("""MATCH (s:ProductStateRecord)-[:stateOf]->(:ProductRelationship {id: $pr})
                        WHERE s.validFrom <= $vf AND s.recordedAt <= $ra
                        RETURN s.id AS id, s.state AS state, s.sourceType AS source ORDER BY s.validFrom DESC, s.recordedAt DESC LIMIT 1""",
                     pr=pr, vf=valid_from, ra=recorded_at)
    g.node("ProductStateRecord", sid, state=state, sourceType=source_type, verificationState="validated",
           validFrom=valid_from, recordedAt=recorded_at)
    g.link("ProductStateRecord", sid, "stateOf", "ProductRelationship", pr)
    if source:
        g.node("SourceRecord", source[0], sourceSystem=source[1], sourceRecordId=source[2], importVersion=source[3])
        g.link("ProductStateRecord", sid, "evidencedBy", "SourceRecord", source[0])
    if previous:
        g.link("ProductStateRecord", sid, "supersedes", "ProductStateRecord", previous["id"])
    # Disagreement with the latest record from a different kind of source (for example CRM versus a confirmed QBR).
    for other in g.run("""MATCH (s:ProductStateRecord)-[:stateOf]->(:ProductRelationship {id: $pr})
                          WHERE s.sourceType <> $src AND s.state <> $state AND s.validFrom <= $vf
                          RETURN s.id AS id, s.state AS state, s.sourceType AS source ORDER BY s.validFrom DESC LIMIT 1""",
                       pr=pr, src=source_type, state=state, vf=valid_from):
        did = f"DISC:{sid}:{other['id']}"
        g.node("Discrepancy", did, description=f"{source_type} says {state}; {other['source']} still says {other['state']}",
               raisedAt=recorded_at, status="open")
        g.link("Discrepancy", did, "involves", "ProductStateRecord", sid)
        g.link("Discrepancy", did, "involves", "ProductStateRecord", other["id"])


def _comment(g: Graph, label: str, cand: dict):
    """The reviewer's comment travels with the finding into memory."""
    if cand.get("comment"):
        g.run(f"MATCH (n:{label} {{id: $id}}) SET n.reviewComment = $c", id=cand["id"], c=cand["comment"])


def promoter(g: Graph, interactions: dict):
    """Return the promote(candidate, reviewer, at) callback used by the task store."""

    def promote(cand: dict, reviewer: str, at: date):
        p, iid = cand["payload"], cand["interaction_id"]
        meta = interactions[iid]
        valid = meta["date"]
        kind = cand["kind"]
        if kind == "experience":
            g.node("ExperienceObservation", cand["id"], summary=p.get("summary") or "", affectedGroup=p.get("affected"),
                   evidenceType=p.get("evidence_type") or "testimony", validFrom=valid, recordedAt=at, verificationState="validated")
            g.link("Interaction", iid, "records", "ExperienceObservation", cand["id"])
            _comment(g, "ExperienceObservation", cand)
            g.link("ExperienceObservation", cand["id"], "concerns", "ProductOffering", p["product"])
            g.link("ExperienceObservation", cand["id"], "supportedBy", "SourceSpan", cand["span_id"])
            g.run("MATCH (e:ExperienceObservation {id: $e}), (s:Sentiment {label: $l}) MERGE (e)-[:hasSentiment]->(s)",
                  e=cand["id"], l=p.get("sentiment") or "not recorded")
            if (p.get("speaker") or "").startswith("ADV-"):
                g.link("ExperienceObservation", cand["id"], "reportedBy", "Advisor", p["speaker"])
        elif kind == "intent":
            previous = g.one("""MATCH (i:Intent)-[:targets]->(:ProductOffering {id: $t}), (i)-[:expressedBy]->(:Advisor {id: $s})
                                WHERE i.validFrom <= $vf RETURN i.id AS id ORDER BY i.validFrom DESC LIMIT 1""",
                             t=p["target"], s=p.get("speaker") or meta["advisor"], vf=valid)
            g.node("Intent", cand["id"], desiredOutcome=p.get("desired_outcome"), reasonOrBlocker=p.get("reason"),
                   validFrom=valid, recordedAt=at, verificationState="validated")
            g.link("Interaction", iid, "expresses", "Intent", cand["id"])
            _comment(g, "Intent", cand)
            g.link("Intent", cand["id"], "targets", "ProductOffering", p["target"])
            if (p.get("speaker") or "").startswith("ADV-"):
                g.link("Intent", cand["id"], "expressedBy", "Advisor", p["speaker"])
            g.link("Intent", cand["id"], "supportedBy", "SourceSpan", cand["span_id"])
            g.link("Intent", cand["id"], "classifiedAs", "IntentConcept", p["concept"])
            for alt in p.get("alternatives", []):
                g.link("Intent", cand["id"], "considersAlternative", "ProductOffering", alt)
            if previous and previous["id"] != cand["id"]:
                g.link("Intent", cand["id"], "supersedes", "Intent", previous["id"])
            if p.get("proposes_state"):
                pr = product_relationship(g, meta["firm"], "Firm", p["target"])
                add_state(g, f"PSR:{cand['id']}", pr, p["proposes_state"], "qbr", valid, at,
                          (f"salesforce:interaction:{iid}", "salesforce", iid, meta["version"]))
        elif kind == "commitment":
            g.node("Commitment", cand["id"], summary=p.get("summary") or "", dueDate=date.fromisoformat(str(p["due"])) if p.get("due") else None, status="open", recordedAt=at)
            g.link("Interaction", iid, "records", "Commitment", cand["id"])
            _comment(g, "Commitment", cand)
            g.link("Commitment", cand["id"], "madeBy", "Rep", p.get("made_by") or meta["author"])
        elif kind == "asset":  # an asset figure the advisor stated: testimony at its stated scope, never the firm's report
            g.node("AssetObservation", cand["id"], metricType=p["metric"], metricValue=float(p["value"]), currency=p["currency"],
                   scope=p["scope"], asOfDate=valid, methodology="stated by the advisor in a QBR", evidenceType="testimony",
                   recordedAt=at)
            g.link("AssetObservation", cand["id"], "measures", "Firm", meta["firm"])
            _comment(g, "AssetObservation", cand)
            g.link("AssetObservation", cand["id"], "reportedBy", "Advisor", p["speaker"])
            g.link("AssetObservation", cand["id"], "supportedBy", "SourceSpan", cand["span_id"])
        elif kind == "commitment_status":
            g.run("MATCH (c:Commitment {id: $id}) SET c.status = $s", id=p["commitment"], s=p["status"])

    return promote


def write_action(g: Graph):
    def write(action: dict, approver: str, at: date, run_id: str = None):
        due = action["due"] if isinstance(action["due"], date) else date.fromisoformat(str(action["due"]))
        g.node("Action", action["id"], title=action["title"], actionStatus="approved", dueDate=due, recordedAt=at)
        if run_id:
            g.link("Action", action["id"], "partOfRun", "ProcedureRun", run_id)
        g.link("Action", action["id"], "arisesFrom", "Interaction", action["interaction_id"])
        g.link("Action", action["id"], "ownedByTeam", "Team", action["team"])
        g.link("Action", action["id"], "createdBy", "Rep", action["created_by"])
        g.link("Action", action["id"], "approvedBy", "Rep", approver)
        g.link("Action", action["id"], "concerns", "ProductOffering", action["product"])
        for label, oid in action["addresses"]:  # pairs, or lists after a JSON round trip
            g.link("Action", action["id"], "addresses", label, oid)
        for prq in action.get("requires", []):
            g.link("Action", action["id"], "requires", "Prerequisite", prq)
        for c in action.get("fulfils", []):
            g.link("Action", action["id"], "fulfils", "Commitment", c)
    return write


def write_completion(g: Graph):
    def write(aid: str, evidence: str, at: date):
        g.run("MATCH (a:Action {id: $id}) SET a.actionStatus = 'completed'", id=aid)
        sid = f"tasks:completion:{aid}"
        g.node("SourceRecord", sid, sourceSystem="task store", sourceRecordId=evidence, importVersion=str(at))
        g.link("Action", aid, "evidencedBy", "SourceRecord", sid)
    return write
