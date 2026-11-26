# Week 6 results — D1 through D12

Scored on 2026-11-26 from `project-context/1.define/prd.md` section 7. Each row started from its own intake in `onboarding/tests/test_scenarios.py`, or from the browser steps named below. Equipment drafts in that file are stand-ins. They are not Gemini. The one live provider call is the browser policy question on H-1003.

The bounded policy detector does not answer wording outside its recorded patterns. That question is not marked passed.

| Row | Expected | Actual | Evidence | Result |
|---|---|---|---|---|
| D1 | Four Riley tasks, Appendix A dates, no approval hold | Four tasks. Policy 2026-03-12, equipment and meeting 2026-03-16, training 2026-03-23. Activation active. | Mocked `test_d1_complete_intake` | Pass |
| D2 | No tasks before Sam’s reply; proposed plan after it; active only after HR approval | Blank Jordan intake had no tasks. “We hired a CSR” proposed four tasks. Alex’s approval set activation active and left every task pending. | Mocked `test_d2_missing_role_then_approval`. Browser: a later Jordan intake showed Proposed plan, then “HR approved the held plan. The plan is active.” | Pass |
| D3 | At most one follow-up, no invented role, visible HR escalation | Two unclear Sam replies left the role blank and the task list empty. One role follow-up. The second reply escalated. | Mocked `test_d3_second_ambiguous_reply_escalates`. Browser H-1001: “One follow-up” and “Escalated to HR. The role was not established.” | Pass |
| D4 | No equipment confirmation; one P2 follow-up; other tasks unchanged | Uncertain loaner stayed unconfirmed. One follow-up cited P2. The other three tasks kept their status. | Mocked reader `test_d4_possible_loaner_does_not_confirm` | Pass |
| D5 | Jordan confirmed; Riley blocked and escalated; no follow-up after the denial | Separate hires. Jordan’s March 2 commitment confirmed equipment. Riley’s “No loaner.” blocked and escalated equipment with no follow-up. | Mocked reader `test_d5_confirmation_and_denial_are_separate` | Pass |
| D6 | Later IT evidence clears the escalation and keeps history; the new hire cannot confirm | IT’s March 16 commitment cleared the escalation and kept the denial message. Riley’s copy of that sentence added no evidence and did not change the plan version. | Mocked reader `test_d6_later_it_evidence_and_wrong_actor` | Pass |
| D7 | Completed policy kept; meeting reconfirmed; training dates match; a covered commitment stays confirmed; an estimate stays unconfirmed | Jordan policy stayed complete with due 2026-02-26. Meeting returned to unconfirmed. Training due became 2026-03-16. The March 2 commitment still confirmed the March 9 start. Riley’s March 19 estimate stayed unconfirmed after a move to March 23; unfinished policy due became 2026-03-19 and training 2026-03-30. | Mocked reader and task updates `test_d7_later_start_preserves_completed_policy`. No direct database edit. | Pass |
| D8 | Earlier start blocks a March 2-only commitment; meeting needs reconfirmation; unfinished dates move; overdue flags appear; completed policy remains | Policy stayed complete, due 2026-02-26. Equipment blocked and overdue. Meeting unconfirmed and overdue. Training due 2026-03-06. | Mocked reader and task update `test_d8_earlier_start_blocks_a_late_commitment` | Pass |
| D9 | Cited P1 and P2 answers; no equipment booking; remote work routed to HR | The recorded P1 and P2 questions published the exact passages. Remote work stored “outside the pack” and no answer. Plan version and equipment readiness did not change. “What should I know before I start?” published nothing. | Mocked answerer `test_d9_bounded_questions_only`. Browser live Gemini on H-1003 published the exact P2 passage. Server log named `gemini-3.5-flash-lite`. The key was not printed. | Pass for those bounded questions. Not a pass for arbitrary paraphrases. |
| D10 | Ready only before revocation; then Needs attention with evidence kept; prior HR decisions preserved and the disposition flagged | After policy acknowledgment, the March 2 commitment, meeting confirmation, and training assignment, readiness was Ready. Revocation returned Needs attention. Policy stayed complete. The IT event remained on the equipment evidence. The approval record remained. The escalation disposition stayed, with `needs_review`. | Mocked reader and task updates `test_d10_ready_then_revocation_flags_the_disposition` | Pass |
| D11 | State survives; replay adds no duplicate work; model failure invents no fact; Jordan does not change Riley | Closing and reopening the case file kept the unconfirmed reply. Replaying the event id left one follow-up. A failed read stayed failed and unconfirmed. Activating Jordan left Riley’s plan version unchanged. | Mocked `test_d11_restart_replay_failure_and_isolation`. This reopen is a new store on the same file, not a killed HTTP process mid-case. | Pass |
| D12 | A third name and different dates follow the same rules; reviewer wording is not a hard-coded sentence; no live provisioning or eligibility decision | Avery Nguyen, start 2026-04-06, stayed held until Morgan’s sentence containing CSR proposed the plan. Dates were 2026-04-02, 2026-04-06, and 2026-04-13. Riley could not confirm equipment. IT’s sentence “The spare unit is committed for 2026-04-06.” confirmed it through the draft, not a stored sentence list. The router has no provisioning, access, identity-document, or eligibility event. | Mocked reader `test_d12_third_name_and_reviewer_wording` | Pass |

Regression alongside this score: `onboarding.tests.test_plan`, `test_policy_question`, and `test_equipment_reply`. The combined run was 50 tests, OK. No model call in that run.

## Sources

- `project-context/1.define/prd.md` section 7 and Appendix A.
- `onboarding/tests/test_scenarios.py`.
- Browser session on `http://127.0.0.1:8000` after `.venv/bin/python -m onboarding.reset_demo`. `.env` was not read or changed.

## Assumptions

- A question passes D9 only when it matches the recorded detector table. An unmatched paraphrase is manual review and is not counted as a cited answer.
- Training is assigned for day-one readiness when the manager records `training` / `assigned` on the existing Appendix A task. Completion is a separate action and is not required for Ready.

## Open Questions

- Policy paraphrase scope remains open. The table does not cover arbitrary wording.
- Decision 7, stacked retries, and decision 10, a provider-wide circuit breaker, stay open.

## Audit

- **Timestamp:** 2026-11-26T21:45:00Z
- **Persona ID:** qa-eng
- **Action:** qa
- **Resolved runtime:** crewai. `AAMAD_TARGET_RUNTIME` was unset.
- **Model / temperature / max_tokens:** The scored file used stand-in readers. The browser question used Gemini `gemini-3.5-flash-lite`, temperature 0, from the server settings. The key was not printed.
- **Prompt trace:** Omitted. The live question text is the P2 loaner sentence above.
