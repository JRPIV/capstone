"""Held-plan approval, start-date changes, and deadlines. No model calls."""

import json
import tempfile
import unittest
from pathlib import Path

from onboarding.router import submit_event
from onboarding.store import CaseStore


JORDAN = {
    "event_id": "evt-jordan",
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


class PlanFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.store = CaseStore(Path(self._dir.name) / "case.sqlite")

    def tearDown(self) -> None:
        self.store.close()
        self._dir.cleanup()

    def test_blank_intake_then_manager_then_hr_approval(self) -> None:
        status, body = submit_event(self.store, JORDAN)
        self.assertEqual(status, 202, body)
        hire = self.store.load_hire(body["hire_id"])
        self.assertEqual(hire["activation"], "held")
        self.assertEqual(hire["tasks"], [])
        self.assertIsNone(hire["plan_version"])

        refused = self._event("evt-riley-role", body["hire_id"], "actor-riley-chen", "new_hire", "reply", "We hired a CSR")
        status, refused_body = submit_event(self.store, refused)
        self.assertEqual(status, 202, refused_body)
        hire = self.store.load_hire(body["hire_id"])
        self.assertEqual(hire["activation"], "held")
        self.assertEqual(hire["tasks"], [])

        proposed = self._event(
            "evt-sam-role", body["hire_id"], "actor-sam-ortiz", "hiring_manager", "reply", "We hired a CSR"
        )
        status, proposed_body = submit_event(self.store, proposed)
        self.assertEqual(status, 202, proposed_body)
        hire = self.store.load_hire(body["hire_id"])
        self.assertEqual(hire["activation"], "proposed")
        self.assertEqual(hire["plan_version"], 1)
        self.assertEqual(len(hire["tasks"]), 4)
        self.assertTrue(all(task["execution_status"] != "complete" for task in hire["tasks"]))

        wrong_version = self._event(
            "evt-wrong-version",
            body["hire_id"],
            "actor-alex-rivera",
            "hr_coordinator",
            "hr_decision",
            {"decision_type": "approve_held_plan", "rationale": "Approve.", "plan_version": 9},
        )
        status, wrong_body = submit_event(self.store, wrong_version)
        self.assertEqual(status, 400)
        self.assertEqual(wrong_body["code"], "unsupported")
        with self.store._lock:
            reserved = self.store._conn.execute(
                "SELECT 1 FROM events WHERE event_id = ?",
                ("evt-wrong-version",),
            ).fetchone()
        self.assertIsNone(reserved)

        wrong_sender = self._event(
            "evt-sam-approves",
            body["hire_id"],
            "actor-sam-ortiz",
            "hiring_manager",
            "hr_decision",
            {"decision_type": "approve_held_plan", "rationale": "Approve.", "plan_version": 1},
        )
        status, sender_body = submit_event(self.store, wrong_sender)
        self.assertEqual(status, 400)
        self.assertEqual(sender_body["code"], "unsupported")

        approved = self._event(
            "evt-approve",
            body["hire_id"],
            "actor-alex-rivera",
            "hr_coordinator",
            "hr_decision",
            {"decision_type": "approve_held_plan", "rationale": "Role is CSR.", "plan_version": 1},
        )
        status, approved_body = submit_event(self.store, approved)
        self.assertEqual(status, 202, approved_body)
        hire = self.store.load_hire(body["hire_id"])
        self.assertEqual(hire["activation"], "active")
        self.assertEqual(hire["plan_version"], 2)
        self.assertEqual(hire["readiness"], "needs_attention")
        self.assertTrue(all(task["execution_status"] != "complete" for task in hire["tasks"]))

    def test_ambiguous_role_follow_up_then_escalation(self) -> None:
        status, body = submit_event(self.store, JORDAN)
        hire_id = body["hire_id"]
        first = self._event("evt-vague-1", hire_id, "actor-sam-ortiz", "hiring_manager", "reply", "Not sure yet.")
        self.assertEqual(submit_event(self.store, first)[0], 202)
        hire = self.store.load_hire(hire_id)
        self.assertEqual(sum(1 for message in hire["messages"] if isinstance(message, dict) and message.get("kind") == "role_follow_up"), 1)
        second = self._event("evt-vague-2", hire_id, "actor-sam-ortiz", "hiring_manager", "reply", "Still unsure.")
        self.assertEqual(submit_event(self.store, second)[0], 202)
        hire = self.store.load_hire(hire_id)
        self.assertEqual(sum(1 for message in hire["messages"] if isinstance(message, dict) and message.get("kind") == "role_follow_up"), 1)
        self.assertEqual(sum(1 for message in hire["messages"] if isinstance(message, dict) and message.get("kind") == "escalation"), 1)
        self.assertEqual(hire["tasks"], [])

    def test_escalation_disposition_is_preserved_and_flagged(self) -> None:
        hire_id = self._active_jordan()
        disposition = self._event(
            "evt-disposition",
            hire_id,
            "actor-alex-rivera",
            "hr_coordinator",
            "hr_decision",
            {"decision_type": "escalation_disposition", "rationale": "Watch the laptop.", "plan_version": 2},
        )
        status, body = submit_event(self.store, disposition)
        self.assertEqual(status, 202, body)
        hire = self.store.load_hire(hire_id)
        self.assertEqual(hire["plan_version"], 2)
        decision = next(item for item in hire["decisions"] if item["event_id"] == "evt-disposition")
        self.assertEqual(decision["rule_result"], "escalation_disposition")
        self.assertFalse(decision["needs_review"])
        changed = self._event(
            "evt-date",
            hire_id,
            "actor-alex-rivera",
            "hr_coordinator",
            "start_date_change",
            "2026-03-09",
        )
        self.assertEqual(submit_event(self.store, changed)[0], 202)
        hire = self.store.load_hire(hire_id)
        decision = next(item for item in hire["decisions"] if item["event_id"] == "evt-disposition")
        self.assertTrue(decision["needs_review"])
        self.assertEqual(decision["rationale"], "Watch the laptop.")
        self.assertEqual(hire["start_date"], "2026-03-09")
        self.assertEqual(hire["plan_version"], 3)

    def test_start_date_blocks_a_late_commitment_and_keeps_a_completed_task(self) -> None:
        hire_id = self._active_jordan()
        self._commit_laptop(hire_id, "2026-03-02")
        self._complete_policy(hire_id)
        changed = self._event(
            "evt-earlier",
            hire_id,
            "actor-alex-rivera",
            "hr_coordinator",
            "start_date_change",
            "2026-02-27",
        )
        self.assertEqual(submit_event(self.store, changed)[0], 202)
        hire = self.store.load_hire(hire_id)
        policy = next(task for task in hire["tasks"] if task["name"] == "Policy acknowledgment")
        equipment = next(task for task in hire["tasks"] if task["name"] == "Equipment readiness")
        meeting = next(task for task in hire["tasks"] if task["name"] == "First-day meeting")
        self.assertEqual(policy["execution_status"], "complete")
        self.assertEqual(policy["due_date"], "2026-02-26")
        self.assertEqual(equipment["readiness"], "blocked")
        self.assertEqual(meeting["readiness"], "unconfirmed")
        self.assertTrue(any(isinstance(message, dict) and message.get("subject") == "meeting" for message in hire["messages"]))

    def test_deadline_escalates_once(self) -> None:
        status, body = submit_event(self.store, JORDAN)
        hire_id = body["hire_id"]
        vague = self._event("evt-vague", hire_id, "actor-sam-ortiz", "hiring_manager", "reply", "Maybe later.")
        self.assertEqual(submit_event(self.store, vague)[0], 202)
        early = self._event(
            "evt-early",
            hire_id,
            "actor-alex-rivera",
            "hr_coordinator",
            "deadline_reached",
            "",
        )
        early["occurred_at"] = "2026-02-27T10:00:00-06:00"
        self.assertEqual(submit_event(self.store, early)[0], 202)
        hire = self.store.load_hire(hire_id)
        self.assertEqual(sum(1 for message in hire["messages"] if isinstance(message, dict) and message.get("kind") == "escalation"), 0)
        late = self._event(
            "evt-late",
            hire_id,
            "actor-alex-rivera",
            "hr_coordinator",
            "deadline_reached",
            "",
        )
        late["occurred_at"] = "2026-03-02T18:00:00-06:00"
        self.assertEqual(submit_event(self.store, late)[0], 202)
        hire = self.store.load_hire(hire_id)
        self.assertEqual(sum(1 for message in hire["messages"] if isinstance(message, dict) and message.get("kind") == "escalation"), 1)
        self.assertEqual(hire["tasks"], [])

    def _active_jordan(self) -> str:
        status, body = submit_event(self.store, JORDAN)
        self.assertEqual(status, 202, body)
        hire_id = body["hire_id"]
        role = self._event("evt-role", hire_id, "actor-sam-ortiz", "hiring_manager", "reply", "We hired a CSR")
        self.assertEqual(submit_event(self.store, role)[0], 202)
        approval = self._event(
            "evt-hr",
            hire_id,
            "actor-alex-rivera",
            "hr_coordinator",
            "hr_decision",
            {"decision_type": "approve_held_plan", "rationale": "Approved.", "plan_version": 1},
        )
        self.assertEqual(submit_event(self.store, approval)[0], 202)
        return hire_id

    def _commit_laptop(self, hire_id: str, ready: str) -> None:
        with self.store._lock:
            self.store._conn.execute(
                """
                UPDATE equipment_state SET state = ?, ready_date = ?
                WHERE hire_id = ? AND device = ?
                """,
                ("committed", ready, hire_id, "assigned_laptop"),
            )
            self.store._conn.commit()

    def _complete_policy(self, hire_id: str) -> None:
        with self.store._lock:
            row = self.store._conn.execute(
                "SELECT body_json FROM tasks WHERE hire_id = ? AND position = 0",
                (hire_id,),
            ).fetchone()
            task = json.loads(row["body_json"])
            task["execution_status"] = "complete"
            self.store._conn.execute(
                "UPDATE tasks SET body_json = ? WHERE hire_id = ? AND position = 0",
                (json.dumps(task), hire_id),
            )
            self.store._conn.commit()

    def _event(self, event_id, hire_id, actor_id, actor_role, event_type, body) -> dict:
        return {
            "event_id": event_id,
            "event_type": event_type,
            "hire_id": hire_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "occurred_at": "2026-02-27T15:00:00-06:00",
            "body": body,
        }
