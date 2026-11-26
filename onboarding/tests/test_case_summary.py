"""Current-case summary after held, proposed, and HR approval. No model call."""

import tempfile
import unittest
from pathlib import Path

from onboarding.case_summary import APPROVED, PROPOSED, case_summary
from onboarding.router import read_hire, submit_event
from onboarding.store import CaseStore


JORDAN = {
    "event_id": "evt-summary-intake",
    "event_type": "intake",
    "actor_id": "actor-alex-rivera",
    "actor_role": "hr_coordinator",
    "occurred_at": "2026-02-27T09:00:00-06:00",
    "body": {
        "employee_name": "Jordan Lee",
        "start_date": "2026-03-02",
        "role": "",
        "office": "Austin",
        "manager_name": "Sam Ortiz",
    },
}


class CaseSummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.store = CaseStore(Path(self._dir.name) / "case.sqlite")

    def tearDown(self) -> None:
        self.store.close()
        self._dir.cleanup()

    def test_held_then_proposed_then_hr_approved(self) -> None:
        status, intake = submit_event(self.store, JORDAN)
        self.assertEqual(status, 202, intake)
        hire_id = intake["hire_id"]
        self.assertEqual(self._summary(hire_id), [])

        status, proposed = submit_event(
            self.store,
            self._event("evt-summary-reply", hire_id, "reply", "We hired a CSR", "actor-sam-ortiz", "hiring_manager"),
        )
        self.assertEqual(status, 202, proposed)
        self.assertEqual(self._summary(hire_id), [PROPOSED])

        status, approved = submit_event(
            self.store,
            self._event(
                "evt-summary-hr",
                hire_id,
                "hr_decision",
                {"decision_type": "approve_held_plan", "rationale": "Role is CSR.", "plan_version": 1},
                "actor-alex-rivera",
                "hr_coordinator",
            ),
        )
        self.assertEqual(status, 202, approved)
        status, hire = read_hire(self.store, hire_id)
        self.assertEqual(status, 200)
        self.assertEqual(hire["activation"], "active")
        self.assertEqual(hire["plan_version"], 2)
        self.assertEqual(hire["case_summary"], [APPROVED])
        reply = next(item for item in hire["decisions"] if item["event_id"] == "evt-summary-reply")
        self.assertEqual(reply["rule_result"], "proposed_plan")
        reply_message = next(item for item in hire["messages"] if isinstance(item, dict) and item["event_id"] == "evt-summary-reply")
        self.assertEqual(reply_message["kind"], "reply")
        self.assertEqual(reply_message["body"], "We hired a CSR")
        hr_message = next(item for item in hire["messages"] if isinstance(item, dict) and item["event_id"] == "evt-summary-hr")
        self.assertEqual(hr_message["kind"], "hr_decision")
        self.assertEqual(hr_message["body"], "Role is CSR.")

    def test_older_policy_answer_does_not_replace_approval(self) -> None:
        hire = {
            "activation": "active",
            "decisions": [
                {"event_id": "reply-1", "rule_result": "proposed_plan"},
                {"event_id": "hr-1", "rule_result": "approve_held_plan"},
            ],
            "events": [
                {"event_id": "policy-1", "state": "complete"},
                {"event_id": "hr-1", "state": "complete"},
            ],
            "messages": [
                {"event_id": "reply-1", "kind": "reply", "body": "We hired a CSR"},
                {"event_id": "policy-1", "kind": "policy_answer", "citation": "P2", "body": "Older passage."},
                {"event_id": "hr-1", "kind": "hr_decision", "body": "Role is CSR."},
            ],
        }
        before = [dict(item) for item in hire["messages"]]
        self.assertEqual(case_summary(hire), [APPROVED])
        self.assertEqual(hire["messages"], before)
        self.assertEqual(hire["decisions"][0]["rule_result"], "proposed_plan")

    def _summary(self, hire_id: str) -> list[str]:
        status, hire = read_hire(self.store, hire_id)
        self.assertEqual(status, 200, hire)
        return hire["case_summary"]

    def _event(self, event_id, hire_id, event_type, body, actor_id, actor_role) -> dict:
        return {
            "event_id": event_id,
            "event_type": event_type,
            "hire_id": hire_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "occurred_at": "2026-02-27T15:00:00-06:00",
            "body": body,
        }
