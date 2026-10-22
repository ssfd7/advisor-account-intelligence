"""LadybugDB schema and query helpers. Table and relationship names follow solution/model/aai-model.ttl."""
import shutil
from pathlib import Path

import real_ladybug as lb

NODES = [
    "Advisor(id STRING PRIMARY KEY, name STRING, crd STRING, sourceRef STRING)",
    "Firm(id STRING PRIMARY KEY, name STRING, secFileNumber STRING, sourceRef STRING)",
    "Platform(id STRING PRIMARY KEY, name STRING)",
    "Affiliation(id STRING PRIMARY KEY, role STRING, validFrom DATE, validTo DATE, recordedAt DATE)",
    "Qualification(id STRING PRIMARY KEY, examName STRING, result STRING, resultDate DATE, recordedAt DATE)",
    "Registration(id STRING PRIMARY KEY, registrationType STRING, registrationStatus STRING, statusDate DATE, recordedAt DATE)",
    "PlatformRelationship(id STRING PRIMARY KEY, status STRING, validFrom DATE, validTo DATE, recordedAt DATE)",
    "ProductOffering(id STRING PRIMARY KEY, name STRING, alias STRING, productCategory STRING, catalogVersion STRING, validFrom DATE)",
    "Capability(id STRING PRIMARY KEY, name STRING, catalogVersion STRING, validFrom DATE)",
    "Prerequisite(id STRING PRIMARY KEY, name STRING)",
    "ProductRelationship(id STRING PRIMARY KEY)",
    "ProductStateRecord(id STRING PRIMARY KEY, state STRING, sourceType STRING, verificationState STRING, validFrom DATE, recordedAt DATE)",
    "Discrepancy(id STRING PRIMARY KEY, description STRING, raisedAt DATE, status STRING)",
    "AssetObservation(id STRING PRIMARY KEY, metricType STRING, metricValue DOUBLE, currency STRING, scope STRING, asOfDate DATE, methodology STRING, evidenceType STRING, recordedAt DATE, reviewComment STRING)",
    "SourceRecord(id STRING PRIMARY KEY, sourceSystem STRING, sourceRecordId STRING, importVersion STRING)",
    "Interaction(id STRING PRIMARY KEY, kind STRING, interactionDate DATE, recordedAt DATE, path STRING)",
    "SourceSpan(id STRING PRIMARY KEY, spanText STRING, startOffset INT64, endOffset INT64)",
    "ExperienceObservation(id STRING PRIMARY KEY, summary STRING, affectedGroup STRING, evidenceType STRING, validFrom DATE, recordedAt DATE, verificationState STRING, reviewComment STRING)",
    "Intent(id STRING PRIMARY KEY, desiredOutcome STRING, reasonOrBlocker STRING, validFrom DATE, recordedAt DATE, verificationState STRING, reviewComment STRING)",
    "IntentConcept(id STRING PRIMARY KEY, label STRING, taxonomyVersion INT64)",
    "Sentiment(id STRING PRIMARY KEY, label STRING, followUp STRING, catalogVersion STRING)",
    "Commitment(id STRING PRIMARY KEY, summary STRING, dueDate DATE, status STRING, recordedAt DATE, reviewComment STRING)",
    "Action(id STRING PRIMARY KEY, title STRING, actionStatus STRING, dueDate DATE, recordedAt DATE)",
    "Rep(id STRING PRIMARY KEY, name STRING)",
    "Team(id STRING PRIMARY KEY, name STRING)",
    "SemanticQBR(id STRING PRIMARY KEY, approvalStatus STRING, dueDate DATE, recordedAt DATE, path STRING)",
    "ProductMention(id STRING PRIMARY KEY, phrase STRING, linkMethod STRING)",
    "Procedure(id STRING PRIMARY KEY, name STRING, procedureVersion STRING)",
    "ProcedureRun(id STRING PRIMARY KEY, startedAt DATE)",
]
EVIDENCED = ["Affiliation", "Qualification", "Registration", "PlatformRelationship", "ProductStateRecord",
             "AssetObservation", "Capability", "Action", "Prerequisite"]
RELS = [
    "ofAdvisor(FROM Affiliation TO Advisor)",
    "withFirm(FROM Affiliation TO Firm, FROM Registration TO Firm)",
    "heldBy(FROM Qualification TO Advisor)",
    "registers(FROM Registration TO Advisor, FROM Registration TO Firm)",
    "ofParty(FROM PlatformRelationship TO Firm, FROM PlatformRelationship TO Advisor)",
    "withPlatform(FROM PlatformRelationship TO Platform)",
    "evidencedBy(" + ", ".join(f"FROM {t} TO SourceRecord" for t in EVIDENCED) + ")",
    "offers(FROM Platform TO ProductOffering)",
    "hasCapability(FROM ProductOffering TO Capability)",
    "hasPrerequisite(FROM ProductOffering TO Prerequisite)",
    "hasProductRelationship(FROM Firm TO ProductRelationship, FROM Advisor TO ProductRelationship)",
    "forProduct(FROM ProductRelationship TO ProductOffering)",
    "stateOf(FROM ProductStateRecord TO ProductRelationship)",
    "supersedes(FROM ProductStateRecord TO ProductStateRecord, FROM Intent TO Intent)",
    "involves(FROM Discrepancy TO ProductStateRecord)",
    "measures(FROM AssetObservation TO Firm, FROM AssetObservation TO Advisor, FROM AssetObservation TO Platform, FROM AssetObservation TO ProductOffering)",
    "reportedBy(FROM AssetObservation TO Firm, FROM AssetObservation TO Platform, FROM AssetObservation TO Advisor, FROM ExperienceObservation TO Advisor)",
    "withParty(FROM Interaction TO Firm, FROM Interaction TO Advisor)",
    "partOf(FROM SourceSpan TO Interaction)",
    "quotes(FROM SourceSpan TO SourceSpan)",
    "records(FROM Interaction TO ExperienceObservation, FROM Interaction TO Commitment)",
    "expresses(FROM Interaction TO Intent)",
    "concerns(FROM ExperienceObservation TO ProductOffering, FROM Action TO ProductOffering)",
    "supportedBy(FROM ExperienceObservation TO SourceSpan, FROM Intent TO SourceSpan, FROM AssetObservation TO SourceSpan)",
    "expressedBy(FROM Intent TO Advisor)",
    "targets(FROM Intent TO ProductOffering)",
    "considersAlternative(FROM Intent TO ProductOffering)",
    "classifiedAs(FROM Intent TO IntentConcept)",
    "hasSentiment(FROM ExperienceObservation TO Sentiment)",
    "ownedByTeam(FROM Interaction TO Team, FROM Action TO Team)",
    "authoredBy(FROM Interaction TO Rep)",
    "arisesFrom(FROM Action TO Interaction)",
    "addresses(FROM Action TO ExperienceObservation, FROM Action TO Intent)",
    "fulfils(FROM Action TO Commitment)",
    "requires(FROM Action TO Prerequisite)",
    "createdBy(FROM Action TO Rep)",
    "approvedBy(FROM Action TO Rep, FROM SemanticQBR TO Rep)",
    "madeBy(FROM Commitment TO Rep)",
    "memberOf(FROM Rep TO Team)",
    "ledBy(FROM Team TO Rep)",
    "interprets(FROM SemanticQBR TO Interaction)",
    "contains(FROM SemanticQBR TO ProductMention)",
    "foundIn(FROM ProductMention TO SourceSpan)",
    "refersTo(FROM ProductMention TO ProductOffering)",
    "follows(FROM ProcedureRun TO Procedure)",
    "startedBy(FROM ProcedureRun TO SemanticQBR)",
    "partOfRun(FROM Action TO ProcedureRun)",
]
# Product State, Metric Type and Affected Group are code lists; they are stored as codes on the records.


class Graph:
    def __init__(self, path: Path, fresh: bool = False):
        path = Path(path)
        if fresh and path.exists():
            shutil.rmtree(path) if path.is_dir() else path.unlink()
        path.parent.mkdir(parents=True, exist_ok=True)
        new = not path.exists()
        self.db = lb.Database(str(path))
        self.conn = lb.Connection(self.db)
        if new:
            for n in NODES:
                self.conn.execute(f"CREATE NODE TABLE {n}")
            for r in RELS:
                self.conn.execute(f"CREATE REL TABLE {r}")

    def run(self, cypher: str, **params):
        result = self.conn.execute(cypher, params)
        cols = result.get_column_names()
        rows = []
        while result.has_next():
            rows.append(dict(zip(cols, result.get_next())))
        return rows

    def one(self, cypher: str, **params):
        rows = self.run(cypher, **params)
        return rows[0] if rows else None

    def node(self, table: str, key: str, **props):
        sets = ", ".join(f"n.{k} = $p_{k}" for k in props)
        self.run(f"MERGE (n:{table} {{id: $key}})" + (f" SET {sets}" if sets else ""), key=key,
                 **{f"p_{k}": v for k, v in props.items()})

    def link(self, src_label: str, src: str, rel: str, dst_label: str, dst: str):
        self.run(f"MATCH (a:{src_label} {{id: $a}}), (b:{dst_label} {{id: $b}}) MERGE (a)-[:{rel}]->(b)", a=src, b=dst)

    def counts(self) -> dict:
        nodes = sum(r["c"] for r in self.run("MATCH (n) RETURN count(n) AS c"))
        rels = sum(r["c"] for r in self.run("MATCH ()-[r]->() RETURN count(r) AS c"))
        return {"nodes": nodes, "relationships": rels}
