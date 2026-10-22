# Pivot

21 October 2026 · Less is more

**Status (21 October 2026):** built and cut down as below, except `interview/` (private, not in git; left for the owner to merge) and retention and decay (designed, not built). See the [README](README.md) and [architecture](solution/architecture.md).

## Vision

**If our relationship teams knew what the firm knows, they would be far more productive.** The pilot's target is three times; the pilot measures it.

Salesforce holds a QBR as text. It does not know the firm's products, services or advisor intents, so what the advisor said is invisible to every system and to every colleague who did not write it. The product turns each QBR into knowledge the firm can act on.

The first release covers one advisor across review cycles. Knowledge pooled across advisors ("what are advisors saying about this product?") comes later, under the same access scopes.

## What the business should take away

1. **The firm finally knows what its advisors tell it.** Products, services, intents and asset figures in a QBR are recognized against the firm's own catalog.
2. **Experts stay in control.** An SME (a business analyst or product specialist) approves every finding before it changes anything; each finding is tied to the advisor's exact words.
3. **No promise falls through the cracks.** Every QBR and every follow-up has an owner and a due date, even when the rep is on leave or has left, and even before the SME has reviewed it.
4. **Reps are prepared in minutes, not hours.** One page: what the advisor uses, said, wants, and what we still owe them.
5. **We stop saying the wrong thing.** No pitching a postponed product, no inflated asset figures, no overstated credentials.
6. **The value is measurable.** A pilot tracks preparation time, lost follow-ups, errors caught and SME review load against today's baseline.

## Pipeline

QBR note (stored on arrival) → **concept detection** → **semantic QBR** (an OKF concept, `status: draft`) → **SME approval** (`status: verified`) → **hydration**: write tools record the approved findings in the knowledge graph and start a follow-up procedure run → brief and owned follow-up.

The SME review step has an owner, a deadline and escalation. A QBR waiting for review stays visible in the team queue.

## OKF, borrowed from the cross-border private equity project

OKF is the [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md): a bundle of Markdown concepts with YAML frontmatter that an agent can read and run. We reuse the bundle layout and the Ontology Grounding extension from the cross-border private equity project:

- **Bundle:** `index.md` declares the ontology (`aai:` prefix, `solution/model/aai-model.ttl`); `procedures/`, `computations/`, `tools/` and `references/mappings/`. No attesters: each computation and tool names the code that implements it.
- **Extension keys:** `reads` on computations (the ontology terms they query), `writes` on tools (the terms they create), `supports` on everything (competency questions and workflow steps), and procedure `steps` with `performed_by: agent | human` and `uses`.
- **Generated glossary:** each computation and tool carries a `# Glossary` generated from the Turtle and the mappings; a stale glossary fails the bundle check.
- **Draft until a person approves:** concepts an agent writes are `status: draft`; only a person marks them verified.

New in this project: the semantic QBR is itself an OKF concept. Its `writes` lists the `aai:` terms its findings would create, and each finding quotes its source sentence. Approving it is the gate; hydration runs the write tools it names.

## Scope by memory type

| Memory type | Business outcome | In scope | Out of scope |
|---|---|---|---|
| **Semantic**: what the firm knows | The firm knows what advisors tell it; we stop saying the wrong thing | Realistic product catalog (specific names, capabilities, prerequisites, aliases); intent taxonomy; AUM/AUA definitions and allowed computations; advisor and firm identities, kept separate when names are similar; exam and registration records, kept separate from each other; current product relationships and intents promoted from approved findings | Full enterprise product ontology; pricing; suitability rules; registration rules engine |
| **Episodic**: what happened, was said, and when | Reps prepared in minutes; everything provable | QBRs and emails, stored on arrival; approved semantic QBRs as dated episodes, each finding tied to its sentence; rejected findings with the reviewer's reason; repetitions linked, not counted twice; newer intent supersedes older intent for the same product only; as-of answers; action outcomes with evidence | Raw clickstream; call audio or transcripts; individual investor interactions |
| **Procedural**: how the firm acts | No promise falls through the cracks | OKF bundle: the QBR understanding and follow-up procedure (steps by agent or human, with `uses`), computations and tools with generated glossaries; hydration: approval creates a procedure run with steps bound to findings, owners and due dates | Automated procedure evolution; agents changing procedures |
| **Working**: in flight, short-lived | Experts stay in control | Concept detection output, the draft semantic QBR awaiting approval, the brief's evidence bundle and draft brief; cleared once the decision is recorded or the draft expires (the source QBR remains in episodic memory) | Long-lived agent scratchpads; cross-session chat memory |
| **Associative**: connecting the note to the firm's knowledge | The firm knows what advisors tell it | Concept detection as entity linking: product mentions, including loose ones ("their UMA"), matched to the catalog by name and alias or left unresolved for the SME; traversal from a finding to its product, capability, prerequisite, commitment and action | Vector similarity treated as truth; associations across advisors in the first release |

**One gate:** source notes are recorded as they arrive; nothing derived from them moves from working memory into semantic, episodic or procedural memory without SME approval. Access scopes apply to all five.

**Retention:** duplicates and expired drafts are pruned; rare high-value events and rejection reasons are kept.

**Out of scope throughout:** real client data, live Salesforce or Snowflake connections, investor portfolios, trades, suitability or product-selection advice, automated outreach, predictive scoring such as CLTV.

## Cut-down

**Keep**

1. README: vision, takeaways, one architecture picture, how to run the demo (absorbs DEMO.md).
2. Product brief, about two pages: vision and takeaways, problem, the Maya scenario, scope by memory type, success measures.
3. One architecture doc, merging solution design and memory architecture, organized by the five memory types and the pipeline.
4. Two diagrams: the pipeline and the five memory types.
5. Knowledge graph model: one Draw.io file (overview plus the pages the demo touches; the overview stays the union of those pages) and the Turtle, with the model generator and checker.
6. Code: the demo told as the business story in five or six steps, the agents, the tests.

**Cut or fold in**

- Requirement tables, ROI formulas and golden-case tables in the brief (the tests cover the golden cases).
- State transitions, context assembly, write path and handoff contract diagrams.
- Separate DEMO.md and solution-design.md.
- Governance Turtle and the long model README (a short note instead).
- The diagram generator, once the two remaining diagrams are produced.
- The event-log dump in the demo.
- `interview/`: one prep file instead of four.

## Build, in order

1. Realistic product catalog with specific names and aliases; move the golden cases to it and keep the tests passing.
2. Concept detection agent (entity linking; asset figures and allowed computations).
3. OKF bundle with `bundle check` and `bundle glossary` ported from the private equity project; semantic QBR generator and SME approval, with review owner, deadline and escalation.
4. Hydration into the knowledge graph and a procedure run.
5. Business demo around the six takeaways.

## Decision

Product names are fictional twins, as specific as Fidelity's but not letter swaps of real names, because the repo is public and no proprietary data is assumed: Crestline Custody and Clearing, Crestline Model Portfolios (CMP), the CPX Unified Managed Account on Crestline Portfolio Exchange, and Crestline Direct Index Builder.
