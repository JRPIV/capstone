# Market Research Document: Continuous Pre-Payroll Audit & Retro-Adjustment Engine

**Primary focus:** The Continuous Pre-Payroll Audit & Retro-Adjustment Engine. It inspects a preliminary payroll with timecards, effective-dated HR changes, and prior-period records; asks the worker, manager, or HR representative who has the missing fact; keeps a conflicting or incomplete reply unresolved; drafts the current-cycle correction and, where needed, the prior-period retro adjustment; and gives the Payroll Controller one docket. The Controller approves and locks the batch.  
**Selected runtime:** `crewai`, from `aamad.config.yml`. `AAMAD_TARGET_RUNTIME` was not set. The runtime is a way to build a demonstration. It is not a reason a customer would buy.  
**Research date:** 2026-11-03.

## Executive Summary

You are evaluating a tool for payroll operations in the days before batch lock, not a new payroll system. The customer to test is an in-house payroll controller at a U.S. employer with a biweekly hourly workforce, time in ADP Workforce Now or UKG, rate changes in HR, and a preliminary gross register from the payroll engine. Desks in that range are thin. In a 2026 KPMG and UKG survey of 319 payroll leaders, 46 percent manage 10,000 to 50,000 employees, a common team is 15 to 24 people, and 74 percent use more than two vendors. Published payroll-software totals for 2025 run from about $9 billion to about $39 billion, depending on the definition (Appendix A). Those figures describe systems this customer already pays for. They do not say what the engine is worth. A 2020 Deloitte benchmark, older than the other surveys, still has the clearest public split of why off-cycle payments happen: missed HR updates 20 percent, missed time 17 percent, retroactive payments 8 percent.

A demonstration is realistic if you keep it to one synthetic employee. A backdated hourly increase is missing from the preliminary register. The engine asks HR which effective date is right, leaves a conflicting reply unresolved, and, once the date is confirmed, drafts the current-period and prior-period gross difference. CrewAI can run that sequence. The hard part is keeping the question, the reply, and both drafts on the same case. Tax, filing, payment, and locking the batch are different jobs. Leave them out. Workday already documents that its own U.S. retro does not recalculate prior-period tax, which is a reason not to invent a second tax calculator.

The useful test is that one case, scored on time to a reviewable correction, manual follow-ups, correction accuracy, unresolved cases at cutoff, and edits the Controller makes before accepting. Detection, email reminders, manager approval, and supported retro are already available. ADP and UKG document the chase inside the time system. Workday documents retro for events it supports. UKG’s May 2026 payroll announcement describes drafted pay-slip corrections for payroll administrators. The pages reviewed do not show one case that crosses time, HR, and the preliminary register, holds a conflicting reply open, and regenerates both gross drafts. That is the bet. It is unproven. One controller interview or one vendor demo can settle it.

## Detailed Findings by Dimension

### 1. Market Analysis & Opportunity Assessment

#### Key Insights

- The customer is the payroll controller, or the practitioner who prepares that controller’s lock, at a U.S. employer with biweekly hourly employees and more than one system of record. Time lives in ADP Workforce Now or UKG Dimensions. The rate change is an effective-dated HR event. The preliminary gross register comes from the payroll engine. A company that already runs time, HR, and payroll inside Workday is a weak first customer, because Workday tells payroll to calculate supported retro before every regular run. A small restaurant group shows the same “rate saved too late” mechanic and is the wrong buyer for this weight of workflow.
- Today’s path is a handoff with a deadline. Before signoff, the manager clears timecard exceptions in the time system. At close, a practitioner emails the people who still have to confirm something and runs the check again. After signoff, payroll keys the late change or carries it to the next cycle. ADP documents the email and the recheck. UKG documents that a punch edit stays off the timecard until a manager acts, and that a late change after signoff should go to payroll rather than reopen the period. UCSF, one public employer, sends anything found after the Tuesday 6 a.m. manager deadline to payroll on a form.
- The need you would be filling is the case that crosses those boundaries and still lacks a confirmed fact. Missed HR updates, missed time, and retro pay are routine reasons for off-cycle payments in the 2020 Deloitte mix. Whether controllers lack a workable screen for that case, or have simply not configured the suite they own, is not known. No price for this kind of docket was found.
- The business result that would matter is a shorter path from a bad preliminary register to a number the Controller can approve, with fewer hand-keyed adjustments. The 2 to 4 percent “payroll leakage” band in the KPMG and UKG report, and the Department of Labor’s $259 million in FY2025 back wages, describe other losses. They are in Appendix B so they are not mistaken for demand.
- Competitors already cover the front and the back of the path. The capability matrix below is the comparison. A blank cell means the materials reviewed do not show the behavior. It does not mean the product lacks it. Dayforce, SAP, Oracle, Paychex, Paycom, and Paylocity were not reviewed at this level.

#### Data Points

Customer and workflow figures. Market-size extracts are in Appendix A. Enforcement totals are in Appendix B.

| Fact | Figure | Source | What it supports |
| --- | --- | --- | --- |
| Payroll as a share of operating expense | 40–60%, described as typical | KPMG and UKG, © 2026, 319 leaders | Pay is large enough that payroll errors are a finance problem |
| Team size against population | 46% manage 10,000–50,000 employees; 23% run payroll with 15–24 people | Same survey | The desk is small relative to the cycle |
| More than two payroll vendors | 74% | Same survey | Split systems are common in this sample |
| Integration named as a challenge | 34% | Same survey | The handoff is a stated pain. The channel is not named |
| Still on manual processes | 23% | Same survey | Some of the work is still keyed |
| Off-cycle cause mix | Terminations 30%; missed HR 20%; missed time 17%; retro 8%; underpayments 12%; bonus 10% | Deloitte / APA, © 2020, 750+ organizations | Upstream HR and time, plus retro, are ordinary off-cycle work |
| Off-cycle volume, North America | 0.3 payments per employee per year | Same study | A frequency, not a dollar loss |
| Manager deadline, one employer | Biweekly managers approve by 6 a.m. Tuesday; later fixes go to payroll on a form | UCSF Controller, current page | The window after close is payroll’s |

Capability matrix. **Doc** = product or administrator documentation describes it. **Ad** = the vendor claims it; it was not seen working. **Part** = a narrower version is documented.

| Behavior | ADP time | UKG time and Pro Pay | Workday Payroll | Celery | PayGuard | Contract-as-Code | SyntraFlow |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Find errors before release | Doc | Doc for time exceptions. Ad for payroll anomaly detection | Doc for retro before each regular run | Ad | Ad | Ad | Ad |
| Read time, HR, and payroll together | Part. Time and approvals | Part. Timecard, then UKG payroll | Doc inside Workday | Ad | One exported file | Ad. Payroll against agreement rules | Ad. UKG time and pay |
| Ask a specific person for a missing fact | Doc. Email for unapproved timecards and manager corrections | Doc. Missed-punch form to the manager. Ad. Administrator asks the product in plain language |  |  |  |  |  |
| Wait for an asynchronous reply | Part. Email and in-app approval | Part. Request, manager decision, employee notice |  |  |  |  |  |
| Keep a conflict or a silence unresolved | Part. Unapproved timecards can remain. Some exceptions can be cleared with a note | Part. An edit stays pending until the manager acts |  |  |  |  |  |
| Recheck after a fact changes | Doc. Restart the exception check | Doc. Approved edit becomes paid time | Doc. Retro can be run again |  |  |  |  |
| Tie a current finding to a prior period |  | Doc. A signed-off historical edit becomes a current-period wage adjustment | Doc for supported events, back to a cutoff date. U.S. prior-period tax is excluded |  |  |  |  |
| Prepare a reviewable gross draft | Part. Practitioner adjusts payroll after close | Ad. Conversational pay-slip corrections for administrators | Doc. Retro differences land in the next open period |  |  | Ad. Clause findings and a decision trail. No pay draft described |  |
| Keep evidence through the Controller’s decision | Part. Exception lists and approvals inside time close | Part. Pending-changes record. Ad. Human review before processing | Doc. Retro reports |  |  | Ad. Decision trail. Reviewer not named | Ad. A person commits. The product does not approve |

#### Source Citations

Customer and workflow: sources 9, 29, and 32–40. Competitors: sources 11–13, 19–25, 35–37, and 41–42. Market size, held in the appendix: sources 1–8.

#### Implications

Aim the first version at the split-system hourly controller, and at one exception: a backdated rate that is wrong on the preliminary register. If your interviews show that this person already finishes that case inside ADP, UKG, or Workday, the commercial case closes. Until someone shows you a price or a purchase, treat willingness to pay as unknown.

### 2. Technical Feasibility & Requirements Analysis

#### Key Insights

- The demonstration needs four inputs for one employee: the preliminary gross register, timecard hours, the HR effective date, and the rate actually paid in the prior period. It needs one output the Controller can read: original gross, revised gross, and the difference, for the current period and the prior period, plus the question, the reply, and whether the case is still unresolved.
- CrewAI fits a short sequence: read, compare, ask, judge the reply, recheck, draft. That is a build choice. UKG and ADP already advertise their own payroll agents, so the framework is not the advantage. The sequence should stop for the Controller. It should not post pay.
- The state of the case is the fragile part. A conflicting reply has to remain visible next to the HR date. A later confirmation has to recalculate only that employee and replace the draft without dropping the history. A scan that runs once, on a clock, and never looks again repeats what ADP’s end-of-period restart, UKG’s pending edit, and Workday’s retro rerun already do inside one system.
- Scale for a class demonstration is one synthetic cycle. The production bottleneck, if this were real, would be false alarms during a short pre-lock window, not the number of people logged in. KPMG and UKG’s staffing numbers are the reason a noisy queue would be abandoned.
- Leave statutory tax, filings, and bank files out. A gross rule of hours times the rate change is enough to test the workflow. Adding tax would create a second calculator beside the payroll engine, which is a different product and a different risk.

#### Data Points

| Constraint | Evidence | Consequence for a demonstration |
| --- | --- | --- |
| Supported retro has a boundary | Workday generates differences only for supported events on or after the worker’s No Retro Processing Prior To date. U.S. and Canadian retro does not recalculate prior-period tax | Your draft should say which periods and which amounts it did calculate |
| Facts can arrive after a preview exists | Toast help: a pay change saved after Preview is invisible until the payroll is reset | The interesting moment is after the preliminary register exists. Toast is a small-employer illustration, not your customer |
| Recheck is already a button inside time | ADP: restart the payroll-exception check after edits | Recheck alone is not new. Recheck of a cross-system case with the reply still attached is the untested behavior |
| Agents are on sale | UKG, 11 May 2026; ADP, 28 January 2026 | Use agents if they help the demo. Do not cite them as differentiation |

No measured share of cycles in which an effective date changes after the preliminary register is built. That frequency decides whether a second pass is worth building.

#### Source Citations

Sources 11, 13, 19–21, 34, and 40.

#### Implications

Build the case file first: inputs, reply, conflict flag, two drafts, Controller decision. Put the model, if you use one, on the explanation of a row the rules already flagged. Keep the gross math deterministic so accuracy can be scored.

### 3. User Experience & Workflow Analysis

#### Key Insights

- The people in the workflow are the Payroll Controller, who decides; the HR representative, manager, or worker who has the missing fact; and the engine, which carries the case. The Controller does not clear timecards. The manager does not lock payroll. Mixing those jobs is how the current handoff loses the thread.
- Your intended path matches the gap in the matrix if, and only if, the case stays whole. Inspect the preliminary payroll beside time, HR, and prior pay. Name the missing fact. Ask the right person and wait. If the reply conflicts or is incomplete, say so and stop. When a fact changes, recheck that finding. Draft the current correction and the prior-period adjustment. Hand the Controller the evidence, the drafts, the open questions, and the history.
- What can run without a person is the comparison and the arithmetic once the effective date is confirmed. What cannot is the decision that a reply is good enough, and the decision to lock. ADP already lets some exceptions be cleared with a note, and lets unapproved timecards remain. Your choice to keep a conflict visibly unresolved is a product decision, not yet a customer preference.
- “Continuous” has two meanings. A scan on a schedule, including one that starts 48 hours before lock, is ordinary pre-payroll review. A recheck when a timecard, an effective date, or a confirmation changes is also ordinary inside the system that owns that fact. The version that would matter here is the second one, applied to an open cross-system case. It matters only when facts still move after the preliminary register exists.
- The screen that fits the job is the docket: one row per exception, the evidence beside it, the reply or the gap, and the draft. A general chat window does not give the Controller a lock decision. Success, on a scripted cycle, is the five measures in the recommendations. No customer was asked whether they would add another queue in the last two days of the cycle.

#### Data Points

| Step you intend | Who does the closest job today | Where | Gap in the evidence |
| --- | --- | --- | --- |
| Inspect preliminary gross, time, HR, prior pay | Practitioner at period close; payroll after signoff | ADP end-of-period steps; UKG signoff then payroll | A single view across all four inputs was not shown |
| Ask the person who knows | Practitioner emails; employee submits a missed punch | ADP email; UKG form to the manager | A question stored on the payroll case was not shown |
| Judge the reply and hold a conflict | Manager approves, rejects, or edits; some ADP exceptions are noted | UKG pending changes; ADP note | A reply that contradicts the HR date, left open on purpose, was not shown |
| Recheck when the fact changes | Practitioner restarts the check; approved edit hits the timecard; retro is run again | ADP, UKG, Workday | The draft of both periods regenerating from that reply was not shown |
| Controller reviews and locks | Practitioner or administrator approves the run | Suite payroll close | The lock stays with a person in every serious product description |

#### Source Citations

Sources 11, 13, 19, and 32–37.

#### Implications

Script two replies for the same employee. One confirms the HR date. One names a different date. The confirmed path should produce a draft. The conflicting path should still be open at cutoff, with both dates visible. If you only ship the happy path, you have not tested the workflow.

### 4. Production & Operations Requirements

#### Key Insights

- For the demonstration, one batch over synthetic files is enough. Run it when the preliminary register is available. If you later start 48 hours before lock, that clock matches a pre-close review. It does not require a hosted service.
- The log that makes the docket trustworthy is short: batch identity, source row, question, reply or timeout, whether the case is unresolved, both drafts, and the Controller’s accept, edit, or hold. A model transcript is not a substitute.
- The files contain pay rates and can contain identifiers. Use invented employees. A real register is a security project of its own.
- The gross rule has to be dated. If the rate table can change underneath a case, the draft should show which rate it used. You do not need a tax-table subscription to learn whether the workflow holds.
- If the engine is down, payroll still has the suite it already uses. The dangerous failure is a clean docket that hid a conflict. An empty “no issues” result should mean the check ran, not that the check was skipped.

#### Data Points

Operational cost and legal exposure are not priced here. Appendix B holds the public loss figures so they stay available and stay separate from a build budget. No license price was found for Celery, PayGuard, Contract-as-Code, SyntraFlow, UKG’s audit features, or ADP Assist. `aamad.config.yml` sets no budget.

| Demonstration control | Pass condition |
| --- | --- |
| Synthetic data only | No real employee, rate, or account number in the repo or the log |
| Conflict visible | The conflicting reply and the HR date both appear on the docket |
| No write-back | Nothing in the demo replaces the gross batch or sets batch lock |
| Rule named on the draft | Hours, rate change, periods, and delta are readable without opening a prompt |

#### Source Citations

Sources 9, 21, and 27. Appendix B uses sources 14–18, 28, and 30.

#### Implications

Treat the log as the product. If a reviewer cannot reconstruct the case from it, the demonstration failed even if the arithmetic was right.

### 5. Innovation & Differentiation Analysis

#### Key Insights

- Several things you might be tempted to claim are already ordinary: a pre-release scan, an audit log, a human approver, an independent check of an export, support for more than one file layout, and an agent that explains a variance. UKG and ADP are selling the agent version into the payroll desk now. Workday already replays supported history.
- The claim that can still be yours is the combination, for the split-system customer: one case, a targeted question, a conflict or a silence left unresolved, a recheck that rewrites the current and prior gross drafts, and a Controller packet that still shows the history. Each piece has a cousin in the matrix. The combination was not shown.
- Three hypotheses, in the order that matters. First, controllers lose time on exceptions no single system both investigates and drafts, and they would use one cross-system packet. The handoff is documented. The empty seat is not. This falls if a UKG, ADP, or Workday demo completes that packet for one employee, or if three controllers say they already do. Second, controllers would rather see a conflict held open than see it noted or dropped. ADP already notes some exceptions and leaves some timecards unapproved, so “open items exist” is not the same preference. This falls if practitioners say an open conflict cannot sit on the lock docket. Third, regenerating the draft when the date is confirmed saves real work inside the pre-lock window. This falls if, in your segment, time and HR are frozen before the preliminary register is built.
- A patent search was not done. The pattern of pre-release checks and suite retro is already sold, so novelty is the wrong bet. A longer-term advantage would be a record of how a particular controller desk disposes of the same exceptions, good enough that the next question is shorter. Two file adapters do not create that. No partnership or price was found that would change the first-year plan.
- The 2026 product announcements point the same direction as your idea and stop short of it in the text: investigate, draft a correction, let a person decide. If those products already ask HR and hold a bad reply, your differentiation is gone. The demo questions in the recommendations are how you find out.

#### Data Points

| Class | Belongs here | Status |
| --- | --- | --- |
| Baseline | Scheduled pre-payroll scan, timecard queues, email or in-app reminders, manager approval, in-system recheck, supported retro, human sign-off, an audit log of approvals | Documented for ADP, UKG, or Workday |
| Possible advantage | The combination in the first row of hypotheses, for the split-system hourly controller | Not shown in the materials reviewed. Pain of late HR and time updates is documented |
| Later advantage, if any | A desk’s own history of how these cases were decided | No evidence. Incumbents already hold pay history and approvals |
| Not yet known | Willingness to pay. How often facts change after the preliminary register. Whether controllers will lock with an item still open | Needs interviews |

#### Source Citations

Sources 9, 11, 13, 19–21, 29, 32–37, and 41.

#### Implications

Position the engine, if you continue, as the packet for one hard exception at a split-system hourly employer. Drop the claim if hypothesis 1 fails the demo questions. Do not spend the class project on a second export format or a more general chatbot.

## Critical Decision Points

### Go/No-Go Factors

Proceed with a demonstration if it is the backdated-increase case, with one confirming reply and one conflicting reply, and if the Controller’s decision is recorded and nothing is posted to payroll. Stop calling the idea differentiated if a vendor demo or a few controller interviews show that packet already exists. Willingness to pay is not a go decision you can make from this research.

### Technical Architecture Choices

Use a deterministic gross rule and a stored case. A language model can word the question and the summary. It should not invent the delta or decide that two dates agree. CrewAI is an acceptable way to sequence those steps. Workday’s retro boundaries are a warning about scope, not a design you need to copy. Do not calculate tax.

### Market Positioning

For a payroll controller closing an hourly cycle across time, HR, and a preliminary register: one exception, the question that was asked, the reply or the open conflict, and the current and prior gross drafts, with the evidence still attached. The customer is the split-system desk described above. A single-suite Workday shop and a Toast-sized employer are the wrong first audiences.

### Resource Requirements

One synthetic cycle, one rule, two scripted replies, and a docket a person can accept, edit, or hold. No budget is set in the project config. Market totals in Appendix A are not a staffing plan. The highest-value hour you can spend next is a conversation with someone who closed last cycle’s backdated rate, using the questions below.

## Risk Assessment Matrix

### High Risk

- UKG or ADP already completes the cross-system packet, and the announcement text simply did not say so. The five demo questions are the check.
- A conflicting reply is stored as if it were confirmed. The conflicting script has to stay unresolved.
- Leakage percentages or back-wage totals get reused as the size of this opportunity. They measure something else. They live in Appendix B for that reason.
- A real payroll file is copied into the project. Use invented employees.

### Medium Risk

- Time and HR are frozen before the preliminary register, so the recheck never sees a new fact. Ask before building the second pass.
- The demonstration shrinks to flagging rows on one file. That tests a baseline feature and misses the bet.
- Controllers refuse to see open items on a lock docket. Hypothesis 2 would be false, and the packet would need a different rule.

### Low Risk

- Another publisher’s market total disagrees with Mordor’s. The disagreement is definition. It does not change the customer.
- A patent exists on anomaly detection. The behavior you would be testing is already surrounded by commercial products. A search was not done and is not the next decision.

## Actionable Recommendations

### Immediate Next Steps

Within the next two days, write down the last backdated-rate story you want a controller to tell, and ask these questions of a payroll controller or of the person who prepares the lock.

1. Who had the missing fact, what did you use to reach them, and how long until you had a number you would show a controller?
2. When the reply disagreed with the HR date, what happened to the case?
3. After the date was settled, what did you rerun, and what did you copy by hand?
4. Can an unresolved item sit on the docket at lock, or does it wait for the next cycle?
5. When time, HR, and payroll disagree, which one are you allowed to treat as wrong?

If you can get a vendor demonstration from UKG Pro Pay, ADP Assist, or Workday Payroll, ask them to do five things with one employee: start from a preliminary gross that has the old rate, ask HR the effective date inside the product, store a contradictory reply on that same case without posting a correction, correct the date and show both period drafts recalculated, and show where the Controller’s accept or hold is stored. If time and payroll must be the same product for the demo to work, write that down. It is still a real finding.

### Short-term Priorities

Over the next month, if you build, build only the scripted case. Score both replies.

| Measure | What to count |
| --- | --- |
| Time to a reviewable correction | From the mismatch to a packet with original, revised, and delta, or to an explicit unresolved state |
| Manual follow-ups | Questions a person had to handle outside the scripted thread |
| Correction accuracy | Draft delta against the known hours and rate change. A conflicted case must not receive a passing delta |
| Unresolved at cutoff | The conflicting reply is still open. The confirmed reply is not |
| Reviewer rework | Edits before accept. The conflicted packet should be held, not cleaned up into a false accept |

Keep the gross rule on the packet. Do not add a second exception type, a live messaging channel, or a tax line.

### Long-term Strategy

Over six to twelve months, the suite vendors will keep attaching investigation and draft corrections to the payroll run. Your idea has a life past the class project only if controllers with split time and HR systems still rebuild this packet by hand after those releases. If the interviews in the next two days show they do not, keep the demonstration as a proof of the workflow and drop the market claim. There is no basis yet for a price, a partnership, or a second country.

## Appendix A. Published market totals

These baskets overlap and disagree. They are context for the systems payroll teams already buy. They are not the market for this engine.

| Publisher | What was counted | 2025 | 2026 | Later | Growth | Accessed |
| --- | --- | --- | --- | --- | --- | --- |
| Mordor Intelligence | Payroll and HR compliance software | $23.4B | $25.59B | $40.69B in 2031 | 9.72% CAGR, 2026–2031 | 2026-11-03 |
| Mordor Intelligence | Payroll and compensation management, mostly services | $28.81B | $30.39B | $39.72B in 2031 | 5.50% CAGR | 2026-11-03 |
| Mordor Intelligence | Payroll services | $32.6B | $35.32B | $52.75B in 2031 | 8.35% CAGR | 2026-11-03 |
| The Business Research Company, via GII, 12 September 2025 | HR payroll software, broad | $38.82B | Not stated | $57.05B in 2029 | 10.1% | 2026-11-03 |
| The Business Research Company, May 2025 page | Same label, different extract | 2024 base $35.27B | Not stated | $57.80B in 2029; $91.70B in 2034 | 10.38% then 9.67% | 2026-11-03 |
| WiseGuyReports | Payroll software | $8.65B | Not stated | $15B in 2035 | 5.7% CAGR | 2026-11-03 |
| Grand View Research | Payroll-administration outsourcing only | $4.28B | Not stated | $9.61B in 2033 | 10.7% CAGR | 2026-11-03 |
| Fortune Business Insights | HR software, parent category | $21.07B | $23.68B | $60.26B in 2034 | 12.38% CAGR | 2026-11-03 |

Mordor’s January 2026 compliance-software cut also reports large enterprises at 61.7 percent of 2025 revenue and cloud at 68.4 percent. Those shares describe the incumbent budget.

## Appendix B. Loss figures that are easy to misuse

| Figure | Source | Why it is not a price for this engine |
| --- | --- | --- |
| 2–4% of labor spend lost to “payroll leakage.” 38% of respondents put the annual amount between $1 million and $5 million. 1% of labor spend at 50,000 employees illustrated as $10–15 million | KPMG and UKG, © 2026. The formula for the 2–4% band is not in the report. UKG sells payroll audit software | Sponsored estimate of a broad loss. No link to a docket or a fee |
| More than $259 million in back wages for 176,957 workers in FY2025, about $1,465 each. FLSA portion $184.4 million, of which overtime was $146.4 million | U.S. DOL Wage and Hour Division, January 2026 release and FLSA table | Enforcement after the fact. Mostly overtime, which this gross-only demonstration does not calculate |
| $418 million across 337 reported federal collective settlements in 2025, about $1.2 million average | Seyfarth Shaw, Lex Machina | Disclosed litigation. Private settlements are missing. Not a software budget |
| Self-reported payroll accuracy 80.15%, about $291 per reported process error | EY, 2022, 508 U.S. respondents at firms of 250–10,000 employees | Outside the 18-month window, and a different definition of “accuracy” from a payment-error rate |
| U.S. customer payroll-processing error rate 0.87% | Beaman metrics deck, 2015 | Included only because it conflicts with the EY percentage. Not current |

## Sources

1. Mordor Intelligence. “Payroll And HR Compliance Software Market.” Dataset note January 2026. https://www.mordorintelligence.com/industry-reports/payroll-and-hr-compliance-software-market. Accessed 2026-11-03.
2. Mordor Intelligence. “Payroll And Compensation Management Market.” https://www.mordorintelligence.com/industry-reports/payroll-and-compensation-management-market. Accessed 2026-11-03.
3. Mordor Intelligence. “Payroll Services Market.” https://www.mordorintelligence.com/industry-reports/global-payroll-services-market. Accessed 2026-11-03.
4. The Business Research Company, via GII Research. “HR Payroll Software Global Market Report 2025.” 12 September 2025. https://www.giiresearch.com/report/tbrc1509655-hr-payroll-software-global-market-report.html. Accessed 2026-11-03.
5. The Business Research Company. “HR Payroll Software Market.” May 2025 page. https://www.thebusinessresearchcompany.com/report/hr-payroll-software-market. Accessed 2026-11-03.
6. WiseGuyReports. “Payroll Software Market.” https://www.wiseguyreports.com/reports/payroll-software-market. Accessed 2026-11-03.
7. Grand View Research. “Payroll Administration — Business Process Outsourcing.” https://www.grandviewresearch.com/horizon/statistics/business-process-outsourcing-market/human-resource/payroll-administration/global. Accessed 2026-11-03.
8. Fortune Business Insights. “HR Software Market.” https://www.fortunebusinessinsights.com/hr-software-market-116228. Accessed 2026-11-03.
9. KPMG LLP and UKG. “Payroll at the tipping point.” © 2026. https://www.ukg.com/sites/default/files/2026-03/2025-2026-KPMG-and-UKG-Global-Payroll-Survey-Report_0.pdf. Accessed 2026-11-03. 319 payroll leaders. Sponsored by a payroll vendor.
10. UKG newsroom on the same KPMG study. https://www.ukg.com/company/newsroom/ukg-and-kpmg-nearly-40-employers-suffer-millions-dollars-preventable-losses-annually-due-global-payroll-errors. Accessed 2026-11-03.
11. UKG newsroom. “UKG Pro Pay with Workforce AI.” 11 May 2026. https://www.ukg.com/company/newsroom/ukg-unveils-agentic-powered-ukg-pro-pay-workforce-ai-payroll-congress-2026. Accessed 2026-11-03.
12. UKG newsroom. Payroll AI agents. 19 May 2025. https://www.ukg.com/company/newsroom/ukg-launches-next-generation-payroll-ai-agents-unlock-productivity-efficiency-and-elevated-employee-engagement. Accessed 2026-11-03.
13. ADP media center. ADP Assist agents. 28 January 2026. https://mediacenter.adp.com/2026-01-28-ADP-R-Accelerates-AI-Leadership-with-Launch-of-New-AI-Agents-Designed-to-Solve-Workforce-Challenges. Accessed 2026-11-03.
14. U.S. Department of Labor. Back-wage recovery for FY2025. 8 January 2026. https://www.dol.gov/newsroom/releases/whd/whd20260108. Accessed 2026-11-03.
15. U.S. Department of Labor, Wage and Hour Division. FY2025 data. https://www.dol.gov/agencies/whd/data. Accessed 2026-11-03.
16. U.S. Department of Labor. FLSA back-wage table. https://www.dol.gov/agencies/whd/data/charts/fair-labor-standards-act. Accessed 2026-11-03.
17. Bloomberg Law. Analysis of FY2025 wage-hour penalties. https://news.bloomberglaw.com/daily-labor-report/wage-hour-penalties-surge-by-millions-as-dol-closes-fewer-cases. Accessed 2026-11-03.
18. Seyfarth Shaw LLP. “2025 FLSA Litigation Metrics & Trends.” https://www.seyfarth.com/dir_docs/brochure/2025-FLSA-Litigation-Metrics-and-Trends.pdf. Accessed 2026-11-03.
19. Workday. “Calculate Retro Payroll.” https://doc.workday.com/admin-guide/en-us/payroll/retroactive-payroll/process-retroactive-payroll/dan1370797361464.html. Accessed 2026-11-03.
20. Workday. “Retro and Off Cycle Processing.” https://doc.workday.com/workday-education/en-us/course-manuals/payroll-for-administrators/retro-and-off-cycle-processing.html. Accessed 2026-11-03.
21. Workday. “Setup Considerations: Adjustments for Prior Periods.” https://doc.workday.com/admin-guide/en-us/payroll/payroll-processing/adjust-payments/xvh1606932481385.html. Accessed 2026-11-03.
22. Celery. “Payroll Guard.” https://www.celeryway.com/products/payroll-guard. Accessed 2026-11-03.
23. Contract-as-Code. https://www.contract-as-code.com/. Accessed 2026-11-03.
24. PayGuard. https://www.payguardhq.com/. Accessed 2026-11-03.
25. SyntraFlow. “UKG Pre-Payroll Validation.” https://www.syntraflow.cloud/ukg-testing/use-cases/pre-payroll-validation/. Accessed 2026-11-03.
26. U.S. Department of Labor. Payroll Audit Independent Determination. https://www.dol.gov/agencies/whd/paid. Accessed 2026-11-03.
27. Internal Revenue Service. “Information return penalties.” https://www.irs.gov/payments/information-return-penalties. Accessed 2026-11-03. Reason to keep filings out of a student project. Amounts are the 2025 table.
28. EY. “Cost and risks due to payroll errors.” 2022. https://eyquest.com/files/Cost_and_Risks_Due_to_Payroll_Errors_2022_Final.pdf. Accessed 2026-11-03.
29. Deloitte, APA, and GPMI. Global Payroll Benchmarking Survey. © 2020. https://www.deloitte.com/content/dam/assets-zone3/us/en/docs/services/consulting/2024/us-apa-payroll-congress-survey-report.pdf. Accessed 2026-11-03.
30. Karen V. Beaman. Global payroll metrics deck, 2015. Accessed 2026-11-03. Historical contrast on “accuracy” only.
31. `aamad.config.yml`. Greenfield project. Runtime target `crewai`.
32. ADP. “Resolving Timecard Exceptions Overview.” https://otcdc1.adp.com/ezLMHelp/V18_30/WFN/General/StandardUI/en-US/ss_help/ss/exceptions-intro.htm. Accessed 2026-11-03.
33. ADP. “Essential Time & Attendance Supervisor Timecard Basics.” https://www.royers.com/adp/manager/docs/tabasicssup.pdf. Accessed 2026-11-03.
34. ADP. “Performing End of Period Operations.” https://otcdc1.adp.com/ezlmhelp/v18_30/wfn/general/standardui/en-us/as_help/as/end_of_period-performing.htm. Accessed 2026-11-03.
35. UKG. Employee punch edits and pending approval. https://communityfiles.ukg.com/support/KOL/OnlineHelp-WorkforceDimensions/en-us/Content/Timekeeping/Punches-employees.htm. Accessed 2026-11-03.
36. UKG Coach. “Weekly Tasks for Managers.” https://coach.ukg.com/cs/coach-demo-v45/content/d_weeklytasksformanagers.html. Accessed 2026-11-03. Training content for a configured site.
37. UKG. “Make historical corrections.” https://customer2.kronos.com/support/kol/onlinehelp-workforcedimensions/en-us/Content/Timekeeping/HistoricalCorrections-managers.htm. Accessed 2026-11-03.
38. Improvizations. UKG Dimensions notification setup. https://blog.improvizations.com/easy-peasy-how-to-set-up-ukg-system-notifications. Accessed 2026-11-03. Implementer article. Notifications can be on-screen, mobile, email, or SMS.
39. UCSF Controller’s Office. “Pay Period Close Quick Reference Guide.” https://controller.ucsf.edu/how-to-guides/timekeeping-scheduling/pay-period-close-quick-reference-guide. Accessed 2026-11-03. One employer.
40. Toast Payroll help. Pay changes and preparing a payroll. https://support.toasttab.com/en/article/Toast-Payroll-Pay-Changes. Accessed 2026-11-03.
41. UKG blog. Payroll investigation in plain language; people still approve. https://www.ukg.com/blog/hr-leaders/ai-should-make-hr-work-easier-not-more-complex. Accessed 2026-11-03.
42. MarketScale. Secondary account of an October 2026 UKG release that drafts corrections for payroll staff. https://www.marketscale.com/industries/software-and-technology/ukgs-new-frontline-ai-aims-to-catch-payroll-problems-before-payday. Accessed 2026-11-03. The UKG release note was not opened.

## Assumptions

- The workflow in the primary focus is the idea under test. Public sources do not establish it as an unmet need.
- “Payroll Controller” is the person who may lock the batch. Vendor pages more often say practitioner, administrator, or manager. Those titles may be the same desk or three desks. The interviews have to sort that out.
- The 10,000-to-50,000-employee band describes survey respondents. It is not a count of buyers.
- A biweekly hourly population with time and HR in different systems is the segment that fits the evidence. A single-suite customer is assumed to be a poor fit until a demo shows otherwise.
- Channels nobody documented, including phone, Slack, and Teams, are not assumed.
- Empty cells in the matrix mean the behavior was not in the pages reviewed.

## Open Questions

- Which screen does your target controller use today for a backdated rate that is wrong on the preliminary register?
- How often does an effective date or a timecard change after that register is built?
- Will a controller leave an unresolved conflict on the lock docket?
- Can UKG Pro Pay, ADP Assist, or Workday complete the five demonstration steps for one employee?
- Which hours, rates, and two replies will define the synthetic case?

## Audit

- Timestamp: 2026-11-03T21:30:00-08:00
- Persona id: `product-mgr`
- Action: `create-mrd`
- Resolved runtime: `crewai` (`aamad.config.yml`; `AAMAD_TARGET_RUNTIME` was not set)
