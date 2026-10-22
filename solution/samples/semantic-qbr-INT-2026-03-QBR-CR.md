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
  decided_by: REP-RIA
  decided_at: '2026-03-21'
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
- aai:reviewComment
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

Decided by Ria Patel on 2026-03-21: reviewed. Source: `INT-2026-03-QBR-CR`.

# Note

The note as saved. Each finding's sentence is in bold and links to the finding below; hover it to see what it says and its status.

> Quarterly review with Maya Chen, Cedar Ridge Advisory.
>
> **[Maya is postponing the CPX UMA evaluation because the integration with her portfolio accounting system has not been verified.](#cand-03-1 "Intent: postponing → CPX Unified Managed Account; proposes state paused. Approved by Dana Ortiz on 2026-03-20. Click to review.")** `CAND-03-1`
>
> Statements are still a problem: **[investors keep calling her team about the CMP quarterly statements](#cand-03-2 "Experience: negative, investor group: Investors still calling about CMP statements (Crestline Model Portfolios). Approved by Dana Ortiz on 2026-03-20; comment: 'Same complaint as January; check the explainer reached investors'. Click to review.")** `CAND-03-2`.
>
> Crestline custody remains in active use.
>
> **[The specialist session promised in January has not happened yet.](#cand-03-3 "Commitment status: CAND-01-4 is open. Approved by Dana Ortiz on 2026-03-20. Click to review.")** `CAND-03-3`
>
> **[Maya said Cedar Ridge's AUM is now about $320 million across all custodians.](#det-int-2026-03-qbr-cr-a1 "Asset: reported AUM 320,000,000 USD, across all custodians. Escalated by Dana Ortiz: 'Stated $320M differs from the firm's reported $300M; decide whether it enters memory as her statement'; approved by Ria Patel on 2026-03-21; comment: 'Accept as her statement: it stays testimony, never merged with reported AUM'. Click to review.")** `DET-INT-2026-03-QBR-CR-A1`

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

<a id="cand-03-1"></a>

## CAND-03-1 · intent

> Maya is postponing the CPX UMA evaluation because the integration with her portfolio accounting system has not been verified.

- Reads as: postponing → CPX Unified Managed Account; proposes state `paused`
- Writes: aai:Intent, aai:targets, aai:considersAlternative, aai:classifiedAs, aai:supersedes, aai:supportedBy, aai:ProductStateRecord, aai:reviewComment
- Decision: approved by Dana Ortiz on 2026-03-20

[Back to the note](#note)

<a id="cand-03-2"></a>

## CAND-03-2 · experience

> investors keep calling her team about the CMP quarterly statements

- Reads as: negative, investor group: Investors still calling about CMP statements (Crestline Model Portfolios)
- Writes: aai:ExperienceObservation, aai:concerns, aai:reportedBy, aai:affects, aai:hasSentiment, aai:supportedBy, aai:reviewComment
- Decision: approved by Dana Ortiz on 2026-03-20; comment: "Same complaint as January; check the explainer reached investors"

[Back to the note](#note)

<a id="cand-03-3"></a>

## CAND-03-3 · commitment status

> The specialist session promised in January has not happened yet.

- Reads as: CAND-01-4 is open
- Writes: aai:Commitment
- Decision: approved by Dana Ortiz on 2026-03-20

[Back to the note](#note)

<a id="det-int-2026-03-qbr-cr-a1"></a>

## DET-INT-2026-03-QBR-CR-A1 · asset

> Maya said Cedar Ridge's AUM is now about $320 million across all custodians.

- Reads as: reported AUM 320,000,000 USD, across all custodians
- Writes: aai:AssetObservation, aai:measures, aai:reportedBy, aai:supportedBy, aai:evidenceType, aai:reviewComment
- Decision: escalated by Dana Ortiz: "Stated $320M differs from the firm's reported $300M; decide whether it enters memory as her statement"; approved by Ria Patel on 2026-03-21; comment: "Accept as her statement: it stays testimony, never merged with reported AUM"

[Back to the note](#note)
