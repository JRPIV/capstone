# System Description: Continuous Pre-Payroll Audit & Retro-Adjustment Engine

**Working title:** The Continuous Pre-Payroll Audit & Retro-Adjustment Engine  
**Author / stakeholder:** Joey (operator), 2026-11-03  
**Selected runtime:** `crewai`, from `aamad.config.yml` `runtime.target`. `AAMAD_TARGET_RUNTIME` was not confirmed. The runtime is not an application pattern.

## 1. Intent and Problem

- **Problem statement:** Payroll operations lose the cycle when timecard defects, cross-jurisdictional withholding errors, and backdated changes reach lock still unresolved. The engine works the 48 hours before payroll lock so the Payroll Controller can lock the batch from an exception docket instead of from an unscanned preliminary gross calculation.
- **Primary users / operators:** The Payroll Controller receives the docket and decides batch lock. Workers and managers take part in asynchronous, conversational exception resolution. The engine reads preliminary gross batches and the records behind them. It does not replace the payroll operation that produces the batch.
- **Success definition:** Forty-eight hours before lock, a preliminary gross batch has been pulled and scanned. Timecard edge cases, cross-jurisdictional withholding errors, and backdated changes that affect the current cycle are on an audit trail. Workers and managers have been asked to resolve the exceptions that require them. At lock, the Payroll Controller has an exception docket that summarizes the remaining risks.

## 2. Domain Context

- **Preliminary gross calculation batch:** The payroll processor’s gross result, pulled before lock. The engine scans it. The engine does not originate it.
- **Payroll lock / batch lock:** The Payroll Controller’s decision that the batch may close. The engine presents the docket for that decision.
- **Timecard edge case:** A time record that would break downstream gross pay. The operator named the class and did not name the cases.
- **Cross-jurisdictional withholding:** A withholding result that is wrong across jurisdictions. Detection is in scope. Filing a return is not stated.
- **Backdated change:** A change with an earlier effective date whose dollars land in the current cycle. This is the retro-adjustment work inside the current cycle.
- **Exception:** One finding from the timecard, withholding, or backdated-change scan that a person must resolve or accept.
- **Exception docket:** The list of open risks presented to the Payroll Controller for batch lock.
- **Audit trail:** The record of what was pulled, what was found, what was asked of workers and managers, and what the docket contained.
- **Existing workflow respected:** A processor already calculates preliminary gross and already has a lock. A time source already exists. Jurisdiction setup already exists. Product names were not given.
- **Constraint from prior research, not from this statement:** `project-context/1.define/mrd.md` finds that in-suite tools already review variances, that U.S. retro inside Workday does not recalculate prior-period tax, and that releasing pay, filing returns, and unsupervised legal conclusions sit outside a viable capstone. Those limits are assumptions until the operator confirms them.

## 3. Discovery Buckets

Each row is the operator’s activity, turned into a testable constraint. Rows tagged assumption were not spoken as activities.

### Must do

| ID | Item | Kind | Testable constraint |
| --- | --- | --- | --- |
| MD-001 | Pull preliminary gross calculation batches 48 hours before payroll lock | requirement | A run started at 48 hours before the stated lock time has retrieved the preliminary gross batch for that cycle. A run with no batch produces a failed pull on the audit trail, not an empty pass. |
| MD-002 | Scan timecard edge cases that break downstream gross pay | requirement | Every gross line whose timecard input matches a defined edge case is listed with the timecard reference and the gross line it would break. A gross line with no such input is not listed as a timecard exception. |
| MD-003 | Detect cross-jurisdictional withholding errors | requirement | Every employee on the batch who is subject to more than one withholding jurisdiction, and whose withheld amount disagrees with the expected amount for that jurisdiction pair, appears as a withholding exception. The expected amount’s source is named on the finding. |
| MD-004 | Evaluate backdated changes that affect the current pay cycle | requirement | A change whose effective date is before the current period, and whose recalculated dollars differ from the current batch, appears as a backdated-change exception with the original amount, the revised amount, and the difference. A backdated change with a zero difference does not appear. |
| MD-005 | Resolve exceptions asynchronously in conversation with workers and managers | requirement | For each exception that requires a worker or a manager, the engine sends a question tied to that exception and accepts a reply later without holding the rest of the scan. The reply, or the absence of a reply, is attached to that exception. |
| MD-006 | Compile an audit trail and present an exception docket to the Payroll Controller for batch lock | requirement | Before lock, the Controller can open one docket for the cycle. The docket lists open exceptions, the risk summary, and the status of each conversation. The trail contains the pull, the findings, the questions, the replies, and the docket that was presented. |

### Must not do

| ID | Item | Kind | Testable constraint |
| --- | --- | --- | --- |
| MN-001 | Originate or replace the preliminary gross calculation | requirement | The gross figures on the docket match the pulled batch. The engine has no path that writes a new gross batch back to the processor. |
| MN-002 | Lock the payroll batch | requirement | Batch lock is an action available to the Payroll Controller. The engine has no control that sets lock by itself. |
| MN-003 | File tax returns, transmit a bank file, or submit a DOL PAID package | assumption | No workflow in the MVP produces a filing, a payment file, or a regulator submission. Recorded from the market-research boundary. Confirm or remove before the PRD. |
| MN-004 | Treat a conversation reply as a posted pay change | assumption | A worker or manager reply updates the exception status. It does not change the pulled gross batch. Confirm if a reply is allowed to propose an adjustment the Controller can accept. |

### Must cost

| ID | Item | Kind | Testable constraint |
| --- | --- | --- | --- |
| MC-001 | Finish the scan inside the 48-hour window | requirement | The docket for a cycle exists before the lock time when the batch was available at the 48-hour mark. |
| MC-002 | Keep unanswered conversations from blocking the docket | assumption | At lock, exceptions with no reply are listed as unresolved. They do not prevent the docket from being presented. Volume, model cost, and a dollar cap were not stated. |

### Must prove

| ID | Item | Kind | Evidence the system must produce |
| --- | --- | --- | --- |
| MP-001 | The audit trail can reconstruct the cycle | requirement | For a completed cycle, a reader can see the batch identity, each finding, the evidence row, the question sent, the reply or the timeout, and the docket presented. |
| MP-002 | The docket is sufficient for the lock decision | requirement | The Payroll Controller can tell, from the docket alone, which risks are open, which are answered, and which jurisdiction, timecard, or backdated change each one came from. |
| MP-003 | The Controller’s lock decision is stored | assumption | The trail records lock or hold, the Controller identity, and the time. The operator said the docket is presented for lock and did not say the decision is written back. |

## 4. Functional Requirements

| ID | Description | Priority | Source bucket ID |
| --- | --- | --- | --- |
| FR-001 | Pull the preliminary gross calculation batch 48 hours before payroll lock and record the pull result. | Must | MD-001 |
| FR-002 | Scan the batch for timecard edge cases that break downstream gross pay and attach each hit to the gross line it affects. | Must | MD-002 |
| FR-003 | Detect cross-jurisdictional withholding errors on the batch and name the jurisdictions and the expected amount’s source. | Must | MD-003 |
| FR-004 | Evaluate backdated changes and show the difference each one makes to the current cycle. | Must | MD-004 |
| FR-005 | Carry on asynchronous conversations with the responsible worker or manager for exceptions that need them, one conversation per exception. | Must | MD-005 |
| FR-006 | Compile the audit trail and present one exception docket to the Payroll Controller before batch lock. | Must | MD-006 |
| FR-007 | Leave batch lock and gross calculation in the hands of the Controller and the processor. | Must | MN-001, MN-002 |

## 5. Non-Functional Requirements

| ID | Description | Priority | Source |
| --- | --- | --- | --- |
| NFR-001 | The docket is available before lock when the preliminary batch was available at 48 hours. | Must | MC-001 |
| NFR-002 | An unanswered conversation does not stop the scan or the presentation of the docket. | Must | MC-002 |
| NFR-003 | Every finding cites the source row. A risk summary without a row is not a finding. | Must | MP-001, MP-002 |
| NFR-004 | Wage, withholding, and timecard values used in a conversation or a log are limited to the exception being resolved. | Assumption | MRD security note. No retention period was stated. |
| NFR-005 | The Controller can read the docket without reading the model transcript. | Must | MD-006 |

## 6. Constraints

- Technology constraint: `runtime.target` is `crewai`. Agent topology is undecided and belongs to `@system.arch`.
- Timing constraint: the operational clock is 48 hours before payroll lock, then the Controller’s lock decision.
- Integration constraint: the engine must be able to pull a preliminary gross batch and the timecard, jurisdiction, and backdated-change records that explain it. The processor, the time system, and the conversation channel were not named.
- Integration constraint: the engine does not write a replacement gross batch and does not set batch lock.
- Budget and timeline: no capstone budget or course deadline was stated beyond the 48-hour operational window.

## 7. Assumptions

- A preliminary gross batch exists 48 hours before lock and can be pulled.
- “Edge cases that break downstream gross pay” can be listed before build. Until that list exists, the scan has no pass condition.
- “Cross-jurisdictional” means at least two withholding jurisdictions for one employee in one cycle. Which jurisdictions, and which table supplies the expected amount, are unset.
- A backdated change is in scope when it changes current-cycle dollars. Posting that difference into the processor is not stated.
- The worker or manager on an exception can be identified from the batch or the timecard.
- Conversation is asynchronous and tied to one exception. The channel is unset.
- Unresolved conversations remain on the docket at lock.
- Filing, payment transmission, and regulator submission stay out until the operator adds them.

## 8. Acceptance Criteria

- **AC-001:** Given a cycle with lock time T and a preliminary gross batch available at T minus 48 hours, when the engine runs, then the audit trail shows a successful pull of that batch.
- **AC-002:** Given a gross line whose timecard matches a listed edge case, when the scan completes, then the docket includes that line, the timecard reference, and the gross effect. Given a gross line with no listed edge case, then it is absent from the timecard section.
- **AC-003:** Given an employee withheld under two jurisdictions at an amount that differs from the named expected source, when the scan completes, then the docket includes both jurisdictions, the withheld amount, the expected amount, and the source. Given a single-jurisdiction employee, then no cross-jurisdictional finding is produced.
- **AC-004:** Given a backdated change that changes current-cycle gross or withholding, when evaluation completes, then the docket shows original, revised, and difference. Given a backdated change with no dollar effect on the cycle, then it is absent.
- **AC-005:** Given an exception that names a worker or a manager, when resolution starts, then one conversation is opened for that exception and a late reply attaches to it. Other exceptions continue without that reply.
- **AC-006:** Given the lock time, when the Controller opens the cycle, then one docket shows open risks, answered exceptions, and unanswered exceptions, and the audit trail matches that docket.
- **AC-007:** Given a completed docket, when a reviewer looks for a write path, then there is no action that replaces the gross batch or sets batch lock.

## 9. Out of Scope / Future Work

- Choosing the application pattern, the agent topology, or the visual design.
- Calculating the preliminary gross batch, locking it, issuing payment, filing an information return, or submitting a DOL PAID package, unless the operator adds one of those later.
- Naming a processor, a time system, or a conversation channel. Those are open inputs, not implied integrations.
- A full multi-country tax engine. Detection of cross-jurisdictional withholding errors is in scope. Coverage of every jurisdiction is not.

## Sources

- Operator statement, 2026-11-03, listing the six activities: pull preliminary gross batches 48 hours before lock; scan timecard edge cases that break downstream gross pay; detect cross-jurisdictional withholding errors; evaluate backdated changes that affect the current cycle; handle asynchronous conversational exception resolution with workers and managers; compile an audit trail and present an exception docket to the Payroll Controller for batch lock.
- `project-context/1.define/mrd.md`, research date 2026-11-03. Used for the payroll-operations frame and for the assumed exclusions in MN-003. Market facts are not restated here.
- `aamad.config.yml`: `project.mode: greenfield`, `runtime.target: crewai`.

## Assumptions

- Rows tagged assumption in the buckets above are not operator requirements.
- The phrase “exception docket” is this document’s name for the operator’s “except docket.”
- “Async, conversational exception resolution” is one thread per exception with a worker or a manager. A general chat about pay was not requested.
- Good enough for the MVP is the docket at lock, including unresolved conversations. Clearing every exception before lock was not requested.

## Open Questions

- Which timecard edge cases count as breaking downstream gross pay?
- Which jurisdictions are in the first cycle, and what table or rule supplies the expected withholding amount?
- Which system emits the preliminary gross batch, and how is it pulled?
- Which channel carries the conversation with workers and managers?
- May a reply propose an adjustment, or does it only explain the exception?
- Is the Controller’s lock or hold decision written onto the audit trail?
- Do filing, payment transmission, and regulator submission stay excluded?

## Audit

- Timestamp: 2026-11-03T10:25:00-08:00
- Persona id: `product-mgr`
- Action: `elicit-requirements`
- Resolved runtime: `crewai`, from `aamad.config.yml` `runtime.target`. `AAMAD_TARGET_RUNTIME` was not confirmed.
- Authoring model: Grok 4.7. Temperature and max_tokens were not set by this persona.
- Prompt Trace: omitted. This is a Define-phase capture of an operator statement. No production model call was made.
