---
type: Semantic QBR
title: 'Semantic QBR: Cedar Ridge Advisory, 2026-03-18'
description: What the QBR of 2026-03-18 says about products, assets, intent and commitments,
  linked to the catalog and tied to the advisor's words.
status: verified
interprets: INT-2026-03-QBR-CR
sources:
- id: INT-2026-03-QBR-CR
  resource: data/salesforce/interactions/INT-2026-03-QBR-CR.md
catalog_version: '2026.2'
procedure:
  resource: /procedures/qbr-understanding-and-follow-up.md
  steps:
  - 3
  - 4
review:
  owner: REP-DANA
  deadline: '2026-03-23'
  decided_by: REP-DANA
  decided_at: '2026-03-20'
  outcome: reviewed
writes:
- aai:SemanticQBR
- aai:interprets
- aai:ProductMention
- aai:foundIn
- aai:refersTo
- aai:Intent
- aai:targets
- aai:considersAlternative
- aai:classifiedAs
- aai:supersedes
- aai:supportedBy
- aai:ProductStateRecord
- aai:ExperienceObservation
- aai:concerns
- aai:reportedBy
- aai:affects
- aai:hasSentiment
- aai:Commitment
- aai:AssetObservation
- aai:measures
- aai:evidenceType
supports:
- CQ1
- CQ3
- CQ4
- CQ6
---

Decided by Dana Ortiz on 2026-03-20: reviewed. Source: `INT-2026-03-QBR-CR`.

# Product mentions

| Phrase | In the sentence | Linked to | How |
|---|---|---|---|
| CPX UMA | Maya is postponing the CPX UMA evaluation because the integration with her portfolio accounting system has not been verified. | CPX Unified Managed Account (`CPX-UMA`) | alias |
| CMP | Statements are still a problem: investors keep calling her team about the CMP quarterly statements. | Crestline Model Portfolios (`CMP`) | alias |
| Crestline custody | Crestline custody remains in active use. | Crestline Custody and Clearing (`CCC`) | alias |

# Asset figures

- **$320 million** read as `reported AUM`, scope "across all custodians", stated by the advisor (testimony, not a reported figure).
  - Rule `compare-over-time`: Two observations may be compared as a change over time only if metric type, currency and scope match.
  - Rule `total-or-share`: A total or a share is allowed only if metric type, currency, scope and as-of date all match.
  - Rule `never`: Never add AUM to AUA, never allocate a firm figure to an advisor or product, never treat an advisor's stated figure as the firm's reported figure.
  - Sentence: "Maya said Cedar Ridge's AUM is now about $320 million across all custodians."

# Findings

## CAND-03-1 · intent

> Maya is postponing the CPX UMA evaluation because the integration with her portfolio accounting system has not been verified.

- Reads as: postponing → CPX Unified Managed Account; proposes state `paused`
- Writes: aai:Intent, aai:targets, aai:considersAlternative, aai:classifiedAs, aai:supersedes, aai:supportedBy, aai:ProductStateRecord
- Decision: approved by Dana Ortiz on 2026-03-20

## CAND-03-2 · experience

> investors keep calling her team about the CMP quarterly statements

- Reads as: negative, investor group: Investors still calling about CMP statements (Crestline Model Portfolios)
- Writes: aai:ExperienceObservation, aai:concerns, aai:reportedBy, aai:affects, aai:hasSentiment, aai:supportedBy
- Decision: approved by Dana Ortiz on 2026-03-20

## CAND-03-3 · commitment status

> The specialist session promised in January has not happened yet.

- Reads as: CAND-01-4 is open
- Writes: aai:Commitment
- Decision: approved by Dana Ortiz on 2026-03-20

## DET-INT-2026-03-QBR-CR-A1 · asset

> Maya said Cedar Ridge's AUM is now about $320 million across all custodians.

- Reads as: reported AUM 320,000,000 USD, across all custodians
- Writes: aai:AssetObservation, aai:measures, aai:reportedBy, aai:supportedBy, aai:evidenceType
- Decision: rejected by Dana Ortiz: figure is approximate; ask for the ADV
