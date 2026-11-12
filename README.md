# Automated Employee Onboarding Workflow

A local demonstration that keeps a new hire’s onboarding plan accurate when facts are missing, replies are uncertain, or the start date changes. It coordinates four tasks, asks the right person for missing facts, updates only the work those facts affect, and answers questions from an approved policy pack.

The Week 6 baseline is proposed. Architecture, the user interface, and the application are not built yet.

## Status

| Item | State |
| --- | --- |
| Mode | Greenfield (`aamad.config.yml`) |
| Runtime target | CrewAI. The application pattern, agent count, and work ownership are not chosen. |
| Define | System description, market research, PRD, and user stories US-001 through US-007 |
| Architecture | Not started. No SAD. |
| Build and delivery | Not started. No application, tests, or runbook. |

The PRD is a proposed release contract, not a record that the product is approved or implemented. An earlier payroll concept is kept under `project-context/1.define/reference/payroll/` and is not this product.

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

This repository uses the AAMAD crew. Persona definitions and the phase checklist are in `AGENTS.md` and `CHECKLIST.md`. The next step is `@system.arch`, which records work ownership, the application pattern, the reference architecture, the model and context strategy, and the control register before any build.

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
