# Capstone submission — Automated Employee Onboarding

Prepared 2026-11-26 for three assignment requirements: a working end-to-end capstone, human-in-the-loop functionality, and an external API integration.

Assessment: **ready** for those three requirements.

The repository is the submission. A public demo address is not published. Hosting cost, the access token, and the recording fallback are in `HOSTING.md`.

## Assignment acceptance checklist

| Requirement | Result | What actually happened | Evidence |
|---|---|---|---|
| 1. Working end-to-end capstone | Met | A blank-role intake stays held with zero tasks. A complete Customer Support Representative intake creates four tasks and an active plan. Equipment uncertainty is recorded and still leaves equipment unconfirmed, with one follow-up. | Browser: `screenshots/01-end-to-end-held-intake.png` (H-1010, Held, version none, zero tasks). Browser: `screenshots/05-end-to-end-riley-tasks.png` (H-1011, Active, version 1, four tasks). Browser: `screenshots/07-equipment-reply-follow-up.png` (one P2 follow-up; equipment still unconfirmed). Mocked tests: 58 passed in 0.882s, no provider call. |
| 2. Human-in-the-loop | Met | Sam Ortiz’s role reply proposes a plan. The plan stays inactive until Alex Rivera, the HR coordinator, confirms approval. Approval does not mark missing evidence complete. | Browser, no model call: `screenshots/02-hitl-proposed-not-active.png` (H-1010 proposed). `screenshots/03-hitl-active-after-approval.png` (Active, version 2, decision `approve_held_plan`, rationale “Role is CSR.”). |
| 3. External API integration | Met | A policy question submitted in the browser called Gemini. The page shows the approved passage and citation P2. A later equipment reply on the same hire also called Gemini and committed a grounded result. | Live provider, browser: `screenshots/06-external-api-policy-citation.png` and the citation row in `screenshots/07-equipment-reply-follow-up.png`. Hire H-1011. Policy event `07d17a89-f663-4ceb-9bab-1a41cb73d739`. Equipment event `dc1822c6-4948-4035-95c5-1372b1642b75`. Server log names `gemini-3.5-flash-lite` for both calls. The key is not recorded here. |

Mocked tests and live evidence are different. The 58 automated tests do not call Gemini. The H-1010 approval path does not call a model. The two H-1011 calls above are live Gemini calls made from the browser on 2026-11-26.

## Startup

From the repository root:

```
.venv/bin/python -m onboarding.server
```

Open `http://127.0.0.1:8000/`. The server listens on `127.0.0.1:8000` and loads `GEMINI_API_KEY` and optional `GEMINI_MODEL_NAME` from the repo-root `.env`. Copy names from `.env.example`. Do not commit the key.

Automated checks, with no provider call:

```
.venv/bin/python -m unittest discover -s onboarding/tests -v
```

Expected: `Ran 58 tests` and `OK`.

Do not run `.venv/bin/python -m onboarding.reset_demo` before this demonstration. It deletes the local case file, including H-1010 and H-1011. Reset form on the page clears the form only.

## Demonstration script (about 4 minutes)

1. Start the server and open the page. Say that this is a local simulator: the sender menu is not login, and the server still checks who may change each fact.
2. Reset form. Choose **Jordan Lee, held intake**. Create intake. Point at Held, version none, zero tasks, and “The role was not on the intake.” This step does not call a model.
3. Click **New event**. Send a reply as Sam Ortiz with `We hired a CSR`. Open Decisions. The plan is proposed and is not active.
4. Click **New event**. Record an HR decision as Alex Rivera, approve the held plan, and confirm the dialog. The plan becomes Active at version 2. The attention list still says policy, equipment, and the first-day meeting are incomplete. Approval does not confirm missing evidence.
5. Reset form. If Hire id still shows the previous case, clear it. Choose **Riley Chen, complete supported intake** and create it. Show the four tasks and Active, version 1. This intake does not wait for HR.
6. Ask a policy question as Riley Chen on the new hire id. Click **New event**, then **Can IT provide an approved loaner by the start date?**, then Ask question. Open Policy. Read the passage and **Citation P2**. Equipment stays unconfirmed. This is the live Gemini call.
7. If time remains, click **New event**, send a reply as Taylor Brooks with `The laptop slips to March 19. A spare might be free on start day.` Activity shows that reply and one follow-up that cites P2. Equipment stays unconfirmed.
8. Event-id check, using a completed reply: edit the message and submit the same event id. The page shows one line: `event_mismatch: This event id was already used with different contents. The new contents were not applied. No second hire was created.` The plan stays Active at its current version. “What happened” still says the plan is active. Activity still shows the original reply. Use **New event** before a different submission.

Use the sentences on the page. Other wording may go to manual review. Out-of-pack topics go to HR.

## Architecture

Python chooses the route, checks the sender and the event id, and writes the case. The model does not choose the next role, tool, or follow-up. CrewAI runs one sequential task with delegation off and agent memory off. Two model routes exist: reading an equipment reply, and answering a supported policy question. HR decisions, start-date changes, deadline checks, task updates, and a role reply on a held hire do not call a model.

Cases are stored in local SQLite. The hire read adds a current-case summary from the plan’s activation. Activity keeps each event’s own text. The page is a static workspace served by the same process. Gemini is `gemini/gemini-3.5-flash-lite` at temperature 0, with one application attempt.

The earlier live equipment failure happened because the prompt placed instructions after the message, and the model copied those instructions into its excerpt. Python rejected the draft because an excerpt must be a contiguous copy of the original message. That check is unchanged. The message now comes last, between start and end markers. H-1011’s laptop reply committed under that rule: the fact was stored, equipment stayed unconfirmed, and one follow-up was sent.

## Known limitations

- The policy detector publishes answers for its recorded question patterns. Other wording may go to manual review. Topics outside the pack go to HR. Deleting the word “not” can still match the late-acknowledgment pattern.
- The reply examples are tested sentences, not every sentence the reader can accept. An excerpt that is not inside the message writes no new fact.
- One application attempt is used. Stacked retries and a provider-wide circuit breaker are not implemented.
- The page is a local simulator for one Austin office and the Customer Support Representative role. It is not authentication, and it is not deployed.
- HR approval does not complete missing evidence. The scenario clock is 2026-03-13, so some due dates are already overdue.
- If Hire id still contains an older case, the next reply or question is sent to that case.
- Earlier failed equipment events remain stored. They were not deleted or retried for this package.

## Materials to submit

- This repository, without `.env` and without secret values.
- `submission/ASSIGNMENT.md` (this file).
- `submission/screenshots/01-end-to-end-held-intake.png`
- `submission/screenshots/02-hitl-proposed-not-active.png`
- `submission/screenshots/03-hitl-active-after-approval.png`
- `submission/screenshots/04-event-mismatch.png`
- `submission/screenshots/05-end-to-end-riley-tasks.png`
- `submission/screenshots/06-external-api-policy-citation.png`
- `submission/screenshots/07-equipment-reply-follow-up.png`

Do not submit the API key. Do not reset the case file if the grader wants to inspect H-1010 and H-1011.

## Sources

- Browser session on `http://127.0.0.1:8000/` on 2026-11-26, hires H-1010 and H-1011.
- Server token-count lines for `gemini-3.5-flash-lite` on the H-1011 policy question and equipment reply.
- `.venv/bin/python -m unittest discover -s onboarding/tests -q`: 58 tests, 0.882s, OK. No Gemini call. The case-summary check is held, then proposed, then HR-approved. The demo-lock check uses a temporary server and a throwaway token.
- `.env.example` names only: `AAMAD_TARGET_RUNTIME`, `GEMINI_API_KEY`, `GEMINI_MODEL_NAME`, `DEMO_ACCESS_TOKEN`, `DEMO_MODEL_CALLS_PER_HOUR`, `ONBOARDING_HOST`, `PORT`, and a commented `ONBOARDING_DB_PATH`. No values for the key or token.

## Assumptions

- The scored assignment is the three requirements named above.
- A local browser demonstration satisfies the working-system requirement. The public host is prepared and not turned on.
- H-1010 and H-1011 remain in the local case file.

## Open Questions

- None for the three assignment requirements. Stacked retries and a provider-wide circuit breaker stay out of scope.

## Audit

- Persona: integration-eng, recording the verification that was run in this session.
- Action: submission packaging.
- Timestamp: 2026-11-26T22:25:00Z.
- Resolved runtime: crewai. `AAMAD_TARGET_RUNTIME` was unset.
- Prompt trace omitted: this file records observed results and does not include prompts or secret values.
