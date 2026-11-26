"""Scored D1–D12 runs. Equipment drafts stand in for Gemini. No database edits."""

import tempfile
import unittest
from pathlib import Path

from onboarding.equipment import ProviderFailure
from onboarding.policy_pack import PASSAGES
from onboarding.router import submit_event
from onboarding.store import CaseStore


class ScenarioScoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.path = Path(self._dir.name) / "case.sqlite"
        self.store = CaseStore(self.path)

    def tearDown(self) -> None:
        self.store.close()
        self._dir.cleanup()

    def test_d1_complete_intake(self) -> None:
        hire = self._intake("d1", "Riley Chen", "2026-03-16", "Customer Support Representative", "Morgan Hale", "2026-03-13T09:00:00-05:00")
        self.assertEqual(len(hire["tasks"]), 4)
        self.assertEqual(hire["activation"], "active")
        self.assertEqual(self._task(hire, "Policy acknowledgment")["due_date"], "2026-03-12")
        self.assertEqual(self._task(hire, "Equipment readiness")["due_date"], "2026-03-16")
        self.assertEqual(self._task(hire, "Customer-support tools orientation")["due_date"], "2026-03-23")

    def test_d2_missing_role_then_approval(self) -> None:
        hire = self._intake("d2", "Jordan Lee", "2026-03-02", "", "Sam Ortiz", "2026-02-27T09:00:00-06:00")
        self.assertEqual(hire["tasks"], [])
        hire = self._send(hire, "d2-role", "actor-sam-ortiz", "hiring_manager", "reply", "We hired a CSR")
        self.assertEqual(hire["activation"], "proposed")
        self.assertEqual(len(hire["tasks"]), 4)
        hire = self._send(
            hire,
            "d2-hr",
            "actor-alex-rivera",
            "hr_coordinator",
            "hr_decision",
            {"decision_type": "approve_held_plan", "rationale": "Role is CSR.", "plan_version": 1},
        )
        self.assertEqual(hire["activation"], "active")
        self.assertTrue(all(task["execution_status"] == "pending" for task in hire["tasks"]))

    def test_d3_second_ambiguous_reply_escalates(self) -> None:
        hire = self._intake("d3", "Jordan Lee", "2026-03-02", "", "Sam Ortiz", "2026-02-27T09:00:00-06:00")
        hire = self._send(hire, "d3-a", "actor-sam-ortiz", "hiring_manager", "reply", "Not sure yet.")
        follow_ups = [message for message in hire["messages"] if isinstance(message, dict) and message.get("kind") == "role_follow_up"]
        self.assertEqual(len(follow_ups), 1)
        hire = self._send(hire, "d3-b", "actor-sam-ortiz", "hiring_manager", "reply", "Still not sure.")
        self.assertEqual(sum(1 for message in hire["messages"] if isinstance(message, dict) and message.get("kind") == "role_follow_up"), 1)
        self.assertEqual(sum(1 for message in hire["messages"] if isinstance(message, dict) and message.get("kind") == "escalation"), 1)
        self.assertEqual(hire["tasks"], [])
        self.assertEqual(hire["role"], "")

    def test_d4_possible_loaner_does_not_confirm(self) -> None:
        hire = self._active_jordan("d4")
        before = [dict(task) for task in hire["tasks"] if task["name"] != "Equipment readiness"]
        text = "The assigned laptop won’t arrive until Thursday, but a loaner may be available Monday."
        hire = self._reply(hire, "d4-it", text, self._possible(text))
        equipment = self._task(hire, "Equipment readiness")
        self.assertEqual(equipment["readiness"], "unconfirmed")
        self.assertEqual(sum(1 for message in hire["messages"] if isinstance(message, dict) and "cites P2" in message.get("body", "")), 1)
        for task in before:
            current = self._task(hire, task["name"])
            self.assertEqual(current["readiness"], task["readiness"])
            self.assertEqual(current["execution_status"], task["execution_status"])

    def test_d5_confirmation_and_denial_are_separate(self) -> None:
        jordan = self._active_jordan("d5j")
        text = "Yes. A loaner will be ready on Monday, March 2."
        jordan = self._reply(jordan, "d5-yes", text, self._commit("permitted_loaner", "2026-03-02", text))
        self.assertEqual(self._task(jordan, "Equipment readiness")["readiness"], "confirmed")
        riley = self._intake("d5r", "Riley Chen", "2026-03-16", "Customer Support Representative", "Morgan Hale", "2026-03-13T09:00:00-05:00")
        riley = self._reply(riley, "d5-no", "No loaner.", self._denial("No loaner."))
        equipment = self._task(riley, "Equipment readiness")
        self.assertEqual(equipment["readiness"], "blocked")
        self.assertTrue(equipment["escalated"])
        self.assertEqual(sum(1 for message in riley["messages"] if isinstance(message, dict) and message.get("kind") == "follow_up"), 0)

    def test_d6_later_it_evidence_and_wrong_actor(self) -> None:
        hire = self._intake("d6", "Riley Chen", "2026-03-16", "Customer Support Representative", "Morgan Hale", "2026-03-13T09:00:00-05:00")
        hire = self._reply(hire, "d6-no", "No loaner.", self._denial("No loaner."))
        self.assertTrue(self._task(hire, "Equipment readiness")["escalated"])
        text = "A loaner will be ready on March 16."
        hire = self._reply(hire, "d6-it", text, self._commit("permitted_loaner", "2026-03-16", text))
        self.assertEqual(self._task(hire, "Equipment readiness")["readiness"], "confirmed")
        self.assertFalse(self._task(hire, "Equipment readiness")["escalated"])
        self.assertTrue(any(message.get("kind") == "escalation" or message.get("body") == "No loaner." for message in hire["messages"] if isinstance(message, dict)))
        before = hire["plan_version"]
        hire = self._reply(hire, "d6-riley", text, self._commit("permitted_loaner", "2026-03-16", text), actor=("actor-riley-chen", "new_hire"))
        self.assertEqual(hire["plan_version"], before)
        self.assertIn("d6-it", self._task(hire, "Equipment readiness")["evidence_refs"])
        self.assertNotIn("d6-riley", self._task(hire, "Equipment readiness")["evidence_refs"])

    def test_d7_later_start_preserves_completed_policy(self) -> None:
        jordan = self._active_jordan("d7j")
        jordan = self._update(jordan, "d7-policy", "actor-jordan-lee", "new_hire", "policy_acknowledgment", "acknowledge")
        jordan = self._update(jordan, "d7-meet", "actor-sam-ortiz", "hiring_manager", "first_day_meeting", "confirm")
        text = "A loaner will be ready on March 2."
        jordan = self._reply(jordan, "d7-it", text, self._commit("permitted_loaner", "2026-03-02", text))
        jordan = self._send(jordan, "d7-date", "actor-alex-rivera", "hr_coordinator", "start_date_change", "2026-03-09")
        policy = self._task(jordan, "Policy acknowledgment")
        self.assertEqual(policy["execution_status"], "complete")
        self.assertEqual(policy["due_date"], "2026-02-26")
        self.assertEqual(self._task(jordan, "First-day meeting")["readiness"], "unconfirmed")
        self.assertEqual(self._task(jordan, "Customer-support tools orientation")["due_date"], "2026-03-16")
        self.assertEqual(self._task(jordan, "Equipment readiness")["readiness"], "confirmed")
        riley = self._intake("d7r", "Riley Chen", "2026-03-16", "Customer Support Representative", "Morgan Hale", "2026-03-13T09:00:00-05:00")
        estimate = "The laptop slips to March 19."
        riley = self._reply(riley, "d7-est", estimate, self._estimate("assigned_laptop", "2026-03-19", estimate))
        riley = self._send(riley, "d7-later", "actor-alex-rivera", "hr_coordinator", "start_date_change", "2026-03-23")
        self.assertEqual(self._task(riley, "Equipment readiness")["readiness"], "unconfirmed")
        self.assertEqual(self._task(riley, "Policy acknowledgment")["due_date"], "2026-03-19")
        self.assertEqual(self._task(riley, "Customer-support tools orientation")["due_date"], "2026-03-30")

    def test_d8_earlier_start_blocks_a_late_commitment(self) -> None:
        hire = self._active_jordan("d8")
        hire = self._update(hire, "d8-policy", "actor-jordan-lee", "new_hire", "policy_acknowledgment", "acknowledge")
        text = "A loaner will be ready on March 2."
        hire = self._reply(hire, "d8-it", text, self._commit("permitted_loaner", "2026-03-02", text))
        changed = self._payload(hire, "d8-date", "actor-alex-rivera", "hr_coordinator", "start_date_change", "2026-02-27")
        changed["occurred_at"] = "2026-03-02T15:00:00-06:00"
        status, body = submit_event(self.store, changed)
        self.assertEqual(status, 202, body)
        hire = self.store.load_hire(hire["hire_id"])
        self.assertEqual(self._task(hire, "Policy acknowledgment")["execution_status"], "complete")
        self.assertEqual(self._task(hire, "Policy acknowledgment")["due_date"], "2026-02-26")
        self.assertEqual(self._task(hire, "Equipment readiness")["readiness"], "blocked")
        self.assertTrue(self._task(hire, "Equipment readiness")["overdue"])
        self.assertEqual(self._task(hire, "First-day meeting")["readiness"], "unconfirmed")
        self.assertTrue(self._task(hire, "First-day meeting")["overdue"])
        self.assertEqual(self._task(hire, "Customer-support tools orientation")["due_date"], "2026-03-06")

    def test_d10_ready_then_revocation_flags_the_disposition(self) -> None:
        hire = self._active_jordan("d10")
        hire = self._send(
            hire,
            "d10-watch",
            "actor-alex-rivera",
            "hr_coordinator",
            "hr_decision",
            {"decision_type": "escalation_disposition", "rationale": "Proceed and watch equipment.", "plan_version": hire["plan_version"]},
        )
        hire = self._update(hire, "d10-policy", "actor-jordan-lee", "new_hire", "policy_acknowledgment", "acknowledge")
        text = "A loaner will be ready on March 2."
        hire = self._reply(hire, "d10-it", text, self._commit("permitted_loaner", "2026-03-02", text))
        hire = self._update(hire, "d10-meet", "actor-sam-ortiz", "hiring_manager", "first_day_meeting", "confirm")
        hire = self._update(hire, "d10-train", "actor-sam-ortiz", "hiring_manager", "training", "assigned")
        self.assertEqual(hire["readiness"], "ready")
        self.assertEqual(self._task(hire, "Customer-support tools orientation")["due_date"], "2026-03-09")
        self.assertEqual(self._task(hire, "Customer-support tools orientation")["execution_status"], "pending")
        revoke = "The loaner commitment is revoked."
        hire = self._reply(hire, "d10-revoke", revoke, self._revoke(revoke))
        self.assertEqual(hire["readiness"], "needs_attention")
        self.assertEqual(self._task(hire, "Policy acknowledgment")["execution_status"], "complete")
        self.assertIn("d10-it", self._task(hire, "Equipment readiness")["evidence_refs"])
        decision = next(item for item in hire["decisions"] if item["event_id"] == "d10-watch")
        self.assertEqual(decision["rationale"], "Proceed and watch equipment.")
        self.assertTrue(decision["needs_review"])
        approval = next(item for item in hire["decisions"] if item["event_id"] == "d10-hr")
        self.assertEqual(approval["rule_result"], "approve_held_plan")

    def test_d11_restart_replay_failure_and_isolation(self) -> None:
        riley = self._intake("d11r", "Riley Chen", "2026-03-16", "Customer Support Representative", "Morgan Hale", "2026-03-13T09:00:00-05:00")
        text = "A spare might be free on start day."
        riley = self._reply(riley, "d11-reply", text, self._possible(text))
        self.store.close()
        self.store = CaseStore(self.path)
        reloaded = self.store.load_hire(riley["hire_id"])
        self.assertEqual(self._task(reloaded, "Equipment readiness")["readiness"], "unconfirmed")
        again, _body = submit_event(self.store, self._payload(reloaded, "d11-reply", "actor-taylor-brooks", "it_fulfiller", "reply", text))
        self.assertEqual(again, 202)
        self.assertEqual(sum(1 for message in self.store.load_hire(riley["hire_id"])["messages"] if isinstance(message, dict) and message.get("kind") == "follow_up"), 1)
        failed = self._reply(reloaded, "d11-fail", "Another note.", self._boom)
        event = next(item for item in failed["events"] if item["event_id"] == "d11-fail")
        self.assertEqual(event["state"], "failed")
        self.assertEqual(self._task(failed, "Equipment readiness")["readiness"], "unconfirmed")
        jordan = self._active_jordan("d11j")
        untouched = self.store.load_hire(riley["hire_id"])
        self.assertEqual(untouched["plan_version"], failed["plan_version"])
        self.assertNotEqual(jordan["hire_id"], riley["hire_id"])

    def test_d12_third_name_and_reviewer_wording(self) -> None:
        hire = self._intake("d12", "Avery Nguyen", "2026-04-06", "", "Morgan Hale", "2026-04-01T09:00:00-05:00")
        self.assertEqual(hire["tasks"], [])
        hire = self._send(hire, "d12-role", "actor-morgan-hale", "hiring_manager", "reply", "The Austin hire is a CSR.")
        self.assertEqual(hire["activation"], "proposed")
        self.assertEqual(hire["role"], "Customer Support Representative")
        hire = self._send(
            hire,
            "d12-hr",
            "actor-alex-rivera",
            "hr_coordinator",
            "hr_decision",
            {"decision_type": "approve_held_plan", "rationale": "Approved.", "plan_version": 1},
        )
        self.assertEqual(self._task(hire, "Policy acknowledgment")["due_date"], "2026-04-02")
        self.assertEqual(self._task(hire, "Equipment readiness")["due_date"], "2026-04-06")
        self.assertEqual(self._task(hire, "Customer-support tools orientation")["due_date"], "2026-04-13")
        wording = "The spare unit is committed for 2026-04-06."
        wrong = self._reply(hire, "d12-wrong", wording, self._commit("permitted_loaner", "2026-04-06", wording), actor=("actor-riley-chen", "new_hire"))
        self.assertEqual(self._task(wrong, "Equipment readiness")["readiness"], "unconfirmed")
        confirmed = self._reply(wrong, "d12-it", wording, self._commit("permitted_loaner", "2026-04-06", wording))
        self.assertEqual(self._task(confirmed, "Equipment readiness")["readiness"], "confirmed")

    def test_d9_bounded_questions_only(self) -> None:
        hire = self._intake("d9", "Riley Chen", "2026-03-16", "Customer Support Representative", "Morgan Hale", "2026-03-13T09:00:00-05:00")
        before = (hire["plan_version"], self._task(hire, "Equipment readiness")["readiness"])
        p1 = "Does a late acknowledgment remain valid after a start-date change?"
        p2 = "Can IT provide an approved loaner by the start date?"
        hire = self._ask(hire, "d9-p1", p1, "P1")
        hire = self._ask(hire, "d9-p2", p2, "P2")
        answer = next(message for message in hire["messages"] if message.get("event_id") == "d9-p2" and message.get("kind") == "policy_answer")
        self.assertEqual(answer["body"], PASSAGES["P2"])
        self.assertEqual(answer["citation"], "P2")
        hire = self._ask(hire, "d9-remote", "Can I work remotely?", None)
        referral = next(message for message in hire["messages"] if message.get("event_id") == "d9-remote" and message.get("kind") == "policy_referral")
        self.assertEqual(referral["body"], "outside the pack")
        self.assertFalse(any(message.get("event_id") == "d9-remote" and message.get("kind") == "policy_answer" for message in hire["messages"]))
        unmatched = self._ask(hire, "d9-free", "What should I know before I start?", None)
        self.assertFalse(any(message.get("event_id") == "d9-free" and message.get("kind") == "policy_answer" for message in unmatched["messages"]))
        self.assertEqual((hire["plan_version"], self._task(hire, "Equipment readiness")["readiness"]), before)

    def test_wrong_sender_cannot_acknowledge_policy(self) -> None:
        hire = self._active_jordan("auth")
        hire = self._update(hire, "auth-sam", "actor-sam-ortiz", "hiring_manager", "policy_acknowledgment", "acknowledge")
        self.assertEqual(self._task(hire, "Policy acknowledgment")["execution_status"], "pending")
        self.assertEqual(hire["plan_version"], 2)

    def _active_jordan(self, prefix: str) -> dict:
        hire = self._intake(prefix, "Jordan Lee", "2026-03-02", "", "Sam Ortiz", "2026-02-27T09:00:00-06:00")
        hire = self._send(hire, f"{prefix}-role", "actor-sam-ortiz", "hiring_manager", "reply", "We hired a CSR")
        return self._send(
            hire,
            f"{prefix}-hr",
            "actor-alex-rivera",
            "hr_coordinator",
            "hr_decision",
            {"decision_type": "approve_held_plan", "rationale": "Approved.", "plan_version": 1},
        )

    def _intake(self, event_id, name, start, role, manager, occurred) -> dict:
        status, body = submit_event(
            self.store,
            {
                "event_id": event_id,
                "event_type": "intake",
                "actor_id": "actor-alex-rivera",
                "actor_role": "hr_coordinator",
                "occurred_at": occurred,
                "body": {
                    "employee_name": name,
                    "start_date": start,
                    "role": role,
                    "office": "Austin",
                    "manager_name": manager,
                },
            },
        )
        self.assertEqual(status, 202, body)
        return self.store.load_hire(body["hire_id"])

    def _send(self, hire, event_id, actor_id, actor_role, event_type, body) -> dict:
        status, response = submit_event(self.store, self._payload(hire, event_id, actor_id, actor_role, event_type, body))
        self.assertEqual(status, 202, response)
        if event_type == "reply":
            self.store.wait_for_event(event_id)
        return self.store.load_hire(hire["hire_id"])

    def _update(self, hire, event_id, actor_id, actor_role, task, action) -> dict:
        return self._send(
            hire,
            event_id,
            actor_id,
            actor_role,
            "task_update",
            {"task": task, "action": action},
        )

    def _ask(self, hire, event_id, question, citation):
        def answerer(_question, _passages):
            if citation is None:
                raise AssertionError("the model was called")
            return {"covered": True, "citations": [citation], "grounding": [PASSAGES[citation]]}

        status, response = submit_event(
            self.store,
            self._payload(hire, event_id, "actor-riley-chen", "new_hire", "policy_question", question),
            answerer=answerer,
        )
        self.assertEqual(status, 202, response)
        self.store.wait_for_event(event_id)
        return self.store.load_hire(hire["hire_id"])

    def _reply(self, hire, event_id, text, draft, actor=("actor-taylor-brooks", "it_fulfiller")) -> dict:
        status, response = submit_event(
            self.store,
            self._payload(hire, event_id, actor[0], actor[1], "reply", text),
            reader=lambda _event, _case: draft,
        )
        self.assertEqual(status, 202, response)
        self.store.wait_for_event(event_id)
        return self.store.load_hire(hire["hire_id"])

    def _payload(self, hire, event_id, actor_id, actor_role, event_type, body) -> dict:
        return {
            "event_id": event_id,
            "event_type": event_type,
            "hire_id": hire["hire_id"],
            "actor_id": actor_id,
            "actor_role": actor_role,
            "occurred_at": "2026-02-27T15:00:00-06:00",
            "body": body,
        }

    def _task(self, hire, name):
        return next(task for task in hire["tasks"] if task["name"] == name)

    def _possible(self, text):
        return {
            "claimed_fact": "possible",
            "uncertainty": True,
            "date_candidates": [],
            "statements": [{"device": "permitted_loaner", "posture": "possibility", "ready_date": None, "excerpt": text}],
        }

    def _commit(self, device, ready, text):
        return {
            "claimed_fact": "committed",
            "uncertainty": False,
            "date_candidates": [ready],
            "statements": [{"device": device, "posture": "explicit_commitment", "ready_date": ready, "excerpt": text}],
        }

    def _estimate(self, device, ready, text):
        return {
            "claimed_fact": "estimate",
            "uncertainty": True,
            "date_candidates": [ready],
            "statements": [{"device": device, "posture": "delivery_estimate", "ready_date": ready, "excerpt": text}],
        }

    def _denial(self, text):
        return {
            "claimed_fact": "none",
            "uncertainty": False,
            "date_candidates": [],
            "statements": [
                {"device": "assigned_laptop", "posture": "denial", "ready_date": None, "excerpt": text},
                {"device": "permitted_loaner", "posture": "denial", "ready_date": None, "excerpt": text},
            ],
        }

    def _revoke(self, text):
        return {
            "claimed_fact": "revoked",
            "uncertainty": False,
            "date_candidates": [],
            "statements": [{"device": "permitted_loaner", "posture": "revocation", "ready_date": None, "excerpt": text}],
        }

    def _boom(self, _event, _case):
        raise ProviderFailure("stand-in")
