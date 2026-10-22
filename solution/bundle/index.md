---
okf_version: "0.2"
ontology: { prefix: aai, namespace: "https://w3id.org/aai/ontology#", resource: ../model/aai-model.ttl }
---

# Procedures

* [QBR understanding and follow-up](procedures/qbr-understanding-and-follow-up.md) - Turn a QBR note into approved knowledge and owned follow-up.

# Computations

* [Product state as of a date](computations/product-state.md) - The confirmed state of one product relationship, with discrepancies.
* [Advisor profile](computations/profile.md) - Affiliations, exams, registrations and gaps, kept apart.
* [Asset observations](computations/asset-observations.md) - AUM and AUA at their evidenced scope, and whether they may be combined.
* [Catalog capability check](computations/capability-check.md) - Documented, or unknown; never assumed.
* [Reported experience](computations/experience.md) - Experience per product, with speaker, affected group and repetitions.
* [Current intent](computations/current-intent.md) - The latest confirmed intent per product, as of a date.
* [Open commitments](computations/open-commitments.md) - Promises made to the advisor and the actions that fulfil them.
* [Proposed follow-up actions](computations/proposed-actions.md) - Up to three actions grounded in approved findings.

# Tools

* [Detect concepts](tools/detect-concepts.md) - Link product mentions to the catalog and find asset figures.
* [Extract candidate findings](tools/extract-findings.md) - Experience, intent and commitments, each with its exact sentence.
* [Draft the semantic QBR](tools/draft-semantic-qbr.md) - Write the draft OKF concept for SME review.
* [Approve the semantic QBR](tools/approve-semantic-qbr.md) - The SME confirms or rejects each finding.
* [Hydrate memory](tools/hydrate.md) - Write approved knowledge to the graph and start the follow-up run.
* [Approve or dismiss an action](tools/approve-action.md) - The owner decides each proposed step.
* [Complete an action](tools/complete-action.md) - Close a step with evidence.
* [Activate coverage](tools/activate-coverage.md) - Offer an absent rep's work to a colleague.

# References

* [Graph mapping](references/mappings/graph.yaml) - Where instances of ontology terms live in the graph. Generated from `aai/graph.py`.
