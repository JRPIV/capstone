# Integration report

The case workspace and the Python API are one process. Sections 1–11 describe the application as it runs. Section 12 keeps the earlier audit entries as history. This turn did not change code, rerun tests, or reset cases.

## 1. Current status

All seven case actions are connected on the page and in `onboarding/router.py`: intake, reply, policy question, start-date change, deadline check, HR decision, and task update. The sender menu lists all six simulator people. Python selects the route. CrewAI runs only the equipment-reply reader or the policy answerer, and only after the router has already accepted the event. The prepared-example crew in `onboarding/kickoff.py` is a separate command. The page does not start it.

The assignment’s three requirements are met by the evidence already recorded in `submission/ASSIGNMENT.md`. This section does not add a new run.

| Requirement | What the recorded checks show | Evidence |
|---|---|---|
| End-to-end functionality | A blank-role intake stays held with zero tasks. A complete Customer Support Representative intake creates four tasks and an active plan. An uncertain equipment reply stays unconfirmed and records one follow-up. | Browser: `submission/screenshots/01-end-to-end-held-intake.png` (H-1010), `05-end-to-end-riley-tasks.png` (H-1011), `07-equipment-reply-follow-up.png`. Mocked tests: 58 passed in 0.882s, no provider call. |
| Human-in-the-loop | Sam Ortiz’s role reply proposes a plan. The plan stays inactive until Alex Rivera approves it. Approval leaves missing evidence incomplete. | Browser, no model call: `submission/screenshots/02-hitl-proposed-not-active.png` and `03-hitl-active-after-approval.png`. H-1010, Active, version 2, decision `approve_held_plan`, rationale “Role is CSR.” |
| External API integration | A browser policy question called Gemini and showed citation P2. A later equipment reply on the same hire called Gemini and committed a grounded result. | Live provider: `submission/screenshots/06-external-api-policy-citation.png` and the citation row in `07-equipment-reply-follow-up.png`. H-1011. Policy event `07d17a89-f663-4ceb-9bab-1a41cb73d739`. Equipment event `dc1822c6-4948-4035-95c5-1372b1642b75`. The server log names `gemini-3.5-flash-lite` for both. The key is not recorded. |

The 58 automated tests do not call Gemini. The H-1010 approval path does not call a model. The two H-1011 calls are the live Gemini calls.

## 2. One vertical workflow

The table is the recorded browser demonstration on 2026-11-26. H-1010 is the approval path. H-1011 is a second hire and is the path that calls Gemini. They are not one case.

| Step | User action | Frontend request | Python routing | CrewAI / Gemini | Stored result | Displayed outcome |
|---|---|---|---|---|---|---|
| 1 | Create intake for Jordan Lee, role blank | `POST /events` as Alex Rivera, `hr_coordinator`, with the held-intake body | Intake rules. No model gate. | Not called | Hire H-1010, activation `held`, no tasks | Held, version none, zero tasks. “The role was not on the intake.” Screenshot 01. |
| 2 | Send a reply as Sam Ortiz: `We hired a CSR` | `POST /events`, `event_type: reply`, then poll `GET /hires/H-1010` | The plan is held, so the role reply is applied by rule | Not called | Activation `proposed`, four tasks, reply decision `proposed_plan` | Decisions: proposed and not active. Screenshot 02. |
| 3 | Record HR decision. A human must approve. Alex Rivera confirms Approve held plan in the dialog. | `POST /events`, `event_type: hr_decision`, `decision_type: approve_held_plan`, plan version 1 | Only Alex and `hr_coordinator`. The version must match. Activation must be `proposed`. | Not called | Activation `active`, plan version 2, decision `approve_held_plan`, rationale “Role is CSR.” Tasks stay incomplete. | “HR approved the held plan. The plan is active.” Attention still lists policy, equipment, and the first-day meeting. Screenshot 03. |
| 4 | Create intake for Riley Chen, complete role | `POST /events` as Alex Rivera with the complete body | Intake rules. The role and Austin office are supported. | Not called | Hire H-1011, activation `active`, plan version 1, four tasks | Active, version 1, four tasks. Screenshot 05. |
| 5 | Ask question as Riley Chen: “Can IT provide an approved loaner by the start date?” | `POST /events`, `event_type: policy_question`, then poll | The detector matches a recorded P2 pattern, so a model draft is allowed. The excerpt must be a contiguous copy of a retrieved passage. | `policy_answerer`, one sequential task, Gemini `gemini-3.5-flash-lite`, temperature 0 | Event `07d17a89-f663-4ceb-9bab-1a41cb73d739` complete. Equipment stays unconfirmed. | Policy tab shows the passage and Citation P2. Screenshot 06. |
| 6 | Send a reply as Taylor Brooks: “The laptop slips to March 19. A spare might be free on start day.” | `POST /events`, `event_type: reply`, then poll | The plan is active and Taylor is the equipment owner, so a model draft is allowed. The excerpt must be a contiguous copy of the message. | `reply_reader`, one sequential task, same Gemini settings | Event `dc1822c6-4948-4035-95c5-1372b1642b75` complete. Equipment unconfirmed. One follow-up cites P2. Plan version stays 1. | Activity shows the reply and that one follow-up. Screenshot 07. |

A click on an example fills the message or question and does not send it. New event fills a new id and does not send it.

## 3. Processing pattern

Every accepted `POST /events` returns HTTP 202 with `status: processing`. That acknowledgment means the event id was accepted. It does not mean the case has finished. The hire read is the result.

Intake finishes inside the request, then returns 202. The page reads `GET /hires/<hire_id>` once.

HR, start date, deadline, task update, a held-hire role reply, a non-owner equipment reply, and a policy question that does not call the model also finish inside the request, then return 202. The page still polls, and the event row is already `complete` when that poll starts.

An equipment reply from Taylor on a plan that is not held, and a policy question whose detector sets `call_model`, return 202 and then run CrewAI on a daemon thread. The page polls because the draft is not in the acknowledgment. Each model task is sequential, with delegation off, agent memory off, `temperature` 0, a 45-second provider timeout, `max_retries` 0, `max_retry_limit` 0, and `max_iter` 2. Those are the settings in `reply_crew.py` and `policy_crew.py`. No measured provider latency is recorded here. The recorded live replies finished before the page showed its waiting sentence.

The page polls `GET /hires/<id>` every 500 milliseconds. The poll loop stops after 60 seconds. Each hire read uses a 10-second request limit, and the original POST uses a 60-second request limit. These are the constants in `workspace/src/main.js`. Stored state `in_flight` is shown as `processing`. Stored state `committed` is shown as `complete`. Any other stored state is shown as `failed`.

While the page is processing, the submit control, example buttons, and New event are unavailable. The status line reads “Processing event.” The detail line says the case on screen is the last verified case. On success the status line reads “Event complete.” A repeated completed event with the same contents returns 202 and adds no work. The status line then reads “Already processed. No additional work added.”

This shape fits the application because the case file is the only writer of facts. The page can acknowledge every route the same way, wait for a model without holding the POST open for the draft, and refuse to treat a missing response as a new fact. A person retries by sending the same event id and the same contents. The page does not fire a second provider call on its own.

## 4. API contract

The page uses the same origin. Locally that is `http://127.0.0.1:8000/`. `GET /`, `GET /styles.css`, and `GET /src/main.js` serve the workspace. CORS allows any origin. Allowed headers are `Content-Type` and `X-Demo-Token`.

| Method and path | Success | Other results |
|---|---|---|
| `GET /health` | `200` `{"status":"ok","demo_lock":false}` when the database answers. The server adds `demo_lock` from whether `DEMO_ACCESS_TOKEN` is set. | `503` `{"status":"unavailable"}` when the database ping fails. |
| `GET /hires/<hire_id>` | `200` and the case below, plus `case_summary`. | `404` `{"message":"No hire is stored for this id.","hire_id":"..."}` |
| `POST /events` | `202` `{"event_id","hire_id","status":"processing"}` | `400`, `401`, `404`, `409`, `429`, or `500`, as in section 5. |
| Any other path |  | `404` `{"message":"That address is not part of this increment."}` |

With `DEMO_ACCESS_TOKEN` unset, posts do not require a token and `demo_lock` is false. With it set, a post without a matching `X-Demo-Token` is `401` and writes nothing. The token value is not in the repository and is not returned by health.

Hire ids are server-assigned from `H-1001` upward. The public event states are `processing`, `complete`, and `failed`.

A hire read includes `hire_id`, `employee_name`, `start_date`, `role`, `location`, `manager_name`, `plan_version`, `readiness`, `readiness_reasons`, `activation`, `tasks`, `messages`, `versions`, `decisions`, `events`, `failure`, and `case_summary`. `activation` is `held`, `proposed`, or `active`. Each event object is `event_id`, `event_type`, `state`, and `failure`. `case_summary` is computed for the response. It is not a stored column. Activity still renders the stored messages.

Simulator identities, both fields required:

| Person | `actor_id` | `actor_role` |
|---|---|---|
| Alex Rivera | `actor-alex-rivera` | `hr_coordinator` |
| Taylor Brooks | `actor-taylor-brooks` | `it_fulfiller` |
| Sam Ortiz | `actor-sam-ortiz` | `hiring_manager` |
| Morgan Hale | `actor-morgan-hale` | `hiring_manager` |
| Jordan Lee | `actor-jordan-lee` | `new_hire` |
| Riley Chen | `actor-riley-chen` | `new_hire` |

Create intake on the page always sends Alex Rivera, even if another person is selected. The other six actions send the selected person. The message text does not choose the sender.

The same event id is compared by a contents key of `event_type`, `actor_id`, `actor_role`, `occurred_at`, `body`, and, for every action except intake, `hire_id`. Same id and same key after commit: `202` and no further work. Same id while that event is `in_flight`: `409` `conflict`, “This event is already running.” A different event id while any event is `in_flight`: `409` `conflict`, naming both ids. Same id and a different key once the event is no longer in flight: `400` `event_mismatch`. A failed event with the same key is run again. That replay can call the model again. It does not apply the new body until the contents match the stored key.

Representative request and acknowledgment. These show the field shapes. They are not a new captured transcript.

```json
{
  "event_id": "example-intake",
  "event_type": "intake",
  "actor_id": "actor-alex-rivera",
  "actor_role": "hr_coordinator",
  "occurred_at": "2026-03-13T09:00:00-05:00",
  "body": {
    "employee_name": "Jordan Lee",
    "start_date": "2026-03-02",
    "role": "",
    "office": "Austin",
    "manager_name": "Sam Ortiz"
  }
}
```

```json
{"event_id": "example-intake", "hire_id": "H-1001", "status": "processing"}
```

The recorded held intake was H-1010, not this example id. `office` is stored as `location`.

```json
{
  "event_id": "example-reply",
  "event_type": "reply",
  "hire_id": "H-1010",
  "actor_id": "actor-sam-ortiz",
  "actor_role": "hiring_manager",
  "occurred_at": "2026-03-13T15:00:00-05:00",
  "body": "We hired a CSR"
}
```

```json
{
  "event_id": "example-hr",
  "event_type": "hr_decision",
  "hire_id": "H-1010",
  "actor_id": "actor-alex-rivera",
  "actor_role": "hr_coordinator",
  "occurred_at": "2026-03-13T15:00:00-05:00",
  "body": {
    "decision_type": "approve_held_plan",
    "rationale": "Role is CSR.",
    "plan_version": 1
  }
}
```

A policy question uses the same envelope with `event_type: policy_question` and a string `body`. A start-date change uses a `YYYY-MM-DD` string. A deadline uses a string note, which may be empty. A task update uses `{"task":"policy_acknowledgment","action":"acknowledge"}`. Allowed pairs are policy acknowledgment `acknowledge`; first-day meeting `confirm` or `held`; training `assigned` or `complete`.

```json
{
  "code": "event_mismatch",
  "message": "This event id was already used with different contents. The new contents were not applied.",
  "event_id": "example-reply",
  "hire_id": "H-1010"
}
```

The page displays that as one line and adds “No second hire was created.”

## 5. Errors and timeouts

A provider failure is a finished event. The server has stored `failed` and a failure message, and the last committed case is still the verified case. An unknown network outcome means the page did not receive a finished event. The page does not mark that event failed.

| Trigger | Backend outcome | Displayed message | Verified facts | Recovery |
|---|---|---|---|---|
| Body is not JSON, is larger than 65536 bytes, or fails the route’s field checks | `400` `unreadable_input`. Nothing new is committed. | The route’s message, then “No new verified fact was written.” Intake: “The intake could not be read, so no plan was written.” | The last hire read stays on screen. | Correct the form. Use New event before a different submission. |
| `hire_id` is not stored | `404`. No write. | “No hire is stored for this id.” | Unchanged. | Create an intake or paste the current hire id. |
| `actor_id` and `actor_role` are not one roster pair | `400` `unsupported`. | “This sender is not a configured simulator identity.” | Unchanged. | Choose one of the six people. |
| HR or start date from anyone but Alex Rivera, `hr_coordinator` | `400` `unsupported` before the event is reserved. | “Only the HR coordinator can record this decision.” or “Only the HR coordinator can change the start date.” | Unchanged. | Select Alex Rivera. |
| HR `plan_version` differs from the case, or Approve held plan when activation is not `proposed` | `400` `unsupported` before the event is reserved. | “The plan version does not match the current case.” or “There is no proposed plan to approve.” | Unchanged. | Read the current version and activation, then use New event. |
| Same event id, different contents, event no longer in flight | `400` `event_mismatch`. The new body is not applied. | “event_mismatch: This event id was already used with different contents. The new contents were not applied. No second hire was created.” | The committed case stays. Screenshot 04. | New event, then submit the new contents. |
| This event is in flight, or any other event is in flight | `409` `conflict`. The new submission does not start. | “conflict: One event is already running. This submission was not started.” The page adds the refused event id when the body includes one. | The running event continues. The on-screen case stays the last read. | Wait until the status leaves Processing event. Retry original event sends the same id and contents. |
| Equipment draft is empty, off-message, or otherwise rejected | Event stored `failed` with `model_failure`. | “model_failure: The equipment reply could not be read. No new verified fact was written.” The sentence is shown once. | No new equipment fact. The previous case remains. | Retry original event runs that same failed event again. |
| Policy draft has no citation, an unknown citation, or an excerpt that is not in the retrieved passage | Event stored `failed` with `model_failure`. | “model_failure: The policy question could not be read. No policy conclusion was written.” | No policy conclusion is published. | Retry original event runs that same failed event again. |
| POST or a poll throws, the acknowledgment does not echo the ids, or 60 seconds pass with the event still `processing` | No failure row is written by the page. | “The page lost contact with the API. The outcome of this event is unknown. It is not recorded as a failed event. Retry sends the same event again.” or “The page stopped waiting after 60 seconds…” with the same unknown-outcome wording. | The last verified hire stays on screen. | Retry original event. If the server already committed it, the retry adds no work. If it is still in flight, the retry receives `conflict`. |
| `DEMO_ACCESS_TOKEN` is set and the header does not match | `401` `demo_lock`. No write. | “demo_lock: This demonstration requires the access token. No case was changed.” | Unchanged. | Enter the token on the page. It stays in the browser session only. |
| Token is set and this hour’s model starts have reached `DEMO_MODEL_CALLS_PER_HOUR` (default 8) | `429` `demo_limit`. The in-flight row is marked failed and the provider is not called. | “demo_limit: The demonstration has reached its model-call limit for this hour. No model call was made.” | No new model fact. | Wait for the next hour, or restart the process, which clears the in-memory count and keeps the database. |
| The router raises while saving | `500`. | “The case could not be saved.” | The request does not return a new hire body. | Retry the same event id after the server is healthy. |

The recorded browser sessions did not produce the 60-second waiting sentence. Both H-1011 model calls finished first. No duration was written down.

## 6. Human approval

A blank role is not a supported Customer Support Representative intake. Jordan Lee’s intake stores activation `held` and no tasks. The plan is not active, and there is nothing for HR to approve yet.

A later role reply from the hiring manager is applied by rule. For Jordan, that person is Sam Ortiz. The sentence `We hired a CSR` stores activation `proposed`, creates the four tasks, and records the reply decision as `proposed_plan`. What happened reads “Proposed plan. It is not active until HR approves it.” The model is not called.

Approve held plan is accepted only from Alex Rivera with `actor_role` `hr_coordinator`, only when `plan_version` equals the current case, and only when activation is `proposed`. The page asks for confirmation in a dialog before it sends. On success the stored decision is `approve_held_plan`, the plan version increases by one, and activation becomes `active`. H-1010 went from version 1 proposed to version 2 active. The reply event stays `proposed_plan` and its message stays “We hired a CSR.” Approval copies the tasks as they are. It does not mark policy, equipment, or the meeting confirmed, because those facts were not in the approval. The attention list still says they are incomplete.

An escalation disposition is a different HR decision. It can be recorded when activation is `proposed` or `active`. It does not activate a held plan.

A complete Riley intake is `active` at version 1 immediately. It does not wait for this approval.

## 7. Logging and verification

What is recorded:

- The case file `onboarding/data/onboarding.sqlite` stores hires, events, tasks, messages, versions, decisions, and equipment state. It is gitignored. `case_summary` is added on the hire read and is not a stored column.
- The server process writes its listen line and the HTTP request lines to standard error. A live model call also writes a provider token-count line. The H-1011 lines name `gemini-3.5-flash-lite`. The key is not printed.
- The page shows the status line, the inline alert, What happened, and the Tasks, Activity, Policy, and Decisions tabs. Screenshots 01–07 are those displays.
- This file’s audit, `submission/ASSIGNMENT.md`, and `project-context/2.build/results.md` are the written checks. The server does not write a separate application log file.

This documentation turn did not rerun any of the checks below.

| Kind | What was recorded | Provider |
|---|---|---|
| Mocked tests | `submission/ASSIGNMENT.md`: 58 tests, 0.882s, OK. Includes held, then proposed, then HR-approved, and the demo-lock check on a temporary database with a throwaway token. `results.md`: D1–D12 from stand-in readers in `onboarding/tests/test_scenarios.py`. That sheet’s combined run was 50 tests, OK. | No Gemini call. |
| API checks | Riley intake `api-riley-1` returned H-1003, four tasks, plan version 1. Uncertain reply `api-reply-1` as Taylor finished complete, equipment unconfirmed, one follow-up, and the same payload again left that count at one. Hire H-1008’s policy call published the exact P2 passage. A temporary server with a throwaway token returned `demo_lock: true`, `401` without the token, and `202` for an intake with the token. | The H-1003 reply and the H-1008 question used the live reader. The demo-lock check used a stand-in key and did not call Gemini. |
| Browser checks | H-1010 held, proposed, approved, and one `event_mismatch`, with no model call. H-1011 complete intake. Screenshots 01–05. Earlier hires H-1004, H-1005, H-1007, and H-1009 remain in the audit and were not opened again. | No Gemini call on the H-1010 approval. |
| Live Gemini | H-1011 policy event `07d17a89-f663-4ceb-9bab-1a41cb73d739` and equipment event `dc1822c6-4948-4035-95c5-1372b1642b75`. Screenshots 06 and 07. An earlier completed equipment reply on H-1007, event `43bbce54-5835-4bf6-9e09-dbd588019bc8`, also named `gemini-3.5-flash-lite`. | Live Gemini. |

## 8. Limitations and decisions

Resolved in the running application:

- The pattern is a workflow. Python chooses the route, checks the sender and the event id, and writes the case. The model does not choose the next role, tool, or follow-up.
- All seven actions and all six people are connected. The visible submit labels are Create intake, Send reply, Ask question, Update start date, Check deadlines, Record decision, and Record status.
- What happened follows `case_summary` for the current activation. Activity keeps each event’s own text.
- An equipment excerpt must be a contiguous copy of the original message. A policy excerpt must be a contiguous copy of a retrieved passage. The equipment message is placed last, between markers, so the model is not asked to copy the instructions.
- The two model tasks use one provider attempt: `max_retries` 0 and `max_retry_limit` 0. `max_iter` stays 2.
- The local server listens on `127.0.0.1:8000` unless `ONBOARDING_HOST` and `PORT` are set. The public host was left off. `DEMO_ACCESS_TOKEN` is optional and is unset for the local demonstration.
- The sender menu is a simulator. It is not login. Reset form clears the form only.

Still open:

- Policy answers are limited to the recorded detector patterns. Other wording may go to manual review. Topics outside the pack go to HR. Deleting the word “not” can still match the late-acknowledgment pattern. `results.md` does not treat that as a pass for arbitrary paraphrases.
- The reply examples are tested sentences, not every sentence the reader can accept.
- The SAD still asks how the retry layers line up, and it still leaves a provider-wide circuit breaker open. The running model tasks do not add a stacked provider retry or a circuit breaker.
- Dollar and token ceilings are unset.
- The 60-second waiting sentence has not been produced in a recorded browser session.
- A shared host, if it is turned on later, has one case file. A person who has the demo token can append events. The hourly model count lives in the process and clears on restart. There is no public reset address.
- The scenario menu still disables “Jordan Lee, proposed plan” and “Stub failure.” Those results are reached by a held intake plus later events.
- If Hire id still contains an older case, the next reply or question is sent to that case.
- The scenario clock used for the demonstration is 2026-03-13, so some due dates are already overdue.
- The prepared-example crew in `onboarding/crew.py` still sets `max_retry_limit` 2. The page does not run that crew. The reply and policy crews set the limit to 0.

## 9. Sources

- `onboarding/server.py`, `onboarding/router.py`, `onboarding/store.py`, `onboarding/plan.py`, `onboarding/rules.py`, `onboarding/case_summary.py`, `onboarding/simulator.py`, `onboarding/demo_guard.py`, `onboarding/reply_crew.py`, `onboarding/policy_crew.py`, `onboarding/equipment.py`, and `onboarding/policy.py`.
- `workspace/index.html` and `workspace/src/main.js`.
- `submission/ASSIGNMENT.md` and `submission/screenshots/01` through `07`.
- `submission/HOSTING.md` for the recorded demo-lock HTTP check. No secret values.
- `project-context/2.build/results.md` for the D1–D12 stand-in score.
- `project-context/2.build/frontend.md` and `project-context/2.build/backend.md` as build records. The behavior above is taken from the code where those records are older.
- `project-context/2.build/sad.md` Pattern Decision: workflow. Two model tasks, no tools, delegation off.
- `project-context/1.define/prd.md` Appendix A for Riley Chen and Jordan Lee.
- `aamad.config.yml`: `project.mode` greenfield, `runtime.target` crewai. `AAMAD_TARGET_RUNTIME` was unset.

## 10. Assumptions

- The scored assignment is the three requirements in section 1.
- The local browser session recorded in `submission/ASSIGNMENT.md` is the working demonstration. H-1010 and H-1011 remain in the local case file.
- A professor can read sections 1–8 without reading the audit. The audit is history, including sentences from earlier in the day that no longer describe the page.
- No assignment-specific integration template was supplied. These numbered sections are the requested report.

## 11. Open Questions

1. Whether to create the Fly.io app and publish a demo URL. The operator left the host off on 2026-11-26.
2. Policy wording outside the recorded detector table remains manual review or an HR referral.
3. How the SAD’s retry-layer note and provider-wide circuit breaker should be closed. The running model tasks use one provider attempt and no circuit breaker.
4. The 60-second polling sentence was not produced in the recorded browser sessions.

## 12. Audit


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

- **Timestamp:** 2026-11-26T22:53:00Z
- **Persona ID:** integration-eng
- **Action:** log-integration
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor for this documentation turn. Temperature and max_tokens were not set. No product model was called.
- **Prompt trace:** Omitted. This entry records the current message flow and the evidence already written in `submission/ASSIGNMENT.md`, `submission/HOSTING.md`, and `project-context/2.build/results.md`. It does not embed secrets.
- **Tool use:** Read the page, the router, the server routes, and the recorded submission checklist. Did not change application code, did not reset cases, and did not run tests or the browser.
- **Outcome:** The current sections name all seven connected actions, the same-origin hire read, and the demo lock. Verification separates the 58 mocked tests, the recorded HTTP checks, and the H-1010 / H-1011 browser screenshots. Earlier audit entries stay as history.
- **Doc sync:** not run. This turn edits only `integration.md`.

- **Timestamp:** 2026-11-26T23:00:00Z
- **Persona ID:** integration-eng
- **Action:** log-integration
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor for this documentation turn. Temperature and max_tokens were not set. No product model was called.
- **Prompt trace:** Omitted. This entry records the submission report. It does not embed secrets or a model prompt.
- **Tool use:** Read the server, router, store, plan, crews, page, PRD Appendix A, SAD Pattern Decision, frontend.md, backend.md, results.md, and `submission/ASSIGNMENT.md`. Did not change application code, PRD, SAD, or UX specifications. Did not reset cases, print a key, or rerun tests.
- **Outcome:** Sections 1–11 are the current integration report: connected flows, the H-1010 and H-1011 step table, acknowledgment and polling, the API contract, error handling, human approval, and the recorded checks. Earlier audit entries stay as history.
- **Doc sync:** not run. This turn edits only `integration.md`.
