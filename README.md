# Advisor Account Intelligence

**If our relationship teams knew what the firm knows, they would be far more productive.**

Salesforce holds a QBR as text. It does not know the firm's products, services or advisor intents, so what the advisor said is invisible to every system and to every colleague who did not write it. This project turns each QBR into knowledge the firm can act on: it links what the advisor said to the firm's own catalog, has an expert approve it, writes it to a governed memory, and gives every follow-up an owner. All data is synthetic; Crestline and its products are fictional.

**Status (21 October 2026):** a runnable demo plays the six takeaways below over a LadybugDB graph and a mock task store; 31 golden tests pass. Claude (`claude-opus-5-5`) can extract findings and write a cited brief that is checked before anyone sees it.

## What the business should take away

1. **The firm finally knows what its advisors tell it.** Products, services, intents and asset figures in a QBR are recognized against the firm's own catalog, including loose mentions like "their UMA".
2. **Experts stay in control.** An SME approves every finding before it changes anything; each finding is tied to the advisor's exact words.
3. **No promise falls through the cracks.** Every QBR and every follow-up has an owner and a due date, even when the rep is on leave or has left.
4. **Reps are prepared in minutes, not hours.** One page: what the advisor uses, said, wants, and what we still owe them.
5. **We stop saying the wrong thing.** No pitching a postponed product, no inflated asset figures, no overstated credentials.
6. **The value is measurable.** A pilot tracks preparation time, lost follow-ups, errors caught and SME review load against today's baseline.

## How it works

![From QBR note to owned follow-up](solution/diagrams/architecture-pipeline.png)

A note is stored when it arrives and queued for its SME. **Concept detection** links product mentions to the catalog and reads asset figures; **candidate findings** (experience, intent, commitments) are extracted with their exact sentences. Both go into a **semantic QBR**, an [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) concept in draft. The **SME approves** or rejects each finding, the one gate into memory. **Hydration** writes approved knowledge to the graph and starts a run of the follow-up procedure, whose steps are owned, dated and covered when the owner is away.

Memory is organized by type: semantic (what the firm knows), episodic (what was said and when), procedural (the OKF bundle and its runs), working (drafts in flight) and associative (linking mentions to the catalog and traversing from a finding to its follow-up). See [the architecture](solution/architecture.md).

## Run the demo

```bash
python3 -m venv .venv && .venv/bin/pip install -r solution/requirements.txt
cd solution
../.venv/bin/python -m aai.demo               # the six takeaways; no LLM; add --step to pause between sections
../.venv/bin/python -m pytest -q              # golden tests
../.venv/bin/python -m aai.bundle check       # OKF bundle and semantic QBRs against the ontology
```

| Section | What you see |
|---|---|
| 1. The firm knows | "CPX UMA", "CMP", "Crestline custody" and Northfield's "their UMA" linked to the catalog; "separate accounts" left unresolved; "$320 million" read as stated AUM with its scope; Maya Chen and May Chen kept apart |
| 2. Experts in control | The review waits for the SME, not the absent author; a rep and the team lead are refused; Dana approves with a comment and escalates the $320M figure to the data steward, who decides it the next day; after approval, the CPX UMA is paused with a discrepancy against the CRM, and the as-of view before approval is unchanged |
| 3. No promise lost | The follow-up run's steps show as unowned while Jordan is on leave; Priya acts only after acknowledging; an overdue email review escalates; closing needs evidence |
| 4. Prepared in minutes | One cited page: uses, said, wants, owed, next, checks |
| 5. The wrong thing, avoided | The January comparison goes on hold because the advisor postponed; stated, reported and platform asset figures are not totalled; registration shown as unknown; an out-of-scope request refused |
| 6. Measurable | SME turnaround, follow-ups recovered, reasons kept, and errors caught, counted from the event log |

Each run rebuilds `solution/.data/`, including the semantic QBRs in `.data/semantic-qbr/`. An approved one is committed as [a sample](solution/samples/semantic-qbr-INT-2026-03-QBR-CR.md).

### With Claude

Copy `.env.example` to `.env` at the project root (git-ignored) and set `ANTHROPIC_API_KEY`, or export it, or use an `ant auth login` profile. Each run costs a few cents.

```bash
cd solution
../.venv/bin/python -m aai.llm extract                          # findings from Claude into data/salesforce/extractions-llm/
../.venv/bin/python -m aai.demo --extractions llm --brief       # the demo on Claude's findings, plus a cited, verified brief
AAI_LIVE=1 ../.venv/bin/python -m pytest -q tests/test_llm.py   # live checks, including prompt injection
```

Extraction uses structured outputs whose enums come from the catalog, taxonomy and roster, so the model can name only known products, intents and reps; spans that are not verbatim are rejected before review. The brief verifier rejects uncited statements, unknown ids, unproposed actions and money figures not in the evidence. On 22 October, on the Crestline notes, Claude copied 13 of 13 spans verbatim, matched 9 of 10 hand-labelled findings, gave every experience a sentiment, and flagged, rather than followed, an injected instruction; the cited brief passed the evidence check ([sample](solution/samples/brief-FIRM-001-2026-03-20.md)). The one miss is deliberate: Claude left Northfield's "their UMA" unmapped because "their" may mean a competitor's UMA, so that review stays pending for the SME. These were single runs, not accuracy rates.

## Repository

| Path | Contents |
|---|---|
| [`business/advisor-account-intelligence-product.md`](business/advisor-account-intelligence-product.md) | Product brief: vision, takeaways, problem, the Maya scenario, scope by memory type, success measures |
| [`solution/architecture.md`](solution/architecture.md) | Pipeline, five memory types, the gate, authority and continuity, the OKF bundle, evaluation, known gaps |
| [`solution/model/`](solution/model/README.md) | Knowledge graph model: Draw.io (overview and four pages) and Turtle |
| `solution/bundle/` | OKF bundle: the QBR procedure, its computations and tools, generated glossaries and graph mapping |
| `solution/aai/` | Detection, pipeline, memory, task store, queries, brief, demo |
| `solution/data/` | Reference catalogs (`reference/`: products, intents, sentiments, asset definitions, roster), synthetic notes, profile exports and extractions |
| `solution/tests/` | Golden and LLM tests |
| `solution/tools/` | Model generator and checker, diagram renderer |
| [`AGENTS.md`](AGENTS.md) | Modelling and Draw.io conventions |

## Limits

Problem statements and targets are hypotheses to validate with a relationship team; none is a measured result. Action proposals are rules, not a model. Concept detection links "their UMA" to the CPX UMA by alias, while Claude treats it as possibly a competitor's; possessive and generic mentions should be marked ambiguous for the SME. Retention and decay are designed but not built. Domain distinctions were checked against FINRA and SEC sources on 19 October 2026; nothing here decides registration, eligibility or suitability.

## Licence

Copyright 2026 Radu Marian. Licensed under the [Apache License 2.0](LICENSE).
