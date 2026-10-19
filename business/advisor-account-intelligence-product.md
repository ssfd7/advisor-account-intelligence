# Advisor Account Intelligence

Business product brief · Version 0.6 · 19 October 2026 · Working assumptions for validation

Technical design: [solution design](../solution/solution-design.md) · [memory architecture](../solution/memory-architecture.md)

## 1. Product decision and grounding

Build an advisor relationship-intelligence product for an investment platform's relationship management and business development teams. It keeps QBR takeaways team-owned through verified completion, and it connects investment professional profiles, advisory firms, the platform products they use or consider, investor and advisor experience, dated asset metrics, professional milestones, and QBR intent to prepare an evidence-backed relationship brief and propose a next business action.

The platform is the proposed buyer and operating organization. RIAs and individual advisors are the business relationships it serves. The primary user is a platform relationship manager preparing for and following up on a QBR with an advisor or advisory firm. This operating model is inferred from the supplied resume and remains a product assumption to confirm.

The product is grounded in the user's Fidelity experience: IPP knowledge graphs, advisor career-pattern analysis, advisor journey maps, next-best-action and CLTV work, QBR intent extraction from Salesforce, business-analyst validation, and graph-based business reporting. That experience establishes relevant prior work; it does not establish the exact product requirements, taxonomy, data access, or measured ROI proposed here. No proprietary implementation or data is assumed available.

The subject is the **advisor's professional and platform relationship journey**: qualifications, affiliations, platform use, business intent, and the actions that support that relationship.

The core business questions are: **Will what was learned in a QBR be acted on, even if the rep who heard it is gone? And what experience are advisors and their investors having with specific products, what alternatives are being considered, and what should the platform do next?** QBRs connect product experience to intent and follow-up. Professional milestones and asset metrics provide context for that conversation.

## 2. Vision

**No QBR takeaway is lost, and every follow-up is grounded in what the advisor actually said.**

Product promise: QBR takeaways remain visible, owned, and actionable when the original rep is unavailable or leaves. The team retains responsibility from captured note through verified completion. The brief makes that follow-up worth doing by connecting it to the right product, experience, and evidence.

Business outcome: fewer lost follow-ups and less preparation effort, leading to better product relationship outcomes where these can be measured.

## 3. Domain context and vocabulary

An advisor can change employers, join or establish an advisory firm, hold different professional registrations, and use several investment platforms. A firm's platform relationship can move from exploration to onboarding, active use, expansion, or departure. These events may overlap; there is no universal linear career ladder.

A platform offers multiple products. An advisor can use one, evaluate another, and reject a third while retaining the same platform relationship. Product experience includes the advisor's operational experience and the end investor's experience reported in the QBR. Keep the speaker, affected party, product, and supporting evidence explicit: an advisor's report of client frustration is not a direct investor statement or a measured outcome.

| Concept | Meaning in this product | Modeling consequence |
|---|---|---|
| Investment adviser / IA | The advisory business or adviser providing investment advisory services; business usage can be ambiguous | Identify whether each source describes an organization or a person |
| Registered investment adviser / RIA | The registered advisory entity, modeled separately from its people | Store firm identity, registration evidence, and dated affiliations |
| Investment professional / advisor | The person whose career and relationships are being understood | Use a stable person identity across firms and platforms |
| Investment adviser representative / IAR | A person's representative role with an adviser | Separate the person, role, firm affiliation, and registration status |
| Investment platform | A provider or service environment for custody, clearing, brokerage, advisory technology, or investment services | Record provider, service type, and scope; distinguish technology use from custody |
| Product offering | A specific investment product, managed investment service, or platform service available through a platform | Give it an identity, category, platform, version/effective dates, and documented capabilities; do not equate these categories |
| Product relationship | An advisor's or firm's use or consideration of a particular offering | Record evaluating, using, expanding, paused, rejected, or discontinued separately for each offering |
| Experience observation | A reported or measured experience involving a product, such as reporting difficulty, onboarding delay, or satisfaction | Identify whose experience, who reported it, when, and whether it is testimony or measured evidence |
| QBR interaction | A platform team's review of investor/advisor experience, product use, alternatives, intent, and commitments | Preserve source excerpts and link each observation and intent to its product target |
| Journey state | A business interpretation supported by observed events | Record evidence, confidence/verification state, and effective dates |

IAPD distinguishes adviser firms and individual representatives; BrokerCheck supplies broker-related information. These are potential reference sources, not assumed integrations. [Investor.gov: IAPD](https://www.investor.gov/introduction-investing/investing-basics/glossary/investment-adviser-public-disclosure-iapd)

### Professional milestones and Series exams

Exam records are signals in the advisor's professional journey. They do not alone establish current registration, platform eligibility, competence, or intent to change firms. Keep exam results, registration records, and platform onboarding requirements separate.

| Milestone | Relevance to the profile |
|---|---|
| SIE and Series 7 | The Series 7 is the general securities representative qualification exam; FINRA identifies the SIE as a corequisite and sponsorship requirements for taking the Series 7 |
| Series 65 | An investment adviser law examination; retain the exam result as a qualification record |
| Series 66 | A combined state law examination with Series 7 as a corequisite; do not interpret its numeric label as progression beyond Series 65 |
| Firm affiliation or registration change | A distinct dated event requiring its own evidence |

Sources: [FINRA Series 7](https://www.finra.org/registration-exams-ce/qualification-exams/series7), [Series 65](https://www.finra.org/registration-exams-ce/qualification-exams/series65), and [Series 66](https://www.finra.org/registration-exams-ce/qualification-exams/series66). Qualification paths and applicable registration requirements need jurisdiction-specific verification; the prototype displays recorded evidence and gaps rather than deciding authorization to practice.

### AUM and AUA

- **AUM — assets under management:** a management-related measure whose entity, scope, methodology, and date must be explicit. Regulatory AUM is a specifically defined Form ADV measure and must be labeled separately from other reported AUM. [SEC Form ADV instructions, Item 5.F guidance](https://www.sec.gov/about/forms/formadv-instructions.pdf)
- **AUA — assets under administration:** an administration-related measure. Retain the reporting provider's definition and scope. Reporters differ in whether their AUA includes managed assets; it is unsafe to assume a universal relationship between AUM and AUA. Compare the definitions in [Principal's financial supplement](https://s21.q4cdn.com/251671177/files/doc_financials/2021/4Q/4Q-2021-financial-supplement.pdf) and [Ameriprise's quarterly filing](https://www.sec.gov/Archives/edgar/data/820027/000082002726000043/amp-20260630.htm).

For every asset observation retain metric type, value, currency, reporting entity, attributed firm/person, platform, product when available, account/service scope, as-of date, methodology, and source. Do not attribute an entire firm's AUM to every associated advisor or product. Do not add AUM to AUA. Calculate platform or product share only when the numerator and denominator have compatible scope and dates. Asset-balance growth alone does not establish net inflows or success of an intervention. A technology product may have no meaningful AUM/AUA attribution; leave it unspecified rather than inventing one.

## 4. Problem statements and root causes

| ID | Business problem | Root cause | Product response |
|---|---|---|---|
| P1 | Teams cannot reliably see which products an advisor or firm uses, has tried, or is considering | Profiles, platform catalogs, and product relationships use disconnected identities | A reconciled advisor–firm–platform–product view with evidence and gaps |
| P2 | Investor/advisor experience and product intent disappear into QBR notes | Statements lack structured links to the product, affected party, alternatives, and desired outcome | Product-linked experience and intent extraction with source attribution and validation |
| P3 | Follow-up promotes a product already rejected or ignores a changed need | Product decisions and reasons are overwritten or attached only to the overall platform | Dated product-specific states, reasons, and current/as-of views |
| P4 | Asset comparisons misstate product adoption or relationship opportunity | AUM/AUA definitions, entity/product scopes, and dates are mixed | Comparable metric views without unsupported allocation, totals, or opportunity estimates |
| P5 | Product outreach misses the stated need or an unresolved experience problem | Product capabilities, prior experience, intent, prerequisites, and action outcomes are disconnected | Recommend a supported comparison, service resolution, demonstration, or clarification before pursuing adoption |
| P6 | QBR takeaways go unfinished when the rep goes on vacation, becomes unavailable, or leaves the firm | Actions are buried in Salesforce paragraphs; responsibility lives with the author rather than a team-owned review and follow-up process | A shared queue for unreviewed QBRs and approved actions, explicit ownership, coverage, escalation, and completion evidence |

These are product hypotheses informed by the supplied experience. Validate their frequency and impact with relationship managers before presenting them as measured customer problems.

P6 is the lead problem. It is user-identified: a rep captures a few QBR paragraphs in Salesforce and becomes unavailable before anyone follows up. Its prevalence and financial impact remain to be measured. A brief alone does not resolve it; follow-up must survive the author's absence, including when no actions have yet been extracted or confirmed. P1–P5 make the follow-up accurate and worth doing.

## 5. Audience and commercial hypothesis

| Audience | Need | Primary questions |
|---|---|---|
| Platform relationship manager | Prepare a relevant QBR and follow through | CQ1–CQ6 |
| Business development / transition specialist | Understand stated interest, prerequisites, and onboarding blockers | CQ2, CQ4, CQ5 |
| Platform service specialist | Resolve adoption issues and outstanding commitments | CQ4–CQ6 |
| Product specialist | Explain relevant capabilities and alternatives against the needs recorded in the QBR | CQ1, CQ4, CQ5 |
| Business analyst / data steward | Validate intent, identity, and metric interpretation | CQ1–CQ4 |
| Compliance reviewer | Supervise product comparisons and advisor-facing communications; confirm record retention | CQ5 |
| Relationship team lead | Assess coverage and improvement in team execution | CQ5, CQ6 |

Initial deployment hypothesis: an internal platform capability. A later commercial version could be licensed to platform providers by team size and review volume. Pricing is unset pending workload cost and willingness-to-pay evidence. The advisor is the platform's relationship/customer, not assumed to purchase this tool directly.

## 6. Competency questions

| ID | Question | Expected answer | Problem |
|---|---|---|---|
| CQ1 | Who is this advisor, which firms/platforms are they associated with, and which products do they use or consider? | Dated profile and product relationships with evidence and gaps | P1 |
| CQ2 | What professional, platform, and product milestones have changed since the last review? | Timeline separating observed events from inferred journey state | P3 |
| CQ3 | What AUM/AUA information is available at firm, platform, or product level, and which observations can be compared? | Scoped asset table, dates, definitions, and exclusions | P4 |
| CQ4 | What investor/advisor experience is reported for each product, what alternatives are being considered, and what is the current intent? | Product-linked experience, needs, alternatives, source attribution, and supersession history | P2, P3 |
| CQ5 | Which product-related action should the relationship manager consider next, why, and what must be confirmed first? | Supported comparison, service resolution, demonstration, or clarification with prerequisites and owner | P5 |
| CQ6 | Which QBRs still need review, which takeaways remain open, and who will follow through if the original rep is unavailable? | Team queue, accountable owner/backup, due status, handoff history, and completion evidence | P6 |

## 7. Scope and initial workflow

First release: **a team-owned QBR follow-up queue and a product-centered QBR brief for one advisor within an RIA firm, across two review cycles**. Include three fictional offerings across two platforms, current use and alternatives, reported investor/advisor experience, product intent and its change between reviews, asset snapshots, and outstanding commitments. Exam/registration evidence and firm affiliation remain profile context.

| Workflow | Starts when | Ends when |
|---|---|---|
| WF1 — Prepare QBR | A relationship manager selects the advisor/firm and review date | A cited product-experience brief and proposed action are ready for review |
| WF2 — Validate change | New evidence or a reviewer correction arrives | A confirmed change, supersession, or unresolved discrepancy is recorded |
| WF3 — Follow through | A QBR note is captured or imported | Its takeaways are reviewed; approved actions have verified completion or an explicit disposition, with open work remaining visible |
| WF4 — Maintain coverage | An owner becomes unavailable, leaves, or a review/action becomes overdue | A covering owner accepts responsibility or the item remains escalated to the accountable team lead |

The initial continuity workflow is: captured QBR → team review queue → extracted candidate takeaways → authorized reviewer confirmation → shared action queue → completion with evidence. Each QBR has a responsible team, review deadline, and review status even when extraction fails or finds no candidates. A reviewer can explicitly record "no action needed." Each approved action has an owner, due date, and escalation route. Reassignment preserves source context and history and requires acknowledgment; merely sending a notification does not complete the handoff. Approved dismissal or cancellation records a reason and reviewer. Advisor-facing product comparisons pass compliance review before they are shared.

For the slice, use a small team roster and manual availability/coverage settings, one shared queue, and a mock task store. Do not require calendar or HR integrations. Absence before validation must be handled by a covering reviewer with appropriate authority, rather than blocking on the original author. This basic coverage capability belongs in phase 1; later specialist collaboration extends it.

All prototype data is synthetic. Platform A and Platform B are fictional. Profile exports, QBR notes, and a follow-up email are supplied as files representing Snowflake and Salesforce exports; no live source-system connections are required initially. Feed and storage details are in the [solution design](../solution/solution-design.md).

Include product information and comparisons needed for a business conversation, using supplied catalog evidence. Capture investor experience reported by the advisor at an aggregate or anonymized level. Outside the initial scope: individual investor portfolios, personalized investment suitability or product-selection decisions, trades, automated outreach, a registration rules engine, predicted advisor success, CLTV modeling, and automated procedure evolution. CLTV and career-pattern analytics are credible future extensions from the supplied experience, but require suitable longitudinal data and a separate validation plan.

## 8. Working scenario and advisor journey

Synthetic example: Maya Chen is an advisor affiliated with Cedar Ridge Advisory, a fictional RIA. The firm uses Platform A's Custody Service and Managed Portfolio Service A. Maya is considering Managed Portfolio Service B on Platform B. All offerings and capabilities in this scenario are fictional.

1. January QBR: Maya reports that investors find Service A's statements difficult to understand and her team spends time explaining them. She is considering Service B and requests a comparison of reporting and integration capabilities. The relationship manager, Jordan, promises a specialist session.
2. A firm snapshot reports $300 million AUM; Platform A reports $180 million AUA for a specified relationship. Neither number identifies assets in Service A. The assistant keeps them separate and marks product-level assets unknown.
3. The catalog contains dated descriptions for both managed services. It can support a feature comparison, but it does not establish that Service B will improve investor experience or is suitable for a particular investor.
4. February email: Jordan forwards the January note to a product specialist, quoting Maya's statement. This is a repetition, not new evidence. Jordan then goes on leave before the specialist session is scheduled; a covering rep, Priya, picks up the open commitment from the team queue.
5. March QBR: Maya postpones the Service B evaluation because a required integration has not been verified. Custody Service A remains in active use. The CRM still lists the evaluation as ready for a pilot.
6. The next brief shows the reported investor experience, advisor workload, both product alternatives, current intent, unverified integration, the CRM discrepancy, and the open commitment. The proposed action is a reporting-and-integration review with a product specialist, plus a service issue for the current reporting problem.
7. The manager approves follow-up. Later evidence records whether the blocker was resolved, whether the evaluation resumed, and whether reported experience changed. No platform exit or product adoption is inferred from intent alone.

A second fictional firm, Northfield Wealth Partners, employs an advisor named May Chen. Her profile and interactions exist in the fixtures but are assigned to a different team; they test identity separation and access exclusion.

Professional milestones, platform relationships, and product relationships are separate tracks. Product states are proposed business labels, not regulatory categories. Pausing one product evaluation must not change the status of other products or imply platform departure. Years of experience remains contextual information rather than a performance score.

### Product state changes and authority

| From → To | Evidence that can make the change | Rule |
|---|---|---|
| (none) → evaluating | Confirmed QBR intent or CRM opportunity record | Testimony alone is recorded as proposed until a reviewer confirms it |
| evaluating → using | Operational record (onboarding, account, or contract) | Never inferred from intent or clickstream alone |
| using → expanding | Operational record or confirmed QBR intent with a target scope | Intent without an operational record stays "planning expansion" |
| evaluating → paused | Confirmed QBR statement or CRM update | If the CRM disagrees, show both and raise a discrepancy; do not silently choose |
| any → rejected | Confirmed QBR statement or CRM record, with a reason | The reason is retained permanently |
| using → discontinued | Operational record | Advisor testimony raises a discrepancy until an operational record confirms it |
| paused/rejected → evaluating | New confirmed intent or an explicit request | Requires new evidence; prior reason remains visible |

Each change is dated, cites its source, and affects only one product relationship.

## 9. User experience and requirements

The relationship manager opens the team queue to see unreviewed QBRs and open actions they own or cover. From an advisor or firm and a review date, they generate a brief. The brief leads with products in use or under consideration, investor/advisor experience, desired outcomes, alternatives, and blockers. It then presents relevant profile/journey context, comparable asset observations, commitments, and up to three proposed business actions. Each action identifies its product target, rationale, sources, prerequisites, owner, and approval status.

| ID | Priority | Requirement | Acceptance example |
|---|---|---|---|
| FR1 | Must | Reconcile person, firm, and platform identities | Maya Chen and May Chen are not automatically merged — CQ1 |
| FR2 | Must | Keep qualifications separate from registration and eligibility | A Series result never becomes an "authorized" label by inference — CQ2 |
| FR3 | Must | Preserve asset definitions and attribution | Firm AUM is not duplicated across advisors or allocated to products without evidence — CQ3 |
| FR4 | Must | Extract product-specific intent and experience | "Considering B" differs from "using B"; advisor-reported investor frustration is attributed correctly — CQ4 |
| FR5 | Must | Retain effective time and recorded time | An as-of answer excludes facts learned later — CQ2, CQ4 |
| FR6 | Must | Explain and approve actions | Evidence and prerequisite checks precede a proposed task write — CQ5 |
| FR7 | Should | Track ownership and outcomes | Retrying a handoff does not duplicate a task — CQ6 |
| FR8 | Must | Enforce access and evidence consistency | Unauthorized records stay outside model context; material revisions trigger revalidation — all CQs |
| FR9 | Should | Ground product comparisons in current catalog evidence | An undocumented capability is marked unknown; no unsupported ranking or promised outcome — CQ5 |
| FR10 | Must | Preserve independent product states and alternatives | Pausing Service B does not end Custody Service A or supersede unrelated intent — CQ1, CQ2, CQ4 |
| FR11 | Must | Retain responsibility before and after extraction | A saved QBR with failed extraction or an absent author remains in the team's review queue — CQ6 |
| FR12 | Must | Maintain coverage and explicit closure | A covering rep accepts reassignment and closes the action with evidence; notification alone leaves it open — CQ6 |

Initial intent labels: exploring/comparing, planning adoption or transition, expanding use, requesting support, postponing, rejecting/discontinuing, and unknown. Each intent has a target offering or unresolved product reference, speaker, desired outcome, reason/blocker, and date. Experience observations remain separate from intent: dissatisfaction does not automatically mean departure. A confirmed intent can propose a product state change under the rules in section 8; it never makes the change by itself where an operational record is required. Review the taxonomy with a business analyst.

### Supporting use case: intent taxonomy curation

**Classification applies a taxonomy to a QBR statement; curation improves the taxonomy itself.** A taxonomy curator or business analyst reviews ambiguous examples, missing concepts, overlapping labels, definitions, and synonyms. This is a separate supporting workflow with its own user and output, rather than an additional phase of the customer product.

For phase 1, manually approve a small seed taxonomy with stable concept IDs, definitions, examples, and a version. Permit multiple supported intents and an unmapped result; do not force every statement into an existing label. Trigger assisted curation only when repeated unmapped or ambiguous statements demonstrably increase review effort. Changes to the taxonomy must not silently relabel history. Implementation is described in the [solution design](../solution/solution-design.md).

## 10. Knowledge and memory (summary)

The product remembers advisors, firms, products, conversations, and work as connected, dated, evidence-backed records. Business consequences:

- **Each fact has a source and an owner.** Registry evidence for registration, a designated source for asset observations, approved catalogs for product capabilities, source conversations for what was stated, and CRM/task systems for approved operational records. A new statement can expose a discrepancy without silently replacing a registered fact. A catalog capability is not proof of an investor outcome.
- **History is kept.** Briefs can be produced as of any past date; superseded intent and rejection reasons remain visible.
- **Changes are narrow.** New information about one product does not overwrite memory about another.
- **Work outlives its author.** QBRs and actions are team-owned; their evidence travels with each handoff.
- **Access follows the relationship.** Teams see only the firms and advisors they are assigned to, including in summaries and handoffs.

Memory types, temporal model, supersession, scopes, decay, and multi-agent handoffs are specified in the [memory architecture](../solution/memory-architecture.md).

## 11. Five-phase delivery plan

| Phase | Business demand and delivery | Questions | Exit evidence |
|---|---|---|---|
| 1. Grounded QBR brief, follow-up queue, and basic temporal memory | Capture QBRs in a team queue, validate takeaways, assign covered follow-up; combine product experience and profile evidence across two review cycles with as-of answers and product-specific supersession. One assistant and manual procedure | CQ1–CQ6 | Supported brief for both review dates; an absence-before-review scenario completed by a covering rep |
| 2. Temporal memory at scale | Retain product trials, experience, rejections, revised intent, and commitments across many reviews and advisors; optional usage summaries | CQ2, CQ4, CQ6 | Historical answers pass over multiple cycles; rejected options do not resurface without reason |
| 3. Governed specialist collaboration | Extend basic rep coverage to product, service, and evidence specialists with distinct permissions | CQ1–CQ6 | Handoffs preserve context, acknowledged ownership, and deadlines; compare specialist agents with one assistant |
| 4. Memory lifecycle | Control duplicate experience reports and stale intent; retain decision reasons and catalog versions | CQ2, CQ4, CQ6 | Savings without losing product rejection reasons or required history; verified promotion works |
| 5. Reliable service at team scale | Support concurrent QBR preparation with predictable latency and cost | All | Agreed traffic and quality targets met; capacity and cost per accepted brief documented |

Phases build on the grounded baseline. Evaluation starts in phase 1. Keep multiple agents only if their measured quality or operational benefit justifies added cost. Independent role permissions remain necessary even if a single orchestrator performs the work. Generic approved procedures may be shared; private advisor/firm interaction content is scoped to authorized teams.

Taxonomy governance starts in phase 1; assisted curation may follow in phase 4 if correction patterns justify it. Clickstream usage summaries may be added from phase 2 and are never a prerequisite for the first brief. Realistic business growth motivates capacity work, but synthetic load tests do not prove real demand.

## 12. Business objectives, baseline, and ROI

No measured customer baseline is supplied. The targets below are hypotheses to validate with a platform relationship team, not Fidelity results or published industry benchmarks.

| Objective | Baseline to collect | Proposed pilot target | Questions |
|---|---|---|---|
| Improve follow-through and coverage | Unreviewed QBR age, missed takeaways, overdue actions, reassignment acceptance time, and follow-ups lost during absence | All seeded absence/departure scenarios retain ownership and reach verified closure; measure real-world improvement against baseline | CQ6 |
| Reduce QBR preparation effort | Human minutes per brief, including source lookup, corrections, and validation of extracted takeaways | At least 30% lower median total human effort, net of added review | CQ1–CQ5 |
| Reduce factual rework | Identity, metric, and stale-intent corrections per brief | No critical misattribution or unsupported eligibility claim in the acceptance suite | CQ1–CQ4 |
| Improve action usefulness | Reviewer acceptance, edits, and later completion | Improve against the same reviewers' baseline; acceptance alone is insufficient | CQ5, CQ6 |
| Improve product relationship outcomes | Time to resolve experience issues; agreed evaluations completed; adoption/retention and contribution margin where measurable | Compare with a matched baseline; set targets after observation and separate action influence from other factors | CQ4–CQ6 |
| Keep operation economical | Model, storage, integration, support, and review cost per brief | Agree a budget after the initial workload is measured | All |

Baseline study: use approximately 20 comparable QBR-preparation tasks, with relationship-manager review. Counterbalance manual and assisted tasks to reduce learning effects, record correction and validation time, and report sample size and variation. Separately, sample recent QBR notes to measure how many takeaways were never followed up and how many of those coincided with rep absence or departure. A synthetic study demonstrates feasibility; live business ROI needs approved representative work.

Calculate over a consistent annual horizon:

- Net minutes saved per brief = preparation minutes saved − added review and validation minutes.
- Labor value released = annual briefs × net minutes saved per brief ÷ 60 × loaded hourly cost.
- Continuity value = lost follow-ups avoided per year × measured value per completed follow-up. Use zero until the baseline sample and pilot establish both terms.
- Annual benefit = labor value released + continuity value + separately measured avoided rework + attributable incremental product contribution margin, with no double counting. Use zero for the margin term until evidence exists; subtract incremental servicing costs when calculating it.
- Year-one cost = implementation and integration cost + annual operation, support, and review cost.
- Year-one ROI = (annual benefit − year-one cost) ÷ year-one cost.

Illustration only: 1,200 briefs/year × (20 minutes saved − 5 minutes added review) ÷ 60 × $100/hour = $30,000/year of capacity value. At an assumed $60,000 year-one cost, labor savings alone give a year-one ROI of −50%. On labor alone, breakeven needs about 2,400 briefs a year at the same net saving, or measured continuity or margin value. The business case therefore depends on team scale and on the continuity measurement, not on preparation time alone. Capacity value is not automatically cash savings. Exclude speculative AUM/AUA growth, retained revenue, and CLTV uplift until attribution is supported. Never use asset balances themselves as revenue.

## 13. Evaluation and acceptance

Start with the scenario in section 8: two RIAs (Cedar Ridge Advisory and Northfield Wealth Partners), two advisors with similar names, three fictional offerings across two platforms, short catalog descriptions, two asset observations, three dated interactions for Maya Chen (January QBR, February forwarded email, March QBR) and one for May Chen, an exam record and a separate registration record, one procedure, and the golden cases below. Include an originating rep (Jordan), a covering rep (Priya), an accountable team lead, and a second team that owns Northfield. Expand to five firms and ten advisors over three review cycles only after the workflow works.

| Test | Expected behavior |
|---|---|
| Similar names or changed firm | Maya Chen and May Chen stay separate; affiliation history is preserved |
| Exam passed; current registration unknown | Show the exam and the gap; do not infer authorization |
| AUM and AUA with different scope/date | Refuse an unsupported total, share, or opportunity calculation |
| Paused evaluation of Service B | Its current recommendation changes; Service A and custody relationships stay correctly scoped |
| CRM disagrees with confirmed QBR statement | Show both and raise a discrepancy; do not silently choose |
| Advisor reports investor dissatisfaction | Attribute it to the advisor's report, not a direct investor statement or an exit intent |
| Product capability missing from catalog | Mark it unknown and propose verification rather than inventing a favorable comparison |
| Previously rejected product | Retrieve the reason; revisit only with relevant new evidence or an explicit request |
| Same assets appear in multiple scopes | Do not add firm, platform, and product observations into a false total |
| Repeated QBR quote in the February email | Do not count the repeated statement as independent confirmation |
| Missing follow-up result | Mark status unknown/open rather than completed |
| Changed evidence before approval | Revalidate the affected recommendation |
| Unauthorized firm interaction | May Chen's Northfield interaction is excluded from retrieval and generated output for Cedar Ridge's team |
| Instructions embedded in a QBR note | Treat as quoted data; no change to retrieval scope, tool use, or output |
| Rep unavailable immediately after saving a QBR | A covering rep discovers the note, validates takeaways, and completes follow-up without contacting its author |
| Extraction fails or yields no candidates | The QBR stays pending review until a reviewer resolves it, including explicit no-action disposition |
| Rep leaves with approved actions open | Work remains team-owned and is reassigned with context and acknowledgment; access revocation does not erase records |
| Backup does not accept or misses the deadline | Escalate to the team lead; never mark the handoff or task complete solely from notification |

Measure required-evidence retrieval, product-target accuracy, experience attribution, supported comparisons, intent extraction and supersession, action usefulness, human correction effort, latency, and cost separately. Designated critical cases must all pass before pilot release; finite tests do not guarantee zero future failures. Technical tests for feeds, taxonomy, and serving are listed in the [solution design](../solution/solution-design.md). The golden cases above are the baseline, not a cap on later coverage.

## 14. Access, ownership, and rollout

The product owner owns value measures. Relationship managers approve proposed actions and operational updates. Business analysts validate extracted experience, intent, and journey labels. Product specialists maintain approved catalog information and clarify prerequisites. Data stewards own identity and asset definitions. Compliance reviewers approve advisor-facing product comparisons and communications before they are shared, and own retention requirements for QBR notes, briefs, and action records. Firm/platform administrators assign access and lifecycle policy. Engineering owns execution, evaluation, and auditability.

The relationship team lead is accountable for unreviewed QBRs and unowned/overdue actions. A designated covering rep can validate and execute within assigned authority. Coverage activation is an explicit operational input; the product need not infer illness or inspect personal calendars. Track closure and reassignment outcomes rather than treating reminders as completed work.

Scope permissions to the operating organization, relationship assignment, firm/advisor, role, and action. A platform reference in an advisor's profile does not grant access to that provider's private data. Apply controls to sources, derived summaries, and handoffs. Preserve who approved an update and which evidence/procedure version supported it. Treat source text as data rather than instructions.

Rollout: synthetic demonstration → review by a relationship manager, business analyst, and compliance reviewer → limited approved pilot → team adoption → capacity expansion. Start with file-based fixtures and a mock task interface. Live Snowflake/Salesforce integrations and Power BI reporting can follow when needed. A timeline and simple intent/action report are sufficient initially; Sankey flows and cohort analysis can follow after enough comparable data exists.

## 15. Open decisions and limits

Confirm the platform business unit and primary user, the initial product categories and catalog sources, how investor experience is captured, the IA/IAR terminology used by the source systems, available asset definitions, the intent taxonomy and curator, authoritative fields, who can approve changes, and which communications require compliance review. For clickstream, confirm actor types, identity mappings, feature-to-product mappings, and tracking coverage. Define data licensing, retention, and deployment requirements before live ingestion.

Do not infer a universal best career stage, "optimal" years of experience, or future advisor value from a small sample. Career-pattern and CLTV extensions require appropriate cohorts, outcomes, and bias checks. The initial product demonstrates profile reconciliation, journey continuity, and useful follow-up rather than predictive scoring.

The decisive continuity demonstration removes the originating rep immediately after the Salesforce-style note is saved. The team queue must let a covering rep discover, validate, own, and complete its takeaways using preserved evidence. This demonstrates the path from organizational knowledge to executed action; financial benefit is then measured through the baseline and ROI method.

The first brief demonstration is successful when a relationship manager can connect reported investor/advisor experience to the right product, understand why an alternative is being considered or postponed, and approve a supported follow-up. The brief must preserve person/firm identity, qualification/registration distinctions, product-specific state, and valid AUM/AUA scope.

## 16. Evidence and design references

The supplied Fidelity resume excerpt is the source for the project's experiential grounding. The cited FINRA, SEC, Investor.gov, and issuer materials establish selected domain distinctions; they do not validate the proposed market need, taxonomy, targets, or ROI. Domain sources were reviewed on 19 October 2026.

[Procedural Graphs: Self-Evolving Execution Structures for LLM Agents](https://arxiv.org/abs/2609.09153) remains an optional design reference. The initial procedure is authored and versioned manually; a separate guidance model and automated graph refinement are deferred until a measured problem warrants them.
