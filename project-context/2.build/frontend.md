# Frontend

## Frontend Workflow Overview

This is the Sprint 3 demonstration page for the automated employee onboarding capstone. One operator uses it locally. The page shows prepared sample cases. It does not contact a live system, and no crew process is running.

1. **Who starts.** The operator opens the onboarding page and starts a run. One person plays the simulated HR coordinator, hiring manager, IT fulfiller, and new hire. The page does not ask a live crew to begin.
2. **What they give.** They choose one prepared example and press Run. The examples are Riley Chen’s complete supported hire, Jordan Lee’s hire with the role missing, Jordan Lee’s plan waiting for HR approval, or a practice failure that writes nothing.
3. **What happens.** The page marks the run as underway, then returns the fixed sample for that example. Reset clears the form and the result and returns the page to its start. After the practice failure, Retry sends that same failed example again, even if a different example was chosen afterward.
4. **How they know.** The banner reads Crew: idle, Crew: running, or Crew: done. A dot is gray, blue, or green for those three, and red when an error is showing. The banner also says that no crew process is running. The last-updated time changes when a result appears, when an error appears, or when Reset is used. An error is written in words, and Retry is shown.
5. **What they get.** A successful example shows a verified case: what happened, whether the plan is active, held, or only proposed, whether it needs attention, who should act next, and the tasks. Riley’s case is an active plan with four tasks and still needs attention. Jordan’s missing-role case has no tasks and asks the manager to confirm the role. Jordan’s other case is a proposed plan that is not active until HR approval. The practice failure adds no case and says no new verified fact was written.

**Status:** Sprint 3 build spec approved and implemented. The four `workspace/` files exist. No live backend is connected.  
**Product:** Automated Employee Onboarding Workflow  
**Persona:** frontend-eng  
**Action:** document-frontend  
**Project mode:** greenfield (`aamad.config.yml`)  
**UX contract:** `project-context/1.define/ux.md`, Approval `approved` (2026-11-19)

C1–C8 are Sprint 3 implementation exceptions. They are not edits to the PRD, the SAD, or the approved `ux.md`. Those contracts stay in force for the MVP. This page is the sprint demonstration. A later increment returns to the full workspace, the four page states, the submit-event and hire-read contracts, and the resilience rules.

No genuine architectural change is required. The Pattern Decision stays a workflow. CrewAI stays off this page. `startRun` and `getRunStatus` are temporary adapters, documented in section 2.5. They do not replace SAD section 4.

The 2026-11-20 halt remains closed. `ux.md` is approved. The operator approved this spec on 2026-11-19, and the page was then built from section 2.

## 1. Sprint 3 exceptions

The professor asked for a simple page on stubbed services. The approved `ux.md` describes a fuller case page. This sprint builds the simple page. The upstream sentences are unchanged.

| # | Sprint 3 page | Contract that stays in force | Exception, this sprint only |
|---|---|---|---|
| C1 | Machine: idle, running, done. A failure is an inline message and Retry, then idle. | `ux.md`: page states are idle, running, done, and error. | The fourth state is not a state on this page. The MVP contract still has it. |
| C2 | Reset clears the form, the result, and the in-memory stub. | `ux.md`: no reset control this sprint. SAD: Reset restores a case-store fixture and is not an event on a hire. PRD: D-rows start from a reset. | This button is a local clear. It is not the SAD test operation. |
| C3 | Retry resubmits a snapshot taken when the failed run started. Later edits to the form do not change that snapshot. | `ux.md`: Run is the only primary action. Retrying is Run again. | Retry is a second control. Its payload rule is section 2.4. |
| C4 | `startRun` and `getRunStatus` return fixed objects. | SAD section 4: submit an event, then read a hire. No run-status API. | Temporary adapters. Section 2.5. They are removed when the live client is bound. |
| C5 | Banner text is `Crew: idle`, `Crew: running`, or `Crew: done`, plus “Stubbed status. No crew process is running.” | `ux.md` has no crew banner. The SAD says CrewAI is not the entry point. | The word Crew names the stub machine. It does not start a process and it does not change the pattern. |
| C6 | This stub does not generate an event id and does not simulate replay, `conflict`, `event_mismatch`, or a lost acknowledgment. | `ux.md` and SAD CR-005. UX-006, UX-011, UX-012, and UX-014. | Deferred past this demo. The rules remain the product rules. |
| C7 | The page implements the baseline in section 2.9. | `ux.md` and PRD §5: headings, labels, keyboard, visible focus, text contrast, errors tied to fields. | Advanced accessibility testing and the resilience paths wait. The baseline does not wait. |
| C8 | One Scenario select and the fixtures in section 2.6. | `ux.md`: every event type, role selector, occurred-at, per-field checks, client-generated intake event id. | The full form remains the later MVP surface. This select is the demo input. |

**Aligned with the contracts.** No network, no streaming, no tool-call details, no cost tracking, and no model call. Status words sit beside the color dot, so color is not the only signal. The dot colors may replace the starting swatches. `ux.md` section 4 allows that replacement. Text uses the `ux.md` text pairs in section 2.9.

**Sprint-only addition.** A last-updated time sits in the banner. It is not written into `ux.md`. It leaves with this demo unless a later UX revision keeps it.

## 2. Simplified build

### 2.1 Page

One static page. No framework, no package manifest, no route, no server.

| File | Role |
|---|---|
| `workspace/index.html` | The page |
| `workspace/styles.css` | Layout, focus, and the banner colors |
| `workspace/src/main.js` | State, snapshot, controls, and rendering |
| `workspace/src/stub.js` | Temporary `startRun` and `getRunStatus` adapters, and the four payloads |

Open the HTML file in a browser. Nothing is fetched.

Regions, top to bottom: banner, Inputs, the three controls, Results. The `h1` is “Onboarding case”. The subtitle is “Sprint 3: Inputs, Run, Results.” Each region is a `section` with an `h2`.

### 2.2 Banner

The banner is the stub’s state. It is not a connection to CrewAI.

| Machine | Banner text | Dot, when no inline error |
|---|---|---|
| idle | Crew: idle | Gray `#6b6560` |
| running | Crew: running | Blue `#1d4e89` |
| done | Crew: done | Green `#1f4d3a` |

When an inline error is present, the dot is red `#9b2c2c`. The banner text stays “Crew: idle”. The error sentence is in the banner region, associated with the form as section 2.9 describes.

Under the status line, always: “Stubbed status. No crew process is running.”

**Last updated** sits in the banner. Before the first finished attempt it reads “Last updated: not yet”. It changes when a run reaches done, when an inline error is set, and when Reset completes. The value is the browser’s local time. It does not tick on its own.

### 2.3 Machine

Exactly one of idle, running, done.

| From | Control | To | Inputs | Results |
|---|---|---|---|---|
| idle | Run, and a scenario is selected | running | The select is frozen for the wait. A snapshot is taken first. | Any case already on screen stays and is labeled “Last verified case”. The inline error clears when running starts. |
| idle | Run, and no scenario is selected | idle | Unchanged. | Unchanged. “Choose a scenario.” Retry stays hidden. No snapshot is written. |
| running | Status read returns a case | done | Editable again. | That case replaces the result. `failedSnapshot` is cleared. |
| running | Status read returns an error payload | idle | Editable again. The select is not changed by the page. | The previous verified case stays, labeled “Last verified case”. The error sentence is shown. `failedSnapshot` is the snapshot from the start of this run. Retry appears. |
| idle, error visible | Retry | running | The select is not read. | Previous verified case stays during the wait. |
| idle or done | Reset | idle | Select returns to “Choose a scenario”. | “No result yet. Run one event to see the case.” Error clears. `failedSnapshot` is discarded. Retry hides. |
| running | Run, Reset, or Retry | running | No change. All three controls are unavailable. Nothing is submitted. | Unchanged. |

There is no cancel control. The stub wait is 400 ms between the resolved start and the status read. The page does not wait 60 seconds and does not retry on its own.

Done means the stub returned a case payload. It does not mean the hire is Ready.

### 2.4 Run, Reset, and Retry

A submission snapshot is a plain object copied by value:

```
{ scenario_id: string, facts: string }
```

`facts` is the “What the operator is submitting” sentence for that scenario, copied at the moment Run or Retry is accepted. The page keeps that object. It does not read it back from the select.

**Run** is available in idle and done, and unavailable while running. If the select is on “Choose a scenario”, Run stays idle and shows the validation error. Otherwise Run copies `{ scenario_id, facts }` from the current option and passes that copy to `startRun`. It does not clear the select.

**Reset** is available in idle and done, and unavailable while running. It does not call `startRun`. It discards `failedSnapshot` and the last verified case, and returns the banner to idle with a gray dot.

**Retry** is shown only when `failedSnapshot` is set, the machine is idle, and the inline error is visible. Retry passes a copy of `failedSnapshot` to `startRun`. It does not read the Scenario select. Changing the select, or any other control, after the failure leaves `failedSnapshot` as it was. Run is how a newly selected scenario is submitted. Reset discards the snapshot, so Retry cannot fire after Reset until another failure stores a new one.

The `stub-failure` payload is always the error object. Retry of that snapshot shows the same error again and stores the same snapshot again. A case appears only when Run or Retry sends `riley-complete`, `jordan-blank`, or `jordan-proposed`.

**Check S3-RETRY-SNAPSHOT.** This is the test for C3.

1. Choose Stub failure. Activate Run. Wait until the machine is idle, the error is visible, and Retry is visible.
2. Change Scenario to Riley Chen, complete supported intake. Do not activate Run.
3. Activate Retry.
4. Pass condition: the object passed to `startRun` has `scenario_id` `stub-failure` and the stub-failure facts sentence. Results do not show Riley’s four tasks. The error “No new verified fact was written.” is shown again. The select may still display Riley.
5. Activate Run.
6. Pass condition: the object passed to `startRun` has `scenario_id` `riley-complete`. Results show the active plan.

### 2.5 Temporary adapters

`startRun` and `getRunStatus` exist only in `workspace/src/stub.js` for this sprint. They are not SAD operations. SAD section 4 still requires a client to submit an event and then read a hire. Integration binds that pair later. These two functions are then unused.

| Temporary adapter | Production contract it does not replace | What the demo returns |
|---|---|---|
| `startRun(snapshot)` | Submit an event: `event_id`, `event_type`, `actor_id`, `actor_role`, `occurred_at`, `body`, and `hire_id` when the type is not intake | `{ run_id: "run-stub-1", scenario_id: snapshot.scenario_id, accepted: true }` |
| `getRunStatus(runId)` | Read a hire: plan, tasks, readiness, messages, `failure` or null | The fixed case for the `scenario_id` last passed to `startRun`, or the error payload |

`run_id` is always `run-stub-1`. `getRunStatus` returns the payload for that remembered `scenario_id` when `runId` is `run-stub-1`. Any other `runId` returns the error payload. The functions do not compute readiness, tasks, or policy. They do not call `fetch`, a socket, a model, or CrewAI. The returned cases use the section 4 fields the page renders (`hire_id`, plan, tasks, readiness, `failure`) so the same rendering can later show a real hire read.

The page calls `startRun` once and then `getRunStatus` once. It does not poll.

### 2.6 Dummy scenarios

The select has a placeholder, “Choose a scenario”, and four options. A description under the select shows the selected row’s facts. Three options are the business outcomes. The fourth is the error used by Retry.

| Scenario id | Business outcome | Facts copied into the snapshot | Payload |
|---|---|---|---|
| `riley-complete` | Active plan | Riley Chen, start 2026-03-16, role Customer Support Representative, office Austin, manager Morgan Hale | Case below. `plan_label`: `active`. `failure`: null. |
| `jordan-blank` | Held intake, role missing, no tasks | Jordan Lee, start 2026-03-02, role blank, office Austin, manager Sam Ortiz | Case below. `plan_label`: `none`. `failure`: null. |
| `jordan-proposed` | Proposed plan awaiting HR approval | Hire H-001, hiring manager, message “We hired a CSR” | Case below. `plan_label`: `proposed`. `failure`: null. |
| `stub-failure` | No new verified fact | Stub failure. No case is written. | `{ status: "error", message: "No new verified fact was written.", case: null }` |

**Verified and unverified.** A payload with `failure: null` is a verified outcome. The page says “Verified case”. Task evidence that is absent is labeled “Unverified”. Unverified evidence does not make the case Ready. The error payload does not replace the last verified case.

**Proposed and active.** `active`: “Active plan. Four tasks created. No approval hold.” `proposed`: “Proposed plan. Not active until HR approval.” `none`: “One request went to Sam Ortiz. No tasks were created.” There is no Approve button. The proposed plan is not rendered as active.

Riley, active, Needs attention. Policy is overdue because Appendix A’s due date is 2026-03-12 and the seeded clock is 2026-03-13. Equipment and the meeting have no evidence. The case is not Ready.

| Task | Owner | Due | Execution | Readiness | Evidence |
|---|---|---|---|---|---|
| Policy acknowledgment | Riley Chen, new hire | 2026-03-12 | pending | unconfirmed | Unverified. Overdue. |
| Equipment readiness | Taylor Brooks, IT fulfiller | 2026-03-16 | pending | unconfirmed | Unverified. |
| First-day meeting | Morgan Hale, hiring manager | 2026-03-16 | pending | unconfirmed | Unverified. |
| Customer-support tools orientation | Morgan Hale, hiring manager | 2026-03-23 | pending | unconfirmed | Unverified. |

Attention reasons: policy acknowledgment is overdue and incomplete; no device is confirmed for the start; the first-day meeting is not confirmed. Next owner: Riley Chen. Next action: record the policy acknowledgment. Hire id: H-002. Plan version: 1.

Jordan, held intake. Zero tasks. The page states that zero tasks were created. Reason: the role was not on the intake. Next owner: Sam Ortiz. Next action: confirm the role. Hire id: H-001. One stored message: “Ask Sam to confirm the role.” This is a verified hold, not an active plan and not Ready.

Jordan, proposed, awaiting HR approval. The four Appendix A tasks are listed with owners Jordan Lee, Taylor Brooks, Sam Ortiz, and Sam Ortiz. Policy due 2026-02-26 is overdue. Equipment and meeting due 2026-03-02. Training due 2026-03-09. Every evidence line says Unverified. Readiness: Needs attention. Hire id: H-001. Plan version: 1. The outcome line says the plan is not active until HR approval.

Results order for a case: what happened, Active or Proposed or no plan, Ready or Needs attention, what needs attention, who owns the next action, then the tasks. Hire id and plan version follow the tasks.

Empty results, before any case: “No result yet. Run one event to see the case.”

### 2.7 Deferred

Not built in this sprint, and not represented by an inactive control:

- Live HTTP, CrewAI, model calls, streaming, tool traces, and cost
- Hire list, version-history browser, task conversation, HR approval
- The full event form, generated event ids, `conflict`, `event_mismatch`, lost acknowledgment, and the 60-second budget
- A History region, a cancel control, and a second route
- Assistive-technology lab testing, and treating an automated scan as acceptance

### 2.8 After approval

Write only the four files in section 2.1. Do not edit `ux.md`, the PRD, or the SAD. Then `*review-ui` can render the page. This spec does not claim the page has been seen.

### 2.9 Baseline accessibility

Implemented on this page:

- One `h1`. Each region has an `h2`.
- The Scenario select has a visible label, “Scenario”. Run, Reset, and Retry are `button` elements with those names.
- Tab order is the select, Run, Reset, and Retry when Retry is shown. Enter and Space activate the focused button.
- `:focus-visible` draws a 2px solid `#1f4d3a` outline with a 2px offset. The dot colors are not used as text.
- Text uses the `ux.md` pairs: `#1c1915` on `#fffcf7` and on `#f4f1ea`, `#4a453c` for secondary text on `#fffcf7`, and `#7a1f1f` on `#f8e6e4` for the error sentence. Those pairs are the contrast baseline. The gray, blue, green, and red dots are indicators beside the words.
- Run, Reset, Retry, and the select are at least 24 by 24 CSS pixels.
- “Choose a scenario.” is a paragraph with id `scenario-error`. When it is shown, the select has `aria-invalid="true"` and `aria-describedby="scenario-error"`. When it is cleared, `aria-invalid` is removed. The stub error sentence is in the banner and is not described as a field error.

Deferred: a contrast audit, a target-size audit, and assistive-technology testing. The implementation still uses the pairs and the sizes above.

## 3. Implementation blockers

None. The operator approved this spec. The page is the four files in section 2.1. `forgetLastScenario` is the stub hook Reset uses to drop the remembered scenario id.

| Check | Result |
|---|---|
| `ux.md` approved | Yes. Exceptions C1–C8 do not require an edit to it. |
| PRD and SAD | Unchanged. No architectural change. Section 4 remains the production contract. |
| Fixtures | Active plan, held intake, proposed plan awaiting HR approval, and one error payload. |
| Retry | Snapshot rule and check S3-RETRY-SNAPSHOT are in section 2.4. |
| Accessibility baseline | Section 2.9. Advanced testing is deferred. The baseline is not. |
| Adapters | Section 2.5. Temporary. They do not replace submit-event or hire-read. |
| `setup.md` | Absent. A static file does not need it. |
| Application source | `workspace/index.html`, `workspace/styles.css`, `workspace/src/main.js`, `workspace/src/stub.js`. |

## 4. Spec gate

**Operator approval of this build spec:** `approved` (operator, 2026-11-19)

Approval of `ux.md` was already recorded and is separate from this gate. This gate is now approved. The PRD, the SAD, and `ux.md` were not edited.

## Sources

- Operator refinement, 2026-11-19: C1–C8 are sprint exceptions; Retry uses a snapshot; the accessibility baseline stays; the three business fixtures stay; `startRun` and `getRunStatus` are temporary adapters. PRD, SAD, and `ux.md` are not modified.
- Professor’s Sprint 3 guidance, 2026-11-19: stub names, Run / Reset / Retry, three primary states, crew-status banner, color dot, last-updated time, no live backend.
- `project-context/1.define/ux.md`. Approved 2026-11-19.
- `project-context/2.build/sad.md`. Pattern Decision, section 4, CR-005, and the Reset test operation. `project-context/1.define/sad.md` is still absent.
- `project-context/1.define/prd.md`. §5, §6, Appendix A, D1 and D2.
- `aamad.config.yml`. `project.mode: greenfield`. `runtime.target: crewai`.

## Assumptions

- A later increment implements the full `ux.md` page and the SAD section 4 client. This spec does not schedule that increment.
- The banner sentence is enough, inside this sprint, to keep the word Crew from claiming a live process. The SAD is not amended for that sentence.
- Riley’s fresh intake is Needs attention. The fixture does not show Ready.
- Jordan’s proposed payload can be selected without first running the held intake. The stub does not compute one from the other.
- The D12 hire has no name in the PRD. This page does not add one.
- `AAMAD_TARGET_RUNTIME` was not read. Config and the adapter default are `crewai`. This spec does not scaffold that runtime.
- The four `workspace/` files are the Sprint 3 page. They are not the CrewAI runtime.

## Open Questions

None for implementation of this spec. The D12 hire remains unnamed in the PRD and is outside this page.

## Audit

- **Timestamp:** 2026-11-20T02:59:00Z
- **Persona ID:** frontend-eng
- **Action:** develop-fe
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was not read.
- **Prompt trace:** Omitted. That action halted because `ux.md` was missing.
- **Outcome:** Halted. No source.

- **Timestamp:** 2026-11-20T03:56:00Z
- **Persona ID:** frontend-eng
- **Action:** document-frontend
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was not read.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set. No application model call was made.
- **Prompt trace:** Omitted. That draft recorded a build spec from `ux.md` and Appendix A.
- **Outcome:** First Sprint 3 build spec. Approval left `pending`. No source.

- **Timestamp:** 2026-11-20T04:23:00Z
- **Persona ID:** frontend-eng
- **Action:** document-frontend
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was not read.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set. No application model call was made.
- **Prompt trace:** Omitted. That revision compared the professor’s guidance with `ux.md`, the PRD, and the SAD.
- **Outcome:** Simplified stub plan and conflict table. Approval left `pending`. No source. `ux.md` and the SAD were not edited.

- **Timestamp:** 2026-11-20T04:31:00Z
- **Persona ID:** frontend-eng
- **Action:** document-frontend
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was not read. Warning: the environment variable was not confirmed.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set by this persona. No application model call was made.
- **Prompt trace:** Omitted. This revision records the operator’s sprint exceptions. It does not call the product model and it does not embed secrets.
- **Tool use:** Reread `project-context/2.build/frontend.md` and applied the operator refinements in place.
- **Outcome:** C1–C8 recorded as Sprint 3 exceptions. Retry snapshot and S3-RETRY-SNAPSHOT added. Accessibility baseline restored. Adapters marked temporary against SAD section 4. Implementation blockers: none. Spec approval remains `pending`. No application source. PRD, SAD, and `ux.md` were not edited.

- **Timestamp:** 2026-11-20T04:50:00Z
- **Persona ID:** frontend-eng
- **Action:** develop-fe
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was not read. Warning: the environment variable was not confirmed.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set by this persona. No application model call was made.
- **Prompt trace:** Omitted. The page was built from the approved spec. It does not call the product model and it does not embed secrets.
- **Tool use:** Wrote the four `workspace/` files. Served them with `python3 -m http.server` and exercised idle, running, done, validation, Retry’s snapshot, the three case fixtures, and Reset in the Cursor browser at 1920×1080, plus an overflow check at 1024×768. The server was stopped afterward.
- **Outcome:** Spec gate set to `approved`. Page implemented. PRD, SAD, and `ux.md` were not edited.
- **Doc sync:** no updates. No allowlisted descriptive doc states a launch command, port, or stack that this page made false. `setup.md` is absent and was not created. 2026-11-20T04:50:00Z, frontend-eng, sync-docs.

- **Timestamp:** 2026-11-20T13:52:00Z
- **Persona ID:** frontend-eng
- **Action:** document-frontend
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was not read.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set by this persona. No application model call was made.
- **Prompt trace:** Omitted. This entry records a reader overview of the existing Sprint 3 page. It does not call the product model and it does not change behavior.
- **Tool use:** Read the opening and closing of `project-context/2.build/frontend.md`. No application source was edited.
- **Outcome:** Added “Frontend Workflow Overview” at the start of this file. Approval status, exceptions, and implementation notes are unchanged.
