# Automated Employee Onboarding Workflow

A local demonstration that keeps a new hire’s onboarding plan accurate when facts are missing, replies are uncertain, or the start date changes. It coordinates four tasks, asks the right person for missing facts, updates only the work those facts affect, and answers questions from an approved policy pack.

The Week 6 baseline is proposed. The SAD, the Sprint 3 page, and the Sprint 3 crew are in the repository.

## Status

| Item               | State                                                                              |
| ------------------ | ---------------------------------------------------------------------------------- |
| Mode               | Greenfield (`aamad.config.yml`)                                                    |
| Runtime target     | CrewAI. The SAD pattern is a workflow. The Sprint 3 crew is two sequential agents. |
| Define             | System description, market research, PRD, and user stories US-001 through US-007   |
| Architecture       | Architecture: SAD completed. Sprint 3 backend architecture documented.             |
| Build and delivery | Sprint 3 page and crew are in the repository. No test suite or runbook.            |

The PRD is a proposed release contract, not a record that the product is approved or implemented. An earlier payroll concept is kept under `project-context/1.define/reference/payroll/` and is not this product.

## Sprint 3 crew

From the repository root, with `OPENAI_API_KEY` and `OPENAI_MODEL_NAME` set in the environment:

```
python -m onboarding.kickoff
```

This command runs the prepared-example crew. It does not open the page. CrewAI 1.15.44 installs on Python 3.10 through 3.13. The repository virtualenv `.venv` is that interpreter. Activate it before the command when the default `python` is 3.14.

## Who it is for

The demonstration uses fictional people at one Austin, Texas office and one role: Customer Support Representative (“CSR” is an accepted alias).

| Person | What they do |
| --- | --- |
| HR coordinator | Reviews the plan, approves a held plan, and handles escalations |
| Hiring manager | Confirms the role, arranges the first-day meeting, and owns training |
| IT fulfiller | Confirms an assigned laptop or an approved loaner |
| New hire | Acknowledges policies and asks onboarding questions |

One person can play every role. The simulator supplies who sent a message. Wording inside a message cannot change that person’s role or the policy pack.

## What the MVP does

A supported plan has exactly four tasks:

| Task | Owner | Due |
| --- | --- | --- |
| Policy acknowledgment | New hire | Two business days before the start date |
| Equipment readiness | IT | Start date |
| First-day meeting | Hiring manager | Start date |
| Customer-support tools orientation | Hiring manager | Five business days after the start date |

Day-one readiness is **Ready** only when policy acknowledgment is complete, equipment is confirmed, and the manager has confirmed the first-day meeting for the current start date. Training must be assigned with a valid deadline. It does not have to be finished before day one. Any other case is **Needs attention**, with the reason shown. An HR decision to proceed does not turn missing evidence into confirmation.

The central case is an uncertain equipment reply. A possible loaner or a delivery estimate stays unconfirmed and prompts one targeted follow-up. Only an explicit, authorized commitment with a ready date on or before the start date confirms equipment.

Seeded hires are Jordan Lee (H-001), whose role is missing at intake, and Riley Chen (H-002), whose record is complete. Dates, policies P1–P4, and the people are fictional. The full fixtures are in `project-context/1.define/prd.md`, Appendix A.

## What this release does not do

- Create production accounts, change access, process identity documents, or decide work eligibility
- Calculate or change payroll or tax
- Connect to production HR, IT, identity, or messaging systems
- Answer pay, overtime, remote-work, or legal-eligibility questions (those go to HR)
- Add more roles or locations, a holiday calendar, live messaging, enterprise sign-in, or a commercial launch

## Where the product is written down

| Artifact | Path |
| --- | --- |
| System description | `project-context/1.define/system-description.md` |
| Market research | `project-context/1.define/mrd.md` |
| Product requirements | `project-context/1.define/prd.md` |
| User stories | `project-context/1.define/user-stories/US-001.md` through `US-007.md` |

The stories are: create a supported plan, resolve a missing role, resolve equipment uncertainty, replan after a start-date change, answer policy questions, review readiness and decisions, and preserve case integrity. Week 6 is done when an independent reviewer can run scenarios D1–D12 from the PRD and reproduce the scored outcomes.

This repository uses the AAMAD crew. Persona definitions and the phase checklist are in `AGENTS.md` and `CHECKLIST.md`. The Solution Architecture Document (SAD) defines the workflow architecture, agent responsibilities, and control requirements. The Sprint 3 frontend and backend establish the initial demonstration. The supported intake on the page calls the local intake API. A reply for the displayed hire also calls that API. A policy question for that hire calls the same API and publishes only an exact listed passage, or routes the question without an invented answer. Jordan Lee’s blank intake stays held until Sam Ortiz confirms a supported role and Alex Rivera approves that proposed plan. Alex can also change an active start date, and a reached deadline escalates an unresolved follow-up. The listed policy patterns do not cover arbitrary paraphrases. A task update records a policy acknowledgment, a meeting confirmation, or training status when the sender is the owner of that fact. `.venv/bin/python -m onboarding.reset_demo` deletes only `onboarding/data/onboarding.sqlite` and its sidecar files. It does not read or change `.env`. Restart the server after a reset.

## Sources

- `project-context/1.define/prd.md` — proposed Week 6 baseline, revised November 5, 2026
- `project-context/1.define/system-description.md`
- `project-context/1.define/mrd.md`
- `project-context/1.define/user-stories/US-001.md` through `US-007.md`
- `aamad.config.yml` — `project.mode: greenfield`, `runtime.target: crewai`

## Assumptions

- Austin, the Customer Support Representative role, the dates, and policies P1–P4 are fictional evaluation data.
- A complete supported intake activates without an extra approval. A missing role holds the plan until the designated manager supplies a supported role and HR approves it.
- A confirmed device stays reserved until onboarding completes unless IT revokes it.
- No spend limit or model is chosen yet. No customer interview has validated usefulness.

## Open Questions

1. Must the capstone use multiple autonomous agents, or can a coordinator with tools satisfy the course requirement? That choice belongs in the SAD.
2. What spend limit and model should govern development and the scored runs?
3. Is an HR or IT practitioner available to review the workflow? If not, Week 6 can still score the specified behavior.

## Audit

- **Timestamp:** 2026-11-06
- **Persona ID:** product-mgr
- **Action:** Replace the scaffold framework README with the current product state from the Define artifacts.
- **Resolved runtime:** `crewai`, from `aamad.config.yml` `runtime.target`. `AAMAD_TARGET_RUNTIME` was not rechecked.
- **Timestamp:** 2026-11-21T00:05:00Z
- **Persona ID:** backend-eng
- **Action:** sync-docs
- **Resolved runtime:** `crewai`, from `aamad.config.yml` `runtime.target`. `AAMAD_TARGET_RUNTIME` was unset.
- **Outcome:** Applied the three approved README sentences for the Sprint 3 crew. The SAD was not edited.
- **Timestamp:** 2026-11-26T16:28:00Z
- **Persona ID:** integration-eng
- **Action:** sync-docs
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target`. `AAMAD_TARGET_RUNTIME` was unset.
- **Outcome:** Operator approved the update. The supported intake on the page is described as calling the local intake API. Reply, policy answers, and HR approval remain unconnected. The SAD was not edited.
- **Timestamp:** 2026-11-26T17:50:00Z
- **Persona ID:** integration-eng
- **Action:** sync-docs
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset.
- **Outcome:** Operator approved the descriptive update. The page now calls the API for a reply on the displayed hire. Policy answers and HR approval stay unconnected. The SAD was not edited.
- **Timestamp:** 2026-11-26T21:20:00Z
- **Persona ID:** backend-eng
- **Action:** sync-docs
- **Resolved runtime:** crewai, from `aamad.config.yml` `runtime.target` and the adapter-registry default. `AAMAD_TARGET_RUNTIME` was unset.
- **Outcome:** Operator approved this change set’s descriptive updates in advance. The page sentence now includes policy questions and says HR approval is not connected. The SAD was not edited.
- **Timestamp:** 2026-11-26T21:40:00Z
- **Persona ID:** backend-eng
- **Action:** sync-docs
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset.
- **Outcome:** The page sentence now includes held-plan approval, start-date change, and deadline. Arbitrary policy paraphrases and task completion remain open. The PRD was not edited.
