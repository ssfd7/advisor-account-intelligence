# Phase 1 demo: absence before review

A runnable slice of the [product brief](../business/advisor-account-intelligence-product.md) with no LLM. Synthetic Snowflake and Salesforce exports are loaded into a LadybugDB graph with provenance and two kinds of time, a mock task store holds the team queue, and a narrated script plays the decisive scenario: Jordan saves the March QBR and goes on leave; Priya, the covering rep, finds it, takes ownership, validates the takeaways and completes the follow-up without contacting Jordan.

```bash
python3 -m venv .venv && .venv/bin/pip install -r solution/requirements.txt
cd solution
../.venv/bin/python -m aai.demo          # narrated scenario; rebuilds solution/.data/ each run
../.venv/bin/python -m pytest -q         # golden cases (20 tests)
```

## What the scenario shows

| Step | Shows | Brief |
|---|---|---|
| 1. Ingest | Second import of the same files adds nothing. Maya Chen and May Chen (similarity 0.94, different CRD) are kept separate and flagged for a steward | FR1, FR7 |
| 2. Profile | Affiliation history (Harbor Point, then Cedar Ridge); Series 65 passed; **no registration record → shown as a gap**, never as "authorized" | CQ1, FR2 |
| 3. Assets | $300M firm-reported AUM and $180M Platform A AUA are listed; a total is refused for three stated reasons; product-level assets unknown | CQ3, FR3 |
| 4. Absence | After Jordan's leave both Cedar Ridge review items show `UNOWNED` but stay in the team queue; the February email has only a repeated quote and stays pending; Priya cannot review without authority | CQ6, FR11 |
| 5. Coverage | The lead activates coverage; offers and notifications go out, but Priya still cannot act until she acknowledges; a retried acknowledgment creates nothing new | FR12, FR7 |
| 6. As-of, before review | Known on 19 March: Service B `evaluating` (CRM); the March statement is not yet validated memory | CQ2, FR5 |
| 7. Review | Priya validates the three March candidates under her acknowledged assignment | WF3 |
| 8. As-of, after review | Service B `paused` from the confirmed QBR, **with a discrepancy against the CRM's pilot-ready stage**; Custody Service A and Service A still `using`. Two independent interactions report investor statement problems; the email only repeats January. Intent `postponing` supersedes `exploring`; the January commitment is still open | CQ2, CQ4, FR4, FR10 |
| 9. Actions | Catalog says Service B integration is **unknown**. Two proposed actions, each with product, what it addresses, source spans, prerequisite (PRQ-001) and the open commitment it fulfils; no adoption pitch for a paused product | CQ5, FR6, FR9 |
| 10. Escalation | The email review Priya never acknowledged escalates to the lead, who closes it as "no action needed" with a reason | WF4 |
| 11. Completion | Closing without evidence is refused; with evidence the action closes and the evidence is written to the graph; the integration review stays open in the queue | FR12 |
| 12. Access | Priya's request about May Chen (Northfield) is refused before retrieval; Omar on the Northfield team sees Northfield's own Service B state | FR8 |

## How it is built

| Path | Contents |
|---|---|
| `data/snowflake/` | Advisors, firms, affiliations, qualifications, registrations, platform relationships, product holdings and asset observations as CSV |
| `data/salesforce/` | Four interaction notes (two Cedar Ridge QBRs, one forwarded email, one Northfield QBR), CRM opportunity stages, and candidate takeaways per interaction |
| `data/reference/` | Product catalog, seed intent taxonomy and team roster |
| `aai/graph.py` | LadybugDB schema; node and relationship tables use the names in [model/aai-model.ttl](model/aai-model.ttl) |
| `aai/ingest.py` | Loads every source with a `SourceRecord` and import version; MERGE on stable identifiers; locates each candidate's exact span and links repetitions with `quotes` |
| `aai/memory.py` | Promotion of validated candidates: valid time from the statement, recorded time from the review, scoped supersession, discrepancies between sources |
| `aai/tasks.py` | Mock task store (SQLite): review items, candidates, actions, assignments, coverage, availability and an event log, with the authority, acknowledgment, escalation and evidence rules |
| `aai/queries.py` | Competency-question answers scoped to the requesting rep, with `valid_at` and `known_at` |
| `aai/demo.py` | The narrated scenario |
| `tests/test_golden.py` | Golden cases from brief §13 |

Stand-ins, to be replaced in later steps of the interview-plan build:

- **Extraction.** Candidate takeaways are fixtures in `data/salesforce/extractions/`, one file per interaction; a missing file means extraction failed and the review item simply stays pending. An LLM extractor would write the same format.
- **The assistant.** `propose_actions` is a rule set, not a model. It demonstrates the evidence contract a model's proposals must meet: target product, addressed observation or intent, source spans, prerequisites and commitments.
- **Clock.** Dates are passed explicitly so the scenario is reproducible.

## Golden cases covered

Covered by `tests/test_golden.py`: duplicate imports; similar names; exam passed with registration unknown; AUM and AUA not totalled; missing capability marked unknown; repeated quote not independent; extraction with nothing new stays pending; unauthorized firm excluded; absent author leaves work visible but unowned; notification does not complete a handoff; retried handoff not duplicated; as-of answer excludes later facts; pausing Service B leaves other products unchanged; CRM disagreement raises a discrepancy; advisor-reported dissatisfaction attributed to the advisor; missing follow-up stays open; actions cite sources and do not pitch a paused product; missed deadline escalates; closing requires evidence; records survive the author's absence.

Not yet covered: a previously rejected product (no fixture), changed evidence before approval triggering revalidation, instructions embedded in a QBR note (needs the LLM extractor), and an advisor who changes firm *during* the review period.

## Findings for the model

Building against `aai-model.ttl` exposed three points for the model README's open decisions:

- **A platform reports assets.** Platform A reports the AUA, but in the model `reportedBy` ranges over Party, and Platform is not a Party. The graph allows `AssetObservation → reportedBy → Platform`; the model should either make Platform a kind of Party or widen the range.
- **Assignment and Coverage live in the task store.** They are concepts in the model; in phase 1 they are operational records outside the graph, and only outcomes (actions, completion evidence) are written back. The model should say which store is authoritative for them.
- **Code lists as properties.** Product State, Metric Type and Affected Group are stored as codes on records rather than as nodes; Intent Concept is a node because supersession and taxonomy versioning need to traverse it.
