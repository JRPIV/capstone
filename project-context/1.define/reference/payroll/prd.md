# Product Requirements Document: Continuous Pre-Payroll Audit & Retro-Adjustment Engine

## 1. Five-line vision

The product serves the payroll practitioner who prepares payroll lock, and the HR representative who can supply a missing effective date. Before lock, a backdated hourly rate change can be missing from the preliminary payroll, with the question and the dollar correction scattered across separate systems. The product investigates that one discrepancy, asks for clarification, judges the reply against the evidence, and prepares current-period and prior-period gross adjustments. The benefit is a reviewable adjustment, or a clearly unresolved case, that a person can check before lock. The system may prepare the adjustment; only the payroll controller approves it, and nothing is released to payroll.

## 2. Users and primary use case

**Payroll practitioner / controller.** This person runs the review before lock. They read the evidence, the replies, and the draft adjustments. They may correct ordinary hours or the hourly rates shown as calculation inputs. They approve or hold the result. They do not establish the effective date by typing one in, and they do not release payroll from this product.

**HR representative.** This is the designated HR approver named on the employee’s rate-change record. They answer on a simulated channel. They may confirm or correct the effective date only by using an approved rate-change record. A reply that merely agrees with the existing HR date does not settle it. A correction must name the supporting record and explain the discrepancy. Their answer does not approve the pay adjustment.

**Primary use case.** A biweekly hourly employee has an approved rate change whose dollars are not in the preliminary payroll. The register and the prior payment still use the old rate. The product opens one case, shows the register, the ordinary hours, the existing HR date, the prior pay, and the approved rate-change record, and asks the designated HR approver which effective date that record supports. If the reply meets the authority rule before the clarification deadline, the product drafts the current-period and prior-period gross adjustments and leaves them for the controller. The controller approves or holds a named version. The preliminary payroll file is unchanged, and the product does not include the adjustment in a payroll release. The same path works for other synthetic employees, rates, dates, and reply wording. One script for one person is not the product.

Two deadlines apply. The clarification deadline is earlier than payroll lock. A supported reply after that deadline and before lock can produce a draft marked “late—requires review.” That draft does not approve itself and does not mean the adjustment is in payroll. A reply at or after lock is kept and sent to later-cycle handling. It does not change an approved result on the closed cycle.

## 3. In and out of MVP

This Week 6 scope is proposed until Joey accepts it.

**In.**

- One exception type: backdated hourly rate changes. The rules apply to every synthetic employee who fits the pay scenario, not to one stored answer.
- Synthetic payroll, time, and HR records only.
- A simulated channel for asynchronous clarification, including different wording, an incomplete answer, and conflicting evidence.
- A fixed authority rule. The designated HR approver confirms or corrects the effective date by using an approved rate-change record. Agreement with the existing HR date is not enough. A correction names that record, explains the discrepancy, and is stored beside the original evidence.
- One targeted follow-up when the first reply is incomplete, ambiguous, or contradictory. If the next reply is still incomplete or contradictory, the case is escalated for human review and the product stops asking. If the clarification deadline comes first, the case is marked unresolved, escalated, and not asked again.
- Deterministic gross pay for a bounded scenario: one job, ordinary hours, one old hourly rate and one new hourly rate, and an effective date on the start of the current period or the immediately previous period. Overtime, mixed rates, mid-period dates, and other pay shapes are flagged and are not given an ordinary-hour adjustment.
- Decimal arithmetic. Each period’s gross adjustment is rounded to the nearest cent. An exact half-cent tie rounds away from zero. That is the synthetic demo’s convention.
- A review screen with the evidence, the adjustment drafts, the history, and the controller’s disposition.

**Out.**

- Live payroll, time, or HR integrations.
- Production employee data.
- Tax calculation, filings, and money movement.
- Automatic payroll release, replacing the preliminary register, or locking the payroll processor.
- Timecard-edge checks and withholding checks. Both stay deferred. A withholding check, if built later, would compare a supplied expected amount. It would not be a tax calculator.

## 4. A handful of user stories

**S1. Detect the discrepancy**

As a payroll controller, I want a backdated ordinary-hour rate discrepancy opened as a case, so I can see it before lock.

- Given the Employee A records in section 5, when the check runs, the screen shows one case with the register rate, the existing HR date, the hours, the prior pay, and the statement that the authorized effective date is still missing.
- Given a second synthetic employee with different hours, rates, and period dates who also fits the bounded scenario, the same kind of case is opened. Employee A’s reply text is not reused as that employee’s result.
- Given overtime, two new rates, or a mid-period date, the case is labeled unsupported and shows no ordinary-hour adjustment.
- Given no rate difference of at least one cent, no case is opened. A missing register is reported as a failed pull, not as “no issues.”

**S2. Ask for clarification**

As the designated HR approver, I want the question kept on the case, so my later reply stays with the evidence.

- Given a case with a named HR approver, the simulated channel sends one question asking for the effective date and the approved rate-change record.
- Given no named approver, the case is escalated for human review and nobody else is asked to settle the date.
- Given a reply that only says the existing HR date is correct and does not use an approved rate-change record, the date stays unresolved and one follow-up names that missing record.
- Given that follow-up was already sent, the product does not send another.

**S3. Handle a weak or conflicting reply**

As a payroll controller, I want an insufficient answer to stay open, so a contradiction cannot become an adjustment ready for review.

- Given a reply whose stated date does not match the approved rate-change record it cites, the case asks once for one record that matches one date, and no draft is ready for review.
- Given a second reply that is still incomplete, ambiguous, or contradictory, the case is escalated for human review, the history keeps both replies, and no further question is sent.
- Given no resolving reply by the clarification deadline, the case is marked unresolved, escalated for human review, and still listed. No adjustment is ready.
- Given a manager’s note, it is stored and does not confirm or correct the date.

**S4. Prepare the gross adjustments**

As a payroll controller, I want current-period and prior-period gross adjustments from the resolved date, including when that date shows the original HR date was wrong.

- Given Employee A’s supported confirmation, the screen shows a prior-period adjustment of $160.00 and a current-period adjustment of $160.00. Each revised gross is $1,760.00. The original HR row is unchanged.
- Given Employee B’s supported correction, the original HR date remains visible, and the correction stores 2026-09-28, record R-B, and the explanation. The prior-period adjustment is $90.00. The current-period adjustment is $95.63. The current revised gross is $1,510.88.
- Given a correction that names the record and the date but has no explanation, the date is not resolved and the follow-up asks for the explanation.
- Given a resolved date that the bounded scenario cannot price, the screen shows the unsupported label and no ordinary-hour adjustment.

**S5. Review and record the decision**

As a payroll controller, I want to approve or hold a specific draft, so the decision is tied to the evidence I saw.

- Given a draft ready for review, approval stores the controller, the time, the evidence version, and the draft version. The preliminary register file is unchanged, and payroll is not released.
- Given an unresolved, escalated, or unsupported case, approval of an adjustment is refused.
- Given a supported reply after the clarification deadline and before lock, the draft is marked “late—requires review.” The reply is not an approval and is not described as included in payroll.
- Given a reply at or after lock, the reply remains visible, the case is marked for a later cycle, and the closed cycle’s approved amounts stay as they were.

**S6. Revalidate after a material change**

As a payroll controller, I want a change to the inputs or the evidence to require a new review, so an old approval cannot cover new numbers.

- Given Employee A approved at $160.00 and $160.00, when the current-period ordinary hours are edited from 80.00 to 81.00 before lock, the current-period adjustment becomes $182.00, the prior-period adjustment stays $160.00, and the previous approval is no longer current.
- The edited hours do not change the effective date or the approved rate-change record. The earlier draft and the earlier approval remain in the history.
- Given new evidence before the clarification deadline that conflicts with a resolved date, the case reopens with one targeted question, and the current approval no longer applies.
- Given new evidence or a reply at or after lock, the closed cycle’s approved result does not change.

## 5. Week 6 definition of done

A passer who was not part of the project can score this. Use the synthetic records below. Recompute the amounts with decimal arithmetic. Round each period’s gross adjustment to the nearest cent, and round an exact half-cent tie away from zero. Pass only if the screen matches these results, the history is visible, the controller’s decision is stored, and the preliminary payroll file is unchanged. A passing run shows that the behavior matches this list. It does not show that the product saves time or reduces workload.

**Shared calendar**

- Prior period starts 2026-09-28. Current period starts 2026-10-12.
- Clarification deadline is 2026-10-23 17:00. Payroll lock is 2026-10-24 17:00.

**Employee A, used for confirmation, silence, and the hours edit**

- Ordinary hours: 80.00 prior, 80.00 current. Old rate $20.00. New rate $22.00.
- Preliminary current gross $1,600.00. Prior paid gross $1,600.00.
- Existing HR date 2026-09-28. Approved record R-A approves 2026-09-28.
- Check: 80.00 × 22.00 = 1,760.00. Adjustment = 1,760.00 − 1,600.00 = 160.00 for each period.

**Employee B, used for the correction**

- Ordinary hours: 72.00 prior, 76.50 current. Old rate $18.50. New rate $19.75.
- Prior paid gross $1,332.00. Preliminary current gross $1,415.25.
- Existing HR date 2026-10-12, which is wrong for this case. Approved record R-B approves 2026-09-28.
- Prior check: 72.00 × 19.75 = 1,422.00. Adjustment = 1,422.00 − 1,332.00 = 90.00.
- Current check: 76.50 × 19.75 = 1,510.875. Unrounded adjustment = 1,510.875 − 1,415.25 = 95.625, an exact half-cent tie. Rounded adjustment = 95.63. Revised current gross = 1,415.25 + 95.63 = 1,510.88.

**Pass/fail**

1. **Supported confirmation.** The designated HR approver for Employee A states 2026-09-28 and uses R-A before the clarification deadline. Pass if both adjustments are $160.00, both revised gross amounts are $1,760.00, the original HR row is unchanged, and the draft is ready for the controller. Fail if the case resolves from the sentence “the HR date is correct” with no approved record.
2. **Supported correction.** The designated HR approver for Employee B states 2026-09-28, identifies R-B, and explains that the HR date was entered one period late. Pass if the original HR date 2026-10-12 is still visible, the correction and explanation are stored separately, the prior adjustment is $90.00, and the current adjustment is $95.63. Fail if the explanation is missing and the case still resolves, or if the HR row is overwritten.
3. **Incomplete answer.** Before any valid reply, Employee A’s approver sends wording that does not state one date or does not identify an approved record. Pass if the date stays unresolved, one follow-up names the missing piece, and no $160.00 draft is ready. Fail if a second follow-up is sent or the case is treated as confirmed.
4. **Contradiction or no response.** Either the approver cites R-A but states 2026-10-12, and a second reply still disagrees; or no resolving reply arrives by 2026-10-23 17:00. Pass if the case is escalated for human review, no further question is sent, no adjustment is ready, and both replies or the absence are visible. Fail if any dollar adjustment can be approved from that case.
5. **Changed evidence after approval.** Approve Employee A’s $160.00 / $160.00 result. Then change current ordinary hours from 80.00 to 81.00 before lock. Pass if the new current adjustment is $182.00 (81.00 × 22.00 − 1,600.00), the prior adjustment remains $160.00, the old approval remains visible but is not current, and the controller must review the new draft. Fail if $160.00 stays approved for the edited hours.
6. **Nothing is posted.** After every step above, the preliminary register file still shows Employee A at $1,600.00 and Employee B at $1,415.25. No tax, payment file, or payroll release exists.

## 6. Genuinely open questions

1. **How complete must the later cycle be after lock?** A reply at or after lock must be kept and must not change the closed approval. Week 6 can either show only a “later cycle” label on that closed case, or open a second cycle and carry the reply into it. The label is enough to score the closed result. Default: show the label and the preserved reply, and do not build the next cycle.
2. **May the controller approve a late draft before lock?** A supported reply between the clarification deadline and lock produces a draft marked “late—requires review” and does not approve itself. It is undecided whether the controller may still approve that marked draft before lock. Default: they may approve it before lock; the late mark stays on the history; approval still does not release payroll.
3. **What text counts as explaining a discrepancy?** Employee B fails if the explanation is missing. It is undecided whether any non-empty explanation is enough, or whether the text must state both dates. Default: the reply must state, in any wording, that the existing HR date is not the date to use and that the approved record’s date is. The demo does not grade writing quality beyond that.
