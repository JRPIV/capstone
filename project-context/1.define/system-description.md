# System Description: Automated Employee Onboarding Workflow

**Working title:** Automated Employee Onboarding Workflow  
**Author / stakeholder:** Joey  
**Selected runtime:** `crewai`, from `aamad.config.yml` `runtime.target`. `AAMAD_TARGET_RUNTIME` was not rechecked. The runtime is not an application pattern. Pattern, agent count, and work ownership belong to the SAD.

## 1. Intent and Problem

- **Problem statement:** HR, IT, hiring managers, and new hires hold different parts of the onboarding picture. An incomplete role, uncertain equipment delivery, or changed start date can make the shared plan unreliable. The project has not measured the time or cost of these failures in a target organization.
- **Primary users / operators:** The HR coordinator reviews the plan, approves held plans, and handles escalations. The hiring manager confirms the role, arranges the first-day meeting, and owns training. The IT fulfiller confirms an assigned laptop or an approved loaner. The new hire acknowledges policies and asks onboarding questions. The demonstration uses fictional people at one Austin office.
- **Success definition:** A local demonstration keeps a four-task plan accurate for synthetic Customer Support Representative hires. It requests missing facts, distinguishes uncertainty from confirmation, updates only the affected work, answers from an approved policy pack, and shows readiness with evidence. Week 6 is complete when an independent reviewer can run D1–D12 from the stated preconditions and reproduce the scored outcomes. No savings target is claimed.

## 2. Domain Context

- **Onboarding plan:** The owned, dated work for one hire. A supported plan has exactly four tasks. Each material plan or evidence change creates a new version.
- **Hire:** A synthetic employee record identified by hire ID. Seeded records are Jordan Lee (H-001) and Riley Chen (H-002). Evaluation also uses a third synthetic name and reviewer-written wording.
- **Approved role and location:** Customer Support Representative at a fictional Austin, Texas office. “CSR” is an approved alias, including within a sentence. Any other clear role or location is unsupported.
- **Task:** Policy acknowledgment, equipment readiness, first-day meeting, or customer-support tools orientation. Execution status is pending or complete. Readiness is confirmed, unconfirmed, or blocked. Overdue and escalated are additional indicators.
- **Controlled fact:** A fact that only a designated role may establish. A reply from the wrong role is kept and cannot establish that fact. The sender’s role comes from the simulator, not from the message text.
- **Clarification round:** One targeted follow-up that names the missing fact. A second insufficient reply, or no reply by the request deadline, escalates. A materially new fact may open a new round. Duplicate or unchanged messages do not reset the limit.
- **Readiness:** Overall day-one state is Ready only when policy acknowledgment is complete, equipment is confirmed, and the first-day meeting is manager-confirmed for the current start. Training must be assigned with a valid deadline and need not be finished before day one. Otherwise the state is Needs attention, with explicit reasons.
- **Policy pack:** Fictional passages P1–P4 in PRD Appendix A. The pack does not answer pay, overtime, remote work, or legal eligibility.
- **Existing workflow respected:** No production HR, IT, identity, or messaging system is connected. Participants are simulated. One person may play every role.
- **Commercial context, not a measured market:** The PRD cites an adjacent onboarding-software category and names Workday, SAP, ServiceNow, Enboarder, and ClearCompany as overlapping products. Those statements are background. They are not acceptance criteria.

## 3. Discovery Buckets

The PRD discovery table is the stakeholder answer to these four buckets. “Requirement” means the proposed Week 6 release contract. “Assumption” means a planning choice the PRD leaves unconfirmed. Nothing in this section approves an assumption or selects an application pattern.

### Must do

| ID | Item | Kind | Testable constraint |
| --- | --- | --- | --- |
| MD-001 | Coordinate the four approved tasks across varied synthetic hires and replies | requirement | A complete supported intake creates exactly the four Appendix A tasks, with that table’s owners and offsets. The same rules hold for a third synthetic name, different dates, and reviewer-written wording, without hard-coded person, date, or sentence matches. |
| MD-002 | Request missing facts, distinguish uncertainty from confirmation, and preserve plan history | requirement | An insufficient reply produces one targeted follow-up naming the missing fact. A possible loaner or a delivery estimate stays unconfirmed. Only an explicit authorized commitment that meets BR-4 confirms equipment. Prior messages, versions, and escalations remain visible. |
| MD-003 | Apply deterministic authority, date, dependency, and approval rules | requirement | Role, meeting, equipment, acknowledgment, and training completion follow BR-2. Austin local time, Monday–Friday dates, and the Appendix A offsets are computed without a holiday calendar. Fixed rules remain in force when model output disagrees. |
| MD-004 | Use Customer Support Representative and the Austin office as the demo segment | assumption | “CSR” activates the approved plan. A clearly different role or location is labeled unsupported and is not mapped to invented tasks. This segment is retained from the supplied draft, not from a confirmed customer. |
| MD-005 | Approve held plans and auto-activate complete records | assumption | A missing role creates no tasks and one manager request. A supported role from the designated manager waits for HR approval. A complete supported intake activates with no approval hold. |
| MD-006 | Reserve a confirmed device until onboarding completes | assumption | Under fictional P2, a confirmed device stays reserved from its ready date until onboarding completes unless IT revokes it. A later start date does not turn a delivery estimate into confirmation. |
| MD-007 | Close a factual escalation without a new HR approval | assumption | No asset tag is required. Sufficient authorized evidence updates the task and closes the related factual escalation. The escalation history remains. That evidence does not approve a separate pending plan. |

### Must not do

| ID | Item | Kind | Testable constraint |
| --- | --- | --- | --- |
| MN-001 | Create production accounts, change access, process identity documents, or decide work eligibility | requirement | No scenario creates an account, changes access, accepts an identity document, or produces an eligibility decision. D12 fails if any of those occur. |
| MN-002 | Treat conversation text as permission to change policy or the sender’s role | requirement | Message wording cannot change P1–P4 or assign the sender a role. Actor identity and role come from the simulator. A new hire’s confirmation cannot confirm equipment. |
| MN-003 | Invent policy, confirm on weak evidence, or hide a failed interpretation | requirement | Out-of-pack questions are routed to HR with no invented answer. “I’ll try,” a possibility, or an estimate does not confirm equipment. A model or retrieval failure shows retry or manual review and leaves the last verified facts unchanged. |
| MN-004 | Contact production HR, identity, or messaging systems | requirement | Tools read synthetic records, retrieve the approved policy pack, write local case history, and exchange simulated messages. A run has no production-system call. |
| MN-005 | Let an exception decision rewrite evidence or block the other tasks | requirement | An HR decision to proceed does not mark missing evidence confirmed or an incomplete task complete. Unresolved equipment does not automatically block policy, meeting, or training. |
| MN-006 | Process payroll or tax | requirement | No path calculates, files, or changes payroll or tax. |

### Must cost

| ID | Item | Kind | Testable constraint |
| --- | --- | --- | --- |
| MC-001 | Run locally with metered model use | assumption | The scored demo runs on one development machine. Each recorded model call can report usage and cost when the provider supplies them. No monetary cap is set. |
| MC-002 | Answer inside proposed local time bounds | assumption | A submitted event is acknowledged within 2 seconds. A result or a visible failure appears within 60 seconds, including any bounded retry. These are planning targets, not observed measurements. |
| MC-003 | Limit demo capacity and concurrency | assumption | Persistent storage holds both seeded hires. One person runs the demo, and events are processed sequentially. |
| MC-004 | Settle model and spend before paid evaluation | assumption | Model choice and a spend limit are recorded before a paid scored run. Usage is recorded before any cost forecast. |

### Must prove

| ID | Item | Kind | Evidence the system must produce |
| --- | --- | --- | --- |
| MP-001 | Pass the independently scored Week 6 scenarios | requirement | A results sheet with inputs, outputs, expected results, and pass/fail for every D1–D12 row. Each row starts from its stated precondition or a reset fixture. Failed attempts are preserved. |
| MP-002 | Show no forbidden outcomes in the evaluation set | requirement | The sheet shows zero unsupported confirmations, invented policy answers, duplicate tasks, and cross-hire changes. |
| MP-003 | Let an unfamiliar reviewer operate the demo | requirement | Using the runbook, the reviewer finds the outstanding owner and next action and records an HR decision without opening a raw model transcript. |
| MP-004 | Record operational measures without claiming savings | requirement | The run records resolution time, human messages required, unnecessary follow-ups, and unresolved day-one conditions. No savings figure is reported from the demo alone. |

## 4. Functional Requirements

| ID | Description | Priority (Must/Should/Could) | Source bucket ID |
| --- | --- | --- | --- |
| FR-001 | Create exactly four owned, dated tasks for a complete supported record; show missing fields or an error for incomplete or unreadable input; label unsupported role or location for HR review; ignore a repeated intake event. | Must | MD-001 |
| FR-002 | Hold task creation while role is missing; ask the designated manager; accept an authorized “CSR” reply as a plan awaiting HR approval; follow up once on an ambiguous reply; escalate on a second insufficient reply or a missed deadline; ignore another participant’s attempt to set the role or approve the plan. | Must | MD-002 |
| FR-003 | Treat a possible loaner as unconfirmed; ask IT once for an explicit commitment and ready date, citing P2; confirm only when BR-4 is met; block and escalate when no permitted device exists by the start date; clear a factual escalation when sufficient authorized evidence arrives later, without erasing its history. | Must | MD-002 |
| FR-004 | After a start-date change, keep completed work complete, recalculate unfinished offsets, reconfirm an unheld meeting, re-evaluate equipment against the new date, and retain prior versions. A repeated change event does not repeat the request. | Must | MD-003 |
| FR-005 | Answer paraphrased P1–P4 questions with a citation that preserves the passage. A loaner answer does not claim equipment was arranged. Route pay, overtime, remote work, and eligibility questions to HR. A retrieval failure produces no policy conclusion. | Must | MD-002 |
| FR-006 | Show BR-6 readiness with evidence links. HR can approve a held plan and record an escalation disposition with identity, timestamp, rationale, and version. A later conflicting change flags that decision for review and preserves it. | Must | MD-003 |
| FR-007 | Persist tasks, messages, versions, and decisions across restart. Apply an event only to its hire. Reject repeated event IDs. Leave last verified facts intact when interpretation fails, and show the failure. | Must | MP-001 |

PRD stories FR-01 through FR-07 are the source text for FR-001 through FR-007. This table does not replace those stories.

## 5. Non-Functional Requirements

| ID | Description | Priority (Must/Should/Could) | Source bucket ID |
| --- | --- | --- | --- |
| NFR-001 | Acknowledge a submitted event within 2 seconds, and show a result or visible failure within 60 seconds, including a bounded retry. | Should | MC-002 |
| NFR-002 | Store both seeded hires, support one person running the demo, and process events sequentially. | Should | MC-003 |
| NFR-003 | Pass restart, duplicate-event, cross-hire isolation, and model-failure checks. | Must | MP-001 |
| NFR-004 | Use synthetic data only. Keep secrets out of the interface, history, and exported artifacts. Take actor identity from the simulator. | Must | MN-001 |
| NFR-005 | Record event ID, hire ID, actor, time, result, evidence, plan version, model latency, and usage or cost when available. | Must | MP-004 |
| NFR-006 | Make core controls keyboard-operable, associate input labels, use readable status text, and avoid color-only distinctions. | Must | MD-003 |
| NFR-007 | Support repeatable local launch, reset, and scenario replay. Claim no hosted uptime SLA. | Must | MC-001 |

NFR-001 and NFR-002 remain planning targets. They are not measured production commitments.

## 6. Constraints

- **Technology:** Local browser and persistent storage. CrewAI conventions apply after the SAD. This description does not choose an application pattern, agent count, or work ownership. Bounded execution, tool permissions, retries, and per-event timeouts are architecture settings still to be confirmed.
- **Calendar:** Austin local time, Monday–Friday business days, no holiday calendar. Task deadlines are 5:00 p.m. Austin time unless P2’s start-of-work rule applies. Relative dates are normalized to the message timestamp and shown; more than one plausible date requires clarification.
- **Identity:** The simulator supplies sender ID and role outside the message text. This is not production authentication.
- **Budget and timeline:** One builder, one development machine, synthetic fixtures, and an independent reviewer. The launch in scope is the Week 6 demonstration. Model and spend limits are unset.
- **Integration:** Inputs are new-hire records, the task and policy pack, actor-attributed messages, task updates, and start-date changes. Persist hire ID, owners, source events, questions, replies, task status, plan version, evidence references, and human decisions. Do not integrate with production HR, IT, identity, or messaging.

## 7. Assumptions

- The PRD is a proposed baseline, not stakeholder approval or implementation completion.
- Austin, the Customer Support Representative role, all dates, and P1–P4 are fictional evaluation data retained from the supplied draft.
- HR approval for a held plan, automatic activation of a complete supported record, device reservation, and closing a factual escalation without a new HR approval are unconfirmed planning choices.
- Response targets and sequential processing are local-demo choices, not observed performance.
- Market research was not skipped. Production deployment and commercial launch are deferred.
- CrewAI is the configured runtime target. Adapter settings were not inspected during this elicitation.

## 8. Acceptance Criteria

- **AC-001:** Given Riley’s complete record, when it is loaded, then exactly four tasks exist, owners and due dates match Appendix A, and the plan is not held for approval. (D1)
- **AC-002:** Given Jordan’s missing role, when the record is loaded, then no tasks exist. When Sam replies “We hired a CSR” and HR approves, then the plan is proposed after the reply and active only after that approval. (D2)
- **AC-003:** Given a reset, when an ambiguous role is supplied twice or the request deadline passes with no reply, then that round has at most one targeted follow-up, no invented role, and a visible HR escalation. (D3)
- **AC-004:** Given an activated Jordan plan, when IT sends the uncertain equipment reply, then equipment is unconfirmed, one P2 follow-up asks for commitment and date, and the other tasks keep their state. (D4)
- **AC-005:** Given separate runs, when Jordan’s sufficient reply is sent, then equipment is confirmed. When Riley’s denial is sent, then equipment is blocked and escalated, with no extra follow-up. (D5)
- **AC-006:** Given Riley’s escalation, when IT confirms a loaner by March 16, then the factual escalation closes and the history remains. When the new hire submits the same confirmation, then equipment stays unconfirmed. (D6)
- **AC-007:** Given completed policy and a meeting confirmed for the old date, when an Appendix A later start is applied, then policy stays complete, the meeting needs reconfirmation, training dates match the table, covered committed equipment stays confirmed, and an estimate alone stays unconfirmed. (D7)
- **AC-008:** Given Jordan equipment committed only for March 2, when the start moves to February 27, then equipment is blocked, the meeting needs reconfirmation, unfinished dates recalculate, overdue flags appear, and completed policy stays complete. (D8)
- **AC-009:** Given paraphrased P1 and P2 questions and a remote-work question, when they are asked, then P1 and P2 are cited correctly, the loaner answer does not imply a booking, and remote work is routed to HR with no invented answer. (D9)
- **AC-010:** Given completed policy, confirmed equipment and meeting, and assigned training, when IT revokes equipment, then the state is Ready only before revocation and Needs attention afterward, and affected prior HR decisions are preserved and flagged for review. (D10)
- **AC-011:** Given a stored reply, when the application restarts, the event ID is replayed, a model call fails, and Jordan is updated while Riley exists, then state survives, work is not duplicated, the failure is visible without invented facts, and Riley is unchanged. (D11)
- **AC-012:** Given a third synthetic hire, different dates, and reviewer-written wording, when the core role and equipment cases are repeated, then the same rules apply and no live provisioning, access change, identity document, or eligibility decision occurs. (D12)

## 9. Out of Scope / Future Work

- **Deferred (P1):** Additional roles and locations, holiday calendars, richer reporting, and a user-selected live communication channel.
- **Future (P2):** Production HR or IT integrations, enterprise identity controls, multiple concurrent operators, and commercial packaging.
- **Excluded now:** Production account or access changes, sensitive identity documents, legal eligibility determinations, and payroll or tax processing.
- **Not claimed:** Legal or regulatory certification, a hosted uptime SLA, production scaling, pricing, or a proven savings figure.

## Sources

- `project-context/1.define/prd.md`, Joey’s chosen PRD, revision date November 5, 2026. Supplies the problem, users, discovery kinds, business rules, stories, non-functional targets, D1–D12, assumptions, and open questions.
- `aamad.config.yml`: `project.mode: greenfield`, `runtime.target: crewai`.
- `project-context/1.define/mrd.md` is the onboarding market-research file. Its title is “Market Research Document: Automated Employee Onboarding Workflow.” The PRD cites “*Employee Onboarding MRD — Business Rewrite*.” That title was not found in the MRD file. The MRD was not edited.
- The previous payroll system description matched `project-context/1.define/reference/payroll/system-description.md` and remains there.

## Assumptions

- This elicitation records the chosen PRD. It does not re-interview Joey, approve the PRD assumptions, or change PRD or MRD text.
- Rows tagged assumption are still open planning choices.
- No application pattern is selected here.

## Open Questions

1. **Course architecture requirement:** Must the capstone demonstrate multiple autonomous agents, or can a coordinator with tools satisfy the rubric? Confirm before the SAD assigns work.
2. **Model budget:** What spend limit and model or provider should govern development and scored runs? This determines execution limits and operating-cost measurement.
3. **Customer validation access:** Is an HR or IT practitioner available to review the workflow? If not, Week 6 can validate specified behavior, while customer usefulness remains unvalidated.
4. **MRD citation:** Which document is the PRD’s “Employee Onboarding MRD — Business Rewrite”? The current `mrd.md` title does not use those words.

## Audit

- **Timestamp:** 2026-11-05
- **Persona ID:** product-mgr
- **Action:** elicit-requirements
- **Resolved runtime:** crewai (`aamad.config.yml` `runtime.target`). `AAMAD_TARGET_RUNTIME` was not rechecked. No application pattern selected.
- **Prompt trace:** Omitted. This file transcribes the chosen PRD into the system-description template and does not add product decisions.
