<h1 align="center">Advisor Account Intelligence</h1>

<p align="center">Business product brief · Version 0.8 · 23 October 2026 · Working assumptions for validation<br>Technical design: <a href="../solution/architecture.md">architecture</a></p>

## 1. Vision

<p align="center"><sub><i>Business vision</i></sub><br><b>Discover the best and most promising advisors, know them deeply, and recommend next best moves for advisors and firm to thrive.</b></p>

<p align="center"><sub><i>Solution vision</i></sub><br><b>Agentic teams<sup>*</sup> that listen to understand, learn and retain what matters, discover what's possible, and turn understanding into opportunities.</b></p>

<p align="center"><sub>* <i>Agentic teams</i> are subject-matter-expert teams with AI agents embedded across the whole advisor lifecycle, and a human in the middle of every decision.</sub></p>

---

This release builds the foundation, knowing each advisor deeply. Next best action, then discovering the most promising advisors, follow on the roadmap (section 9).

Salesforce holds a QBR as text. It does not know the firm's products, services or advisor intents, so what the advisor said is invisible to every system and to every colleague who did not write it. The product turns each QBR into knowledge the firm can act on.

## 2. What the business should take away

1. **The firm finally knows what its advisors tell it.** Products, services, intents and asset figures in a QBR are recognized against the firm's own catalog.
2. **Experts stay in control.** An SME (a business analyst or product specialist) approves every finding before it changes anything; each finding is tied to the advisor's exact words.
3. **No promise falls through the cracks.** Every QBR and every follow-up has an owner and a due date, even when the rep is on leave or has left, and even before the SME has reviewed it.
4. **Reps are prepared in minutes, not hours.** One page: what the advisor uses, said, wants, and what we still owe them.
5. **We stop saying the wrong thing.** No pitching a postponed product, no inflated asset figures, no overstated credentials.
6. **The value is measurable.** A pilot tracks preparation time, lost follow-ups, errors caught and SME review load against today's baseline.

## 3. The problem

A rep captures a few QBR paragraphs in Salesforce, then goes on leave or leaves. The investor experience the advisor described, the product they are weighing and the session that was promised disappear into the note. When follow-up does happen it can pitch a product the advisor has postponed, add AUM to AUA, or treat a passed exam as a current registration.

The root cause is that the note is text the firm cannot read: it does not link "their UMA" to the firm's own offering, it does not separate what the advisor said from what was confirmed, and its follow-ups belong to whoever wrote it. These are hypotheses from the author's Fidelity experience with QBR intent extraction, advisor knowledge graphs and relationship analytics; their frequency and cost are what the pilot measures. No proprietary data or implementation is assumed.

## 4. Users and roles

| Role | In the product |
|---|---|
| Relationship manager | Owns follow-up for assigned firms; prepares from the one-page brief; covers for a colleague when the lead asks |
| SME (business analyst or product specialist) | Approves, rejects or escalates each finding in a semantic QBR, within a review deadline, with comments kept in memory |
| Team lead | Accountable for unreviewed QBRs and unowned work; activates coverage; receives escalations; can close a review as "no action needed" with a reason |
| Data steward and product specialists | Own identities, asset definitions, the catalog and its aliases; decide findings an SME escalates to them |
| Compliance reviewer | Approves advisor-facing comparisons before they are shared |

## 5. The scenario

All names are fictional. Crestline is the firm; its catalog lists Crestline Custody and Clearing, Crestline Model Portfolios (CMP), the CPX Unified Managed Account on Crestline Portfolio Exchange, and Crestline Direct Index Builder.

1. **January QBR.** Maya Chen of Cedar Ridge Advisory says her investors find the CMP statements hard to understand, and that she is considering "the UMA on Crestline Portfolio Exchange". Jordan, her relationship manager, promises a specialist session. Dana, the team's SME, approves the findings; Jordan approves a comparison and dismisses two minor actions with a reason.
2. **February email.** Jordan forwards the January note. It is a repetition, not new evidence; its review goes overdue and escalates to the team lead.
3. **March QBR.** Maya is postponing the CPX UMA evaluation because her portfolio accounting integration is unverified; investors still call about statements; she says Cedar Ridge's AUM is "about $320 million". The CRM still says the evaluation is pilot-ready. Jordan saves the note and goes on leave the next day.
4. **What happens.** The review waits for Dana, not Jordan. Dana approves three findings, comments on one, and escalates the $320M figure to Ria, the data steward, who accepts it the next day as Maya's statement. Memory now says "paused", with a discrepancy against the CRM. The follow-up run's steps are Jordan's, so they show as unowned; the lead offers them to Priya, who acts only after acknowledging. The January comparison goes on hold: it would pitch a postponed product. The $320 million stays Maya's statement, apart from the firm's reported $300M AUM and the platform's $180M AUA, and nothing is totalled. Maya's registration is shown as unknown despite her passed exams. Priya closes the service issue with evidence; the integration review stays open and owned.

A second firm, Northfield Wealth Partners, has an advisor named May Chen. Her records stay separate and outside Cedar Ridge's team's access; her note mentions "their UMA" (linked) and "separate accounts" (left unresolved for the SME).

## 6. Scope by memory type

| Memory type | Business outcome | In scope | Out of scope |
|---|---|---|---|
| **Semantic**: what the firm knows | The firm knows what advisors tell it; we stop saying the wrong thing | Realistic catalog with names, aliases, capabilities and prerequisites; intent catalog; sentiment catalog; AUM/AUA definitions and allowed computations; advisor and firm identities, kept apart when names are similar; exams and registrations, kept apart; current product states and intents from approved findings | Full enterprise ontology; pricing; suitability rules; registration rules engine |
| **Episodic**: what happened, was said, and when | Reps prepared in minutes; everything provable | Notes and emails stored on arrival; approved semantic QBRs, each finding tied to its sentence; rejected findings with reasons; repetitions linked; narrow supersession; as-of answers; outcomes with evidence | Clickstream; call audio; individual investor interactions |
| **Procedural**: how the firm acts | No promise falls through the cracks | The OKF bundle with the QBR procedure, computations and tools; procedure runs binding steps to findings, owners and due dates | Agents changing procedures |
| **Working**: in flight | Experts stay in control | Detection output, the draft semantic QBR, the brief's evidence and draft | Long-lived scratchpads; cross-session chat |
| **Associative**: connecting the note to the firm's knowledge | The firm knows what advisors tell it | Entity linking of product mentions, including loose ones, or leaving them unresolved; traversal from a finding to product, prerequisite, commitment and action | Vector similarity as truth; associations across advisors in the first release |

The first release covers one advisor across review cycles. Pooled knowledge across advisors comes later, under the same access scopes. Out of scope throughout: real client data, live Salesforce or Snowflake connections, investor portfolios, trades, suitability or product-selection advice, automated outreach, predictive scoring such as CLTV.

## 7. Rules the product keeps

- **Product states.** A conversation can propose evaluating, paused or rejected for one product. Using, expanding and discontinued need an operational record. A change to one product never changes another or the platform relationship. A CRM record that disagrees raises a discrepancy; neither side is overwritten.
- **Assets.** AUM and AUA are different measures; reporters define AUA differently, and regulatory AUM is a specific Form ADV measure ([SEC Form ADV instructions](https://www.sec.gov/about/forms/formadv-instructions.pdf)). A total or share needs matching metric, currency, scope and date. A firm figure is never allocated to an advisor or product. An advisor's stated figure is testimony.
- **Credentials.** An exam result (SIE, Series 65 or 66) is not a registration and does not establish eligibility ([FINRA qualification exams](https://www.finra.org/registration-exams-ce/qualification-exams)). Missing registration evidence is shown as unknown.
- **Catalog.** An undocumented capability is unknown, never assumed.
- **Sentiment.** Each reported experience carries the speaker's sentiment from the sentiment catalog. A negative experience leads to a service issue, a mixed one to a clarification, praise to nothing. Sentiment is testimony, not a measured outcome.

## 8. Success measures

| Measure | Baseline to collect | Pilot target |
|---|---|---|
| Preparation time | Human minutes per brief, including lookup and correction | Toward 3× faster preparation; at least 30% lower median effort net of SME review |
| Lost follow-ups | Takeaways never followed up, and how many coincided with absence | Every seeded absence reaches an owner and verified closure |
| Errors caught | Pitches of postponed products, unsupported totals, overstated credentials, missed discrepancies | No critical misattribution in the acceptance suite; count what was caught |
| SME review load | Findings per QBR, review minutes, overdue reviews | Agree a ceiling after the first month |

Baseline: about 20 comparable preparation tasks with relationship-manager review, counterbalanced between manual and assisted, plus a sample of recent notes checked for lost follow-ups. Capacity freed is not cash saved; retained revenue and AUM growth are excluded until attribution is supported.

## 9. Roadmap

1. **Now: know them deeply.** This release, sections 2 to 8.
2. **Next: next best action.** Just-in-time recommendations for the advisor and the firm, including career moves, product and service steps. Signals: approved intent and sentiment, open commitments, affiliation changes, exam milestones, asset observations. An expert approves each recommendation before it is shared; acceptance and outcomes are measured against a baseline.
3. **Then: discover the best and most promising advisors.** Knowledge pooled across advisors under the same access scopes, career-pattern signals with bias checks, and retention and revenue effects only once they can be attributed. CLTV and predictive scoring stay out until then.

## 10. Open decisions and limits

Confirm the business unit and SME role, the catalog sources and alias owners, which communications need compliance review, and retention requirements for notes and semantic QBRs. All data is synthetic, and the problem statements and targets are hypotheses to validate. Domain distinctions were checked against FINRA and SEC sources on 19 October 2026; registration rules still need jurisdiction-specific review.
