# Backend

## Backend workflow overview

This is the Sprint 3 crew for the same prepared examples the onboarding page already shows. One command runs it locally. The page is not called, and the page does not call this crew.

The scenario is the five lines already written in `project-context/2.build/frontend.md`:

1. **Who starts.** The operator opens the onboarding page and starts a run. One person plays the simulated HR coordinator, hiring manager, IT fulfiller, and new hire. The page does not ask a live crew to begin.
2. **What they give.** They choose one prepared example and press Run. The examples are Riley Chen’s complete supported hire, Jordan Lee’s hire with the role missing, Jordan Lee’s plan waiting for HR approval, or a practice failure that writes nothing.
3. **What happens.** The page marks the run as underway, then returns the fixed sample for that example. Reset clears the form and the result and returns the page to its start. After the practice failure, Retry sends that same failed example again, even if a different example was chosen afterward.
4. **How they know.** The banner reads Crew: idle, Crew: running, or Crew: done. A dot is gray, blue, or green for those three, and red when an error is showing. The banner also says that no crew process is running. The last-updated time changes when a result appears, when an error appears, or when Reset is used. An error is written in words, and Retry is shown.
5. **What they get.** A successful example shows a verified case: what happened, whether the plan is active, held, or only proposed, whether it needs attention, who should act next, and the tasks. Riley’s case is an active plan with four tasks and still needs attention. Jordan’s missing-role case has no tasks and asks the manager to confirm the role. Jordan’s other case is a proposed plan that is not active until HR approval. The practice failure adds no case and says no new verified fact was written.

Lines 3 and 4 stay on the page. This crew prints line 5 from fixed mock data: Riley’s active plan, Jordan’s held intake, Jordan’s proposed plan, and the practice failure.

**Status:** Sprint 3 build spec approved and implemented. The `onboarding/` package, `.env.example`, `requirements.txt`, and the README kickoff command exist. Section 5 adds the intake API the operator approved on 2026-11-26. The supported intake page is connected. Section 6 adds the equipment reply API. The page sends a reply for the displayed hire. Section 7 adds the bounded policy-question route. HR approval, start-date change, and deadline use `POST /events` and call no model. The Gemini kickoff command is still the prepared-example crew, not this API.  
**Product:** Automated Employee Onboarding Workflow  
**Persona:** backend-eng  
**Action:** document-backend  
**Project mode:** greenfield (`aamad.config.yml`)  
**Runtime:** `crewai`, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` is unset.

B1–B7 are Sprint 3 implementation exceptions. They are not edits to the PRD, the SAD, or `ux.md`. Those contracts stay in force for the MVP. A later increment builds the case router, the two SAD model roles, the rule gate, and the section 4 API. Integration wires the page after that.

No genuine architectural change is required. The Pattern Decision stays a workflow. Python still owns the sequence. `allow_delegation` stays false. The model does not choose the next role.

## 1. Sprint 3 exceptions

The operator asked for two agents, two YAML tasks, a sequential crew unless the SAD’s gates require Flow, one tool with mock data allowed, and one kickoff command in the README. The page stays on its stub.

| # | Sprint 3 crew | Contract that stays in force | Exception, this sprint only |
|---|---|---|---|
| B1 | One sequential kickoff runs both YAML tasks. The second task receives the first task’s output. | SAD section 2: the two model tasks are alternative routes. Python selects one. Context is passed by the router, not by `Task.context` between them. | This demo chains the two tasks once so one command can show both. The router is not built. |
| B2 | The YAML roles are `fixture_reader` and `case_reporter`. | SAD runtime roles are `reply_reader` and `policy_answerer`. | Those two roles are not implemented here. These names are the demonstration pair. |
| B3 | `fixture_reader` has one read-only tool, `read_prepared_cases`. The tool returns the four prepared payloads. | SAD Pattern Decision: the two model tasks have no tools. CR-004: no write tool and no network tool. | The tool reads a local dict copied from the page stub. It does not write, use the network, or read live state. CR-004’s write and network bans still hold. |
| B4 | There is no HTTP API, no event submission, and no hire read. | SAD section 4. | `workspace/src/stub.js` remains the page’s data. Integration binds the real client later. |
| B5 | The README gains one kickoff command. | The README still describes Define status and does not launch a crew. | The command runs this package only. It does not open the page. |
| B6 | CR-002 and CR-003 are not executed. Process mode is sequential. | Those controls are application gates after a draft. The SAD does not select CrewAI Flow. | Fixed payloads stand in for the gated result. Nothing is written to a case store. |
| B7 | `max_rpm` stays unset. | The CrewAI adapter asks for a crew-level rate. PRD Open Question 2 has no spend cap. | Same open item as the SAD. This spec does not invent a cap. |

**Aligned with the contracts.** One operator. Synthetic fixtures only. No production HR, IT, identity, or messaging call. No persistent store in the Sprint 3 crew. No second public model route. The page banner can stay “Stubbed status. No crew process is running.” because this command does not start from the page.

Section 5 supersedes B4 for intake only. The Sprint 3 crew command still does not listen on a port. The case file in section 5 is application storage. CrewAI memory stays off.

## 2. Simplified build

### 2.1 Process mode

Sequential. `Process.sequential` in `onboarding/crew.py`.

The SAD’s gates are application checks after a draft (CR-002, CR-003, and the publication check in section 4). They are not CrewAI Flow steps. The recorded CrewAI process is sequential, with `allow_delegation: false`, `memory: false`, and no hierarchical process. This sprint follows that process mode. Flow is not added.

Task order is fixed in code:

1. `load_prepared_cases` (`fixture_reader`)
2. `report_prepared_cases` (`case_reporter`), with context equal to the first task

`kickoff_for_each` is not used. There is one kickoff per command. The four examples travel inside the one tool result. They are not four crews.

Crew limits for this package:

| Control | Value | Why |
|---|---|---|
| `allow_delegation` | `false` | The model does not choose the next role. |
| `memory` | `false` | Reproducible kickoff. No cross-run memory. |
| `max_iter` | `2` on each agent | Inside the adapter ceiling of 12. One tool call, plus one retry inside the task if the first step skips the tool. |
| `max_execution_time` | `60` seconds | Matches the PRD event budget already recorded in the SAD. |
| `max_retry_limit` | `2` | Meets the adapter floor. This package does not add another application retry around `kickoff`. |
| `max_rpm` | unset | B7. No spend cap exists to convert into a rate. |

Temperature and max tokens are not set in code. The provider default applies when a model name is present. The model name is an environment value, not a product choice in this file.

### 2.2 Files to add after approval

| File | Role |
|---|---|
| `onboarding/config/agents.yaml` | `fixture_reader` and `case_reporter` |
| `onboarding/config/tasks.yaml` | `load_prepared_cases` and `report_prepared_cases` |
| `onboarding/crew.py` | Builds the sequential crew and binds the one tool |
| `onboarding/kickoff.py` | `python -m onboarding.kickoff` |
| `onboarding/__init__.py` | Package marker |
| `onboarding/tools/__init__.py` | Package marker |
| `onboarding/tools/read_prepared_cases.py` | The one tool and the mock dict |
| `.env.example` | Variable names only |
| `requirements.txt` | `crewai` only, unpinned until the installed version is recorded at implementation |

Do not add a database, a web framework, or a file under `workspace/`.

### 2.3 Agents

Both agents live in `onboarding/config/agents.yaml`. Tools are named there and bound in `crew.py` before kickoff. A YAML tool name with no Python binding is a failed start: exit 1 and the failure sentence in section 2.7. No provider call in that case.

`fixture_reader`

- **Role:** Prepared-case reader
- **Goal:** Call `read_prepared_cases` once and return that JSON unchanged.
- **Backstory:** You read only the local prepared examples for this demonstration. You do not invent a hire, a task, a date, or a policy.
- **Tools:** `read_prepared_cases` only
- **allow_delegation:** `false`
- **max_iter:** `2`

`case_reporter`

- **Role:** Case reporter
- **Goal:** Turn the prepared JSON into the result text the onboarding page shows for those examples.
- **Backstory:** You copy outcome lines, plan labels, readiness, the next owner, the next action, and task names from the tool result. You leave Riley as Needs attention. You leave the held intake with no tasks. You leave the proposed plan inactive. For the failure payload you report only that no new verified fact was written.
- **Tools:** none
- **allow_delegation:** `false`
- **max_iter:** `2`

Neither agent is `reply_reader` or `policy_answerer`.

### 2.4 Tasks

Both tasks live in `onboarding/config/tasks.yaml`.

`load_prepared_cases`

- **Agent:** `fixture_reader`
- **Description:** Include the five scenario lines from the overview, then instruct the agent to call `read_prepared_cases` once and return its JSON with the keys `riley-complete`, `jordan-blank`, `jordan-proposed`, and `stub-failure`. No fifth example.
- **Expected output:** The tool JSON, keys unchanged.

`report_prepared_cases`

- **Agent:** `case_reporter`
- **Context:** `load_prepared_cases`
- **Description:** Using only that JSON, write the stdout contract in section 2.7. Do not recompute due dates. Do not move a task from Riley onto Jordan. Do not describe a case for `stub-failure`.
- **Expected output:** The four blocks in section 2.7, in that order.

### 2.5 Tool

One tool: `read_prepared_cases`.

- No parameters. The model cannot ask it for a different hire or a live system.
- Returns one JSON object whose keys are the four scenario ids in `workspace/src/stub.js`.
- Values are copied into `onboarding/tools/read_prepared_cases.py` at implementation. The Python package does not import `workspace/`. The page and the crew share the same prepared text because the values are copied, and they stay separate processes.
- `stub-failure` is `{ "status": "error", "message": "No new verified fact was written.", "case": null }`.
- The other three values use the case fields the page already renders: `hire_id`, `plan_label`, `outcome_line`, `readiness_label`, `attention_reasons`, `next_owner`, `next_action`, `messages`, `failure`, and `tasks` (name, owner, due, execution, readiness, evidence).

Copy these outcome lines with the cases:

| Scenario id | Outcome line the report must keep |
|---|---|
| `riley-complete` | Active plan. Four tasks created. No approval hold. |
| `jordan-blank` | One request went to Sam Ortiz. No tasks were created. |
| `jordan-proposed` | Proposed plan. Not active until HR approval. |
| `stub-failure` | No new verified fact was written. |

Riley’s tasks, in order: Policy acknowledgment (Riley Chen, new hire, 2026-03-12), Equipment readiness (Taylor Brooks, IT fulfiller, 2026-03-16), First-day meeting (Morgan Hale, hiring manager, 2026-03-16), Customer-support tools orientation (Morgan Hale, hiring manager, 2026-03-23). Hire id H-002. Readiness label Needs attention. Next owner Riley Chen. Next action: Record the policy acknowledgment.

Jordan held: hire id H-001, `plan_label` `none`, zero tasks, next owner Sam Ortiz, next action Confirm the role, one message “Ask Sam to confirm the role.”

Jordan proposed: hire id H-001, `plan_label` `proposed`, the four Appendix A tasks with owners Jordan Lee, Taylor Brooks, Sam Ortiz, and Sam Ortiz, and dues 2026-02-26, 2026-03-02, 2026-03-02, and 2026-03-09. Next owner Alex Rivera. Next action: Await HR approval.

The tool sets a process-local flag `tool_called` when it runs. `kickoff.py` reads that flag after kickoff.

### 2.6 Kickoff command

After approval, add this subsection to `README.md`. It is the only run command this sprint adds.

```
## Sprint 3 crew

From the repository root, with `OPENAI_API_KEY` and `OPENAI_MODEL_NAME` set in the environment:

python -m onboarding.kickoff
```

The names, with empty values, go in `.env.example`. The README and the example file do not contain a key or a chosen model. `kickoff.py` refuses to construct the crew when either variable is missing or empty. It then prints the failure sentence and exits 1. It does not print the key.

The command takes no arguments. It does not start a server and it does not open `workspace/index.html`.

### 2.7 Stdout contract

On a run where the tool was called and the report contains every required sentence, exit 0 and print four blocks, in this order, as plain text:

1. **Riley Chen, complete supported intake.** The outcome line, hire id H-002, the word Active, the readiness label Needs attention, next owner Riley Chen, and the four task names with the owners and dues in section 2.5.
2. **Jordan Lee, held intake.** The outcome line, hire id H-001, zero tasks, next owner Sam Ortiz, next action Confirm the role.
3. **Jordan Lee, proposed plan.** The outcome line, hire id H-001, the word Proposed, the sentence that it is not active until HR approval, next owner Alex Rivera, and the four task names.
4. **Practice failure.** The sentence “No new verified fact was written.” and no task list under that heading.

The readiness label printed for Riley and for both Jordan cases is Needs attention. The report does not label any of these four examples Ready.

When `tool_called` is false, or a required sentence from the table in section 2.5 is missing, exit 1 and append:

```
No new verified fact was written.
```

That appendix is the visible failure. The process does not write a file and does not retry the kickoff.

### 2.8 Checks

These checks are the acceptance list for the implementation turn. They are not run in this spec turn.

| Id | Pass condition |
|---|---|
| S3-KICKOFF-EXISTS | `README.md` contains one `python -m onboarding.kickoff` command and no second crew command. |
| S3-KICKOFF-RILEY | Exit 0 output includes Riley’s outcome line, H-002, Needs attention, and the four Riley task names. |
| S3-KICKOFF-JORDAN-BLANK | The held-intake block includes Jordan’s outcome line and does not list the four task names. |
| S3-KICKOFF-JORDAN-PROPOSED | The proposed block includes “Proposed plan. Not active until HR approval.” |
| S3-KICKOFF-FAILURE | The last block is “No new verified fact was written.” |
| S3-KICKOFF-ISOLATION | Riley’s task names appear in the Riley block only. |
| S3-NO-UI | `workspace/` is byte-for-byte unchanged by the implementation. The kickoff command does not listen on a port. |
| S3-NO-SECRET | `.env.example` and the README contain the variable names and no key value. |

A missing provider key is an expected exit 1, not a failed check, until the operator supplies `OPENAI_API_KEY` and `OPENAI_MODEL_NAME`. S3-KICKOFF-RILEY through S3-KICKOFF-FAILURE run only after those two variables are set.

### 2.9 Deferred

Not built in this sprint:

- `reply_reader`, `policy_answerer`, and the Python router that selects one of them
- CR-002, CR-003, and the rest of the case store
- Submit-event and hire-read for reply, start-date change, policy question, deadline, and HR decision. Intake only is section 5.
- Wiring `startRun` or `getRunStatus` to this crew
- Reset and Retry as crew operations
- D1–D12, P1–P4 retrieval, and a scored model call
- A spend cap and `max_rpm`

### 2.10 After approval

Write the files in section 2.2, add the README subsection in section 2.6, and copy the mock dict from `workspace/src/stub.js`. Do not edit the PRD, the SAD, `ux.md`, or any file under `workspace/`. Then run the checks in section 2.8 that do not need a provider key. Record a live kickoff only if the operator has already put the two environment variables in the shell. Do not invent their values.

After that code change, run `*sync-docs` once. This spec turn does not run it.

## 3. Implementation blockers

None. The operator approved section 4 on 2026-11-20. The files in section 2.2 are written.

| Check | Result |
|---|---|
| Work Ownership, Pattern Decision, Control Register | Present in `project-context/2.build/sad.md`. |
| `project-context/1.define/sad.md` | Absent. This spec uses the SAD under `project-context/2.build/`. |
| `project-context/2.build/setup.md` | Absent. This sprint’s file list is section 2.2. `@project.mgr` has not written setup. |
| Pattern | Workflow, sequential, delegation off. Flow is not used. |
| UI | Unwired. `workspace/` stays the stubbed page. |
| Provider | Key and model name come from the environment at run time. Empty values fail closed. Both were unset in this shell, so the live kickoff checks were not run. |
| Empty environment | `python -m onboarding.kickoff` prints `No new verified fact was written.` and exits 1. An extra argument does the same. |
| Tool binding | `fixture_reader` binds `read_prepared_cases` only. A YAML name outside that binding raises `ToolBindingError` before a provider call. The tool schema has no parameters. |
| Crew object | Sequential process, `memory` false, `max_rpm` unset. Both agents use `max_iter` 2, `max_retry_limit` 2, and `max_execution_time` 60. |
| Page | `workspace/` checksums matched after implementation. |

## 4. Spec gate

**Operator approval of this build spec:** `approved` (operator, 2026-11-20)

Approval of `ux.md` and of the frontend spec is separate. This gate covers the crew in section 2 only. The PRD, the SAD, and `ux.md` are not edited by this spec.

## 5. Intake API increment

The operator approved this slice on 2026-11-26 after integration found no submit-event or hire-read API. It is the smallest backend that can accept one intake and store the case. It does not wrap the prepared-example crew, and it does not call Gemini.

Python selects the path. The only path in this slice is intake. The rule gate writes the case. CrewAI `memory` stays false on the unchanged sample crew. The case file is SQLite owned by the application.

| Method and path | Result |
|---|---|
| `POST /events` | Accepts one intake. Returns the same `event_id`, a server-assigned `hire_id`, and `status: processing`. |
| `GET /hires/<hire_id>` | Returns the stored hire, or a message that no hire is stored for that id. |
| `GET /health` | Returns `{"status": "ok"}` when the process can read the case file. |

The process listens on `127.0.0.1:8000`. Start it with `python -m onboarding.server`. The case file is `onboarding/data/onboarding.sqlite` and is gitignored.

A client-supplied `hire_id` on intake does not choose the case. Issued ids start at `H-1001`, so they do not reuse seeded `H-001` or `H-002`.

| Intake result | What is stored |
|---|---|
| Complete Customer Support Representative record in Austin, including the alias “CSR” | Active plan, four Appendix A tasks, `failure: null`, readiness `needs_attention` |
| Blank role and office Austin | One message asking the named manager to confirm the role. No tasks. |
| Any other non-blank role, or an office other than Austin | A hire with no tasks and an HR-review message |
| Unreadable intake | `unreadable_input`. No hire id is created. |

The same event id and the same recorded contents return the original acknowledgment and add no second plan. Different contents for that id return `event_mismatch`. An id still in flight returns `conflict`. Start-date change, policy question, and deadline are refused before a hire write. That refusal has no error code, because the architecture document has no code for a route this slice does not run. Equipment reply is section 6.

Files added: `onboarding/store.py`, `onboarding/rules.py`, `onboarding/router.py`, `onboarding/server.py`. `.gitignore` ignores `onboarding/data/`. Unchanged: `onboarding/kickoff.py`, `onboarding/crew.py`, both YAML files, `onboarding/tools/read_prepared_cases.py`, and the Gemini settings. `workspace/` now calls the intake API for the supported intake.

Checked against a temporary case file, then once over HTTP on `127.0.0.1:8000`. The Riley request from the approved example returned `H-1001`, not `H-002`. The hire read had the four tasks, policy due `2026-03-12` and overdue, equipment and meeting due `2026-03-16`, training due `2026-03-23`, readiness `needs_attention`, and `failure: null`. A second submit added no tasks. A changed body returned `event_mismatch`. A blank role for Jordan Lee stored no tasks and the message “Ask Sam Ortiz to confirm the role.” An in-flight id returned `conflict`. No provider key was read.

## Sources

- Operator request, 2026-11-20: same scenario as the stubbed frontend, the five lines pasted above, two agents, two YAML tasks, sequential unless the SAD gates require Flow, one tool, mock data allowed, one README kickoff command, UI left unwired, stop after the spec.
- `project-context/2.build/frontend.md`. The five lines and the four prepared examples.
- `workspace/src/stub.js`. Payload fields and outcome lines to copy after approval.
- `project-context/2.build/sad.md`. Work Ownership, Pattern Decision, Control Register, section 2 CrewAI composition, section 4 API. `project-context/1.define/sad.md` is absent.
- `project-context/1.define/prd.md`. Appendix A owners and dues. Open Question 2 on model and spend.
- `.cursor/rules/adapter-crewai.mdc`. YAML agents and tasks, sequential process, delegation off, memory off, `max_iter`, `max_retry_limit`.
- `aamad.config.yml`. `project.mode: greenfield`. `runtime.target: crewai`.
- Operator approval, 2026-11-26: intake-only server, Python router and rule gate, local SQLite case file, Gemini sample crew left unchanged.

## Assumptions

- The five frontend lines are the scenario. One kickoff reports all four examples in line 5, because the operator asked for one command and line 5 names all four results.
- Lines 3 and 4 (banner, Reset, Retry) stay on the page. The crew does not implement them.
- Copying the stub dict into the tool package is the mock. Importing `workspace/` would couple the page to the crew, which this sprint leaves unwired.
- `max_retry_limit: 2` is the adapter floor on the crew object. No second retry loop is wrapped around `kickoff`. The SAD’s open retry-layer question stays open for the real model tasks.
- `AAMAD_TARGET_RUNTIME` was unset in this shell. Config and the adapter default resolve to `crewai`.
- A live provider call is optional for approval. The files and the fail-closed empty-env path are the implementation. A green S3-KICKOFF-RILEY run waits on the operator’s own key and model name.
- System Python is 3.14.10. Installed CrewAI 1.15.44 requires Python `>=3.10,<3.14`, so the project virtualenv `.venv` uses Python 3.12.16. `.venv` is gitignored. `requirements.txt` stays unpinned `crewai`.
- CrewAI 1.15.44 puts `max_retry_limit` on each agent, default 2, and has no crew-level field with that name. Both agents set 2. No second retry loop wraps `kickoff`.
- Constructing a `Crew` creates CrewAI’s kickoff-output database under the library storage path. This package does not write a case file into the repository.
- Section 5 follows the SAD’s proposed local SQLite file. The backend persona text says not to add persistent storage. The operator approved the case file. CrewAI memory stays off, and the sample crew does not open that file.
- SAD section 4 leaves paths and JSON key spelling open. `POST /events`, `GET /hires/<hire_id>`, and `GET /health` are the approved completion of that choice. HTTP status numbers are 202 for the acknowledgment, 200 for a hire read and for health, 400 for `unreadable_input` and `event_mismatch`, 409 for `conflict`, and 404 when the hire id is unknown.
- A repeated, already saved event returns the original acknowledgment with `status: processing`. The architecture document does not define a second acknowledgment status.
- The intake body uses `employee_name`, `start_date`, `role`, `office`, and `manager_name`. The hire read returns the office as `location`.
- Hire ids start at `H-1001`. `H-001` and `H-002` stay the seeded example ids and are not chosen by the client.
- “CSR”, including inside a sentence, is the supported role. Any other non-blank role is the HR-review label in this slice. A blank role outside Austin uses that same label and does not send the manager request.
- Equipment is overdue only after its due date. Policy, meeting, and training are overdue at 5 p.m. Austin time on the due date. The IT owner on a new active plan is Taylor Brooks, the seeded IT fulfiller.
- The server loads the repository-root `.env` at startup and does not replace variables already set. It does not print the key. The sample crew keeps its own configuration.

## 6. Equipment reply increment

The operator authorized this slice on 2026-11-26 from the SAD section 4 equipment reply contract. Python selects `reply_reader` from `onboarding/config/reply_agents.yaml` and `onboarding/config/reply_tasks.yaml`. That crew is separate from the prepared-example crew. It has no tools, delegation off, memory off, and a sequential process. The prepared-example files, the intake rules, and the Gemini variable names are unchanged.

Actor ids use the spelling already sent by the intake page, `actor-alex-rivera`. The same pattern names the other Appendix A people: `actor-taylor-brooks`, `actor-sam-ortiz`, `actor-morgan-hale`, `actor-jordan-lee`, and `actor-riley-chen`. A reply is accepted only when both `actor_id` and `actor_role` match one of those pairs. Equipment evidence changes only for `actor-taylor-brooks` with role `it_fulfiller`.

`POST /events` for a reply that passes those checks returns `202` with `status: processing` before the model returns. `GET /hires/<hire_id>` lists `events`. The client finds its `event_id` and reads `processing`, `complete`, or `failed`. The task list on that document is the current case. A completed reply does not mean that event created the intake tasks.

Retry configuration for this route: the application calls the reader once per accepted attempt, the LLM `max_retries` is 0, and the agent `max_retry_limit` is 0. `max_iter` stays 2 as the SAD ceiling. The adapter’s floor of 2 is not used here, because that setting would add provider retries the equipment contract does not allow. Decision 7 stays open for the prepared-example crew, which still sets `max_retry_limit` 2 and was not changed.

Mocked tests in `onboarding/tests/test_equipment_reply.py` passed, 17 tests, with a stand-in reader. They covered first uncertainty, false certainty, a second uncertainty, contextual denial, “No loaner” without a missed laptop, a valid confirmation with `uncertainty: true`, an estimate that leaves a commitment in place, revocation, an unauthorized sender, a duplicate event, `event_mismatch`, deadline boundaries, an invalid draft, provider failure, event completion, the single-event conflict, intake’s four tasks, and the blank-role intake.

One live call used fictional Riley data and the sentence “The laptop slips to March 19. A spare might be free on start day.” The local `.env` has `GEMINI_API_KEY` and no `GEMINI_MODEL_NAME`, so the call used the kickoff default `gemini/gemini-3.5-flash-lite`, temperature 0. The acknowledgment was `processing`. The hire read then showed that event `complete`, equipment unconfirmed, plan version 1, four tasks, one follow-up, and rule result `follow_up`. `application_calls` was 1. A patch on `crewai.LLM.call` counted 0 because this installed CrewAI build does not send the request through that method. The process printed one token-count notice for `gemini-3.5-flash-lite`. No key was written into this file. This live result is separate from the mocked tests.

Repeat the mocked tests with `.venv/bin/python -m unittest onboarding.tests.test_equipment_reply`. Repeat the live reply only with a local key: start `python -m onboarding.server`, submit Riley’s intake, then submit one reply as `actor-taylor-brooks` / `it_fulfiller` for that hire id, and read `events` on the hire. Do not print the key.

The page sends a reply for the displayed hire. The hire read includes `events` for intake, reply, and policy question. Policy questions are section 7.

## 7. Policy question increment

The operator authorized this slice on 2026-11-26 from the SAD section 4 question detector and publication contract. Python classifies the question with `onboarding/policy_pack.py`. That table is the only matcher. It does not answer arbitrary paraphrases, and it does not close Open Questions, “Policy paraphrase scope,” in the SAD. Retrieval terms only choose candidate passages. `policy_answerer` is a separate tool-free sequential task in `onboarding/config/policy_agents.yaml` and `onboarding/config/policy_tasks.yaml`. Delegation and agent memory stay off. The Gemini settings match the reply reader: temperature 0, timeout 45, `max_retries` 0, `max_retry_limit` 0, `max_iter` 2, and one application call. The prepared-example crew was not changed.

A published answer is the exact P1–P4 passage. A mixed out-of-pack question is stored as a completed policy event with reason “outside the pack” and no passage. That record is not `approve_held_plan` or `escalation_disposition`. `covered: false`, an irrelevant citation, partial coverage, an ambiguous question, and an equipment-changing instruction are manual review. Invalid grounding, a citation outside the retrieved set, and an empty excerpt are `model_failure`. A proposal that says a device is reserved for this hire, that equipment readiness is confirmed, or that a task is complete is manual review and publishes nothing. Partial coverage still calls the model when a candidate exists, then publishes nothing. None of these outcomes change equipment evidence, task completion, readiness, or `plan_version`.

HR approval, start-date change, and deadline follow the resolved event schemas in the SAD. A blank role stays held. The designated manager’s supported reply creates a proposed plan. Alex Rivera’s `approve_held_plan` activates it and increments the plan version. A start-date change recalculates unfinished dates, reconfirms an unheld meeting, and blocks a commitment that misses the new start. A reached follow-up deadline escalates that subject once. No page or API marks a task complete.

Mocked tests in `onboarding/tests/test_policy_question.py` passed, 14 tests, with a stand-in answerer. They covered the recorded detector examples, an exact P2 answer, a mixed remote-work referral, `covered: false`, an irrelevant citation, partial coverage, an equipment instruction, invalid grounding, prompt injection, a duplicate event, changed contents under the same event id, provider failure, and unchanged case facts. The same run rechecked a reply after a policy question. `onboarding/tests/test_equipment_reply.py` passed, 19 tests.

One live call used fictional Riley data, hire `H-1008`, event `live-policy-q-1`, and the question “Can IT provide an approved loaner by the start date?” The server used the repository `.env` and the default `gemini/gemini-3.5-flash-lite`. The event finished `complete`, rule `published`, route `policy_answerer`, with the exact P2 passage, plan version 1, four tasks, and readiness `needs_attention`. The process printed one token-count notice for `gemini-3.5-flash-lite`. No key was written into this file. This live result is separate from the mocked tests. A browser submission of “Can I work remotely?” on the same hire showed “Outside the pack. Routed to HR. No policy answer was published.” and left the four tasks in place.

Repeat the mocked tests with `.venv/bin/python -m unittest onboarding.tests.test_policy_question onboarding.tests.test_equipment_reply`. Repeat the live question from the repository root with `.venv/bin/python -m onboarding.server`, then submit Riley’s intake and one policy question as `actor-riley-chen` / `new_hire`. Read the hire and compare a `policy_answer` body with Appendix A P2. Do not print the key.

## Open Questions

1. Which provider model should `OPENAI_MODEL_NAME` use, and what spend cap sets `max_rpm`? PRD Open Question 2. This spec does not choose either.
2. `project-context/2.build/setup.md` is still absent. This sprint does not ask `@project.mgr` to write it before the crew files.
3. Who may submit an intake, and how the server binds the role selector, are still open. This slice checks that `actor_role` is one of the four simulator roles. It does not compare that role with a saved selector.
4. Policy question is section 7. Start-date change and deadline are implemented. A disallowed sender or state returns `unsupported` before the event is reserved.
5. An unknown hire read has no architecture error code. The response is HTTP 404 and a message.
6. The README kickoff section still names `OPENAI_API_KEY` and `OPENAI_MODEL_NAME`. `onboarding/kickoff.py` and `.env.example` use `GEMINI_API_KEY` and `GEMINI_MODEL_NAME`. Section 5 did not change that command.
7. An HR decision is `event_type` `hr_decision` on `POST /events`. A policy referral is not that call. The bounded detector does not close the SAD paraphrase-scope question. A task update records policy acknowledgment, meeting confirmation, and training status for the authorized sender.

## Audit

- **Timestamp:** 2026-11-20T20:50:00Z
- **Persona ID:** backend-eng
- **Action:** document-backend
- **Resolved runtime:** `crewai`, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset. Warning: the environment variable was not set.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set by this persona. No application model call was made. The crew model is unset on purpose.
- **Prompt trace:** Omitted. This entry records a build spec from the frontend journey, the stub payloads, the SAD, and the CrewAI adapter. It does not call the product model and it does not embed secrets.
- **Tool use:** Read the backend persona, `aamad.config.yml`, `project-context/2.build/sad.md`, `project-context/2.build/frontend.md`, `workspace/src/stub.js`, `workspace/src/main.js`, the PRD Appendix A, and the CrewAI adapter rule. Confirmed `AAMAD_TARGET_RUNTIME` unset, `project-context/1.define/sad.md` absent, `setup.md` absent, and `backend.md` absent before this write.
- **Outcome:** Sprint 3 backend build spec written. Approval left `pending`. No application source, no README edit, no UI change. PRD, SAD, and `ux.md` were not edited.

- **Timestamp:** 2026-11-20T23:55:00Z
- **Persona ID:** backend-eng
- **Action:** develop-be
- **Resolved runtime:** `crewai`, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset. Warning: the environment variable was not set.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor for this implementation turn. Temperature and max_tokens were not set. The crew `llm` is `OPENAI_MODEL_NAME` at run time. That variable was unset, so no product model was called. Crew temperature and max tokens are not set in code.
- **Installed runtime:** `crewai` 1.15.44 on Python 3.12.16 in `.venv`.
- **Prompt trace:** Omitted. Kickoff was not executed with a provider key, and this package does not write a trace file.
- **Tool use:** Wrote the section 2.2 files and the README subsection. Installed CrewAI into `.venv`. Ran the empty-environment command, the extra-argument command, the tool-binding check, and crew construction without `kickoff`. Compared `workspace/` checksums before and after.
- **Outcome:** Spec gate set to `approved`. Sequential crew implemented. Page left unwired. PRD, SAD, and `ux.md` were not edited. Live checks S3-KICKOFF-RILEY through S3-KICKOFF-FAILURE were not run because `OPENAI_API_KEY` and `OPENAI_MODEL_NAME` were unset.

- **Timestamp:** 2026-11-21T00:05:00Z
- **Persona ID:** backend-eng
- **Action:** sync-docs
- **Resolved runtime:** `crewai`, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. This entry records approved README sentence replacements. It does not call the product model.
- **Outcome:** Operator approved all descriptive updates. Three README sentences now name the Sprint 3 crew. Spec drift in the SAD was left unchanged: the sprint crew has one read-only mock tool and chains `fixture_reader` then `case_reporter`, while the SAD still names `reply_reader` and `policy_answerer` with no tools and alternative routes. That difference is the approved B1–B3 exception. `@system.arch` owns any SAD revision.

- **Timestamp:** 2026-11-26T15:58:59Z
- **Persona ID:** backend-eng
- **Action:** implement-endpoint
- **Resolved runtime:** `crewai`, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset. Warning: the environment variable was not set.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor for this implementation turn. Temperature and max_tokens were not set. No product model was called. The intake server does not read the Gemini settings.
- **Prompt trace:** Omitted. This entry records the approved intake slice. It does not call the product model and it does not embed secrets.
- **Tool use:** Added `onboarding/store.py`, `onboarding/rules.py`, `onboarding/router.py`, and `onboarding/server.py`, and ignored `onboarding/data/`. Ran the Riley intake, a repeated event, `event_mismatch`, a blank-role intake, an in-flight `conflict`, and `GET /health` plus `POST /events` on `127.0.0.1:8000`. Did not read `.env`. Did not edit the sample crew, the YAML files, or `workspace/`.
- **Outcome:** Intake submit and hire read are available. The page stays on its stub. PRD, SAD, and `ux.md` were not edited.
- **Doc sync:** no updates. No allowlisted descriptive sentence was made false. The page is still unwired. The README kickoff section’s OpenAI names were already stale and were not changed. 2026-11-26T15:58:59Z, backend-eng, sync-docs.

- **Timestamp:** 2026-11-26T16:28:00Z
- **Persona ID:** integration-eng
- **Action:** sync-docs
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. This entry records approved descriptive sentence replacements. It does not call the product model.
- **Outcome:** Operator approved the updates. The intake section now says the supported intake page is connected, and `workspace/` calls that API. The Gemini crew files stay unchanged. PRD and SAD were not edited.

- **Timestamp:** 2026-11-26T17:20:00Z
- **Persona ID:** backend-eng
- **Action:** implement-endpoint
- **Resolved runtime:** `crewai`, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset. Warning: the environment variable was not set.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor for this implementation turn. Temperature and max_tokens were not set. The reply reader uses temperature 0, timeout 45 seconds, `max_retries` 0, and `max_iter` 2. The live call used `gemini/gemini-3.5-flash-lite` because `GEMINI_MODEL_NAME` is unset. The key was not printed.
- **Prompt trace:** Omitted. The mocked tests do not call the provider. The one live call’s raw provider payload is not stored here.
- **Tool use:** Added the reply roster, ledger, reply crew, and `onboarding/tests/test_equipment_reply.py`. Extended the router and the case store. Ran the 17 mocked tests. Ran one live reply. Did not edit the prepared-example crew, `workspace/`, the PRD, or the SAD.
- **Outcome:** Equipment reply is available on the existing event API. The page does not send replies. `policy_answerer` is not built.
- **Doc sync:** no updates. The page, README, and integration note still say the page does not send replies, and the prepared-example crew is still not the API. 2026-11-26T17:20:00Z, backend-eng, sync-docs.

- **Timestamp:** 2026-11-26T17:50:00Z
- **Persona ID:** integration-eng
- **Action:** sync-docs
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. This entry records approved descriptive sentence replacements. It does not call the product model.
- **Outcome:** Operator approved the updates. The status and section 6 now say the page sends a reply for the displayed hire. The prepared-example crew stays separate. PRD, SAD, and `ux.md` were not edited.

- **Timestamp:** 2026-11-26T20:25:00Z
- **Persona ID:** backend-eng
- **Action:** implement-endpoint
- **Resolved runtime:** `crewai`, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset. Warning: the environment variable was not set.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor. Temperature and max_tokens were not set. No product model was called. The key was not printed.
- **Prompt trace:** Omitted. The missing-key test does not call the provider.
- **Tool use:** Added `load_runtime_env` to `onboarding/server.py`, matching `kickoff.py` with `override=False`. Ran 19 equipment-reply tests. Intake without `GEMINI_API_KEY` stored four tasks. A reply with the key absent finished as `model_failure` on that event, with the message kept unverified and the plan unchanged. A preset variable was left in place. A process with the variable unset loaded `.env` and the key was present. `.env` was not edited.
- **Outcome:** The server loads the repository-root `.env` at startup and does not replace variables already set.

- **Timestamp:** 2026-11-26T20:25:00Z
- **Persona ID:** backend-eng
- **Action:** sync-docs
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. This entry records the approved assumption sentence.
- **Outcome:** Operator approved the update. The assumption now says the server loads `.env` without replacing variables already set. PRD, SAD, and `ux.md` were not edited.

- **Timestamp:** 2026-11-26T21:20:00Z
- **Persona ID:** backend-eng
- **Action:** implement-endpoint
- **Resolved runtime:** `crewai`, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset. Warning: the environment variable was not set.
- **Model / temperature / max_tokens:** Grok 4.7 via Cursor for this turn. The policy crew uses temperature 0, timeout 45, and `max_retries` 0. The key was not printed.
- **Prompt trace:** Omitted. The mocked tests do not call the provider. The live call’s prompt is the policy task YAML with the question and P2 passage. It is not copied here.
- **Tool use:** Added the detector, publication gate, `policy_answerer` YAML, and the `policy_question` route. Ran 14 policy tests and 19 equipment tests. One live supported question on hire `H-1008` published the exact P2 passage. `.env` was not edited.
- **Outcome:** Policy questions follow the bounded detector. HR approval, start-date change, and deadline stay unimplemented. The paraphrase-scope question stays open.

- **Timestamp:** 2026-11-26T21:20:00Z
- **Persona ID:** backend-eng
- **Action:** sync-docs
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. The operator approved descriptive updates for this change set before implementation.
- **Outcome:** Status, section 7, and open questions 4 and 7 now describe the policy route. PRD, SAD, and `ux.md` were not edited.
- **Timestamp:** 2026-11-26T21:40:00Z
- **Persona ID:** backend-eng
- **Action:** develop-be
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset.
- **Outcome:** HR decision, start-date change, and deadline follow the SAD schemas. Mocked tests in `onboarding/tests/test_plan.py` passed with the existing policy and equipment suites, 37 tests. No model call in those tests. PRD and `ux.md` were not edited.

- **Timestamp:** 2026-11-26T22:05:00Z
- **Persona ID:** backend-eng
- **Action:** develop-be
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset.
- **Prompt trace:** Omitted. The live draft was checked for excerpt membership only. The key was not printed.
- **Outcome:** The reply task now places the message after the instructions and substitutes the message last. An excerpt must still be a contiguous substring. A recorded failed event is read again; a committed event is not. Mocked suite: 52 tests OK, no provider call. Stored hire H-1006 remains failed.
