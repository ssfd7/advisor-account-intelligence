"""Answers to the competency questions, scoped to what the requesting rep may see.

`valid_at` is the date the answer is about; `known_at` is the latest recorded time allowed, so an as-of answer
excludes facts learned later.
"""
from datetime import date

from .graph import Graph
from .roster import Roster


class OutOfScope(Exception):
    pass


def _check(roster: Roster, user: str, party: str):
    if party not in roster.scope(user):
        raise OutOfScope(f"{party} is not assigned to any team of {user}; no records retrieved")


# ------------------------------------------------------------ CQ1, CQ2: profile and product state

def product_state(g: Graph, roster: Roster, user: str, party: str, product: str, valid_at: date, known_at: date) -> dict:
    _check(roster, user, party)
    pr = f"PR:{party}:{product}"
    records = g.run("""MATCH (s:ProductStateRecord)-[:stateOf]->(:ProductRelationship {id: $pr})
                       WHERE s.validFrom <= $va AND s.recordedAt <= $ka AND s.verificationState = 'validated'
                       RETURN s.id AS id, s.state AS state, s.sourceType AS source, s.validFrom AS validFrom, s.recordedAt AS recordedAt
                       ORDER BY s.validFrom DESC, s.recordedAt DESC""", pr=pr, va=valid_at, ka=known_at)
    discrepancies = g.run("""MATCH (x:Discrepancy)-[:involves]->(s:ProductStateRecord)-[:stateOf]->(:ProductRelationship {id: $pr})
                             WHERE x.raisedAt <= $ka RETURN DISTINCT x.id AS id, x.description AS description""", pr=pr, ka=known_at)
    if not records:
        return {"product": product, "state": "unknown", "source": None, "since": None, "history": [], "discrepancies": [],
                "discrepancy_ids": []}
    top = records[0]
    return {"product": product, "state": top["state"], "source": top["source"], "since": top["validFrom"],
            "history": records, "discrepancies": [x["description"] for x in discrepancies],
            "discrepancy_ids": [x["id"] for x in discrepancies]}


def profile(g: Graph, roster: Roster, user: str, advisor: str, valid_at: date, known_at: date) -> dict:
    _check(roster, user, advisor)
    adv = g.one("MATCH (a:Advisor {id: $id}) RETURN a.name AS name, a.crd AS crd", id=advisor)
    affiliations = g.run("""MATCH (f:Affiliation)-[:ofAdvisor]->(:Advisor {id: $id}), (f)-[:withFirm]->(firm:Firm)
                            WHERE f.recordedAt <= $ka
                            RETURN firm.id AS firm, firm.name AS name, f.role AS role, f.validFrom AS validFrom, f.validTo AS validTo
                            ORDER BY f.validFrom""", id=advisor, ka=known_at)
    current = [a for a in affiliations if a["validFrom"] <= valid_at and (a["validTo"] is None or a["validTo"] >= valid_at)]
    quals = g.run("""MATCH (q:Qualification)-[:heldBy]->(:Advisor {id: $id}) WHERE q.recordedAt <= $ka
                     RETURN q.examName AS exam, q.result AS result, q.resultDate AS date ORDER BY q.resultDate""", id=advisor, ka=known_at)
    regs = g.run("""MATCH (r:Registration)-[:registers]->(:Advisor {id: $id}) WHERE r.recordedAt <= $ka
                    RETURN r.registrationType AS type, r.registrationStatus AS status, r.statusDate AS date""", id=advisor, ka=known_at)
    gaps = [] if regs else ["No registration record for this advisor: current registration status is unknown. "
                            "Exam results do not establish registration or eligibility."]
    products, platforms = [], []
    for a in current:
        platforms += g.run("""MATCH (p:PlatformRelationship)-[:ofParty]->(:Firm {id: $f}), (p)-[:withPlatform]->(pl:Platform)
                              WHERE p.validFrom <= $va AND p.recordedAt <= $ka
                              RETURN pl.name AS platform, p.status AS status, p.validFrom AS since""", f=a["firm"], va=valid_at, ka=known_at)
        for r in g.run("""MATCH (:Firm {id: $f})-[:hasProductRelationship]->(pr)-[:forProduct]->(o:ProductOffering)
                          RETURN o.id AS id, o.name AS name ORDER BY o.id""", f=a["firm"]):
            s = product_state(g, roster, user, a["firm"], r["id"], valid_at, known_at)
            products.append({"firm": a["name"], "product": r["name"], **{k: s[k] for k in ("state", "source", "since", "discrepancies")}})
    return {"advisor": adv, "affiliations": affiliations, "current_firms": [a["name"] for a in current],
            "qualifications": quals, "registrations": regs, "gaps": gaps, "platforms": platforms, "products": products}


# ------------------------------------------------------------ CQ3: assets

def assets(g: Graph, roster: Roster, user: str, party: str, known_at: date) -> list:
    _check(roster, user, party)
    return g.run("""MATCH (o:AssetObservation)-[:measures]->(t {id: $p}), (o)-[:reportedBy]->(rep)
                    WHERE o.recordedAt <= $ka
                    RETURN o.id AS id, o.metricType AS metric, o.metricValue AS value, o.currency AS currency,
                           o.scope AS scope, o.asOfDate AS asOf, rep.id AS reporter, o.methodology AS methodology
                    ORDER BY o.asOfDate""", p=party, ka=known_at)


def combine_assets(observations: list) -> dict:
    """Totals or shares are allowed only when metric type, scope, currency and as-of date all match."""
    reasons = []
    for key, label in (("metric", "metric types"), ("scope", "scopes"), ("currency", "currencies"), ("asOf", "as-of dates")):
        values = {o[key] for o in observations}
        if len(values) > 1:
            reasons.append(f"different {label}: " + " vs ".join(map(str, values)))
    if reasons:
        return {"allowed": False, "reasons": reasons}
    return {"allowed": True, "total": sum(o["value"] for o in observations)}


def capability(g: Graph, product: str, text: str) -> dict:
    """Catalog-grounded capability lookup: undocumented means unknown, never absent or present."""
    found = g.run("""MATCH (:ProductOffering {id: $p})-[:hasCapability]->(c:Capability)
                     WHERE lower(c.name) CONTAINS lower($t) RETURN c.name AS name, c.catalogVersion AS version""", p=product, t=text)
    return {"product": product, "query": text, "status": "documented" if found else "unknown", "matches": found}


# ------------------------------------------------------------ CQ4: experience and intent

def experience(g: Graph, roster: Roster, user: str, firm: str, valid_at: date, known_at: date) -> list:
    _check(roster, user, firm)
    obs = g.run("""MATCH (i:Interaction)-[:withParty]->(:Firm {id: $f}), (i)-[:records]->(e:ExperienceObservation)-[:concerns]->(o:ProductOffering),
                         (e)-[:supportedBy]->(s:SourceSpan)
                   WHERE e.validFrom <= $va AND e.recordedAt <= $ka
                   OPTIONAL MATCH (e)-[:reportedBy]->(a:Advisor)
                   OPTIONAL MATCH (e)-[:hasSentiment]->(sen:Sentiment)
                   RETURN e.id AS id, o.name AS product, e.summary AS summary, e.affectedGroup AS affected, e.evidenceType AS evidence,
                          sen.label AS sentiment,
                          a.name AS reportedBy, i.id AS interaction, e.validFrom AS date,
                          s.startOffset AS spanStart, s.endOffset AS spanEnd ORDER BY e.validFrom""",
                f=firm, va=valid_at, ka=known_at)
    quoted = g.run("""MATCH (q:SourceSpan)-[:quotes]->(s:SourceSpan)-[:partOf]->(i:Interaction)-[:withParty]->(:Firm {id: $f}),
                            (q)-[:partOf]->(qi:Interaction)
                      RETURN qi.id AS by, i.id AS original, s.startOffset AS spanStart, s.endOffset AS spanEnd""", f=firm)
    for o in obs:  # repeated where a later span quotes text overlapping this observation's own span
        o["repeated_in"] = sorted({q["by"] for q in quoted if q["original"] == o["interaction"]
                                   and q["spanStart"] < o["spanEnd"] and o["spanStart"] < q["spanEnd"]})
        del o["spanStart"], o["spanEnd"]
    return obs


def intents(g: Graph, roster: Roster, user: str, firm: str, valid_at: date, known_at: date) -> list:
    """Current intent per product: the latest validated intent known at `known_at` and not superseded by then."""
    _check(roster, user, firm)
    rows = g.run("""MATCH (i:Interaction)-[:withParty]->(:Firm {id: $f}), (i)-[:expresses]->(n:Intent)-[:targets]->(o:ProductOffering),
                          (n)-[:classifiedAs]->(c:IntentConcept)
                    WHERE n.validFrom <= $va AND n.recordedAt <= $ka
                    OPTIONAL MATCH (n)-[:considersAlternative]->(alt:ProductOffering)
                    RETURN n.id AS id, o.id AS targetId, o.name AS target, c.label AS intent, n.reasonOrBlocker AS reason, n.validFrom AS date,
                           collect(alt.name) AS alternatives ORDER BY date""", f=firm, va=valid_at, ka=known_at)
    current = {}
    for r in rows:
        r["alternatives"] = r["alternatives"] or []
        current[r["target"]] = r
    return list(current.values())


def commitments(g: Graph, roster: Roster, user: str, firm: str, known_at: date) -> list:
    _check(roster, user, firm)
    rows = g.run("""MATCH (i:Interaction)-[:withParty]->(:Firm {id: $f}), (i)-[:records]->(c:Commitment)-[:madeBy]->(r:Rep)
                    WHERE c.recordedAt <= $ka
                    OPTIONAL MATCH (a:Action)-[:fulfils]->(c)
                    RETURN c.id AS id, c.summary AS summary, c.dueDate AS due, c.status AS status, r.name AS madeBy,
                           collect(a.id) AS actions""", f=firm, ka=known_at)
    for r in rows:
        r["actions"] = r["actions"] or []
    return rows


# ------------------------------------------------------------ CQ5: proposed actions (rule-based stand-in for the assistant)

def propose_actions(g: Graph, roster: Roster, user: str, firm: str, interaction: str, at: date) -> list:
    """Up to three actions, each with its target product, what it addresses, sources and prerequisites.
    Never proposes adoption of a product whose current intent is postponing or rejecting."""
    _check(roster, user, firm)
    team = roster.team_for_party(firm).id
    proposals = []  # intents first: a product decision always gets a slot
    for n in g.run("""MATCH (i:Interaction {id: $iid})-[:expresses]->(n:Intent)-[:targets]->(o:ProductOffering),
                            (n)-[:classifiedAs]->(c:IntentConcept), (n)-[:supportedBy]->(s:SourceSpan)
                      OPTIONAL MATCH (o)-[:hasPrerequisite]->(q:Prerequisite)
                      RETURN n.id AS id, o.id AS product, o.name AS name, c.label AS intent, s.id AS span, collect(q.id) AS prereqs""",
                   iid=interaction):
        open_commitments = [c["id"] for c in commitments(g, roster, user, firm, at) if c["status"] == "open"]
        promotes = n["intent"] not in ("postponing", "rejecting or discontinuing")
        if promotes:
            title = f"Supported comparison of {n['name']} against current services"
        else:
            title = f"Reporting-and-integration review with a product specialist ({n['name']}); verify prerequisites before any evaluation resumes"
        proposals.append({"id": f"ACT:{n['id']}", "interaction_id": interaction, "team": team, "created_by": user,
                          "title": title, "product": n["product"], "promotes": promotes, "addresses": [("Intent", n["id"])], "sources": [n["span"]],
                          "requires": n["prereqs"], "fulfils": open_commitments, "due": date.fromordinal(at.toordinal() + 21)})
    for e in g.run("""MATCH (e:ExperienceObservation)-[:concerns]->(o:ProductOffering), (e)-[:supportedBy]->(s:SourceSpan),
                            (i:Interaction {id: $iid})-[:records]->(e), (e)-[:hasSentiment]->(sen:Sentiment)
                      RETURN e.id AS id, o.id AS product, o.name AS name, e.summary AS summary, s.id AS span,
                             sen.followUp AS followUp""", iid=interaction):
        # the sentiment catalog decides: a negative experience is a service issue, a mixed one is clarified, others need none
        verb = {"service issue": "Open service issue", "clarify with the advisor": "Clarify the reported experience"}.get(e["followUp"])
        if not verb:
            continue
        proposals.append({"id": f"ACT:{e['id']}", "interaction_id": interaction, "team": team, "created_by": user,
                          "title": f"{verb}: {e['summary']} ({e['name']})", "product": e["product"],
                          "promotes": False, "addresses": [("ExperienceObservation", e["id"])], "sources": [e["span"]], "requires": [],
                          "fulfils": [], "due": date.fromordinal(at.toordinal() + 14)})
    return proposals[:3]
