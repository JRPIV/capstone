# System Architecture Document: Automated Employee Onboarding Workflow

**Status:** Proposed Week 6 MVP architecture. Work Ownership, Pattern Decision, Reference Architecture, Model and Context Strategy, Control Register, and Production Shape are recorded. Product questions and implementation decisions that are still open are listed under Open Questions.  
**Purpose:** Coordinate a local onboarding demonstration. The application keeps each new hire’s plan accurate, interprets replies, answers from an approved policy pack, and shows HR what still needs attention.  
**The main design:** AI helps read language. Application code applies the rules and keeps the record. HR approves a plan that was held for a missing role, and HR decides exceptions.  
**Product:** Automated Employee Onboarding Workflow. Fictional employees, fictional policies, and simulated HR and IT messages. No connection to production HR, IT, identity, or messaging systems.  
**Primary input:** `project-context/1.define/prd.md` (proposed Week 6 baseline, revised November 13, 2026). Product behavior in this document follows that file. The business-process figure and the Jordan Lee walkthrough stay in PRD §2. They illustrate the rules. They are not extra architecture, and they are not extra scored tests. D1–D12 remain the scored set.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md`  
**MRD** (optional): `project-context/1.define/mrd.md`  
**System Description** (when present): `project-context/1.define/system-description.md`  
**User Stories** (when present): `project-context/1.define/user-stories/US-001.md` through `US-007.md`  
**MVP Scope**: Customer Support Representative, including the alias “CSR,” in Austin. Four Appendix A tasks. One operator. One event at a time. Jordan Lee (H-001), Riley Chen (H-002), and additional fictional inputs.  
**Selected Runtime**: `crewai`. `aamad.config.yml` sets `runtime.target: crewai`. `AAMAD_TARGET_RUNTIME` is unset. The adapter registry default is `crewai`. Checked again on November 13, 2026.

References such as **BR-1** identify a business rule in the PRD. **FR** identifies a feature requirement, **US** a user story, and **D1–D12** the twelve demonstration scenarios. **P1–P4** are the approved policy passages. Task owners, deadlines, and the seeded records are Appendix A.

## System Architecture Specification

### Work Ownership

Each row is one user-visible step from the PRD §2 journey and from US-001 through US-007. The owner is model, existing system, human, or collaborative (draft, then decide).

In this MVP, **existing system** means the local case store and the deterministic rules this product will implement. That store still has to be built. Workday, SAP, ServiceNow, Enboarder, and ClearCompany are market context. None of them is the system of record.

Four limits of a model call decide the split:

- **Probabilistic output.** A draft can read “may,” “I’ll try,” or a paraphrase as a commitment. Confirmation, readiness, task creation, and authority are rule outcomes.
- **Knowledge cutoff.** P1–P4 are the policy source. The model does not supply policy from its own knowledge.
- **Limited working memory.** Tasks, messages, versions, evidence, and decisions live in local storage. The model does not hold the plan.
- **Steerability.** Follow-up limits, idempotency, employee separation, and the equipment rule are code. A prompt cannot be the control that enforces them.

| Step | Owner (model / existing system / human / collaborative) | Reversibility | Stakes | Accountable party | Rationale |
|------|----------------------------------------------------------|---------------|--------|-------------------|-----------|
| Submit an intake, reply, start-date change, or policy question | human | Later authorized updates can correct the situation. The original message stays in history. | Medium. The message is evidence. Wording alone does not change a controlled fact. | Person playing the simulated role | The server records who sent the event separately from the message text (PRD §3 Identity). One person may play every role. |
| Validate intake and create or hold the plan | existing system | An error or an unreadable input writes no plan. A successful activation is one versioned plan. | High. Invented tasks or an empty ready state fail D1 and D12. | Application | Two activation paths are specified in PRD §2 and BR-1. A complete supported record activates the four Appendix A tasks. A blank role creates one manager request and no tasks. A repeated intake event does not create a second plan (FR-01, FR-07). |
| Interpret a written reply | collaborative | A rejected interpretation does not change verified facts. The message is kept. | High. Treating “a loaner may be available” or “I’ll try” as confirmation fails D4 and D5. | Application for any fact that is recorded. The sender for the words. | The reply reader drafts a structured reading. The application accepts it only when the server-side role and BR-1 through BR-5 agree. “CSR,” including inside a sentence, is a rule, not a model privilege (BR-1, BR-7). |
| Record a confirmed fact, ask one follow-up, or escalate | existing system | The update keeps history. An escalation stays visible after later evidence closes the factual issue. | High. A second follow-up in the same round, or a fact taken from the wrong role, fails D3 through D6. | Application | Sender authority, evidence, and the one-follow-up limit are BR-2 and BR-3. A definite equipment denial is blocked and escalates without another clarification (PRD §2 step 6, BR-4). |
| Approve a plan held for a missing role | human | The approval stays in history. It authorizes the plan to begin. It does not certify later readiness. | High. A held plan that becomes active without HR fails D2. | HR coordinator | A supported role from the designated manager produces a proposed plan. HR activates it. Facts supplied before that approval do not activate the plan (PRD §2 steps 3–4, Appendix A, BR-1). |
| Hold a role or location change after activation | existing system, then human review | The current plan stays in place. No new task set is written. | Medium. Automatic replanning would invent work this MVP excludes. | Application for the hold. HR coordinator for the review. | BR-1 and PRD §2 step 8 require HR review. This row does not add a decision type beyond US-006. |
| Adjust unfinished work after a start-date change | existing system | Earlier plan versions remain available. Completed work stays complete. | High. A wrong date, a meeting left confirmed for the old date, or an estimate treated as a commitment fails D7 and D8. | Application | Offsets, meeting reconfirmation, and equipment re-evaluation are BR-5, BR-7, P2, and P3. A duplicate change event does not repeat the request (FR-04). |
| Answer a question covered by the policy pack | collaborative | A failed draft is withheld. Task evidence is unchanged. | Medium. A wrong citation, or a loaner answer that claims equipment was arranged, fails D9. | Application for the published answer. The pack for the meaning. | The policy answerer drafts from retrieved P1–P4 passages. The application publishes the answer only when the citation is valid and the meaning check passes (FR-05). |
| Route an unsupported policy question to HR | existing system | No policy conclusion is recorded. | Medium. An invented answer on pay, overtime, remote work, or eligibility fails D9. | Application for the route. HR for any answer given outside the product. | Those topics are outside P1–P4 (PRD §2, Appendix A). |
| Show readiness, overdue work, and supporting evidence | existing system | Recalculated from saved records. The summary writes no new fact. | High. Showing Ready without all four BR-6 conditions fails D10. | Application | Execution status stays separate from readiness. An HR exception does not turn missing evidence into confirmation. Unresolved equipment does not stop the other three tasks (BR-4, BR-6, PRD §2). |
| Decide whether to proceed despite an exception | human | The decision remains, tied to the plan version it concerned. A later conflicting change flags it for review. | High. The decision can authorize proceeding while evidence is still missing. | HR coordinator | Exceptions stay with a person (PRD §1, FR-06). The application stores identity, time, rationale, and plan version, and leaves the unresolved task visible. |
| Restore the last verified case after restart or failure | existing system | An invalid update is withheld. A repeated event ID adds no work. The same id with different contents is rejected and does not open a second case. | High. A lost plan, a duplicate, a cross-hire change, or a hidden failure fails D11. | Application | Tasks, messages, versions, and decisions persist locally. A write names one hire (FR-07, CR-004, CR-005). |

**Feasibility verdict**: `feasible as scoped`  
**Load-bearing constraint** (required when the verdict is constrained): None. The PRD already places approvals and exceptions with people, live records and BR-1 through BR-7 with the application, and unbounded language in a draft the application accepts or rejects. Production accounts, access changes, identity documents, eligibility decisions, and payroll or tax processing are outside the owned steps.

### Pattern Decision

- **Primary shape**: workflow
- **Workflow sub-shape**: combination: routing, then chaining on the selected model route
- **Deciding factor**: Predictability. The next step is fixed by the event type and by BR-1 through BR-7. Code chooses the path. The model does not choose the next step, the next tool, or whether to send a follow-up. An incorrect confirmation could make an unprepared employee appear ready (D4–D6), so that choice cannot sit with the model.
- **Rejected alternatives and reversal cost**:
  - **Augmented call.** One model response cannot hold the case across a later reply, a start-date change, and an HR approval. Reversal cost is low as a starting point and high as a destination: storage, routing, and the human decision record would still have to be built.
  - **Agent.** The path can be written in advance, and a false confirmation is consequential. The MRD executive summary says to use agents to interpret responses and choose follow-up actions. The PRD is the release contract: BR-3 already chooses the follow-up (one targeted request, then escalation). Reversal cost of an agent is high, because a later turn could route around BR-1 through BR-7. PRD Open Question 1 remains open if the course requires autonomous agents. This SAD does not change that product question.
- **Progression used**: A schema-bound prompt produces each draft. Retrieval is used only for P1–P4 on the policy route. The evaluator is the application’s rules, not a second model loop. Fine-tuning is not recommended. The rules and the four-passage pack are the control, and fine-tuning availability was not checked.

CrewAI may call the two roles “agents.” This product is still a workflow, because Python selects the task and the application writes the case. There is no autonomous manager and no delegation. Several named model roles are a workflow when code owns the sequence. They would be an agent only if a model chose the next role.

Agent-only fields are not applicable:

- **Tool allowlist**: Not applicable. The primary shape is workflow. The two model tasks have no tools. Writes stay on the application. See the Control Register.
- **Turn budget**: Not applicable to an agent loop. Each model task is one draft. `max_iter` is set in the CrewAI subsection so the task cannot wander.
- **Stop conditions**: Not applicable to an agent loop. The application stops a model task when a schema-valid draft returns, the 60-second event budget is exhausted, or the call fails. The visible result is then the rule outcome or the failure state in US-007.

### Reference Architecture

| Shape | Use when | Known failure to prevent |
|-------|----------|--------------------------|
| Agent | Path cannot be written in advance | Unbounded tools |
| Retrieval | Stable documents, not live state | Retrieval used as a substitute for live state |
| Document pipeline | Structured extraction with an exception path | No exception path |
| Routing | Inputs vary in kind | No human escalation, or an agent shipped before the routed workflow was measured |
| Coding agent | Agentic exploration, then deterministic edit/test/review | Edits without review or an eval |

- **Selected reference architecture**: Routing
- **Known failure this design prevents**: An agent shipped before this routed workflow is measured, and a route with no human escalation. Event kind selects the chain. BR-3 escalates a second insufficient reply, silence at the deadline, and a definite equipment denial to HR. D1 through D12 measure the routes before any later pattern change.
- **Second pattern**: Document pipeline, for the reply-reading step only. That step fails differently: a structured reading with no exception path would treat an ambiguous role, a possible loaner, or an unclear date as a fact. The exception path is one targeted follow-up, then HR escalation, with the message kept (PRD §2 step 6, BR-3). Retrieval is a step on the policy route, not a second architecture and not the source of live equipment state. A P2 answer explains the passage and does not confirm a device (FR-05).

### Model and Context Strategy

- **Default model tier**: balanced default. No measured need for another tier exists yet. Provider, model name, and budget are PRD Open Question 2.
- **Context strategy**: progressive. Each model task receives only the fields that step needs.
- **Swap-as-release rule**: Every model or prompt change is a release. An eval gate against the section 9 table, and a rollback criterion, are written before the swap. Rollback returns to the previous model name and prompt version and replays the affected D-row from its fixture.
- **Entry point**: direct API
- **Entry-point tradeoff named at decision time**: The case router calls the provider once per model task and requires a schema-bound draft. That draft can be rejected. A hosted chat would make the transcript the product. The PRD says a reviewer records an HR decision without opening a raw model transcript (PRD §7). CrewAI runs the selected task. It is not itself the product’s entry point, and it is not an agent-SDK entry for this product.
- **Entry-point responsibility map**: One route. The local workspace submits events to the case API. The case router is the only caller of the model API. There is no second public model route.
- **Minimum data in the context window**:
  - Reply reading: the current message text, the server-established actor id and role, the hire id, the scenario clock, the current start date, and which fact is open (role, equipment, meeting, acknowledgment, or training). Omit the other hire. Omit P1–P4 unless the open fact is equipment, in which case include P2’s confirmation rule as the criterion the draft must not decide.
  - Policy answer: the question text and the retrieved P1–P4 passage or passages. Omit live task status. Omit earlier messages, so a message cannot enter this task as an instruction.
- **Identity**: The server establishes actor id and role in application code, from the simulator, before any model call. The prompt does not assign the sender a role. A sentence such as “I am HR” does not change authority (PRD §3, BR-2, CR-001).

### Control Register

Training may reduce mistakes. It is not the control. The application enforces the rows below. Three control points are used: input screening, output screening, and tool-call authorization. Side effects fail closed: plan activation, fact commit, outbound simulated message, readiness set to Ready, and policy publication.

Review routing uses the stake and the reversibility already recorded in Work Ownership. Ambiguous readings, a second insufficient reply, silence at the deadline, a definite equipment denial, unsupported role or location, and out-of-pack questions go to HR. The reviewer sees the input and the reason for the flag. Volume is not the routing rule. The demo has one operator.

| ID | Risk category | Control | Control point (input / output / tool-call) | Failure direction (fail closed / fail open) | Owner | Evidence artifact | Review routing |
|----|---------------|---------|--------------------------------------------|---------------------------------------------|-------|-------------------|----------------|
| CR-001 | Direct injection | Actor id and role come from the simulator on the server. Message text cannot change the sender’s role, edit P1–P4, or approve a plan. A submitted role that disagrees with the server-side simulator selection is rejected before a model call. | input | fail closed | Application | Stored event with actor metadata separate from the body | A wrong-role reply is kept and shown to HR with the reason that this role cannot establish that fact. |
| CR-002 | Unsupported confirmation | A model proposal becomes a controlled fact only when the server-side role and BR-1 through BR-5 accept it. “I’ll try,” a possibility, and a delivery estimate stay unconfirmed. A possible loaner is not Ready. | output | fail closed | Application | Proposal, rule result, and plan version | The first insufficient reply produces one follow-up that names the missing fact. The second, a missed deadline, or a definite device denial escalates to HR with the messages and the missing fact. |
| CR-003 | Indirect injection and invented policy | The policy task sees the question and the retrieved P1–P4 passages only. Publication requires a citation inside that set and a meaning check that preserves the passage. A loaner answer does not assert that equipment was arranged. Pay, overtime, remote work, and eligibility produce a route to HR and no drafted answer. Retrieval failure publishes no policy conclusion. | output | fail closed | Application | Citation check, meaning-check result, and, on failure, the retry or manual-review state | HR receives an out-of-pack question with the reason “outside the pack.” |
| CR-004 | Tool abuse | Model tasks have no write tool and no network tool. The application may read the named hire, read the approved pack, append a simulated message, and write that hire’s local history. Production HR, IT, identity, messaging, account, access, eligibility, and payroll operations are not allowed. A write names one hire id. | tool-call | fail closed | Application | Task tool configuration and a denied-call record | A denied call is visible as a failure. Last verified facts stay. HR sees that failure on the hire. |
| CR-005 | Duplicate side effects | For every event type, the server binds the submitted event id to the recorded contents defined in section 4 and reserves that pair before any follow-up is sent. After a committed result, the same id and the same recorded contents are a no-op: the original result remains, and the retry creates no additional task, question, completion, follow-up, decision, or hire. The in-flight check comes first. The same id while the first attempt is in flight returns `conflict`, whether or not the body matches, and does not start a second case. Once that attempt is no longer in flight, the same id with different recorded contents is rejected as `event_mismatch`: the new body is not applied, a committed result is not overwritten, and no second hire or plan is created. If that id has no committed result, the same contents may be retried; a different body is `event_mismatch`, not a new event. | input | fail closed | Application | Event-id index, including the recorded contents | No HR review. The original result remains the record. A mismatch is an error the workspace shows. |
| CR-006 | Token-budget and time exhaustion | The event budget is 60 seconds, including one additional attempt. Each model task uses `max_iter` 2. When the budget or the call fails, the UI shows retry or manual review and writes no new verified fact. Dollar and token ceilings are unset until PRD Open Question 2 is answered. Hitting a configured ceiling uses this same closed failure. The stop applies to that event. It is not a provider-wide circuit breaker. | tool-call | fail closed | Runtime | Per-event trace: event id, hire id, latency, usage when the provider supplies it | HR sees the failure and the last verified plan, not a partial model fact. |
| CR-007 | Data exposure | Synthetic fixtures only. Provider keys and raw provider payloads stay out of the workspace, the case history, and exports. | output | fail closed | Application | Review of the workspace, history, and export against PRD §5 | The operator reviews the demo artifacts. The model is not the reviewer. |
| CR-008 | Decision-log gap | A fact commit, plan activation, outbound follow-up, or HR decision is stored with event id, hire id, actor, time, route, proposal if any, rule result, evidence reference, and the plan version the decision concerns. A commit that cannot store that record is refused. | output | fail closed | Application | Plan version and case history | The reviewer reconstructs the step from the case. A raw transcript is not required (PRD §7). |
| CR-009 | Fairness injection | Who is asked, and which four tasks exist, comes from Appendix A and BR-2. The corpus is P1–P4. Prompt framing for the two drafts cannot assign a different task set. An unsupported role or location is labeled for HR review. This MVP makes no eligibility decision. | input | fail closed | Application | D12 record and the unsupported-role label | HR sees the intake and the label. The product does not map the person onto invented tasks. |

### Production Shape

- **Expected volume:** One operator, sequential events, and both seeded hires in local storage. A third synthetic hire appears in D12. This is the demonstration volume from PRD §5. It is not a production forecast. The MRD has no measured throughput or runtime cost.
- **Retries:** The product rule is one additional attempt after a short delay, inside the same 60-second event budget (PRD §5). The event id and its recorded contents are reserved before any follow-up is sent, so a retry cannot send a second follow-up. A client resubmission is not a second case and is not an extra model attempt stacked inside the in-flight budget. After a committed result, the same contents are a no-op and send nothing further. While the first attempt is in flight, the resubmission is `conflict`, whether or not the body matches. After an uncommitted failure, only the same contents may be submitted again. That later execution still fails closed under CR-006: the failed attempt writes no new verified fact, and the reservation still blocks a second follow-up. Different contents, once the attempt is no longer in flight, are `event_mismatch`. Fallback is the visible manual-review state. There is no second model that invents a fact. How that one additional attempt lines up with CrewAI `max_retry_limit`, `max_iter`, and any provider-library retry is an open implementation decision. Those layers must not stack into more than one additional model attempt for the event. CR-006 is unchanged.
- **Per-event timeout:** When the 60-second budget is exhausted, further model calls for that event stop. The case stays on the last verified facts, and the workspace shows the failure. This timeout is scoped to the event.
- **Provider-wide circuit breaker:** A mechanism that pauses calls for every hire after repeated provider failures is not specified. Whether the MVP needs one is an open implementation decision. The per-event timeout is not that mechanism.
- **Failure mode of this architecture:** The router sends an event down the wrong chain, or a model draft is written before the rule gate. Mitigation: the route is a function of event type plus stored case state, and only the application writes after CR-002 and CR-003.
- **Traces and dashboards:** Each event writes the CR-008 record. That per-request trace is the MVP observability design. The Week 6 results sheet is the aggregate record: resolution time, human messages, unnecessary follow-ups, unresolved day-one conditions, timing, and usage when available. An aggregate dashboard is P1 (“richer reporting”).

### 1. MVP Architecture Philosophy & Principles

**MVP Design Principles**:

- The reviewer can see what is ready, what is missing, who owns the next action, and why, without a raw transcript (PRD §6 and §7).
- The orchestration is the recorded workflow: route, then a rule gate, with a model draft only on reply reading and in-pack policy answers.
- Observable by default: the CR-008 case record and a health check.
- Deliver adds local launch configuration only. No hosted deploy is in this release.

**Core vs Future Features**:

- **MVP**: FR-01 through FR-07, BR-1 through BR-7, Appendix A fixtures and P1–P4, the browser workspace in PRD §6, simulated actors, local persistence, reset and replay. Day-one readiness is in scope. Closing or archiving the case is not (PRD §2 process boundary, PRD Open Question 5).
- **Future**: P1 adds roles, locations, a holiday calendar, richer reporting, and a user-selected live channel. P2 adds production HR/IT integrations, enterprise identity, concurrent operators, and commercial packaging. Excluded now: production accounts, access changes, identity documents, eligibility decisions, and payroll or tax.
- Deferrals follow the PRD. This SAD does not pull P1 into the MVP.

**Technical Architecture Decisions**:

- The primary surface is the PRD §6 workspace: hire list, task plan, readiness summary, task-specific conversation, version history, and a simulated actor selector. `ux.md` does not exist yet. Layout belongs to `@ux.designer`. This SAD does not turn that workspace into a general chat.
- The frontend framework is not named by the PRD. The proposed MVP shape is one local Python process that serves the workspace and the API, so the demo has a single launch command. Python is a proposed choice. The repository has not settled it. A separate SPA is future work unless `ux.md` requires it.
- Runtime communication implements the workflow: the workspace submits an event, the API acknowledges it, the router runs one chain, and the workspace reads the updated case. Model calls are non-streaming. The user sees a processing state, then the case result or a visible failure.

**Requirement mapping**:

| PRD / story | Component |
|---|---|
| FR-01 / US-001 intake, both activation paths, idempotency | Router and case system. No model task. |
| FR-02 / US-002 missing role, HR approval | Case system request and hold. Reply-reading task when the manager answers. HR decision on the workspace. |
| FR-03 / US-003 equipment uncertainty | Reply-reading task, then BR-4 in the case system. |
| FR-04 / US-004 start-date change | Case system only. |
| FR-05 / US-005 policy answers | Policy task, pack retrieval, citation and meaning gate. Out-of-pack route has no model task. |
| FR-06 / US-006 readiness and decisions | Case system summary from BR-6. HR writes the decision against a plan version. |
| FR-07 / US-007 restart, replay, isolation, failed interpretation | Local store and CR-004 through CR-008. |

### 2. Application Runtime Specification

The pattern is a workflow. Runtime roles exist only for the two model tasks. The router, the rules, and the store are application code. There is no manager agent and no delegation.

**Runtime roles**:

| Role | Job | Permissions and memory |
|---|---|---|
| `reply_reader` | Return a schema-bound reading of one message. For equipment, that reading is the section 4 equipment reply draft: one `statements` entry per device claim, plus claimed fact, uncertainty, and date candidates. The draft does not confirm a fact. | No tools. No persistent memory. The router passes the minimum context above. |
| `policy_answerer` | Return a proposal for the candidate passages: `citations`, one `grounding` excerpt per citation, and `covered` as trace only, or a structured cannot-answer with no citations. The proposal is not the published answer. | No tools. No persistent memory. The router passes the question and the candidate passages only. |

**Task / Turn Orchestration**:

- The router selects at most one model task from the event type and the stored case. Intake, start-date change, deadline, HR decision, duplicate event, unsupported role or location, and out-of-pack questions call no model.
- Reply chain: `reply_reader` draft, then the application accepts or rejects it, then the application commits, sends one targeted follow-up, or escalates.
- Policy chain: the section 4 question detector classifies the question first. Recognition does not use retrieval terms. Any pay, overtime, remote-work, or legal-eligibility match routes the whole question to HR and calls no model, even when a pack obligation or an equipment instruction is also present. An equipment-changing instruction is manual review and calls no model. An ambiguous question, including a pack match plus a clause that matched nothing, is manual review and calls no model. Otherwise keyword retrieval selects candidate passages only and does not decide that the question is answered. No candidates means manual review and no model. A question that matched nothing uses that same retrieval path; the gate still cannot publish it, because no pack obligation was detected. Otherwise `policy_answerer` returns a proposal, and the publication gate decides. The model’s `covered` flag does not decide.
- Context passed into a task is the minimum set above. The task does not receive the other hire’s plan.
- Expected model output is a schema, not a user-facing essay. The workspace renders the application’s labels (“Awaiting IT confirmation,” “No device confirmed for start,” “Meeting needs reconfirmation”) from PRD §6.
- Errors: a schema-invalid draft, a timeout, or a provider error leaves the last verified facts and sets a visible failure. Cancellation for that event is the 60-second budget. A second event while one event is in flight is refused for the whole demo (one operator, sequential processing, PRD §5).
- Budgets: acknowledge the submission within 2 seconds. Finish with a result or a visible failure within 60 seconds, including one additional attempt (PRD §5). `max_iter` 2 on each model task.

**Runtime-Conditional Configuration**:

- **crewai**: Checked against `.cursor/rules/adapter-crewai.mdc`. Sequential process. `allow_delegation: false`. `memory: false`. Composition is two YAML roles and two YAML tasks. Python selects which task runs. The router is not a third CrewAI role. Proposed files, not yet created: `config/agents.yaml`, `config/tasks.yaml`, and `crew.py`. `max_iter: 2` is inside the adapter ceiling of 12 and is justified because the task is one draft, with one internal schema retry, not a tool loop. `max_execution_time: 60` seconds matches the PRD event budget. `max_rpm` is unset until PRD Open Question 2 sets a spend cap. The adapter asks for a crew-level rate, so this setting is not yet satisfied. Hierarchical process is not used. `kickoff_for_each` is not used. Events are sequential, and the merge key is `event_id`. The two model tasks are alternative routes, not a chain of both, so task context is passed by the router rather than by `Task.context` between them. The rule gate after the draft is application code.
- **Retry setting:** The adapter requires `max_retry_limit >= 2`. A crew value of 2 would meet that floor. The product rule is one additional attempt in total, including library retries. Setting `max_retry_limit: 2` and also retrying inside the application would exceed that rule if the CrewAI value means two retries. This conflict is open. Do not implement a stacked retry until it is resolved.
- **claude-agent-sdk**: Not selected.
- **cursor-sdk**: Not selected.

### 3. Frontend Architecture Specification

**Technology Stack**:

- The PRD requires a local browser workspace and does not name a framework, component library, or styling system (PRD §6).
- Proposed choice: the same Python process serves the HTML workspace and the API. The repository has not settled Python, the frontend framework, or a styling system. No second UI framework is required for the MVP unless `ux.md` requires one.
- `@ux.designer` may refine layout without changing BR-1 through BR-7 or the authority and readiness rules (PRD §6).

**Application Structure**:

- One workspace view. Regions: hire list, the selected hire’s task plan, readiness summary, the conversation for the selected task, and version history. The actor selector, event submission, and test reset sit with the event controls.
- The frontend epic builds these regions against the section 4 contracts and does not wire the live client. The integration epic binds them.
- Core controls are keyboard-operable, inputs have labels, status is text, and status is not color alone (PRD §5). The demo is one laptop operator. A phone layout is not a PRD requirement.

**Interface Requirements**:

- Primary surface: the PRD §6 workspace. The simulated actor selector supplies messages and events. Confirmation and approval controls render only for the selected simulated role. The backend also enforces that permission (BR-2).
- The workspace generates the intake `event_id` before submission and keeps that submission so a lost acknowledgment can be retried with the same id and the same recorded contents. It does not assign `hire_id`. The event id does not activate a plan, confirm a fact, set readiness, or choose a role.
- States the workspace must show: processing, result, delivery failure, timeout, unsupported input, overdue, escalated, unconfirmed, blocked, and manual review. Messages remain visible when they do not resolve the task. Out-of-pack questions are requests for HR help, not generic refusals (PRD §6).
- The summary answers what is ready, what is uncertain, who owns the next action, and what changed. Each confirmed arrangement links to its evidence (FR-06).
- Future-work placeholders, visibly marked and inactive: additional roles and locations, a holiday calendar, richer reporting, and a live communication channel.

### 4. Backend Architecture Specification

**API Architecture**:

The model call is non-streaming. The submission is acknowledged before the model returns, which is how the 2-second target and the 60-second result target coexist (PRD §5).

| Contract | Required information |
|---|---|
| Submit an event | Client-supplied `event_id` (required on every event, including intake; the server stores it and does not replace it). `hire_id` is required for every type except `intake`, which may omit it. Also `event_type`, `actor_id`, `actor_role`, `occurred_at`, and `body` |
| Event types | `intake`, `reply`, `start_date_change`, `policy_question`, `deadline_reached` |
| Simulated roles | `hr_coordinator`, `hiring_manager`, `it_fulfiller`, `new_hire` |
| Submission acknowledgment | The submitted `event_id` unchanged, the server-assigned `hire_id`, and `status: processing`, within 2 seconds |
| Read a hire | Current case state: start date, role, location, `plan_version`, tasks (owner, execution status, readiness, due date, evidence refs), overall readiness (`ready` or `needs_attention`) plus reasons, messages, versions, decisions, and `failure` or null. Also `events`, one entry per submitted event: `event_id`, `event_type`, `state` (`processing`, `complete`, or `failed`), and `failure` or null. The task list is the current case. It is not a claim that the event the client just submitted created every task. |
| Record an HR decision | `decision_id`, `hire_id`, `actor_id`, `actor_role`, `decision_type`, `rationale`, `plan_version` |
| Decision types | `approve_held_plan`, or `escalation_disposition` |
| Error response | `code`, readable `message`, `event_id`, and `hire_id` when the server has assigned one |

Error codes distinguish `unreadable_input`, `unsupported`, `model_failure`, `conflict`, and `event_mismatch`. `conflict` is the sequential-processing refusal. The same `event_id` still in flight returns `conflict`, and so does a different `event_id` while any event is in flight. The equipment reply contract states how the client tells those cases apart. `event_mismatch` is the code for a repeated `event_id` whose recorded contents differ. It is a separate code because `conflict` already means the in-flight lock. A content mismatch must not be shown as a request to wait for the running event, and `unreadable_input`, `unsupported`, and `model_failure` name other failures. A missing `event_id` or simulator role is rejected before any model call. A missing `hire_id` is rejected before any model call for every event type except intake. A non-intake `hire_id` must be one the server has already assigned. An unknown `hire_id` is rejected before any model call. Intake may omit `hire_id`. An intake rejection before the server assigns a hire does not invent a `hire_id`. The body is the intake record, the message text, the new start date, or the question. A deadline event may carry an empty body. The demonstration clock supplies `occurred_at` on the original submission. A lost-acknowledgment retry resubmits that same submission, including the same `occurred_at`. Rate limiting for the MVP is the one-event lock, not a public quota.

Endpoint paths and full JSON schemas are not finalized. Section 4 names the fields Build and UX must keep stable, including the client-generated intake `event_id`. Who generates that id is decided in this section. Completing the paths is an open implementation decision. It is not a new product rule.

Reset is a separate test operation that restores a known fixture so a D-row can start from its precondition (PRD §7). It is not an event on a hire, and it is not case closure.

**How the server establishes the sender’s role.** The workspace role selector is the source of identity. The server binds `actor_id` and `actor_role` to that simulator selection before it reads the message for meaning. The message body is never parsed for a role, an approval, or a policy change (PRD §3, BR-2, CR-001). If the submitted role does not match the server-side selection, the event is rejected and no model call is made. The exact binding — a server-side selector record versus another trusted control that is not the message text — is an open implementation decision. The trust rule is not open: the server establishes the role, and the text does not.

**Intake validation contract.** The PRD asks this SAD for the contract shape and leaves the mandatory-field list open (PRD §2 step 1, PRD Open Question 4). This contract does not add fields.

- A readable intake carries the business facts the PRD already names: employee identity, start date, role, office, and designated manager. The id rule in this bullet is an operator-proposed contract amendment validated on 2026-11-19. It is not original PRD text. The client generates the intake `event_id` before submission. That id is required, and the server stores it without replacing it with a different id. The server assigns `hire_id` on intake and returns that id on the acknowledgment. A client-supplied `hire_id` on intake does not select or create the case. PRD §2 step 1 says the application associates the record with a unique hire ID and submission event ID. “Associates” is read here as the server binding that client-supplied event id to the server-assigned hire id and enforcing uniqueness. The PRD was not rewritten.
- The client-generated event id is an idempotency key. It does not activate a plan, confirm a fact, set readiness, or choose a role. Activation, accepted facts, readiness, role, and plan contents stay with the server rules in this section (BR-1, BR-2, BR-6).
- An unreadable input returns `unreadable_input` and writes no plan (FR-01, D1’s error rule).
- A blank role creates one request to the designated manager and no tasks (BR-1, D2).
- A clearly unsupported role or location, including a role other than Customer Support Representative or its alias “CSR,” is labeled for HR review and is not mapped onto invented tasks (BR-1, D12).
- Any other field the product later marks mandatory, when missing, is shown as missing and creates no plan (FR-01). Which fields those are, and the handling of each, stay with the product manager.
- A complete supported Customer Support Representative record for Austin activates the four Appendix A tasks with no HR hold (BR-1, D1).

**Two activation paths.** Both are code. Neither calls a model to decide whether tasks exist.

1. **Automatic activation.** The intake is complete, the role is Customer Support Representative or the alias “CSR,” including inside a sentence, and the office is Austin. The application creates exactly the four Appendix A tasks, with those owners and offsets, and marks the plan active (BR-1, FR-01, D1). Deadlines that have already passed are stored as overdue. They are not moved (Appendix A, PRD §2 step 4).
2. **Held activation.** The role is blank. The application sends one request to the designated manager and creates no tasks (D2). A reply that establishes the supported role, from that manager only, creates a proposed plan and waits. HR approval is the event that activates it. A reply from another participant cannot establish the role or approve the plan (BR-2, FR-02). Equipment facts, meeting facts, or other confirmations supplied before approval do not activate the held plan (PRD §2, Appendix A). An ambiguous role reply uses the clarification rule below. It does not invent a role (D3).

**Day-one readiness (BR-6).** Readiness is a pure function of stored evidence. It is recomputed when accepted evidence or the start date changes (PRD §2 step 7). Execution status is separate: pending or complete. Task readiness is confirmed, unconfirmed, or blocked. Overdue and escalated are additional indicators.

The overall state is **Ready** only when all four conditions hold:

1. Policy acknowledgment is complete. Late acknowledgment remains valid (P1).
2. Equipment is confirmed: the IT fulfiller has explicitly committed to an assigned laptop or a permitted loaner, with a ready date on or before the start date, and that commitment has not been revoked (BR-4, P2). A possible device or a delivery estimate is unconfirmed. A known lack of any permitted device by the start date is blocked.
3. The hiring manager has confirmed the first-day meeting for the current start date. The meeting need not already have been held (P3).
4. Customer-support tools orientation is assigned to the hiring manager with the Appendix A deadline, start plus five business days. Training need not be complete before day one (P4).

Otherwise the state is **Needs attention**, with the reasons, the responsible people, and the next actions. An HR decision to proceed despite an exception does not convert missing evidence into confirmation and does not mark the task complete (FR-06, D10). Unresolved equipment does not stop the other three tasks (BR-4, PRD §2).

**Date changes, duplicates, isolation, and decision versions.**

- A start-date change keeps completed work complete, recalculates unfinished Appendix A offsets, and writes a new plan version (BR-5, FR-04, D7, D8). Dates use Austin local time, Monday–Friday, and no holiday calendar. Deadlines are 5 p.m. unless P2’s start-of-work rule applies (BR-7). An unheld meeting becomes unconfirmed and generates a reconfirmation request for the new date (P3). Equipment is re-evaluated against the new start: a confirmed device stays reserved from its ready date unless IT revokes it (P2). A delivery estimate does not become a confirmation because the start date moved. An earlier start marks missed deadlines overdue. The phrase “until onboarding completes” in P2 has no closing event yet (PRD Open Question 5). This SAD does not add an automatic end to that reservation other than IT revocation.
- Event idempotency applies to every event type and fails closed (FR-07, D11, US-007, CR-005). Recorded contents are the submitted field values for `event_type`, `actor_id`, `actor_role`, `occurred_at`, and `body`, plus `hire_id` on every type other than intake. Comparison is of those values. It is not a raw byte match. The in-flight check comes first. The same `event_id` while the first attempt is still in flight returns `conflict`, whether or not the body matches, and that submission is not applied and is not a second case. After a committed result, the same `event_id` and the same recorded contents are a no-op: the original result remains, with no additional task, question, completion, follow-up, decision, or hire. The same `event_id` and different recorded contents, once that attempt is no longer in flight, return `event_mismatch`. The new body is not applied. A committed result is not overwritten. No second hire and no second plan are created. This includes a different body for an id that never committed: that mismatch is not a silent new event. An uncommitted failure with no committed result for that id may be retried only when the id and the recorded contents are the same. The id and those contents are reserved before any follow-up is sent, so a retry cannot send a second follow-up.
- An update names one hire id. Jordan’s case cannot change Riley’s plan (FR-07, D11, CR-004).
- An HR decision stores identity, timestamp, rationale, and the plan version it concerns (FR-06, CR-008). `approve_held_plan` is the second activation path. `escalation_disposition` records how HR is handling an exception, including a decision to proceed. A later change that affects that decision flags it for review and preserves the earlier decision (BR-7). The original approval remains historical authorization to begin. It is not a later Ready certificate.

**Clarification.** An insufficient reply produces one targeted follow-up that names the missing fact and carries an explicit response deadline (BR-3, PRD §2 step 6). A second insufficient reply in that round, or silence at that deadline, escalates to HR. A definite equipment denial escalates immediately and does not spend another follow-up (BR-4, D5). Duplicate or unchanged messages do not reset the allowance. A materially new fact may open a new round. Sufficient authorized evidence after escalation updates the task and closes the factual escalation. It does not approve a separate held plan, and the history remains (D6). For equipment, the draft, the ledger, the follow-up deadline, and what changes `plan_version` are the contract below.

**Resolved event schemas.** Recorded 2026-11-26. This closes the HR-decision, start-date, and deadline field gaps in implementation decision 11. It does not add a product rule. Paths stay `POST /events` and `GET /hires/<hire_id>`. No model is called for these three controls. Intake, equipment replies, policy questions, and the Gemini settings are unchanged.

The hire read adds `activation` (`active`, `proposed`, `held`, or `review`), `employee_name`, and `manager_name`. A complete supported intake is `active`. A blank role is `held` with no tasks. An unsupported role or location is `review` with no tasks.

- **Role reply on a held hire.** A `reply` is not an equipment reading while `activation` is `held`. The designated manager is the roster person whose name equals `manager_name`: Sam Ortiz is `actor-sam-ortiz` / `hiring_manager`, and Morgan Hale is `actor-morgan-hale` / `hiring_manager`. The body establishes the role only when it matches the intake supported-role test, including “CSR.” That reply stores the four Appendix A tasks, sets the role to Customer Support Representative, sets `activation` to `proposed`, and sets `plan_version` to 1. The plan is not active. Any other sender is stored and changes nothing else. A manager reply that does not match sends one follow-up and does not invent a role. A second insufficient reply sends no second follow-up.
- **HR decision.** `event_type` is `hr_decision`. `event_id` is the decision id. The body is an object with `decision_type` (`approve_held_plan` or `escalation_disposition`), a non-empty `rationale`, and `plan_version`. Only `actor-alex-rivera` / `hr_coordinator` may submit it. `plan_version` must equal the hire’s current `plan_version`. `approve_held_plan` applies only when `activation` is `proposed`. It sets `activation` to `active`, stores the decision, and increments `plan_version`. It does not mark a task complete and does not change readiness evidence. `escalation_disposition` stores the decision and rationale and changes no task, readiness, equipment evidence, or `plan_version`. A later material plan version sets `needs_review` on each earlier escalation disposition and keeps that record.
- **Start-date change.** `event_type` is `start_date_change`. The body is one `YYYY-MM-DD` date. Only `actor-alex-rivera` / `hr_coordinator` may submit it, and only when `activation` is `active`. Completed tasks keep their completion and due date. Unfinished policy, equipment, meeting, and training dates use the Appendix A offsets. A meeting that is not complete becomes unconfirmed and one reconfirmation request is stored. A committed ready date on or before the new start stays confirming. An estimate does not become a commitment. A commitment that misses the new start does not confirm; the equipment task is blocked, matching D8. The change writes the next `plan_version`.
- **Deadline.** `event_type` is `deadline_reached`. The body may be empty. Any configured simulator identity may submit it. The model is not called. A stored follow-up whose deadline is at or before `occurred_at` escalates the still-unresolved subject and does not send another follow-up. A deadline that has not arrived changes no fact.
- **Task update.** `event_type` is `task_update`. The body is an object with `task` and `action`. No model is called. `policy_acknowledgment` / `acknowledge` is accepted only from the new hire whose roster name equals `employee_name`. It sets that task complete and confirmed, keeps an already-overdue flag so a late acknowledgment stays late, and stores the event id as evidence. `first_day_meeting` / `confirm` is accepted only from the designated hiring manager. It confirms the meeting for the current start and leaves execution pending. `first_day_meeting` / `held` is the same sender and marks the meeting complete, so a later start-date change does not ask for reconfirmation. `training` / `assigned` and `training` / `complete` are accepted only from that manager. Assignment confirms the existing Appendix A training task and leaves execution pending. Completion marks it complete. An accepted update increments `plan_version` and flags earlier escalation dispositions. A wrong sender, or a hire that is not `active`, keeps the message and changes no task, readiness, or plan version. Any other task/action pair is `unreadable_input` before the event is reserved.

A sender, a decision type, or a plan state that these bullets do not allow is `unsupported` before the event is reserved. A body that is not the shape above is `unreadable_input`.

**Equipment reply contract.** Recorded 2026-11-26 from the operator-approved proposal. This contract does not change intake activation, the four-task rule, or the prepared-example crew. CrewAI stays sequential, with delegation off and agent memory off. Python selects `reply_reader`, validates the draft, and is the only writer of case state. The model has no tools and does not choose a follow-up.

The draft for one equipment message is:

- `statements`: an array with one entry for each device claim in that message. A laptop estimate and a possible loaner are two entries, not one blended fact.
- Each entry has `device` (`assigned_laptop`, `permitted_loaner`, or `unspecified`), `posture` (`explicit_commitment`, `possibility`, `delivery_estimate`, `denial`, `revocation`, or `unclassified`), `ready_date` (one `YYYY-MM-DD` or null), and `excerpt` (a contiguous substring of the original message).
- `claimed_fact` (string), `uncertainty` (boolean), and `date_candidates` (array of `YYYY-MM-DD`) remain. They are trace only. `uncertainty: false` does not confirm equipment. A date candidate is not a chosen ready date until a statement carries it.

Python accepts a statement only when the excerpt occurs in the original message, the device and posture are in the lists above, and a non-null `ready_date` is a member of `date_candidates`. Any other statement is unsupported and is not applied. If no statement is supported, the draft is ungrounded: the event fails, the ledger does not change, no follow-up is sent, and the original message is kept as unverified. Two supported statements for the same device that differ in posture or ready date are a contradiction. Python applies neither statement for that device and does not pick a winner. The other device in the same message is still applied when its own statements agree. A contradicted device makes the reply insufficient for that device. It does not become a commitment or a denial.

A supported statement is still only a proposal. It becomes verified equipment evidence only when the sender check and the ledger rules below both pass (CR-002, BR-4). Model output alone never writes a commitment.

**Sender check.** Before the model call, `actor_id` and `actor_role` must both match one configured simulator identity. A role with no matching id, or an id whose configured role differs, is `unsupported`. The model is not called, and the case is unchanged. The spelling of actor ids remains implementation decision 9. After the roster match, only the identity that owns this hire’s equipment task, Taylor Brooks with role `it_fulfiller`, may change equipment evidence. Any other roster-valid sender is stored, cannot confirm, deny, or revoke equipment, and does not spend the IT follow-up (BR-2, CR-001). The message text is not part of either check.

**Ledger.** The application stores, per hire, a state for the assigned laptop and a state for the permitted loaner: `unknown`, `possible`, `estimate` with one date, `committed` with one date, `denied`, or `revoked`. It also stores the follow-up count for the current equipment round. Python applies each non-contradictory supported statement from an authorized sender in message order:

- `explicit_commitment` is stored as `committed` only when the device is `assigned_laptop` or `permitted_loaner` and `ready_date` is on or before the hire’s start date. Otherwise that statement is an estimate or, when the date is missing, insufficient. It is not a commitment.
- `possibility` stores `possible` and does not replace a `committed` device.
- `delivery_estimate` stores `estimate` with its date and does not replace a `committed` device. A later start date does not turn an estimate into a commitment (BR-5, P2).
- `denial` stores `denied` for that device only.
- `revocation` stores `revoked` for that device only. This is how IT withdraws an earlier commitment (P2).
- `unspecified` or `unclassified` changes no device.

A later authorized commitment replaces `possible`, `estimate`, or `denied` for that same device. A later denial or revocation replaces a commitment for that device only. The other device is left as stored. Prior messages and the replaced evidence stay in the case history.

After those updates, the task is confirmed when at least one device is `committed` with a ready date on or before the start date. Confirmation cites the message as evidence and sends no follow-up. A device is established unavailable when it is `denied`, `revoked`, or an `estimate` dated after the start date. `unknown` and `possible` are not established unavailable. The task is blocked, and the case escalates with no follow-up, only when both devices are established unavailable. “No loaner” denies the loaner. On Riley’s March 16 start it blocks the task only because the stored laptop estimate of March 19 is already after that start. With the laptop still `unknown`, “No loaner” is not a task denial.

An authorized reply that does not confirm and is not a contextual denial is insufficient. The first insufficient reply in the round sends one follow-up naming the missing fact, an assigned laptop or permitted loaner with a ready date on or before the start date, and citing P2. A later insufficient reply in that round sends nothing and escalates. Equipment stays unconfirmed unless both devices are established unavailable. An unchanged body, matched against an equipment reply already stored in the round, is kept, does not change the ledger, does not send a follow-up, and does not escalate. A materially new authorized fact after escalation updates the task and closes that factual escalation while keeping its history (D6). It does not approve a held plan. A new insufficient fact after that close may open a new round with a fresh one-follow-up allowance (BR-3).

**Follow-up deadline.** The product requires an explicit deadline on the request and controls it by the demonstration clock (BR-3). It does not set the clock time. Appendix A uses 5 p.m. on the intake day for silence tests. The operator-approved choice, recorded here, is the equipment follow-up’s deadline: 5:00 p.m. America/Chicago on the calendar date of the reply’s `occurred_at` when that date is Monday–Friday and `occurred_at` is before 5:00 p.m. When `occurred_at` is at or after 5:00 p.m., or the date is Saturday or Sunday, the deadline is 5:00 p.m. America/Chicago on the next Monday–Friday. There is no holiday calendar (BR-7). The timestamp is stored on the follow-up. Silence is measured against that stored timestamp. A reply sent on the intake day before 5:00 p.m. lands on the same clock Appendix A uses for an intake-day silence test.

**Plan version.** BR-7 requires a new version for each material plan or evidence change and does not define a follow-up. The operator-approved choice, recorded here: a follow-up that does not change task readiness, the escalated indicator, or stored equipment evidence leaves `plan_version` unchanged. The trace names that current version (CR-008). A confirmation, a blocked denial, a revocation that changes readiness, or an escalation that sets the escalated indicator creates the next version. The trace names the new version.

**Event completion.** The model call is non-streaming. `POST /events` acknowledges a reply that passed the pre-model checks within 2 seconds, before Gemini returns, with the same `event_id`, the hire id, and `status: processing` (PRD §5). That body is not the outcome. The client reads `GET /hires/<hire_id>` and finds its own `event_id` in `events`:

- `processing` means that event is still in flight. The tasks, readiness, and `plan_version` on the same document are the current case from earlier commits. They are not this event’s output.
- `complete` means the rule gate committed this event. Its `failure` is null. The task list is still the current case, including tasks created by intake or by earlier events. What this event changed is the decision record stored with this `event_id` (CR-008).
- `failed` means an invalid draft, a timeout, or a provider error. `failure.code` is `model_failure`. Verified tasks, readiness, and `plan_version` stay on the last committed case. The original message is kept. No follow-up is sent.

The hire-level `failure` field is the current case failure. It is set when the newest finished event failed, and it is null when a newer event on that hire has reached `complete`. Each event’s own `failure` stays on that event so an earlier failure remains visible (FR-07, D11). One event may be in flight for the whole demonstration (PRD §5). The same `event_id` in flight returns `conflict` whether or not the body matches. A different `event_id` while any event is in flight also returns `conflict`, names both ids, and does not start work. After an event is no longer in flight, the same id and the same recorded contents are a no-op when the result committed, and may be retried when it failed with no committed result (CR-005). Different contents for that id are `event_mismatch` and change nothing. This route makes one provider call per accepted attempt. It does not add a second application retry. Implementation decision 7 stays open for how CrewAI and library retries share that one additional attempt.

**Policy publication.** Recorded 2026-11-26. This resolves implementation decision 8. It does not change intake, equipment replies, or the prepared-example crew. No policy outcome changes equipment evidence, task completion, readiness, or `plan_version`. Event states stay `processing`, `complete`, and `failed`. HR referral and manual review are `complete` with `failure` null. They are not new status words. `model_failure` is `failed`. A second model judge is not used.

**Published text.** Publishing the exact approved passage, with its id, satisfies the meaning half of FR-05 and D9: the published words are the passage, so a paraphrase cannot drift. It does not establish that the passage answers the question. The application publishes no model prose. The proposal fields are `citations` (passage ids), `grounding` (one excerpt per citation), and `covered` (boolean, trace only). The only answer text that may be stored is the exact P1–P4 passage for each passage that passes the gate below.

**What is not proof.** None of these establish that a passage answers the question: a keyword or retrieval-term match, citation membership in P1–P4, citation membership in the retrieved set, an excerpt that occurs in the passage, or the model’s `covered` flag. Retrieval terms only select candidate passages.

**Coverage.** Python classifies the question with the question detector below and with no other classifier. That detector is separate from the retrieval terms. A retrieval hit does not mark an obligation. An obligation applies only when a listed pattern matches. The ten obligations are:

| Obligation | Passage | The question asks |
|---|---|---|
| `P1-due` | P1 | whether acknowledgment is due before the start date, or how many business days before |
| `P1-late` | P1 | whether a late acknowledgment remains valid, including after a start-date change |
| `P2-provide` | P2 | whether IT provides an assigned laptop or an approved loaner by the start date |
| `P2-confirm` | P2 | whether a possibility, an estimate, or anything short of an explicit ready date confirms equipment, or what confirmation requires |
| `P2-continue` | P2 | whether other tasks continue while equipment is unresolved |
| `P3-meeting` | P3 | whether the manager must confirm a first-day meeting for the current start date |
| `P3-reconfirm` | P3 | whether a changed start date requires the meeting to be confirmed again |
| `P4-due` | P4 | when orientation is due, or whether it falls within five business days after the start, for the Austin customer-support role |
| `P4-owner` | P4 | who owns orientation scheduling or completion |
| `P4-not-prereq` | P4 | whether equipment is a prerequisite for assigning or scheduling training |

A passage covers an obligation only when this table names that passage for it. The question is fully covered only when at least one of these obligations is detected and every detected obligation is covered by a candidate passage. Asking what P2 says about confirmation is `P2-confirm` only when a `P2-confirm` pattern matches. Directing the system to confirm, reserve, or set readiness for a device on this case is an equipment instruction, not `P2-confirm`.

**Question detector.** Recorded 2026-11-26. This is the only procedure that decides which obligations, out-of-pack topics, and equipment instructions are present. It does not publish passage text, select candidate passages, or call the model. It does not change intake, equipment replies, Gemini settings, sequential execution, delegation, or agent memory. An out-of-pack result remains a completed policy event with the reason “outside the pack” and no policy conclusion. It is not an HR decision of type `approve_held_plan` or `escalation_disposition`.

These patterns do not establish coverage for arbitrary language. A listed match detects that one row. A synonym, spelling, or word order that is not listed does not match. There is no stemming beyond the rewrite list. A clause is not dropped because it is short, polite, or a greeting. There is no stop-word list beyond the token deletions below.

**Normalization and matching.** Apply these steps in order. Do not add another language rule.

1. Unicode NFKC, then Unicode casefold.
2. Delete apostrophe characters U+0027, U+2018, U+2019, and U+0060. Do not replace them with a space. `don't` becomes `dont`.
3. Split on `?`, `!`, `.`, and `;`. Discard empty pieces.
4. Split each piece on the exact separators ` and ` and ` but `. Do not split on ` or ` or on a comma. Apply that split repeatedly. Keep a split only when both sides contain at least two whitespace-separated words. Otherwise leave the piece unsplit. Discard empty pieces. Each remaining piece is a clause.
5. In each clause, a token is a maximal run of Unicode letters or digits. Every other character is a separator only. `start-date` becomes `start` and `date`. `i-9` becomes `i` and `9`.
6. Replace or delete tokens with this closed list only. No other token changes.

| Token | Becomes |
|---|---|
| `dont`, `doesnt`, `isnt`, `arent` | `do`, `does`, `is`, `are` |
| `cant` | `can` |
| `wont` | `will` |
| `no`, `not`, `never` | deleted |

7. A phrase matches a clause when its tokens are a contiguous sub-sequence of that clause’s tokens. Comparison is exact.
8. A pattern is one or more phrases. Every phrase in the pattern must match. Order between phrases does not matter, and other tokens may sit between them. Alternatives are separate patterns. Any one alternative is enough.
9. A row matches a clause when at least one of its patterns matches and none of its must-not phrases match. A must-not phrase uses the same contiguous-token rule.
10. Negation does not flip or cancel a row. Step 6 deletes `no`, `not`, and `never`, and it rewrites the six contracted tokens. The clause is then matched as if those tokens were absent. `Does a late acknowledgment not remain valid?` is the same match as `Does a late acknowledgment remain valid?`.

**Pack patterns.** The passage column is the only passage that covers that obligation. Must-not phrases block that obligation on that clause only.

| ID | Passage | Accepted patterns, separated by `;` | Must-not phrases | Positive example | Must not match this ID |
|---|---|---|---|---|---|
| `P1-due` | P1 | `how many business days` + `acknowledge`; `how many business days` + `acknowledges`; `acknowledge` + `before the start`; `acknowledges` + `before the start`; `acknowledgment` + `two business days`; `acknowledgment due` | `late` | How many business days before the start date must the new hire acknowledge the written policies? | Does a late acknowledgment remain valid after a start-date change? |
| `P1-late` | P1 | `late acknowledgment`; `acknowledged late`; `acknowledgment` + `remains valid`; `acknowledgment` + `still valid`; `acknowledgment` + `start date change`; `acknowledgment` + `start date changes` | `first day meeting`; `orientation`; `loaner` | Does a late acknowledgment remain valid after a start-date change? | Must the manager confirm a first-day meeting for the current start date? |
| `P2-provide` | P2 | `approved loaner`; `provide` + `loaner`; `provides` + `loaner`; `assigned laptop` + `loaner`; `provide` + `laptop`; `provides` + `laptop` | `confirm the laptop`; `reserve a loaner`; `reserve the laptop`; `prerequisite` | Can IT provide an approved loaner by the start date? | Does a delivery estimate confirm equipment? |
| `P2-confirm` | P2 | `possibility` + `confirm`; `estimate` + `confirm`; `estimate` + `confirmation`; `delivery estimate` + `confirm`; `delivery estimate` + `confirmation`; `explicit ready date`; `what confirmation requires`; `what does confirmation require`; `same day ready date`; `ready date` + `confirm`; `ready date` + `confirmation` | `for this hire`; `for this case`; `for riley`; `for jordan` | Does a possibility or a delivery estimate confirm equipment? | Please confirm the laptop for this hire. |
| `P2-continue` | P2 | `other tasks` + `continue` + `equipment`; `tasks continue` + `equipment`; `while equipment is unresolved`; `equipment is unresolved` | `prerequisite` | Do other tasks continue while equipment is unresolved? | Is equipment a prerequisite for assigning or scheduling training? |
| `P3-meeting` | P3 | `first day meeting`; `manager` + `confirm` + `meeting`; `manager` + `confirms` + `meeting` | `reconfirm`; `reconfirmation`; `confirmed again`; `changed start`; `start date change`; `start date changes`; `new start date` | Must the manager confirm a first-day meeting for the current start date? | Does a changed start date require the meeting to be confirmed again? |
| `P3-reconfirm` | P3 | `reconfirm`; `reconfirmation`; `confirmed again`; `changed start date` + `meeting`; `start date change` + `meeting`; `start date changes` + `meeting`; `new start date` + `meeting`; `changed date` + `meeting` | `late acknowledgment` | Does a changed start date require the meeting to be confirmed again? | Must the manager confirm a first-day meeting for the current start date? |
| `P4-due` | P4 | `orientation` + `five business days`; `when` + `orientation` + `due`; `orientation` + `after starting`; `orientation` + `after the start`; `orientation due` | `who owns`; `who schedules`; `who is responsible`; `prerequisite` | When is customer-support tools orientation due? | Who owns orientation scheduling? |
| `P4-owner` | P4 | `who owns` + `orientation`; `who schedules` + `orientation`; `manager owns` + `orientation`; `who is responsible` + `orientation`; `orientation` + `scheduling` + `who` | `five business days`; `prerequisite`; `orientation due` | Who owns orientation scheduling? | When is orientation due? |
| `P4-not-prereq` | P4 | `equipment` + `prerequisite`; `prerequisite` + `training`; `prerequisite` + `orientation`; `assigning or scheduling training`; `equipment` + `required before` + `training` | `confirm the laptop`; `reserve a loaner` | Is equipment a prerequisite for assigning or scheduling training? | Do other tasks continue while equipment is unresolved? |

**Out-of-pack topics.** These are not pack obligations and they do not select a passage. Any one match is enough. The stored reason is still “outside the pack.” No topic name is added to that reason.

| Topic | Accepted phrases | Positive example | Must not match this topic |
|---|---|---|---|
| Pay | `pay`; `salary`; `wage`; `wages`; `compensation`; `paycheck` | What is my salary? | Can IT provide an approved loaner by the start date? |
| Overtime | `overtime`; `time and a half`; `extra hours` | Do I get overtime? | When is orientation due? |
| Remote work | `remote`; `remotely`; `work from home`; `wfh`; `telework`; `telecommute` | Can I work remotely? | Do other tasks continue while equipment is unresolved? |
| Legal eligibility | `eligible to work`; `work authorization`; `visa`; `i 9`; `i9`; `legal eligibility`; `right to work` | Am I eligible to work? | Does a late acknowledgment remain valid? |

**Equipment-changing instructions.** A clause matches an instruction when at least one phrase below matches, except for the question-opener rule in the next sentence. The phrases are: `confirm the laptop`; `confirm the loaner`; `confirm a loaner for`; `please confirm`; `reserve the laptop`; `reserve a loaner`; `reserve the device for`; `reserve a device for`; `set equipment readiness`; `mark equipment ready`; `mark the laptop ready`; `mark the loaner ready`; `book the laptop`; `book a loaner`; `change equipment evidence`; `update equipment readiness`. If the clause’s first token is `does`, `do`, `is`, `are`, `can`, `could`, `should`, `what`, `when`, `whether`, `will`, `who`, `which`, `how`, `if`, `must`, or `why`, and the clause does not contain `for this hire`, `for this case`, `for riley`, or `for jordan`, none of those instruction phrases match. `Please confirm the laptop for this hire.` matches. `Does a possibility or a delivery estimate confirm equipment?` does not. If an instruction matches a clause, no pack obligation is recorded for that clause. An out-of-pack topic on that clause is still recorded.

**Multiple clauses.** Classify every clause. A clause may match more than one pack obligation. Record every pack obligation that matched. That is not ambiguous. A clause that matches no pack obligation, no out-of-pack topic, and no equipment instruction is unmatched.

**Precedence.** After every clause is classified, apply the first matching row. Stop.

| Order | Condition | Result |
|---|---|---|
| 1 | Any clause matched an out-of-pack topic | HR referral for the whole question, including when another clause is a pack obligation, an equipment instruction, or unmatched. Reason “outside the pack.” Model not called. No policy conclusion. No partial passage. |
| 2 | Any clause matched an equipment instruction | Manual review for the whole question, including when another clause matched a pack obligation. Model not called. Nothing published. Case facts unchanged. |
| 3 | At least one clause matched a pack obligation, and at least one clause is unmatched | Ambiguous. Manual review. Model not called. The matched clause is not published. |
| 4 | Every clause matched at least one pack obligation | Detected set is the union of those obligations. Candidate retrieval may run. The publication gate, including the partial-coverage row, decides. |
| 5 | No clause matched a pack obligation, an out-of-pack topic, or an equipment instruction | Unmatched. This is the recorded “no pack obligation was detected” path. Candidate retrieval may run. No candidate means manual review and no model call. If candidates are retrieved, the model may run, and the gate cannot publish because no pack obligation was detected. |

**Candidate retrieval.** This step is not recognition. It runs only for precedence rows 4 and 5. It does not add, remove, or cover an obligation. Tokenize the whole question with steps 1, 2, 5, and 6, without clause splits. A passage is a candidate when any of its terms is a whole token. The closed term list is:

| Passage | Terms |
|---|---|
| P1 | `acknowledgment`; `acknowledge`; `acknowledges` |
| P2 | `laptop`; `loaner`; `equipment` |
| P3 | `meeting` |
| P4 | `orientation`; `training`; `prerequisite` |

No candidate means manual review and no model call. A candidate does not mean the question is covered.

**Acceptance examples.** The detector results below are required. Publication still depends on the existing gate.

| Question | Detector result | Required outcome |
|---|---|---|
| Can IT provide an approved loaner by the start date? | `P2-provide` only. Not an instruction. | Supported path. Retrieval candidate P2. Publish the exact P2 passage only if the gate passes. Equipment evidence, tasks, readiness, and `plan_version` stay unchanged. |
| What is the office wifi password? | Unmatched. No retrieval term. | Manual review. Model not called. No policy conclusion. |
| How many business days before the start date must the new hire acknowledge the written policies, and does a delivery estimate count as confirmation? | `P1-due` and `P2-confirm`. Retrieval candidates are P1 only, because the question has no `laptop`, `loaner`, or `equipment` token. | Partial coverage. Manual review. No passage is published, including P1. |
| Can IT provide an approved loaner by the start date, and can I work remotely? | `P2-provide` and remote work. | HR referral, reason “outside the pack.” Model not called. The loaner passage is not published. |
| Please confirm the laptop for this hire. | Equipment instruction. `for this hire` blocks `P2-confirm`. | Manual review. Model not called. Case facts unchanged. |
| Does a late acknowledgment not remain valid after a start-date change? | Same as the unnegated question: `P1-late` only. | Supported path for P1. The deleted `not` does not create a different obligation. |
| Can IT provide an approved loaner by the start date, and where should I park? | `P2-provide` plus an unmatched clause. | Ambiguous. Manual review. Model not called. The loaner passage is not published. |

**Paraphrase scope.** FR-05 requires a cited answer that preserves meaning across paraphrased questions. D9 requires a cited answer for a paraphrased P1 question and a P2 loaner question. The PRD does not list those paraphrase wordings. This detector answers only the patterns in the tables above. A paraphrase outside the tables is unmatched or ambiguous and uses the fallback. That is narrower than a reading of FR-05 and D9 in which every paraphrase of P1–P4 is answered automatically. This SAD does not close that product decision. Backend implements this table only and does not add phrases.

**Before the model.** Use the detector precedence. Any pay, overtime, remote-work, or legal-eligibility match routes the whole question to HR, including when a pack obligation is also present. No supported part is published. The model is not called. The stored reason is “outside the pack.” There is no policy conclusion. An equipment instruction, with or without a pack obligation, is manual review. The model is not called, nothing is published, and the case facts stay as they were. If both an out-of-pack topic and an equipment instruction are present, the HR route wins. An ambiguous question is manual review and calls no model. Keyword retrieval runs only for a fully classified pack question or an unmatched question. No candidate passage means manual review and no model call.

**Publication gate.** The model runs only after at least one candidate passage was retrieved and the before-model routes did not apply. The gate publishes the exact text of a covering passage only when all of the following hold:

1. The question is fully covered, and each detected obligation is covered by a candidate passage.
2. The proposal cites that covering passage, and its grounding excerpt is a contiguous substring of that passage.
3. The proposal does not assert live task state. It must not say that a device is reserved for this hire, that equipment readiness is confirmed, or that a task is complete (CR-003).

`covered: true` does not satisfy item 1. `covered: false` does not veto item 1 and does not prove that the passages are irrelevant. A cannot-answer proposal (`covered: false`, or no citations) publishes nothing.

**Outcome map.** No row stores a policy conclusion except a gate that publishes passage text. A published passage is the conclusion. Every other row stores none.

| Case | Outcome | Event | Policy conclusion |
|---|---|---|---|
| `covered: false`, or no citations, after passages were retrieved | Manual review | `complete` | None. The flag is not proof of irrelevance. There is no citable proposal to publish. |
| Invalid grounding: the citation is in the retrieved set, but the excerpt is not a contiguous substring of that passage | `model_failure` | `failed` | None. The question is kept. |
| Valid but irrelevant citation: the citation and excerpt are valid for a retrieved passage that does not cover a detected obligation, or no pack obligation was detected | Manual review | `complete` | None. |
| Partial coverage: at least one pack obligation is covered and at least one is not, and no out-of-pack obligation is present | Manual review | `complete` | None. No partial passage is published. |
| Ambiguous: at least one pack obligation matched and at least one clause matched nothing | Manual review | `complete` | None. The matched clause is not published. The model is not called. |
| Out-of-pack topic, including a mix with a supported part | HR referral, reason “outside the pack” | `complete` | None. No supported part is published. |
| Instruction to confirm or reserve equipment, with no out-of-pack topic | Manual review | `complete` | None. Case facts are unchanged. |

A schema-invalid proposal, a timeout, or a provider error is `model_failure` on `failed`, with no policy conclusion. The question is kept. Verified tasks, readiness, equipment evidence, and `plan_version` stay on the last committed case.

**Data Architecture**:

Persistence is in the MVP because FR-07 and US-007 require tasks, messages, versions, and decisions to survive restart. Proposed choice: one local SQLite file. The repository has not settled the database. The stored records are hire, task, message, plan version, decision, evidence reference, and the event id with its recorded contents. The event id is unique in that store. A later submission of the same id does not overwrite those contents. After a committed result, the same contents are a no-op. Different contents are `event_mismatch`. An id with no committed result may be retried only with the same contents. There is no archive or close record. Case closure is PRD Open Question 5.

**Runtime Integration Layer**:

The API process runs the router in process. The router calls the CrewAI entry only for `reply_reader` and `policy_answerer`. Prompt text and the schema result are written to the CR-008 trace with secrets removed. Lifecycle logs for Build go under `project-context/2.build/logs` when that phase runs. Configuration for the pattern is the YAML files plus the code router. The model is not configured by a chat session. User-facing history shows the evidence and the decision, not the raw provider payload (CR-007).

**Authentication & Secrets**:

No `.env.example` exists yet. The provisional secret name is `MODEL_API_KEY`. Creating `.env.example` with that name, and no value, is a setup task. The provider-specific name, if different, replaces it when PRD Open Question 2 is answered. No secret value belongs in the repo, this SAD, or the case history. The simulator is demonstration authority. It is not production authentication (PRD §3).

### 5. DevOps & Deployment Architecture

**CI/CD**: The Deliver phase generates lint, test, and build only. This SAD does not start a live deploy.

**Hosting**: The smallest target is one process on the developer machine. Proposed choices, subject to setup confirmation: port 8000, and `GET /health` returning success when the process and the local store are reachable. The PRD requires a repeatable local launch and recovery, not a hosted uptime SLA (PRD §5).

**IaC / multi-region / advanced monitoring**: Future work. The PRD requires no cloud region.

**Observability**: Per-event CR-008 traces are the request design. The results sheet is the aggregate design. They stay separate. A live dashboard is not an MVP component (Production Shape).

### 6. Data Flow & Integration Architecture

![Onboarding events reach the case through a router](../diagrams/system-arch/onboarding-workflow.svg)

The figure source is `project-context/diagrams/system-arch/onboarding-workflow.html`. It was checked against this revision. It still matches the design: the workspace submits an event, the router either applies the rules or asks one model task for a draft, the policy pack is read only into the policy answerer, and the case system is the only writer. The PRD business-process figure and the Jordan walkthrough are not redrawn here. Production HR, IT, identity, and messaging systems stay off the figure because they are out of scope. The provider API is not a separate node. The two model tasks are those calls. The workspace reads the updated case after the commit. That return is the section 4 hire read model, not a second arrow on the figure.

| Incoming event | Processing | Visible result |
|---|---|---|
| Complete, supported intake | Fixed rules. No model call. | Active plan with the four Appendix A tasks. No HR hold. |
| Intake missing a role | Fixed rules. No model call. | One request to the designated manager. No tasks. |
| Supported role from that manager | Reply reader, then BR-1. | Proposed plan, still held for HR approval. |
| HR approves the held plan | Fixed rules. No model call. | The four tasks activate. The approval is stored against that plan version. |
| Unsupported role or location | Fixed rules. | HR review label. No invented task set. |
| Other missing fields | Fixed rules. | The missing fields are shown. No plan. The mandatory list beyond role remains PRD Open Question 4. |
| Unreadable intake | Input validation. | Error. No plan. |
| Written reply | Reply reader, then authority and evidence rules. | Confirmed update, one targeted follow-up, or escalation. |
| Start-date change | Date and planning rules. No model call. | Unfinished work updated. Completed work kept. Prior version kept. |
| Covered policy question | Pack lookup, policy answerer, publication checks. | Cited answer, or visible failure or manual review. |
| Unsupported policy question | Route to HR. No model call. | No invented answer. |
| Deadline without sufficient evidence | Fixed rules. | Escalation. The fact stays unconfirmed. |
| HR decision | Permission and version checks. | Decision saved against the named plan version. Missing evidence stays missing. |
| Repeated event ID | Idempotency check against the reserved id and its recorded contents. No model call. | Same contents after a committed result: original result, and no additional task, question, completion, follow-up, decision, or hire. Different contents, once the attempt is no longer in flight: `event_mismatch`. The new body is not applied, and no second hire or plan is created. Same id still in flight: `conflict`. Not a second case. No committed result: the same contents may be retried; a different body is `event_mismatch`. |

External integrations required for the MVP: the model provider API, and no others. Simulated messages are local records.

Errors appear in the hire’s `failure` field and in the workspace. The last verified plan remains available (FR-07, D11).

### 7. Performance & Scalability Specifications

- Acknowledge a submission within 2 seconds. Show a result or a visible failure within 60 seconds, including one additional attempt. These are the PRD §5 planning targets for the local demo, not a hosted SLA and not a measured baseline.
- Process one event at a time. Storage holds both seeded hires and the D12 third hire.
- Horizontal scaling, a queue, and a second operator are deferred. The PRD excludes them, and the MRD has no measured volume to size against.
- Token and dollar controls sit on the runtime. CR-006 fails closed. The numeric cap waits on PRD Open Question 2. Usage is recorded when the provider supplies it, before any cost forecast.

### 8. Security & Compliance Architecture

- **AuthN / AuthZ.** The simulator is the actor source, and the server establishes the role as specified in section 4. BR-2 is the authorization rule, enforced in the case system. Hiding an approval control is not sufficient. There is no enterprise SSO in this release.
- **Encryption and validation.** Local synthetic data has no hosted transport requirement. Inputs are validated before a model call. Secrets use the name `MODEL_API_KEY` and stay out of artifacts.
- The Control Register is the application-layer safety design. `@security.eng` verifies it against the code before Deliver. `security.require_security_assessment` is absent from `aamad.config.yml`. The template default is true, so the assessment is required.
- **Compliance.** No legal or regulatory certification is claimed (PRD §5). Retention, production permissions, and integration recovery are undefined. They are carried as PRD Open Question 3. Week 6 can still score D1–D12.

### 9. Testing & Quality Assurance Specifications

- Unit tests cover BR-1 through BR-7, both activation paths, the four BR-6 conditions, duplicate handling, and hire isolation without a model call.
- Integration tests run D1 through D12 from the stated fixture or a reset, and they keep failed attempts (PRD §7). Previous scenarios must not silently supply evidence.
- A smoke path launches the local process, loads one seeded hire, and shows the readiness summary.
- Runtime checks: each model task returns schema-valid output or a recorded failure. The CR-008 trace exists for every commit. YAML tasks reference only `reply_reader` and `policy_answerer`.
- `@qa.eng` runs `*verify-change` before Deliver. `quality.require_evals` is absent from `aamad.config.yml`. The template default is true, and this pattern includes a model call, so evals are required before Deliver.
- `@security.eng` writes `project-context/2.build/security.md` before Deliver.

**Evaluation Criteria**:

Thresholds below come from the PRD’s pass conditions and from the consequence of a wrong output. The cost cap is not invented. `@qa.eng` `*run-evals` builds the dataset, graders, and `evals.md` from this table. This table is the pass/fail contract only.

| ID | Dimension | Metric | Threshold | Grading Method | Source |
|----|-----------|--------|-----------|-----------------|--------|
| EC-001 | Accuracy | D1–D12, each run from its stated precondition or a reset fixture | Every row passes. Failed attempts are kept. | Human | PRD §7 definition of done |
| EC-002 | Accuracy | Unsupported confirmations, invented policy answers, duplicate tasks, and cross-hire changes in the evaluation set | Zero of each | Code-based | PRD §7 technical measures |
| EC-003 | Latency | Time to acknowledge a submitted event | Within 2 seconds | Code-based | PRD §5. Planning target, not a measured baseline. |
| EC-004 | Latency | Time to a result or a visible failure, including one additional attempt | Within 60 seconds | Code-based | PRD §5. Planning target, not a measured baseline. |
| EC-005 | Safety | Accounts created, access changes, identity documents processed, eligibility decisions, and payroll or tax actions | Zero | Code-based | PRD §3 Must not; D12 |
| EC-006 | Safety | Policy answers that lack a valid P1–P4 citation, change the passage meaning, or claim equipment was arranged | Zero in the D9 set | Human | FR-05; US-005; D9 |
| EC-007 | Security | Production HR, IT, identity, or messaging calls; actor role taken from message text; secrets present in the workspace, history, or export | Zero | Code-based | PRD §3 and §5; CR-001, CR-004, CR-007 |
| EC-008 | Cost | Provider usage recorded per scored scenario, and spend against the operator cap | Cap is unset. Paid scored runs wait until the operator sets one. Usage is still recorded when the provider supplies it. | Human | PRD Open Question 2; MRD resource plan |

### 10. MVP Launch & Feedback Strategy

- The launch in scope is the Week 6 demonstration, not a commercial beta (PRD §9). The reviewer receives the runbook and the pass/fail sheet. The shown path is the normal journey, an uncertain equipment reply, clarification, updated readiness, and a changed start date.
- Success metrics are the section 9 table. No savings figure is claimed. The MRD’s market sizes are adjacent-category context, not an addressable-market target.
- Outcome document fields for Deliver:
  - **Before metric:** Unresolved day-one conditions and coordination effort in a target organization. The PRD states this has not been measured. The before value is “unmeasured.”
  - **Auditable control:** CR-002 and BR-6. A possibility is not readiness. Ready requires completed policy acknowledgment, a valid IT equipment commitment that has not been revoked, a manager-confirmed meeting for the current start date, and training assigned with a valid deadline.
  - **Measurement owner:** An independent reviewer records the Week 6 sheet. Joey is the product owner.
  - **When the after metric is recorded:** At the Week 6 demonstration, on the completed results sheet, from D1 through D12.

Training must be assigned with a deadline, but completion is not required before day one (P4). An unheld but confirmed meeting counts as arranged, not completed (P3). Unresolved equipment must not prevent progress on the other three tasks (BR-4). An HR exception may authorize proceeding, and it does not turn missing evidence into confirmation (FR-06).

## Implementation Guidance for AI Development Agents

1. `@project.mgr` writes `setup.md` and the local runtime, including `MODEL_API_KEY` in `.env.example` with no secret value.
2. `@ux.designer` writes `ux.md` for the PRD §6 workspace. The surface is already specified. Do not replace it with a general chat.
3. `@frontend.eng` builds the workspace regions against the section 4 fields, without binding the live API.
4. `@backend.eng` implements the router, both activation paths, the BR-6 readiness function, the two CrewAI tasks, the rule gate, and the local store. No additional agents.
5. `@integration.eng` wires the workspace to the section 4 contracts.
6. `@qa.eng` runs unit, integration, smoke, `*run-evals` from section 9, and `*verify-change`.
7. `@security.eng` assesses the Control Register, then `@devops.eng` writes local launch configuration, the runbook, and the outcome document. No live deploy without operator authorization.

Resolve the open implementation decisions below before building the control they affect. A change to product behavior, including intake completeness and case closure, goes to `@product-mgr`. This document does not make that change.

## Architecture Validation Checklist

- [x] PRD requirements mapped to architectural components
- [x] Work Ownership, Pattern Decision, Reference Architecture, Model and Context Strategy, and Control Register are complete
- [x] Runtime roles exist only when the Pattern Decision requires them
- [x] Frontend and backend contracts agree on fields and on non-streaming behavior
- [x] Secrets via env vars only
- [x] MVP vs Future Work boundaries explicit
- [x] Resolved `AAMAD_TARGET_RUNTIME` recorded in Audit

## Sources

- `project-context/1.define/prd.md`. November 13, 2026 proposed baseline. Section 2 journey and activation, BR-1 through BR-7, FR-01 through FR-07, P1–P4, Appendix A owners and deadlines, §3 identity and runtime limits, §5 targets, §6 workspace, §7 D1–D12, §9 demonstration, and Open Questions 1–5.
- Operator proposal, 2026-11-19. The client generates the intake `event_id` before submit so a lost acknowledgment can be retried without a second case. The server assigns `hire_id` and keeps activation, facts, readiness, role, and plan contents. A repeated event id is idempotent, and the same id with different contents is rejected. Validated against PRD §2 step 1, the PRD §3 repeated-event rule, and US-007 acceptance criterion 2. The PRD was not rewritten.
- Operator-approved equipment-reply proposal, 2026-11-26. Multi-statement draft, ledger, contextual denial, asynchronous acknowledgment, follow-up deadline, and plan-version rule. Recorded in section 4. The PRD was not rewritten. Application code was not changed.
- Operator request, 2026-11-26, to record the policy publication check before backend implementation. The four points are in section 4. The PRD was not rewritten. Application code was not changed.
- Operator request, 2026-11-26, to close the policy detector gap with a finite pattern table. The question detector, retrieval term list, acceptance examples, and Open Question 7 are in this SAD. The PRD was not rewritten. Application code was not changed.
- `project-context/1.define/system-description.md`. Confirms that pattern and work ownership belong to this SAD.
- `project-context/1.define/user-stories/US-001.md` through `US-007.md`. Acceptance criteria for the user-visible steps. These stories still say only PRD questions 1–3 are open. The November 13 PRD is authoritative for questions 4 and 5.
- `project-context/1.define/mrd.md`. Week 6 scope and the interpretation-versus-rules split. Market figures are context only. The file title differs from the title the PRD cites.
- `aamad.config.yml`. `project.mode: greenfield`, `runtime.target: crewai`. Quality and security flags are omitted.
- `.cursor/templates/sad-template.md`. Heading order, pattern vocabulary, reference-architecture table, control-register columns, and the evaluation table.
- `.cursor/templates/aamad-config-template.yml`. Defaults for `quality.require_evals` and `security.require_security_assessment` when the project file omits them. Both default to true.
- `.cursor/rules/adapter-crewai.mdc` and `.cursor/rules/adapter-registry.mdc`. Sequential process, YAML tasks, `max_iter` ceiling, `max_retry_limit` floor, `max_rpm`, and the unset-runtime default.
- `.cursor/skills/draw-diagram/SKILL.md` and `vendor/diagram-design/references/style-guide.md`. The section 6 figure uses the shipped skin the operator kept.

## Assumptions

- “Existing system” is the local case store and rule engine to be built.
- Python, SQLite, port 8000, `/health`, and the secret name `MODEL_API_KEY` are proposed choices. The PRD and `aamad.config.yml` do not settle them.
- A complete supported intake activates without the HR approval step. HR approval applies only to a plan that was held for a missing role. Facts supplied before that approval do not activate it.
- Role or location changes after activation are held for HR review. This SAD does not add a new decision type.
- Start-date changes preserve completed work, recalculate unfinished Appendix A offsets on Austin Monday–Friday dates with no holiday calendar, require meeting reconfirmation when the meeting has not been held, and re-evaluate equipment against the new start.
- A valid later reply can close a factual escalation without approving a held plan. The escalation history remains. A later conflicting change flags the affected HR decision for review and keeps the earlier decision.
- Out-of-pack answers, if a person gives one, are outside the model. The product’s step ends at the route to HR.
- The 2-second and 60-second figures are planning targets from PRD §5.
- `require_evals` and `require_security_assessment` apply because the project config omits them and the template default is true.
- The architecture figure uses the shipped diagram skin. It omits production systems and draws the provider call as the two model tasks.
- US-001 through US-007 were not rewritten for PRD Open Questions 4 and 5. Where a story and the November 13 PRD differ on an open question, the PRD governs. A story change belongs to `@product-mgr`.
- The intake event-id rule in section 4 is an operator-proposed contract amendment validated by system-arch on 2026-11-19. PRD §2 step 1 says the application associates the record with a unique hire ID and submission event ID. That verb is read as the server binding a client-supplied event id to a server-assigned hire id. It is not read as a requirement that the server mint the event id. The PRD and US-007 were not edited. US-007 still holds: a repeated event id creates no additional tasks, questions, or completions. Business-state authority stays on the server.
- The equipment follow-up deadline and the plan-version rule in the equipment reply contract are the operator-approved choices from 2026-11-26. Saturday and Sunday roll forward to the next Monday because BR-7 already limits business days to Monday–Friday. The PRD was not rewritten. Appendix A’s intake-day silence clock still matches a follow-up issued on that day before 5:00 p.m.
- The policy obligation table is a reading of P1–P4 for the publication gate. It does not add a passage to the pack. The question detector is a closed pattern list for those obligations, the four out-of-pack topics, and equipment-changing instructions. Retrieval terms remain a separate candidate filter. The detector does not cover arbitrary paraphrases.

## Open Questions

Product questions stay with the PRD numbering. This SAD does not answer them. A change to any of them goes to `@product-mgr`.

1. **Course architecture requirement (PRD Open Question 1).** Must the capstone demonstrate multiple autonomous agents? This SAD records a workflow with two bounded model tasks. A course rule that requires an autonomous agent conflicts with the predictability decision and needs an operator decision before Build changes the pattern.
2. **Model budget (PRD Open Question 2).** What spend limit, provider, and model govern development and scored runs? `max_rpm`, the CR-006 numeric ceiling, the final environment-variable name, and EC-008’s dollar threshold wait on this answer.
3. **Customer validation and production compliance (PRD Open Question 3).** Is an HR or IT practitioner available? Retention, production permissions, and integration recovery are undefined. Week 6 can still score D1–D12.
4. **Intake completeness (PRD Open Question 4).** Who submits the new-hire record, which fields are mandatory, and what happens when a required field other than role is missing? The validation contract above covers the behaviors the PRD already specifies. It does not choose the remaining fields.
5. **Case closure (PRD Open Question 5).** When does onboarding end, and when should the case close or be archived? Day-one readiness is not closure. P2’s reservation “until onboarding completes” has no end event other than IT revocation until this question is answered. No automatic closure is specified.
6. **MRD title.** The PRD cites “Employee Onboarding MRD — Business Rewrite.” `mrd.md` is titled “Market Research Document: Automated Employee Onboarding Workflow.” This SAD used that file as the MRD. The title mismatch is unresolved. It does not change the product rules.
7. **Policy paraphrase scope.** FR-05 and D9 require cited answers for paraphrased P1 and P2 questions. The PRD does not give those wordings. The section 4 detector answers only its listed patterns. A paraphrase outside that list is unmatched or ambiguous and is not published. Whether each demonstration paraphrase must be added to the detector, or whether manual review is acceptable for anything outside the list, is undecided. `@product-mgr` owns a PRD change. This SAD does not add patterns to close it.

**Diagram style:** Resolved. The operator kept the shipped default (`paper #f5f5f5`, `ink #2d3142`, `accent #bf4520`).

**Implementation decisions.** Resolve each one before building the control it affects. Record the result in this document. These are not new product requirements.

7. **Retry layers.** The prose allows one additional attempt inside the 60-second event budget. The CrewAI adapter requires `max_retry_limit >= 2`, and `max_iter` 2 can also repeat work inside a task. Provider libraries may retry as well. Set one total-attempt policy so those layers do not stack past one additional model attempt, and so a retry cannot send a second follow-up.
8. **Faithful-meaning check.** Resolved 2026-11-26 in the policy publication contract. The published words are the exact approved passage, so meaning does not depend on a paraphrase. Relevance is the question detector in section 4, not a citation, an excerpt, a retrieval hit, or `covered`. No second model judge is added. The detector is a finite pattern table. It does not answer arbitrary paraphrases. That product limit is Open Questions, “Policy paraphrase scope.” It is not closed here.
9. **Simulator binding.** Resolved 2026-11-26. The page sends a roster `actor_id`, and the server accepts the event only when `actor_id` and `actor_role` match one person in the simulator roster. The six ids use the intake-page spelling. The designated manager binding is in the resolved event schemas.
10. **Provider-wide circuit breaker.** The 60-second limit stops further attempts for one event. A shared breaker across events and hires is not specified. Decide whether the MVP needs one or whether it is deferred.
11. **API and UI completion.** Section 4 names the fields. Who generates the intake `event_id` is decided there: the client generates it before submit, and the server does not replace it. That choice is not open. The equipment reply draft, the `events` list on the hire read, the policy publication proposal, and the HR, start-date, and deadline schemas are specified. Layout stays with `ux.md`. Decision 10 remains open.

## Audit

- **Timestamp:** 2026-11-12T05:08:17Z
- **Persona ID:** system-arch
- **Action:** decompose-work
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset. Resolved from `aamad.config.yml` `runtime.target` and the adapter-registry default.
- **Prompt trace:** Omitted. That action recorded ownership from the PRD, system description, and US-001 through US-007.

- **Timestamp:** 2026-11-12T05:34:00Z
- **Persona ID:** system-arch
- **Action:** select-pattern, define-controls, create-sad
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset. Same resolution as above. Warning: the environment variable was not set.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set by this persona. No application model call was made.
- **Prompt trace:** Omitted. That revision recorded decisions from the MRD, PRD, system description, user stories, and the SAD template. It did not generate product behavior.
- **Tool use:** Read the SAD template, MRD, config template, CrewAI adapter rules, and the then-current `sad.md`. Checked `AAMAD_TARGET_RUNTIME` (unset). Checked for `.env.example` (absent).

- **Timestamp:** 2026-11-12T05:40:00Z
- **Persona ID:** system-arch
- **Action:** draw-diagram
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset.
- **Diagram:** `project-context/diagrams/system-arch/onboarding-workflow.html` and `project-context/diagrams/system-arch/onboarding-workflow.svg`. Type: architecture. Semantic pattern: none. Size: doc-inline. Tool: diagram-design, commit `0b9b10cab3dbf695642fa1a6c4b4f60df9083689`. Skin: shipped default, kept by the operator. Font source: system. `self_check.py --offline` printed OK.
- **Left out of the figure:** production HR, IT, identity, and messaging systems; a separate provider-API node; the return read from the case to the workspace.

- **Timestamp:** 2026-11-14T02:45:00Z
- **Persona ID:** system-arch
- **Action:** create-sad
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset. Resolved from `aamad.config.yml` `runtime.target` and the adapter-registry default. Warning: the environment variable was not set.
- **Scope of this revision:** Re-checked work ownership, pattern, controls, and eval criteria against the November 13 PRD. Added both activation paths, the four BR-6 conditions, date-change and decision-version behavior, the server-side role rule, and the policy publication gate. Separated the per-event timeout from a provider-wide circuit breaker. Carried PRD Open Questions 1–5 forward under the PRD’s numbers. Recorded implementation decisions 7–11. Did not copy the Jordan walkthrough or the PRD process diagram.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set by this persona. No application model call was made.
- **Prompt trace:** Omitted. This revision records architecture from the saved PRD, the SAD template, the CrewAI adapter, and the existing SAD. It does not generate product behavior.
- **Tool use:** Read `prd.md`, `sad-template.md`, `aamad.config.yml`, the CrewAI adapter rule, the config template defaults, and the existing architecture diagram. Checked `AAMAD_TARGET_RUNTIME` (unset) and `.env.example` (absent).
- **Diagram:** Checked `project-context/diagrams/system-arch/onboarding-workflow.html` and its SVG against this revision. The components still match. The figure was not redrawn. The business-process figure remains `project-context/1.define/diagrams/onboarding-process.svg`, linked from the PRD.

- **Timestamp:** 2026-11-19T19:40:00-08:00 (America/Los_Angeles)
- **Persona ID:** system-arch
- **Action:** validate-contract
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset. Resolved from `aamad.config.yml` `runtime.target` and the adapter-registry default. Warning: the environment variable was not set.
- **Path exception:** This persona’s declared output path is `project-context/1.define/sad.md`. That file does not exist. This revision edits the existing greenfield SAD at `project-context/2.build/sad.md` only. No second SAD was created.
- **Validated:** The operator proposal that the client generates the intake `event_id` before submit, that the server still assigns `hire_id`, and that business-state authority stays on the server. Accepted. PRD §2 “associates” is read as the server binding a client-supplied event id to a server-assigned hire id. That reading preserves US-007 and the PRD repeated-event rule, and it does not move activation, facts, readiness, role, or plan contents to the client. The same id with different recorded contents is `event_mismatch` because `conflict` already means the sequential in-flight refusal. The PRD and `project-context/1.define/ux.md` were not edited. No application code was written.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set by this persona. No application model call was made.
- **Prompt trace:** Omitted. This revision amends the saved SAD from the operator proposal, PRD §2 and §3, and US-007. It does not generate product behavior.
- **Tool use:** Read `project-context/2.build/sad.md`, `project-context/1.define/prd.md`, `project-context/1.define/user-stories/US-007.md`, and `aamad.config.yml`. Searched the SAD for event-id, hire-id, CR-005, and `conflict`.

- **Timestamp:** 2026-11-26T16:50:00Z
- **Persona ID:** system-arch
- **Action:** create-sad
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset. Resolved from `aamad.config.yml` `runtime.target` and the adapter-registry default. Warning: the environment variable was not set.
- **Path exception:** This persona’s declared output path is `project-context/1.define/sad.md`. That file does not exist. This revision edits the existing greenfield SAD at `project-context/2.build/sad.md` only. No second SAD was created. No application code was written.
- **Scope of this revision:** Recorded the equipment reply contract in section 4: multi-statement draft with excerpts, Python validation of unsupported and contradictory statements, the equipment ledger including later commitment, denial, and revocation, the authorized-sender check, one follow-up, contextual denial, the operator-approved deadline with Saturday and Sunday rolling to the next Monday, the operator-approved plan-version rule, and per-event `processing`, `complete`, and `failed` on the hire read. Intake rules and the prepared-example crew are unchanged. Implementation decision 7 and actor-id spelling (decision 9) stay open. No product question was left unresolved by this revision.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set by this persona. No application model call was made.
- **Prompt trace:** Omitted. This revision records architecture from the PRD, the existing SAD, the backend notes, and the operator-approved proposal. It does not generate product behavior.
- **Tool use:** Read `.cursor/agents/system-arch.md`, `aamad.config.yml`, `project-context/1.define/prd.md`, `project-context/2.build/sad.md`, and `project-context/2.build/backend.md`. No application file was edited.

- **Timestamp:** 2026-11-26T20:45:00Z
- **Persona ID:** system-arch
- **Action:** create-sad
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset. Resolved from `aamad.config.yml` `runtime.target` and the adapter-registry default. Warning: the environment variable was not set.
- **Path exception:** This persona’s declared output path is `project-context/1.define/sad.md`. That file does not exist. This revision edits the existing greenfield SAD at `project-context/2.build/sad.md` only. No second SAD was created. No application code was written.
- **Scope of this revision:** Recorded the policy publication check in section 4. The published answer is the exact passage. Relevance is the obligation table. A mixed out-of-pack question routes entirely to HR. `covered: false` and a valid but irrelevant citation are manual review. Invalid grounding is `model_failure`. An equipment instruction does not change case facts. Decision 8 is closed. Decision 11 still leaves the HR-decision schema, actor-id spelling, and frontend tooling open.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set by this persona. No application model call was made.
- **Prompt trace:** Omitted. This revision records architecture from FR-05, D9, CR-003, and the existing policy publication paragraph. It does not generate product behavior.
- **Tool use:** Read `.cursor/agents/system-arch.md`, `project-context/2.build/sad.md`, and the policy sections of `project-context/1.define/prd.md`. No application file was edited.

- **Timestamp:** 2026-11-26T21:05:00Z
- **Persona ID:** system-arch
- **Action:** create-sad
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset. Resolved from `aamad.config.yml` `runtime.target` and the adapter-registry default. Warning: the environment variable was not set.
- **Path exception:** This persona’s declared output path is `project-context/1.define/sad.md`. That file does not exist. This revision edits the existing greenfield SAD at `project-context/2.build/sad.md` only. No second SAD was created. No application code was written.
- **Scope of this revision:** Recorded the question detector in section 4: normalization, the ten obligation patterns, out-of-pack phrases, equipment-instruction phrases, clause and negation rules, precedence, a separate retrieval-term list, and acceptance examples. Unmatched and ambiguous questions use the recorded manual-review or no-obligation fallback. Open Question 7 flags the narrower paraphrase scope and leaves it undecided. Intake, equipment replies, Gemini settings, and the referral-versus-HR-approval distinction are unchanged.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set by this persona. No application model call was made.
- **Prompt trace:** Omitted. This revision records the detector from the existing policy publication contract, FR-05, D9, and Appendix A. It does not generate product behavior.
- **Tool use:** Read `.cursor/agents/system-arch.md`, `project-context/2.build/sad.md`, and the policy sections of `project-context/1.define/prd.md`. No application file was edited.

- **Timestamp:** 2026-11-26T21:30:00Z
- **Persona ID:** system-arch
- **Action:** create-sad
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset. Resolved from `aamad.config.yml` `runtime.target` and the adapter-registry default. Warning: the environment variable was not set.
- **Path exception:** The declared output path `project-context/1.define/sad.md` does not exist. This revision edits `project-context/2.build/sad.md` only.
- **Scope of this revision:** Recorded the HR decision, held-plan role reply, start-date change, and deadline schemas. Decisions 9 and 11 are resolved for those controls. Decision 10 stays open.
- **Prompt trace:** Omitted. This records the smallest field contract already required by FR-02, FR-04, FR-06, D2, and D8.
- **Tool use:** Read the SAD API section, PRD D1–D12, and US-002, US-004, and US-006.

- **Timestamp:** 2026-11-26T21:45:00Z
- **Persona ID:** system-arch
- **Action:** create-sad
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset.
- **Path exception:** The declared output path `project-context/1.define/sad.md` does not exist. This revision edits `project-context/2.build/sad.md` only.
- **Scope of this revision:** Recorded the task-update schema for policy acknowledgment, meeting confirmation, a held meeting, and training status. It follows BR-2, BR-6, P1, and P3. No application code was written in this revision.
