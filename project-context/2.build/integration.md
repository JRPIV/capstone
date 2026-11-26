# Integration

## Message flow

Intake, equipment reply, policy question, HR decision, start-date change, deadline, and task update are connected. The page at `http://127.0.0.1:8000/` sends the same JSON as before. The primary button label follows the selected action. A policy result still shows the exact cited passage, “Outside the pack. Routed to HR. No policy answer was published.”, or “Manual review. No policy conclusion was published.”

Acting as lists all six simulator people. The message does not set the sender. The server still checks the actor id and role together.

For intake, the server’s acknowledgment is `status: processing` after the hire is stored. The page reads `GET /hires/<hire_id>` once. It keeps one intake event id, and Run and Retry send that same id and the same recorded contents.

For a reply, the page sends `event_type: reply` with the selected sender, the displayed hire id, the event id in the field, the occurred-at value, and the message. A new reply needs a new event id. Retry sends the same event id and the same recorded contents. The acknowledgment is `processing` before the model finishes. The page then reads the hire until that `event_id` is `complete` or `failed`, or until 60 seconds pass. A polling timeout says the outcome is unknown and is not a failed event. A `failed` event shows its code and keeps the last verified case. While the reply is running, Run is unavailable and the case on screen stays labeled “Last verified case.”

## Verification

### Mocked tests

Not re-run in this integration turn. `backend.md` records 17 passing tests in `onboarding/tests/test_equipment_reply.py` with a stand-in reader and no Gemini call.

### API test

Checked over HTTP on 2026-11-26 against the restarted server on `127.0.0.1:8000`. This call used the live reader.

| Check | Result |
|---|---|
| Riley intake `api-riley-1` | `POST /events` returned 202. Hire `H-1003`, four tasks, plan version 1, that event `complete`. |
| Uncertain reply `api-reply-1` as `actor-taylor-brooks` / `it_fulfiller` | Acknowledgment 202 with `status: processing`. The hire read then showed that event `complete`, failure null, equipment unconfirmed, escalated false, plan version 1, four tasks, and one follow-up. |
| Same event id and the same payload again | 202 `processing`. Follow-up count stayed 1. |

### Browser test

Checked in the browser at `http://127.0.0.1:8000/` on 2026-11-26. The server was the project virtualenv with `GEMINI_API_KEY` loaded and not printed. The uncertain reply and the “No loaner” reply were live Gemini calls. The polling-timeout sentence was not observed, because both replies finished inside 60 seconds.

| Check | Result |
|---|---|
| Fresh Riley intake | Event `b2e723af-38b4-46a1-8e44-52d40ff31c28`, hire `H-1004`, four tasks, plan version 1, equipment unconfirmed. |
| Uncertain reply as IT fulfiller, Taylor Brooks | Event `6c4e8634-eae3-480f-a10c-abe0293f7f89`. Equipment stayed unconfirmed and not escalated. Plan version stayed 1. The page showed one follow-up, due `2026-03-13T17:00:00-05:00`. |
| Run again with that same event id and message | “No additional work was added.” Follow-up count stayed 1. Plan version stayed 1. |
| New event `9f2a1c44-7b10-4d2e-9a55-1c8e0b6d4a21`, message “No loaner.” | Equipment readiness Blocked, escalated yes, evidence that event id. Reason: “No permitted device is available by the start date.” Plan version 2. Follow-up count stayed 1. |
| Same event id with a different message | Banner showed `event_mismatch`. The blocked case stayed. Retry was shown. |
| Reload, then Riley intake again | Reply fields stayed hidden on Intake. Event `4b034ea2-8fd5-4875-9b89-3d63225eb4e6`, hire `H-1005`, four tasks, plan version 1. |
| Overlapping click | While Crew was running, Run was unavailable and a click sent nothing. A second browser tab was not used. |

## Limitations

- The acknowledgment never changes from `processing`. Completion and failure are the event row on the hire read.
- The page still uses the sprint banner and an inline error. It does not add the separate error page state from `ux.md`.
- Reset clears the screen only. It does not delete the stored hire. The intake event id remains until the page is reloaded.
- Jordan’s held intake is connected. The proposed-plan scenario and the practice failure stay disabled. HR decision, start-date change, and deadline are connected. Policy question uses only the listed patterns.
- The prepared-example Gemini crew is not started by the page. A reply starts `reply_reader` on the server.
- Sam Ortiz and Jordan Lee are not on the reply sender list. Those roles are bound to Morgan Hale and Riley Chen for this page.

## How to repeat the Riley reply check

1. From the repository root, run `.venv/bin/python -m onboarding.server`. The server loads the repository-root `.env` and does not replace variables already set. It does not print the key.
2. Open `http://127.0.0.1:8000/`.
3. Leave Event type on Intake. Choose “Riley Chen, complete supported intake” and press Run. Confirm Needs attention, four tasks, and a hire id that is not `H-002`.
4. Change Event type to Reply. Leave Simulated role on “IT fulfiller, Taylor Brooks.” Confirm Hire id matches the hire just shown and Event id is filled. Leave Occurred at at `2026-03-13T15:00:00-05:00`.
5. Set Message to `The laptop slips to March 19. A spare might be free on start day.` Press Run. Wait until the banner says Crew: done.
6. Confirm equipment readiness is Unconfirmed, escalated is no, plan version is 1, and the page shows one follow-up.
7. Press Run again without changing the event id or the message. The page says no additional work was added, and the follow-up count stays one.
8. Replace Event id with a new id. Set Message to `No loaner.` Press Run.
9. Confirm equipment readiness is Blocked, escalated is yes, the reason says no permitted device is available by the start date, and the follow-up count is still one.
10. Keep that event id, change the message, and press Run. The banner shows `event_mismatch`, and the blocked case stays.
11. Reload the page, choose Riley again, and press Run. A new hire appears with four tasks, and the reply fields stay hidden while Event type is Intake.

## Sources

- `onboarding/server.py`, `onboarding/router.py`, `onboarding/store.py`, `onboarding/equipment.py`, and `onboarding/simulator.py`.
- `workspace/index.html`, `workspace/src/main.js`, and `workspace/styles.css`.
- `project-context/2.build/backend.md` section 6. The HTTP check matched the recorded acknowledgment, the `events` list, and the one-follow-up replay.
- `project-context/2.build/sad.md` section 4, Equipment reply contract. The client finds its event on the hire read. The task list is the current case.
- `project-context/1.define/ux.md`. One Run control. The message does not change the sender. Retry keeps the event id. A committed replay adds no work. A lost result says the outcome is unknown.
- `project-context/1.define/prd.md` Appendix A. Riley Chen, start 2026-03-16, Austin, Customer Support Representative, manager Morgan Hale.

## Assumptions

- Serving the page from the same process, and allowing browser calls with `Access-Control-Allow-Origin: *`, stays the browser-access fix.
- The sprint page’s inline error is enough to show a refusal, a failed event, or a polling timeout. The fourth UX page state is not rebuilt here.
- Binding hiring manager to Morgan Hale and new hire to Riley Chen is the smallest use of the approved role select. It does not add a person picker.

## Open Questions

1. Descriptive updates for `frontend.md`, `backend.md`, and `README.md` were approved and applied on 2026-11-26. The reply sentences were applied after the operator approved the later proposal. PRD, SAD, and `ux.md` were not edited.
2. Whether the page should later call the blank-role path, which the server already implements, is outside this slice.
3. The 60-second polling timeout was not produced in the browser. Both live replies finished first.

## Audit

- **Timestamp:** 2026-11-26T16:23:42Z
- **Persona ID:** integration-eng
- **Action:** integrate-api, verify-messageflow, log-integration
- **Resolved runtime:** `crewai`, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset. Warning: the environment variable was not set.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set. No product model was called. The Gemini crew was not run and was not edited.
- **Prompt trace:** Omitted. This entry records the browser round trip. It does not embed secrets.
- **Tool use:** Read the intake server, router, store, page, SAD section 4, and `ux.md` retry rules. Served the page from `127.0.0.1:8000`. Ran Riley once, ran the same event again, displayed a refusal, displayed a lost connection, and retried that same event id.
- **Outcome:** The supported intake is connected. The case file held one hire and four tasks. Other routes stay disconnected.

- **Timestamp:** 2026-11-26T16:28:00Z
- **Persona ID:** integration-eng
- **Action:** sync-docs
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. This entry records approved descriptive updates in `frontend.md`, `backend.md`, and `README.md`.
- **Outcome:** Operator approved all descriptive updates. Those sentences now match the connected intake. PRD, SAD, and `ux.md` were not edited.

- **Timestamp:** 2026-11-26T17:45:00Z
- **Persona ID:** integration-eng
- **Action:** integrate-api, verify-messageflow, log-integration
- **Resolved runtime:** `crewai`, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset. Warning: the environment variable was not set.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor for this turn. Temperature and max_tokens were not set. The live replies used the server’s existing Gemini settings. The key was not printed.
- **Prompt trace:** Omitted. This entry records the HTTP check and the browser round trip. It does not embed secrets.
- **Tool use:** Read the equipment reply contract, `backend.md`, this file, and the page. Connected reply on the existing Run control. Restarted the server with the virtualenv. Ran one HTTP intake and reply, then the browser flow for hires `H-1004` and `H-1005`. Did not edit the backend, the Gemini configuration, the PRD, the SAD, or `ux.md`.
- **Outcome:** Reply is connected for the displayed hire. The uncertain reply stayed unconfirmed with one follow-up and plan version 1. The same event added no second follow-up. “No loaner” blocked and escalated equipment and added no follow-up. Intake still creates four tasks. Policy answers and HR approval stay disconnected.

- **Timestamp:** 2026-11-26T17:50:00Z
- **Persona ID:** integration-eng
- **Action:** sync-docs
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. This entry records approved descriptive updates in `README.md`, `frontend.md`, and `backend.md`.
- **Outcome:** Operator approved all descriptive updates. Those sentences now say the page sends a reply for the displayed hire. PRD, SAD, and `ux.md` were not edited.

- **Timestamp:** 2026-11-26T20:25:00Z
- **Persona ID:** backend-eng
- **Action:** sync-docs
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. This entry records the approved restart sentence.
- **Outcome:** Operator approved the update. The repeat steps now say `.venv/bin/python -m onboarding.server` loads the repository-root `.env`. PRD, SAD, and `ux.md` were not edited.

- **Timestamp:** 2026-11-26T21:20:00Z
- **Persona ID:** integration-eng
- **Action:** integrate-api, verify-messageflow, log-integration
- **Resolved runtime:** `crewai`, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset. Warning: the environment variable was not set.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor for this turn. The live policy call used the server’s Gemini settings, temperature 0. The key was not printed.
- **Prompt trace:** Omitted. This entry records the HTTP check and the browser round trip.
- **Tool use:** Connected policy question on the existing Run control. Restarted the server with the virtualenv. Live API hire `H-1008` published the exact P2 passage. The browser submitted “Can I work remotely?” and showed the outside-the-pack line. Intake fields hide again when Event type is Intake.
- **Outcome:** Policy question is connected. HR approval, start-date change, and deadline stay disconnected. The bounded patterns do not close the paraphrase-scope question.
- **Timestamp:** 2026-11-26T21:40:00Z
- **Persona ID:** integration-eng
- **Action:** integrate-api
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset.
- **Outcome:** Browser hire H-1009 went from held intake to Sam Ortiz’s proposed plan, Alex Rivera’s approval, a start-date change to 2026-03-09, and a deadline that escalated the meeting. No Gemini call on that path.

- **Timestamp:** 2026-11-26T21:55:00Z
- **Persona ID:** integration-eng
- **Action:** verify-messageflow
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. This check used the existing API. No new model call.
- **Outcome:** The redesigned page created Riley hire H-1005, replayed that intake with no additional work, and loaded stored hire H-1003. Its policy tab showed the existing P2 answer. Equipment stayed unconfirmed. The request bodies were unchanged.

- **Timestamp:** 2026-11-26T22:05:00Z
- **Persona ID:** integration-eng
- **Action:** verify-messageflow
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. The page shows the server failure message once. The key was not printed.
- **Outcome:** A recorded failure is read again with the same event id. A completed event adds no work. The failure sentence is not repeated. Live hire H-1007, event `43bbce54-5835-4bf6-9e09-dbd588019bc8`, completed from the page: equipment unconfirmed, plan version 1, one follow-up. The server log named `gemini-3.5-flash-lite`.

- **Timestamp:** 2026-11-26T22:10:00Z
- **Persona ID:** integration-eng
- **Action:** integrate-api
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. The examples are copied from the SAD question detector and the recorded reply sentences. No model call.
- **Outcome:** The reply and policy inputs show those exact sentences and the unsupported outcomes. The page does not add patterns. A wording outside the policy table is not supported. A reply sentence is not a phrase match.

- **Timestamp:** 2026-11-26T22:20:00Z
- **Persona ID:** integration-eng
- **Action:** integrate-api
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. No model call. Detector results were checked locally for the eleven recorded questions. Matching rules were not changed.
- **Outcome:** The policy question field lists every recorded detector example, grouped by P1–P4. A click fills the question and does not submit. Other wording may go to manual review, and out-of-pack topics go to HR. The reply field lists tested role, uncertainty, commitment, and denial sentences with the required sender and prior case. Those replies are examples, not an exhaustive wording list. The event id, sender, hire id, and time are left unchanged.
- **Doc sync:** no updates. `frontend.md` does not state that these controls are absent.

- **Timestamp:** 2026-11-26T22:40:00Z
- **Persona ID:** integration-eng
- **Action:** integrate-api
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. No model call. The key was not printed.
- **Outcome:** `GET /hires/<id>` adds `case_summary` from the current activation and the latest completed event. It does not rewrite stored messages or decisions. H-1010 stays active at version 2. Its summary is “HR approved the held plan. The plan is active.” The reply decision remains `proposed_plan` and the reply message remains “We hired a CSR.” Replaying that reply from the page, then submitting different text under the same event id, showed one `event_mismatch` line and left the summary on the approval. H-1011 stayed active at version 1. Mocked tests: 54 passed, no Gemini call.
- **Doc sync:** no updates. `frontend.md` does not say the summary follows the form’s event id.
