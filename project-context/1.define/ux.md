# UX Specification: Sprint 3 — Inputs, Run, Results

## Context & Instructions

This document is the interaction and behavior contract for one Sprint 3 workflow: **Inputs → Run → Results**. It is the handoff to `@frontend.eng`. It is not the final visual design. The frontend agent chooses hierarchy, layout, styling, and component composition, and preserves the required interactions and business rules below.

It specifies that workflow only. It does not design the rest of the PRD §6 workspace, and it does not change BR-1 through BR-7, the authority rules, or the readiness rules.

The workflow is the SAD runtime loop. The operator submits one event, the workspace shows that the event was accepted, and the workspace then shows the updated case or a visible failure. Model calls are not streamed. A model draft is not the result the operator reads. The result is the application’s case, or the failure, with the last verified facts left in place.

**Approval status** is `approved`. The operator recorded the Sprint 3 workflow on 2026-11-19 and approved the workspace redesign on 2026-11-26. The redesign section below is the visual contract. It does not change the workflow rules in this document.

## Input Requirements

**PRD**: `project-context/1.define/prd.md` — §5 (acknowledgment, 60-second result, one operator, sequential processing, accessibility), §6 (plain labels, processing and failure, no authority change)
**SAD**: `project-context/2.build/sad.md` — Work Ownership, Pattern Decision (workflow), Reference Architecture, Model and Context Strategy, Control Register, Frontend Architecture, section 4 contracts, section 6 data-flow table, implementation decision 11
**User Stories** (when present): `project-context/1.define/user-stories/US-001.md`, `US-002.md`, `US-007.md`. `US-003` through `US-006` constrain what a result may mean. This sprint does not design their dedicated screens.
**Design-system mode**: `create`. `aamad.config.yml` does not set `ui.design_system_mode`. The project mode is greenfield, so the default is `create`.
**Design-system source** (adopt): N/A
**Review / as-is UI** (brownfield): N/A. `project.mode` is `greenfield`.

## Responsibility split

Three kinds of statement appear in this document. The frontend agent treats them differently.

### Non-negotiable requirements

These come from the PRD, the SAD, the user stories, or from a consistency fix that preserves those rules. The frontend agent does not trade them away for layout.

- One operator, one in-flight event, sequential processing. The client does not send a second event while one is running.
- The server remains the authority for role, commit, idempotency, and readiness. The page does not approve a plan, confirm a fact, or hide a control that still performs a forbidden action.
- Page states are only **idle**, **running**, **done**, and **error**. The server’s one additional attempt stays inside **running**. It is not a second page state and not a second event id.
- The workspace generates the intake `event_id` before the request is sent and keeps that id with the recorded contents. The server assigns `hire_id` and does not replace the event id. The event id does not activate a plan, confirm a fact, set readiness, or choose a role. This is the operator amendment validated in the SAD on 2026-11-19.
- A retry of a lost acknowledgment sends that same event id and the same recorded contents. The client does not mint a new id in order to retry. The same id with different recorded contents is `event_mismatch`: the new body is not applied, and no second hire or plan is created. `conflict` stays the in-flight refusal only.
- Results change only from a hire read or a stated failure. The page does not invent tasks, a Ready label, or a partial model fact. On failure or an uncertain outcome, the last verified case stays visible.
- A proposed plan is labeled as not active. An active plan is labeled as active. Those are different outcomes.
- Required information, keyboard operation, visible labels, visible focus, text status, and errors tied to the fields that failed.
- Synthetic data only. No raw provider payload, secret, or model transcript.

### UX recommendations

The frontend agent may refine these. A refinement still has to meet the non-negotiable requirements.

- Grouping the work into three regions named Inputs, Run, and Results, in that reading order, on one page.
- The sentence-level copy in this document, when the meaning is kept.
- Which visual pattern carries primary versus secondary information, as long as the Results questions in section 2 are answerable in that priority.
- The starting color, type, and spacing inventory in section 4.
- Stacking the three groups in one column at the laptop widths in section 6.

### Open decisions

These need the product owner or an architecture decision. Neither design agent should close them inside the layout.

- They are listed under Open Questions. Where the page needs an interim behavior so the workflow is still usable, that interim is stated next to the decision and is not a new product feature.

## UX Specification

### 1. User and task

- **Who is acting.** One operator on one laptop, playing the simulated roles through a role selector. The selector roles are HR coordinator, hiring manager, IT fulfiller, and new hire. Seeded people already named by the PRD are Alex Rivera (HR coordinator), Taylor Brooks (IT fulfiller), Sam Ortiz, Morgan Hale, Jordan Lee (H-001), and Riley Chen (H-002). The operator may play every role. The message text does not choose the role.
- **What they need to accomplish.** Submit one onboarding event and see what the case system committed: an updated hire, or a visible failure that writes no new verified fact.
- **The primary action.** **Run**. It submits the event currently in the form. It does not approve a plan, confirm equipment, or send a second event while one is in flight.
- **Constraints.**
  - One event at a time. The client withholds a second submission while a run is in flight. If a second submission still reaches the server, the server’s `conflict` response is the safeguard. The in-flight event continues.
  - The workspace should show that the submission was accepted within 2 seconds, then a result or a visible failure within 60 seconds, including the server’s one additional attempt. These are the PRD §5 planning targets. That attempt is not a new event id and not a second click.
  - Synthetic fixtures only. Provider keys and raw provider payloads are not shown.
  - The operator must be able to finish this task with a keyboard, with visible labels, and with status in text. Status is not color alone.
  - There is no cancel control. The SAD stops a model task by returning a draft, exhausting the 60-second budget, or failing the call. The visible outcome is then the result or the failure.

### 2. Flow and structure

**Requirement.** One local page. No app navigation and no second route. The SAD specifies one workspace view and does not require a separate SPA. The page always offers three jobs, including while a run is in flight:

1. **Inputs** — compose one event.
2. **Run** — the page state and the Run control.
3. **Results** — the hire read, or an empty result when no case exists yet.

**Recommendation.** Present those jobs as three visible groups in that order. The frontend agent may recompose them if the run state stays perceivable during processing and the Results priority in this section is preserved.

**Entry.** Open the local workspace. The page starts in **idle**.

**Exit.** Leave the page. This sprint does not add sign-out, case closure, or a reset control.

**Recovery.**

- Invalid client input stays **idle**. Values stay in the fields. Focus moves to the first invalid field. Nothing is sent.
- A failed run stays on this page in **error**. Values stay in the fields. Results keeps the last verified case if one exists.
- A second click while **running** sends nothing. A server `conflict` for a submission that arrived anyway does not replace the in-flight run. That code still applies if the second body differs.
- After **error**, Run with unchanged contents retries the same event id. After **done**, Run with those same contents replays that id. Changing the intake contents starts a new intake under a new client-generated event id. The page does not clear the form by itself.

**Page state.** The page is in exactly one of **idle**, **running**, **done**, or **error**. Task words such as overdue, escalated, unconfirmed, and blocked are labels inside a **done** result. They are not extra page states.

| From | Action | To |
|------|--------|----|
| idle | Run, and the client checks pass | running |
| idle | Run, and a required field is missing | idle. The missing fields are named. Focus moves to the first. No request is sent. |
| running | Acknowledgment, then the case read returns and `failure` is null | done |
| running | The server reports `unreadable_input` or `model_failure`, or it reports that the budget ended and no new fact was written | error. Confirmed non-commit. |
| running | The client stops hearing a response before a terminal case read (delivery failure or client timeout) | error. Outcome uncertain. Last verified case stays. |
| running | The operator activates Run again on this page | running. No request. Run stays unavailable. No conflict notice, because the client sent nothing. |
| running | A second submission still reaches the server | running for the accepted event, plus the conflict notice, whether or not the body matches. The second event did not start. |
| done or error, contents unchanged | Run | running. The same event id and the same recorded contents are sent again. |
| error or done, intake contents changed | Run | running. A new intake event id is generated first. The previous id is not sent with the new contents. |
| error or done, non-intake contents changed, typed event id unchanged | Run | running. The server answer is `event_mismatch` once the first attempt is no longer in flight. |

A repeated event id that the server treats as a no-op is **done**. Results shows the original case and says that no additional work was added. It does not look like a new plan and it does not look like a failure.

No journey figure is included. This action stops at `ux.md` and does not write a diagram file.

#### Run, validation, and the server conflict safeguard

Two different mechanisms were easy to conflate. They are specified separately.

**Client validation (idle).** Run stays available while the page is idle, including when required fields are empty. The operator discovers errors by activating Run. The activation names each missing required field, moves focus to the first, leaves every value in place, and does not send. Run is not disabled to stand in for that message. A disabled control would hide the error and would not match a keyboard activation.

**Client in-flight lock (running).** After a valid Run, Run becomes unavailable until the page leaves **running**. The status text says why: a run is already in progress. Activating the unavailable control sends no request and does not show a conflict notice. This is what the operator can do from the page, and it is the behavior UX-007 tests.

**Server conflict (safeguard).** SAD `conflict` is the sequential-processing refusal. The page still has to handle it if a second submission arrives outside the locked control: a second tab, a retried request, or a test harness. The accepted event stays **running**. The notice reads that one event is already running and this submission was not started, and it names the refused event when the server returns that id. UX-011 tests this path. It is not tested by clicking the unavailable Run button.

The server’s one additional attempt inside the 60-second budget is not either of these. The page stays **running** through that attempt. The client does not start a retry of its own while the page is running.

#### Event identity, retry, and uncertain outcomes

SAD CR-005 is the rule, including the 2026-11-19 amendment. Recorded contents are `event_type`, `actor_id`, `actor_role`, `occurred_at`, and `body`, plus `hire_id` on every type except intake. Comparison is of those values.

The workspace generates the intake `event_id` before it sends the intake, stores it with those contents, and sends that same id again when the acknowledgment is lost. The server assigns `hire_id` and returns it on the acknowledgment. A client value does not choose the hire. The operator does not type either id for an intake.

| Situation | What the client sends on the next Run | What Results shows |
|-----------|----------------------------------------|--------------------|
| Confirmed non-commit, contents unchanged | The same event id and the same recorded contents | Last verified case. The error says no new verified fact was written. |
| Same event id and the same contents after a committed result | That same pair | **Done.** The event was already recorded. No additional work, hire, or plan was added. |
| Delivery failure or client timeout, including before any acknowledgment, contents unchanged | The same event id and the same recorded contents. Intake uses the id generated before the first send. | Last verified case. The outcome of this run is unknown. The page does not say the commit failed, and it does not say Ready for this run. |
| Intake contents changed since that id was sent | A new intake event id, generated before this send, with the new contents. The old id is not paired with the new contents. | The status says this is a new intake. |
| Same event id with different recorded contents, and that attempt is no longer in flight | The mismatched pair only if it still reaches the server (a typed non-intake id, a second client, or a harness). The intake form does not send this pair. | **Error,** code `event_mismatch`. The new contents were not applied. No second hire or plan. The last verified case stays. This is not the conflict notice. |

The page does not update the verified case from a timeout. It updates that case only when a hire read arrives. A retry the server treats as a no-op replaces the error with **done** and the original result. It does not append a second plan.

Changing an intake so the same person can be corrected, or so a different person can be submitted, is a new event id. Reusing the old id for that correction is `event_mismatch`, including when the first attempt never committed. For reply, start-date change, policy question, and deadline reached, the operator’s event id is sent as typed. The server rejects a changed body under that id. The workspace does not rewrite a typed id.

#### Screen: Inputs

Purpose: collect one event. The event types are the SAD set: `intake`, `reply`, `start_date_change`, `policy_question`, `deadline_reached`.

**Requirement.** The operator can supply:

- **Simulated role**, required: HR coordinator, hiring manager, IT fulfiller, new hire. The selected role is what the server treats as the sender. The message text is not the role.
- **Event type**, required. Changing it changes which body fields are required. Values already entered in fields that remain on screen are kept.
- **Occurred at**, required. The demonstration clock is an input.
- Body fields for the selected type:

| Event type | Fields the operator fills | Not collected on this page |
|------------|---------------------------|----------------------------|
| Intake | Employee name, start date, role, office, designated manager | Hire id. The server assigns it. The workspace generates the event id before send. The operator does not type either. Role may be blank. |
| Reply | Hire id, event id, message | A role typed inside the message. |
| Start-date change | Hire id, event id, new start date | A model prompt. |
| Policy question | Hire id, event id, question | A passage picker. Retrieval stays on the server. |
| Deadline reached | Hire id, event id | A message. The body may be empty. |

- Hire id, when collected, accepts the seeded ids H-001 and H-002 and another synthetic id for the D12 hire. There is no hire list.
- Event id, when collected, is the operator’s id so the same submission can be run again.
- Blank role is a valid intake. The result is the held path, not a client error.
- Client checks, run only when the operator activates Run:
  - Simulated role, event type, and occurred at are present.
  - Intake requires employee name, start date, office, and designated manager.
  - Reply and policy question require hire id, event id, and non-empty text.
  - Start-date change requires hire id, event id, and a new start date.
  - Deadline reached requires hire id and event id.
- A failed check names the fields and leaves every value in place. The server may still return `unreadable_input` after a request is sent. That response is **error**, not this client check.

**Recommendation.** Helper text on the role control: “The message does not change who is sending this.” A multiline control for a long reply. Show the generated intake event id and the server-assigned hire id as secondary metadata. The retry depends on the retained id, not on the operator reading it.

#### Screen: Run

Purpose: show the page state and hold the only primary action.

**Requirement.**

- The action is named **Run**.
- In **idle**, Run is available even when required fields are missing. Activating it either validates, as above, or moves the page to **running**.
- In **running**, Run is unavailable and the reason is in text. Inputs stays on the submitted values and does not accept edits until the page leaves **running**, so a later retry is still that submission. Before the acknowledgment, the status says the event is being submitted. After the acknowledgment, the status says it was accepted, includes the event id and hire id, and says a result or a visible failure is expected within 60 seconds. There is no fifth state for the moment before acknowledgment.
- In **done**, the status says done and includes the event id. Run is available.
- In **error**, the status includes the readable message, the code when the server sent one, and the next step. Run is available, except that its meaning follows the event-identity table.
- The conflict notice appears only after a server `conflict`. It does not appear when the unavailable Run control swallows a local activation.
- Status is a live announcement. Color is not the only signal.

**Recommendation.** Keep the status and Run in the same group so the reason Run is unavailable stays with the control.

#### Screen: Results

Purpose: show the case the application committed, or show that nothing verified is known for this run.

**Requirement: priority.** A person reading a **done** result can answer these questions in this order, before relying on technical metadata:

1. **What happened.** The outcome of this event, in the application’s words. Examples the case may already contain: “Awaiting IT confirmation,” “No device confirmed for start,” “Meeting needs reconfirmation,” “Proposed plan. Not active until HR approval,” “Labeled for HR review. No tasks were created,” “This event was already recorded. No additional work was added.”
2. **Readiness.** **Ready** or **Needs attention**, and only when the case says so.
3. **What needs attention.** The reasons. If nothing does, the result says the case is Ready rather than leaving a blank where reasons would be.
4. **Who owns the next action.** The responsible person and the next action. If the case has no next action, the result says so.
5. **Where the support is.** Each current task by name, with owner, execution status (pending or complete), readiness (confirmed, unconfirmed, or blocked), due date, overdue or escalated in words, and a way to read the evidence and the stored message or question. Zero tasks is stated, with the reason from the outcome line. Evidence that is absent is stated as absent.

**Primary information** is those five answers. **Secondary metadata** is hire id, event id, plan version, occurred-at, error codes, and evidence-reference strings. Secondary metadata stays available. It does not lead the result, and it is not the only place a task name or an owner appears.

**Requirement: verified facts.**

- **Empty, idle, and no case has been read.** The result says that there is no result yet and that the next step is to run one event. No sample hire, no fake Ready state, and no task rows.
- **Done.** `failure` is null. There is no error banner. A proposed plan and an active plan both use this result. The outcome line distinguishes them. This page has no Approve control.
- **Running.** The previous verified result may stay on the page. It is labeled as the last verified case, not as the outcome of the event that is still running. If there has never been a case, the empty line stays.
- **Error, confirmed non-commit.** A banner carries the message and the code (`unreadable_input`, `model_failure`, or the server’s budget failure). It says no new verified fact was written. The last verified case follows when one exists. When none exists, the banner says no plan was written, and the page does not show Ready or invented tasks.
- **Error, uncertain.** The banner says the outcome is unknown. It does not claim that the commit failed. The last verified case stays, labeled as last verified. The page does not show Ready for the unknown run. Run without editing resends the same event id and the same recorded contents.
- **Error, `event_mismatch`.** The banner names that code and says this event id was already used with different contents, the new contents were not applied, and no second hire or plan was created. The last verified case stays. The banner is not a request to wait for a running event.
- **Unsupported role or location, a blank role, and other missing business fields** are **done** when the server commits that rule outcome. They are not the error state. An unsupported outcome says it is labeled for HR review and lists no invented tasks. A blank role says one request went to the designated manager and lists no tasks. Missing fields named by the server are listed as missing, and the result is not Ready.

**Recommendation.** The frontend agent chooses how the five primary answers are grouped and emphasized. A definition list, a task stack, and a banner are acceptable patterns, not required components. The outcome line and the readiness line should be readable without opening secondary metadata.

#### Out of scope

This sprint does not specify, and the page must not pretend to offer:

- A hire list, a hire switcher, or a multi-hire browser. Storage may hold Jordan, Riley, and the D12 hire. This page shows the hire returned for the event that just ran.
- A task-plan editor, a task-specific conversation, or a version-history browser. Results may show the current tasks, the stored message, and the current plan version because those fields are on the hire read. Browsing earlier versions is a later surface.
- The HR decision form: approve a held plan, or record an escalation disposition. Results may say that a plan is proposed and not active. It does not collect the decision.
- Reset, replay as a separate control, and case closure or archive. Reusing an event id goes through Run. There is no second replay button.
- A fourth region named History, a dashboard, a general chat, streaming tokens, a cancel button, or a partial model result.
- Confirmation or approval buttons for any role, including a confirm-before-retry dialog. Hiding a control that still runs is not the design. The controls are absent here. The server remains the authority check.
- A phone layout, a second operator, production HR, IT, identity, or messaging, account or access changes, identity documents, eligibility decisions, and payroll or tax.
- Future-work controls for more roles and locations, a holiday calendar, richer reporting, and a live channel. They are not drawn as inactive decorations on this page.
- Endpoint paths, JSON schemas, and the frontend framework. SAD implementation decision 11 leaves those open.
- A rendered prototype. The operator directed this work to stay in `ux.md` and not to write code or a high-fidelity design.

US-003, US-004, US-005, and US-006 still govern the product rules. A later increment designs the screens on which the operator resolves equipment, changes a start date as its own focused layout, reads a policy answer as its own focused layout, and records an HR decision. If one of those events is submitted through this page, Results uses the same information requirements and the application’s labels. This document does not add those stories’ extra controls.

### 3. Visual direction

This section is guidance. It is not a visual lock.

- **Reference.** No operator-supplied brand file and no adopted design system. The structural reference is the SAD data flow: one event in, one chain, one case read back. The figure `project-context/diagrams/system-arch/onboarding-workflow.svg` is an architecture drawing. It is not a layout to copy.
- **What to borrow.** A restrained operational page. One primary action. Plain language from PRD §6. The five Results questions matter more than chrome.
- **What not to copy.** Do not turn the architecture diagram into the screen. Do not use a chat thread, a dashboard of metrics, cards of testimonials, or a raw model transcript. Do not invent status colors that are the only signal.
- **Authority.** The frontend agent may change grouping, order of visual weight, density, and component shapes. It may not drop a required state, invent an approval action, or make metadata the only carrier of readiness, ownership, or failure.

### 4. System references

- **Canonical source.** `create` mode, because no design system was named. The inventory below is a starting point for this page. It is not an approved token set, and the frontend agent may replace the values.
- **What is required.** Status is text as well as color. Focus is visible on every interactive control. Ordinary text and status text meet WCAG 2.2 AA contrast (4.5:1, or 3:1 for large text). Pointer targets meet the WCAG 2.2 24-by-24 CSS-pixel minimum. Semantic controls (`button`, inputs, headings, landmarks) are used for the real controls. The SAD does not require Tailwind, a component library, or a second UI framework.
- **Token mapping.** Whatever values are chosen should be shared roles (background, text, action, focus, running, ready, attention, error), not one-off colors on each element. CSS custom properties are a suitable mapping if the implementation is server-rendered HTML. They are not a requirement if the chosen stack has another theme mechanism.

Starting inventory the frontend agent may replace:

| Role | Value | Use |
|------|-------|-----|
| canvas | `#f4f1ea` | Page background |
| surface | `#fffcf7` | Group backgrounds |
| text | `#1c1915` | Body and headings |
| text-muted | `#4a453c` | Secondary metadata and hints |
| border | `#d9d3c7` | Group and field borders |
| action | `#1f4d3a` | Run background |
| action-text | `#fffcf7` | Run label |
| focus | `#1f4d3a` | Focus indicator |
| status-running-bg / status-running-text | `#e7f0f6` / `#1c3d5a` | Running status |
| status-ready-bg / status-ready-text | `#e5f2ea` / `#1f4d3a` | Ready and done |
| status-attention-bg / status-attention-text | `#f8ead7` / `#6b3e12` | Needs attention |
| status-error-bg / status-error-text | `#f8e6e4` / `#7a1f1f` | Error and field errors |

Starting type scale, system UI stack, no required webfont: page title 1.5rem/600, region title 1.125rem/600, body 1rem/400, label 0.875rem/600, metadata 0.875rem/400, body line-height 1.5. A recommended page title is “Onboarding case,” with a subtitle “Sprint 3: Inputs, Run, Results.”

Starting spacing scale: 4, 8, 16, 24, 32, 48 px.

Behaviors the components must provide, without mandating their visual composition:

- The page has one top-level heading.
- Inputs, the run state, and the result are identifiable regions.
- Every input has a visible label. Field errors are programmatically tied to those inputs.
- One primary button, Run. The unavailable state is marked unavailable and does not still submit.
- The status line is announced when the page state changes.
- The result can show an error or uncertain banner and the last verified case together.

A chat bubble, a metric card, a timeline, and an approval dialog are out of scope, not merely unapproved variants.

### 5. State matrix

The page state is idle, running, done, or error.

| State | Screen / route | What the user sees | Next useful action |
|-------|----------------|--------------------|--------------------|
| Loading | Same page. Page state **running**. | Run is unavailable, and the status says why. After acknowledgment, the status includes the event id and hire id. Results, if any, is labeled as the last verified case. Inputs shows the submitted values and does not accept edits. | Wait. Do not expect a second click to start another event or to produce a conflict notice. |
| Empty | Results, page state **idle**, and no case has been read. | “No result yet. Run one event to see the case.” Inputs are editable. Run is available. | Fill in the event and Run. Missing fields are reported when Run is activated. |
| Populated | Results, page state **done**. | Primary: what happened, Ready or Needs attention, what needs attention, who owns the next action, and where the tasks and evidence are. Secondary: ids, plan version, evidence-reference strings. No raw transcript. No error banner. | Read the outcome. Run again with the same contents to replay that event id. Change the intake contents to start a new intake under a new event id. |
| Validation | Inputs, page state **idle**. | Run was activated. Each missing required field is named. Example: “Enter the hire id.” Values remain. No request was sent. Run stays available. | Correct the named field and activate Run again. |
| Error | Run and Results, page state **error**. | Confirmed non-commit: the code, the message, and “No new verified fact was written,” with the last verified case if one exists. Uncertain timeout or delivery failure, including a lost intake acknowledgment: the outcome is unknown, the last verified case is unchanged, and Run without editing resends the same event id and contents. `event_mismatch`: the new contents were not applied and no second case was created. `unreadable_input` with no prior case does not say Ready. | Retry the same contents under the same id. To submit different contents, use a new event id. On an intake, the workspace generates that new id when the contents change. Manual review is this error with the last verified case, not another page. |
| Permission | Inputs and Results. | The role selector is the only identity control. There is no approve or confirm button. A server rejection because the submitted role does not match the simulator is **error**, inputs kept, and no model transcript. A reply the rules refuse is **done** when the server commits that outcome: the message is kept, and the outcome line says this role cannot establish the fact. | Choose the simulated role that matches the action, then Run. Recording an HR approval is out of scope. |
| Unavailable | Run, page state **running**. | The Run control is visible and unavailable. The status says a run is already in progress. | Wait for done or error. A local activation does not submit and does not show a conflict notice. |

Agent and runtime states from the SAD, mapped onto the four page states:

| SAD behavior | Page state | What the operator must be able to tell |
|--------------|------------|----------------------------------------|
| Processing after acknowledgment, including the server’s one additional attempt | running | The event was accepted and is not finished. The attempt is not a second event. |
| Case read with `failure` null | done | The application committed this outcome. A proposed held plan is labeled as not active. |
| Schema-invalid draft, provider error, or budget exhaustion that the server reports as writing no fact | error, confirmed | What failed, and that no new verified fact was written. |
| Client timeout or delivery failure before a terminal read | error, uncertain | That commit is unknown, and that the last verified case is unchanged. |
| `conflict` for a submission that reached the server while another event is in flight | running | The first event is still the run. The second submission did not start. |
| Local activation of Run while it is unavailable | running | Nothing was sent. This is not the conflict notice. |
| Same event id and the same recorded contents after a committed result | done | The original result is the record. Nothing new was added. |
| Same event id and different recorded contents, attempt no longer in flight | error, `event_mismatch` | The new contents were not applied. No second hire or plan. This is not `conflict`. |
| HR approval of a held plan | Not a page state | The result can say the plan is proposed. This page does not collect the approval. |
| Waiting for a person mid-call | Not used | The SAD does not pause a model task for the operator. The next human message is a new event from idle or a retry of a known id from error. |
| Cancelled by the operator | Not used | There is no cancel control. Exhausting the 60-second budget is error. |
| Partial model fact | Not used | CR-006 forbids showing a partial model fact. Results keeps the last verified case. |

### 6. Responsive behavior

**Requirement.** Viewports to design and later inspect:

- **1280×800**, the primary laptop viewport.
- **1024×768**, the narrowest width this sprint specifies.

A phone layout is not a PRD requirement and is not designed here. At both widths, every required field, the Run control, the page-state text, the error or uncertain banner, and the five primary result answers remain available. Text wraps. Status is not color alone. Secondary metadata may wrap or sit after the primary answers. It is not removed.

**Recommendation.** One column, Inputs then Run then Results. Do not move the groups into a dashboard of side-by-side cards. Keep the status text with Run. When a task row would overflow 1024, stack that task as labeled lines instead of dropping a primary fact. The empty-result sentence stays a sentence.

### 7. Acceptance criteria

Each row is observable on the rendered page. Passing a row does not close the related story’s full MVP scope. UX-007 and UX-011 are different tests. UX-009 matches the idle validation rule. UX-005 and UX-012 are different failure tests.

| ID | Criterion | Story | How it is observed |
|----|-----------|-------|--------------------|
| UX-001 | On first load the page is idle. Inputs is editable. Run is available. Results says no result yet, with no hire and no Ready label. | US-001 | Open the page before any submission. |
| UX-002 | A valid Run switches the page to running, makes Run unavailable, announces why, keeps the submitted values visible, and does not accept edits to those values while running. | US-001 | Submit Riley Chen’s complete supported intake and read the status before the result. |
| UX-003 | A committed intake with a null failure shows done. Primary answers include four Appendix A tasks, or, for a blank role, zero tasks and one manager request. The outcome is not a raw model transcript. Event id is present and is not the lead of the result. | US-001, US-002 | Read Results after a complete intake and after a blank-role intake. |
| UX-004 | An unsupported role or location ends done, with an HR-review label and no invented tasks. An unreadable intake ends error, with no plan and no Ready label. | US-001 | Run one unsupported intake and one unreadable intake. |
| UX-005 | A server-confirmed model or budget failure ends error, says no new verified fact was written, keeps Inputs, and still shows the last verified case when one existed. | US-007 | Fail a run after a successful intake and compare the task list with the prior result. |
| UX-006 | Replaying a committed event id with the same recorded contents shows done and states that no additional work was added. The case does not gain a second plan or a second hire. | US-001, US-007 | After a committed intake, Run again without editing. The page resends the generated event id. For the other event types, leave the typed event id and the body unchanged and Run. |
| UX-007 | While the page is running, Run is unavailable. Activating it sends no request and shows no conflict notice. The status stays running for the accepted event. | US-007 | Activate Run again before the first result returns. Confirm that no second submission leaves the page. |
| UX-008 | A held plan that is only proposed answers “what happened” with “Proposed plan. Not active until HR approval.” No Approve button is on the page. | US-002 | Read Results after the manager reply that produces a proposed plan. |
| UX-009 | With a required field empty, Run is still available. Activating it stays idle, names the field, moves focus to it, keeps the other values, and sends nothing. | US-001 | Clear the hire id on a reply and activate Run. |
| UX-010 | Status words are present for idle, running, done, error, Ready, Needs attention, overdue, and escalated. Those words are still understandable if color is ignored. Core controls are reachable by keyboard in idle, done, and error. In running, Run is reachable as an unavailable control and the reason is announced. Every input has a visible label, and a validation error is tied to its field. | US-006, US-007 | Tab through the page in idle, running, done, and error. Trigger UX-009 and inspect the field error. |
| UX-011 | A second submission that reaches the server while the first event is in flight leaves the page running for the first event and shows the conflict notice. The second event does not start. | US-007 | Deliver the second submission through an integration harness or a second client. Do not use the unavailable Run button as this test. |
| UX-012 | After a timeout or delivery failure, including an intake whose acknowledgment never arrived, the error says the outcome is unknown, the last verified case is unchanged, and Run without editing sends the same event id and the same contents. If the server had already committed, the follow-up is done, says no additional work was added, and does not create a second hire. | US-007 | Drop the intake response before acknowledgment, then Run once without editing. Repeat once against an event id that is already committed. |
| UX-013 | On a done result, a reader can answer what happened, readiness, what needs attention, who owns the next action, and where the tasks and evidence are, without using event id or evidence-reference strings as the cue. Those strings are still present. On an error with a prior Ready case, the banner makes clear that Ready is the last verified case, not the outcome of the failed or unknown run. | US-006, US-007 | Read one done result and one error-after-success result. Ask the five questions in order. |
| UX-014 | A repeated event id whose recorded contents differ, after that attempt is no longer in flight, ends error with `event_mismatch`. The new contents are not applied, the last verified case is unchanged, and no second hire appears. The banner does not tell the operator to wait for a running event. | US-007 | Submit the mismatched pair from an integration harness. Do not use the intake form’s edited-field path, which generates a new event id instead. |

### 8. Prototype (when the surface is new)

- **Hardest screen and why.** Results in **uncertain error** after a verified Ready case already exists. The reader has to see that the outcome is unknown, that Ready belongs to the last verified case, and that a retry will reuse the known event id.
- **Path.** Not written. `project-context/1.define/prototypes/` has no file from this action.
- **Why it was not written.** The operator directed this work to stop at `ux.md` and not to write code or a high-fidelity design. The hardest-screen prototype waits until that direction changes.

## Assumptions and approval

**Approval status**: `approved`

- The operator asked for one Sprint 3 workflow named Inputs → Run → Results, with page states idle, running, done, and error, and an explicit out-of-scope list. That request is the scope of this file. The SAD still names the fuller PRD §6 workspace for the MVP. This file does not delete that workspace. It leaves it undesigned.
- The operator’s review asked for consistent Run, validation, and retry behavior; a split between requirements, recommendations, and open decisions; and a Results priority that does not prescribe the final visual design. This revision records that review. It does not record approval.
- “Screens” in the earlier draft are the three jobs on the one SAD workspace page. They are not three routes and not a required visual chrome.
- Manual review, confirmed failure, and uncertain timeout or delivery failure are the **error** page state. Overdue, escalated, unconfirmed, blocked, and a proposed plan are words inside **done**.
- A blank role, an unsupported role or location, and a duplicate event id are successful rule outcomes when the server commits them. They use **done**.
- `unsupported` as an error code remains a server code in the SAD. On this page, an unsupported role or location that is labeled for HR review is shown as done. A code of `unsupported` that arrives with `failure` set is shown as error. The copy follows the code and the `failure` field the server actually returns.
- Actor ids are not invented here. The selector submits the simulated role. The server binds `actor_id`. The visible control is the role name.
- The intake event id is generated by the workspace before submit. This follows the SAD amendment validated by `@system.arch` on 2026-11-19. It is not original PRD text. The PRD was not rewritten. Hire id stays server-assigned. The other event types still ask the operator for hire id and event id.
- Occurred-at is a required labeled value because the demonstration clock is the source of that input. How the control is drawn is a frontend choice.
- The color, type, and spacing inventory is a starting point under `create`. It is not binding. Contrast, focus, labels, and text status remain binding because PRD §5 and the accessibility baseline require them.
- The operator approved this specification on 2026-11-19. That approval covers the Sprint 3 Inputs → Run → Results contract, including the validated intake event-id amendment. It does not approve the undesigned PRD §6 regions.

## Approved workspace redesign

Recorded 2026-11-26. The operator approved this visual direction and authorized implementation in the same turn. Preview data in the reference is not application data.

**Reference.** `/Users/joeyrparker/.codex/visualizations/2026/11/26/01a21870-eeff-7fc0-9d56-26ad8132c0f0/onboarding-workspace.html`. Borrow hierarchy, density, and the light tokens. Do not copy its fictional hire, its preview-only submit, or its Lucide icon loader.

**Tokens.** Page `#F5F7FA`, panel `#FFFFFF`, text `#17263C`, secondary `#53657B`, line `#DCE3ED`, action `#2858C7` with white text, selected `#EEF3FF`, attention `#885009` on `#FFF7E8`, success `#21644F` on `#EAF7F0`, error `#A12A36` on `#FFF0F2`. System font. Body 14px. Hire heading 28px. Radius 12px panels and 8px controls. Spacing from 4, 8, 12, 16, 20, 24, 32.

**Structure.** Header “Onboarding / Case workspace.” Case identity from the stored hire. Two columns at 960px and above: case, then Take action. One column below that, with a Take action jump. Tabs: Tasks, Activity, Policy, Decisions. Composer actions map to the existing event types. Event details hold the event id and occurred-at. Demo setup holds form reset and says it does not delete cases.

**Status words.** Ready to submit, Processing event, Event complete, Event failed, Connection lost — outcome unknown, Still waiting — outcome unknown. Do not say Crew. Do not say Gemini unless a backend stage says so. This increment does not have that stage, so the status stays Processing event.

**Conflicts.** None that change product rules. The reference’s actor list is shorter than the roster; the page keeps all six simulator identities. The reference’s date field is a note; the page sends the existing `YYYY-MM-DD` body.

## Sources

- `project-context/2.build/sad.md`. Frontend Architecture, section 4 submit and hire-read contracts, section 6 incoming-event table, Control Register CR-001 through CR-008 (especially CR-005 idempotency and CR-006 fail-closed failure), Production Shape, and the “processing, then case result or visible failure” runtime note.
- `project-context/1.define/prd.md`. §2 process and plain outcome language, §5 responsiveness, capacity, privacy, and accessibility, §6 primary surface and labels, §7 D1, D2, and D11 as the outcomes this page must be able to show, Appendix A task names and seeded people.
- `project-context/1.define/user-stories/US-001.md`, `US-002.md`, `US-006.md`, `US-007.md`.
- `aamad.config.yml`. `project.mode: greenfield`. `ui.design_system_mode` unset, resolved to `create`.
- `.cursor/templates/ux-template.md` and `.cursor/skills/product-design/SKILL.md`, `reference.md`, `states.md`, and `accessibility.md`.
- Operator instruction for the first draft: one Sprint 3 workflow, Inputs → Run → Results, states idle / running / done / error, out of scope stated, stop after the UX document, do not write code.
- Operator review of that draft: reconcile Run-during-processing with conflict, reconcile disabled Run with validation, specify uncertain retry without breaking event-id idempotency, separate requirements from visual guidance, and prioritize Results information. No code and no high-fidelity design.
- Operator decision, 2026-11-19: the client may generate the intake event id before submission. Hire id and business-state authority stay on the server. The same event id with different contents must be rejected. Validated in `project-context/2.build/sad.md` before this UX revision. `event_mismatch` is the code recorded there.

## Open Questions

- Does the next UX increment add the hire list, task conversation, version history, and HR decision form onto this same page, or does a later `ux.md` revision replace this slice? The SAD names those regions. This sprint does not.
- PRD Open Question 4 remains open. Which intake fields besides role are mandatory, and what the server shows for each, is a product decision. Until then, this page treats only the listed client checks as checks Run can fail, and it prints the missing-field list the server returns.
- SAD implementation decision 11 remains open for endpoint paths, full JSON schemas, and the frontend framework. This document does not choose them.
- When the server returns the code `unsupported`, should the page always use done (HR-review label) or sometimes error? The assumption above follows `failure` being null or set. `@backend.eng` can confirm that split when the schema is fixed.
- The exact simulator `actor_id` values are not in the SAD. The page shows role names only until those ids are fixed.
- No brand source was provided. The starting inventory stands until the operator adopts one or the frontend agent replaces the values inside the accessibility constraints.
- The intake event-id amendment is resolved in the SAD. It is not an open UX choice. Endpoint paths and full JSON schemas remain open under SAD implementation decision 11.
- The section 4 contract lists `unsupported` among error codes, while a labeled unsupported role is a committed rule outcome. The done-versus-error split above is an assumption, repeated here so it is not treated as a visual choice.

## Audit

- **Persona ID:** ux-designer
- **Action:** design-ux
- **Timestamp:** 2026-11-19T19:20:00-08:00
- **Resolved project.mode:** greenfield (`aamad.config.yml`)
- **Resolved ui.design_system_mode:** create (unset in config; greenfield default from the product-design reference)
- **Resolved runtime:** not used. `AAMAD_TARGET_RUNTIME` was not read as an override. `aamad.config.yml` `runtime.target` is `crewai`. This action does not scaffold the runtime.
- **Tool use:** Read the UX persona, product-design skill, reference, states, and accessibility notes; the UX template; `aamad.config.yml`; SAD frontend, section 4, and section 6; PRD §2, §5, §6, and Appendix A; US-001, US-002, US-006, and US-007. No prototype file and no application source were written.
- **Model:** Grok 4.7, IDE session. Temperature and max_tokens are not parameters of this persona action.
- **Prompt trace:** Omitted. This action writes a design contract from local artifacts. It does not call the product model and it does not embed secrets.
- **Outcome:** Wrote `project-context/1.define/ux.md`. Approval remains `pending`.

- **Persona ID:** ux-designer
- **Action:** design-ux (revision before approval)
- **Timestamp:** 2026-11-19T19:40:00-08:00
- **Resolved project.mode:** greenfield
- **Resolved ui.design_system_mode:** create
- **Tool use:** Reread `project-context/1.define/ux.md` and the product-design state rules. Revised the same file. No prototype, no application source, and no high-fidelity design.
- **Model:** Grok 4.7, IDE session. Temperature and max_tokens are not parameters of this persona action.
- **Prompt trace:** Omitted for the same reason as the first entry.
- **Outcome:** Reconciled Run, validation, conflict, and retry. Separated requirements, recommendations, and open decisions. Restated Results by information priority. Approval remains `pending`.

- **Persona ID:** ux-designer
- **Action:** design-ux (incorporate validated SAD amendment)
- **Timestamp:** 2026-11-19T19:55:00-08:00
- **Resolved project.mode:** greenfield
- **Resolved ui.design_system_mode:** create
- **Tool use:** Read the SAD amendment from `@system.arch` in `project-context/2.build/sad.md` (CR-005, section 4 submit and intake rules, section 6 repeated-event row). Updated this file to match. Did not edit the SAD or the PRD. No application code and no high-fidelity design.
- **Model:** Grok 4.7, IDE session. Temperature and max_tokens are not parameters of this persona action.
- **Prompt trace:** Omitted. The behavior is copied from the validated SAD amendment. No product-model call and no secrets.
- **Outcome:** Intake retries reuse the client-generated event id. `event_mismatch` is the different-contents error. Approval remains `pending`.

- **Persona ID:** ux-designer
- **Action:** design-ux (record operator approval)
- **Timestamp:** 2026-11-19T19:56:00-08:00
- **Resolved project.mode:** greenfield
- **Resolved ui.design_system_mode:** create
- **Tool use:** Updated the approval status in this file after the operator replied “Approved.” No application source was written.
- **Model:** Grok 4.7, IDE session. Temperature and max_tokens are not parameters of this persona action.
- **Prompt trace:** Omitted. The change records an operator decision and does not call the product model.
- **Outcome:** Approval status set to `approved`. `@frontend.eng` may implement.

- **Persona ID:** ux-designer
- **Action:** design-ux
- **Timestamp:** 2026-11-26T21:50:00Z
- **Resolved project.mode:** greenfield
- **Resolved ui.design_system_mode:** create
- **Tool use:** Read the operator brief and the local visual reference. Recorded the approved workspace redesign in this file. Did not edit the PRD or the SAD. Did not copy preview case data into the application.
- **Prompt trace:** Omitted. The operator approved the visual direction in the same request.
- **Outcome:** The redesign section is the visual contract. Workflow rules in this document stay in force.
