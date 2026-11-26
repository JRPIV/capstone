"""Focused equipment-reply tests. The reader is a stand-in, not Gemini."""

import os
import tempfile
import threading
import unittest
from pathlib import Path

from onboarding.equipment import MODEL_FAILURE, ProviderFailure, follow_up_deadline
from onboarding.reply_crew import RETRY_LIMITS, render_description, reply_task_text
from onboarding.router import submit_event
from onboarding.server import load_runtime_env
from onboarding.store import CaseStore


RILEY_INTAKE = {
    "event_id": "evt-riley-intake",
    "event_type": "intake",
    "actor_id": "actor-alex-rivera",
    "actor_role": "hr_coordinator",
    "occurred_at": "2026-03-13T09:00:00-05:00",
    "body": {
        "employee_name": "Riley Chen",
        "start_date": "2026-03-16",
        "role": "Customer Support Representative",
        "office": "Austin",
        "manager_name": "Morgan Hale",
    },
}
UNCERTAIN = "The laptop slips to March 19. A spare might be free on start day."
LOANER = "A loaner will be ready on March 16."
DENIAL = "No loaner."
REVOKE = "The loaner commitment is revoked."


class EquipmentReplyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.store = CaseStore(Path(self._dir.name) / "case.sqlite")
        status, body = submit_event(self.store, RILEY_INTAKE)
        self.assertEqual(status, 202)
        self.hire_id = body["hire_id"]
        self.calls = 0

    def tearDown(self) -> None:
        self.store.close()
        self._dir.cleanup()

    def test_intake_still_creates_four_tasks(self) -> None:
        hire = self._hire()
        self.assertEqual(hire["plan_version"], 1)
        self.assertEqual(hire["readiness"], "needs_attention")
        self.assertEqual(len(hire["tasks"]), 4)
        self.assertEqual(hire["failure"], None)
        self.assertEqual(hire["events"][0]["state"], "complete")
        again, replay = submit_event(self.store, RILEY_INTAKE)
        self.assertEqual(again, 202)
        self.assertEqual(replay["hire_id"], self.hire_id)
        self.assertEqual(len(self._hire()["tasks"]), 4)

    def test_blank_role_intake_is_unchanged(self) -> None:
        store = CaseStore(Path(self._dir.name) / "blank.sqlite")
        payload = {
            "event_id": "evt-blank",
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
        status, _body = submit_event(store, payload)
        self.assertEqual(status, 202)
        hire = store.load_hire(_body["hire_id"])
        self.assertEqual(hire["tasks"], [])
        self.assertEqual(hire["messages"], ["Ask Sam Ortiz to confirm the role."])
        store.close()

    def test_first_uncertainty_requests_one_follow_up(self) -> None:
        self._reply("evt-uncertain", UNCERTAIN, self._uncertain_draft(True))
        hire = self._hire()
        equipment = self._equipment(hire)
        self.assertEqual(equipment["readiness"], "unconfirmed")
        self.assertFalse(equipment["escalated"])
        self.assertEqual(hire["plan_version"], 1)
        self.assertEqual(self._follow_ups(hire), 1)
        self.assertIn("cites P2", hire["messages"][1]["body"])
        self.assertIn("2026-03-13T17:00:00-05:00", hire["messages"][1]["body"])
        self.assertEqual(self.calls, 1)
        self.assertEqual(len(hire["tasks"]), 4)

    def test_false_certainty_does_not_confirm(self) -> None:
        draft = self._uncertain_draft(False)
        draft["statements"][0]["posture"] = "explicit_commitment"
        self._reply("evt-false", UNCERTAIN, draft)
        equipment = self._equipment(self._hire())
        self.assertEqual(equipment["readiness"], "unconfirmed")
        self.assertEqual(equipment["evidence_refs"], [])
        self.assertEqual(self._hire()["plan_version"], 1)

    def test_second_uncertainty_escalates_without_a_second_follow_up(self) -> None:
        self._reply("evt-first", UNCERTAIN, self._uncertain_draft(True))
        later = "A spare might still be free next week."
        draft = {
            "claimed_fact": "still possible",
            "uncertainty": True,
            "date_candidates": [],
            "statements": [
                {
                    "device": "permitted_loaner",
                    "posture": "possibility",
                    "ready_date": None,
                    "excerpt": later,
                }
            ],
        }
        self._reply("evt-second", later, draft)
        hire = self._hire()
        equipment = self._equipment(hire)
        self.assertEqual(equipment["readiness"], "unconfirmed")
        self.assertTrue(equipment["escalated"])
        self.assertEqual(self._follow_ups(hire), 1)
        self.assertEqual(hire["plan_version"], 2)
        self.assertEqual(self.calls, 2)

    def test_contextual_denial_blocks_without_another_follow_up(self) -> None:
        self._reply("evt-estimate", UNCERTAIN, self._uncertain_draft(True))
        draft = {
            "claimed_fact": "no loaner",
            "uncertainty": False,
            "date_candidates": [],
            "statements": [
                {
                    "device": "permitted_loaner",
                    "posture": "denial",
                    "ready_date": None,
                    "excerpt": DENIAL,
                }
            ],
        }
        self._reply("evt-denial", DENIAL, draft)
        hire = self._hire()
        equipment = self._equipment(hire)
        self.assertEqual(equipment["readiness"], "blocked")
        self.assertTrue(equipment["escalated"])
        self.assertEqual(self._follow_ups(hire), 1)
        self.assertEqual(hire["plan_version"], 2)
        self.assertIn("No permitted device is available by the start date.", hire["readiness_reasons"])

    def test_no_loaner_without_a_missed_laptop_does_not_block(self) -> None:
        draft = {
            "claimed_fact": "no loaner",
            "uncertainty": False,
            "date_candidates": [],
            "statements": [
                {
                    "device": "permitted_loaner",
                    "posture": "denial",
                    "ready_date": None,
                    "excerpt": DENIAL,
                }
            ],
        }
        self._reply("evt-loaner-only", DENIAL, draft)
        equipment = self._equipment(self._hire())
        self.assertEqual(equipment["readiness"], "unconfirmed")
        self.assertFalse(equipment["escalated"])
        self.assertEqual(self._follow_ups(self._hire()), 1)

    def test_valid_confirmation_ignores_the_uncertainty_flag(self) -> None:
        draft = {
            "claimed_fact": "loaner ready",
            "uncertainty": True,
            "date_candidates": ["2026-03-16"],
            "statements": [
                {
                    "device": "permitted_loaner",
                    "posture": "explicit_commitment",
                    "ready_date": "2026-03-16",
                    "excerpt": LOANER,
                }
            ],
        }
        self._reply("evt-yes", LOANER, draft)
        hire = self._hire()
        equipment = self._equipment(hire)
        self.assertEqual(equipment["readiness"], "confirmed")
        self.assertEqual(equipment["evidence_refs"], ["evt-yes"])
        self.assertEqual(self._follow_ups(hire), 0)
        self.assertEqual(hire["plan_version"], 2)
        self.assertEqual(hire["readiness"], "needs_attention")
        self.assertNotIn("Equipment is not confirmed.", hire["readiness_reasons"])

    def test_revocation_and_estimate_do_not_invent_readiness(self) -> None:
        self.test_valid_confirmation_ignores_the_uncertainty_flag()
        estimate = "The laptop slips to March 19."
        draft = {
            "claimed_fact": "laptop later",
            "uncertainty": False,
            "date_candidates": ["2026-03-19"],
            "statements": [
                {
                    "device": "assigned_laptop",
                    "posture": "delivery_estimate",
                    "ready_date": "2026-03-19",
                    "excerpt": estimate,
                }
            ],
        }
        self._reply("evt-estimate-later", estimate, draft)
        self.assertEqual(self._equipment(self._hire())["readiness"], "confirmed")
        self.assertEqual(self._hire()["plan_version"], 2)
        revoke = {
            "claimed_fact": "revoked",
            "uncertainty": False,
            "date_candidates": [],
            "statements": [
                {
                    "device": "permitted_loaner",
                    "posture": "revocation",
                    "ready_date": None,
                    "excerpt": REVOKE,
                }
            ],
        }
        self._reply("evt-revoke", REVOKE, revoke)
        hire = self._hire()
        self.assertEqual(self._equipment(hire)["readiness"], "blocked")
        self.assertTrue(self._equipment(hire)["escalated"])
        self.assertEqual(hire["plan_version"], 3)
        self.assertGreaterEqual(len(hire["decisions"]), 2)

    def test_revocation_with_no_other_device_returns_to_unconfirmed(self) -> None:
        self.test_valid_confirmation_ignores_the_uncertainty_flag()
        revoke = {
            "claimed_fact": "revoked",
            "uncertainty": False,
            "date_candidates": [],
            "statements": [
                {
                    "device": "permitted_loaner",
                    "posture": "revocation",
                    "ready_date": None,
                    "excerpt": REVOKE,
                }
            ],
        }
        self._reply("evt-revoke-only", REVOKE, revoke)
        hire = self._hire()
        self.assertEqual(self._equipment(hire)["readiness"], "unconfirmed")
        self.assertFalse(self._equipment(hire)["escalated"])
        self.assertEqual(hire["plan_version"], 3)

    def test_unauthorized_sender_does_not_call_the_model(self) -> None:
        mismatch = self._reply_payload("evt-mismatch", UNCERTAIN)
        mismatch["actor_role"] = "hr_coordinator"
        status, body = submit_event(self.store, mismatch, reader=self._boom)
        self.assertEqual(status, 400)
        self.assertEqual(body["code"], "unsupported")
        self.assertEqual(self.calls, 0)
        other = self._reply_payload("evt-hr", UNCERTAIN)
        other["actor_id"] = "actor-alex-rivera"
        other["actor_role"] = "hr_coordinator"
        status, body = submit_event(self.store, other, reader=self._boom)
        self.assertEqual(status, 202)
        self.store.wait_for_event("evt-hr")
        hire = self._hire()
        self.assertEqual(self._equipment(hire)["readiness"], "unconfirmed")
        self.assertEqual(hire["decisions"][-1]["rule_result"], "sender_cannot_establish_equipment")
        self.assertEqual(self._follow_ups(hire), 0)
        self.assertEqual(self.calls, 0)

    def test_duplicate_event_and_event_mismatch(self) -> None:
        payload = self._reply_payload("evt-once", UNCERTAIN)
        self._reply("evt-once", UNCERTAIN, self._uncertain_draft(True))
        before = self._hire()
        status, replay = submit_event(self.store, payload, reader=self._counting(self._uncertain_draft(True)))
        self.assertEqual(status, 202)
        self.assertEqual(replay["status"], "processing")
        self.assertEqual(self.calls, 1)
        self.assertEqual(self._follow_ups(self._hire()), 1)
        changed = self._reply_payload("evt-once", "A different sentence.")
        status, body = submit_event(self.store, changed, reader=self._boom)
        self.assertEqual(status, 400)
        self.assertEqual(body["code"], "event_mismatch")
        self.assertEqual(self._hire()["tasks"], before["tasks"])
        self.assertEqual(self.calls, 1)

    def test_deadline_boundaries(self) -> None:
        self.assertEqual(follow_up_deadline("2026-03-13T16:59:00-05:00"), "2026-03-13T17:00:00-05:00")
        self.assertEqual(follow_up_deadline("2026-03-13T17:00:00-05:00"), "2026-03-16T17:00:00-05:00")
        self.assertEqual(follow_up_deadline("2026-03-14T10:00:00-05:00"), "2026-03-16T17:00:00-05:00")
        self.assertEqual(follow_up_deadline("2026-03-15T12:00:00-05:00"), "2026-03-16T17:00:00-05:00")

    def test_invalid_draft_and_provider_failure_keep_the_case(self) -> None:
        before = self._hire()
        bad = {
            "claimed_fact": "ready",
            "uncertainty": False,
            "date_candidates": ["2026-03-16"],
            "statements": [
                {
                    "device": "permitted_loaner",
                    "posture": "explicit_commitment",
                    "ready_date": "2026-03-16",
                    "excerpt": "this excerpt was not in the message",
                }
            ],
        }
        self._reply("evt-bad", UNCERTAIN, bad)
        failed = self._event(self._hire(), "evt-bad")
        self.assertEqual(failed["state"], "failed")
        self.assertEqual(failed["failure"]["code"], "model_failure")
        self.assertEqual(failed["failure"]["message"], MODEL_FAILURE)
        hire = self._hire()
        self.assertEqual(hire["tasks"], before["tasks"])
        self.assertEqual(hire["plan_version"], 1)
        self.assertEqual(hire["failure"]["code"], "model_failure")
        self.assertFalse(hire["messages"][-1]["verified"])
        self.assertEqual(hire["messages"][-1]["body"], UNCERTAIN)
        self.assertEqual(self._follow_ups(hire), 0)

        def explode(_event, _case):
            self.calls += 1
            raise ProviderFailure("down")

        payload = self._reply_payload("evt-down", UNCERTAIN)
        status, _ack = submit_event(self.store, payload, reader=explode)
        self.assertEqual(status, 202)
        self.store.wait_for_event("evt-down")
        down = self._event(self._hire(), "evt-down")
        self.assertEqual(down["state"], "failed")
        self.assertEqual(down["failure"]["code"], "model_failure")
        self.assertEqual(self._hire()["tasks"], before["tasks"])
        self.assertEqual(self.calls, 2)

    def test_a_recorded_failure_is_read_again(self) -> None:
        payload = self._reply_payload("evt-retry-fail", UNCERTAIN)

        def explode(_event, _case):
            self.calls += 1
            raise ProviderFailure("down")

        status, _ack = submit_event(self.store, payload, reader=explode)
        self.assertEqual(status, 202)
        self.store.wait_for_event("evt-retry-fail")
        self.assertEqual(self._event(self._hire(), "evt-retry-fail")["state"], "failed")
        self.assertEqual(self.calls, 1)
        self._reply("evt-retry-fail", UNCERTAIN, self._uncertain_draft(True))
        finished = self._event(self._hire(), "evt-retry-fail")
        self.assertEqual(finished["state"], "complete")
        self.assertEqual(finished["failure"], None)
        self.assertEqual(self.calls, 2)
        self.assertEqual(self._follow_ups(self._hire()), 1)
        self._reply("evt-retry-done", UNCERTAIN, self._uncertain_draft(True))
        calls_after_commit = self.calls
        done = self._reply_payload("evt-retry-done", UNCERTAIN)
        status, replay = submit_event(self.store, done, reader=self._counting(self._uncertain_draft(True)))
        self.assertEqual(status, 202)
        self.assertEqual(self.calls, calls_after_commit)
        self.assertEqual(self._event(self._hire(), "evt-retry-done")["state"], "complete")
        self.assertEqual(replay["event_id"], "evt-retry-done")

    def test_reply_prompt_keeps_the_message_after_the_instructions(self) -> None:
        text = render_description(
            {"body": "Test {start_date}", "occurred_at": "2026-03-13T09:00:00-05:00", "actor_role": "it_fulfiller"},
            {"start_date": "2026-03-16"},
        )
        self.assertLess(text.index("Return JSON only"), text.index("MESSAGE_START"))
        self.assertIn("MESSAGE_START\nTest {start_date}\nMESSAGE_END", text)
        self.assertIn("Start date: 2026-03-16", text)
        _description, expected = reply_task_text(
            {"body": "Test", "occurred_at": "2026-03-13T09:00:00-05:00", "actor_role": "it_fulfiller"},
            {"start_date": "2026-03-16"},
        )
        self.assertIn("claimed_fact", expected)

    def test_event_completion_is_visible_without_claiming_the_intake_tasks(self) -> None:
        started = threading.Event()
        release = threading.Event()

        def reader(_event, _case):
            self.calls += 1
            started.set()
            self.assertTrue(release.wait(2))
            return self._uncertain_draft(True)

        payload = self._reply_payload("evt-slow", UNCERTAIN)
        status, ack = submit_event(self.store, payload, reader=reader)
        self.assertEqual(status, 202)
        self.assertEqual(ack["status"], "processing")
        self.assertTrue(started.wait(2))
        during = self._hire()
        current = self._event(during, "evt-slow")
        self.assertEqual(current["state"], "processing")
        self.assertEqual(current["failure"], None)
        self.assertEqual(len(during["tasks"]), 4)
        self.assertEqual(during["tasks"][0]["name"], "Policy acknowledgment")
        release.set()
        self.assertEqual(self.store.wait_for_event("evt-slow"), "committed")
        done = self._hire()
        finished = self._event(done, "evt-slow")
        self.assertEqual(finished["state"], "complete")
        self.assertEqual(finished["failure"], None)
        self.assertEqual(done["failure"], None)
        self.assertEqual(len(done["tasks"]), 4)
        self.assertEqual(done["decisions"][-1]["event_id"], "evt-slow")
        self.assertEqual(self.calls, 1)

    def test_a_second_event_while_one_is_running_conflicts(self) -> None:
        started = threading.Event()
        release = threading.Event()

        def reader(_event, _case):
            self.calls += 1
            started.set()
            self.assertTrue(release.wait(2))
            return self._uncertain_draft(True)

        first = self._reply_payload("evt-hold", UNCERTAIN)
        submit_event(self.store, first, reader=reader)
        self.assertTrue(started.wait(2))
        other = self._reply_payload("evt-other", DENIAL)
        status, body = submit_event(self.store, other, reader=self._boom)
        self.assertEqual(status, 409)
        self.assertEqual(body["code"], "conflict")
        self.assertIn("evt-hold", body["message"])
        self.assertIn("evt-other", body["message"])
        release.set()
        self.store.wait_for_event("evt-hold")
        self.assertEqual(self.calls, 1)

    def test_retry_limits_do_not_add_a_second_application_call(self) -> None:
        self.assertEqual(RETRY_LIMITS["application_attempts"], 1)
        self.assertEqual(RETRY_LIMITS["llm_max_retries"], 0)
        self.assertEqual(RETRY_LIMITS["max_retry_limit"], 0)
        self.assertEqual(RETRY_LIMITS["max_iter"], 2)
        self._reply("evt-once-limit", UNCERTAIN, self._uncertain_draft(True))
        self.assertEqual(self.calls, 1)

    def _reply(self, event_id: str, body: str, draft: dict) -> None:
        payload = self._reply_payload(event_id, body)
        status, _ack = submit_event(self.store, payload, reader=self._counting(draft))
        self.assertEqual(status, 202, _ack)
        self.store.wait_for_event(event_id)

    def _counting(self, draft: dict):
        def reader(_event, _case):
            self.calls += 1
            return draft

        return reader

    def test_intake_without_key_and_missing_key_reply_failure(self) -> None:
        previous = os.environ.pop("GEMINI_API_KEY", None)
        try:
            intake = dict(RILEY_INTAKE)
            intake["event_id"] = "evt-no-key-intake"
            status, body = submit_event(self.store, intake)
            self.assertEqual(status, 202)
            hire = self.store.load_hire(body["hire_id"])
            self.assertIsNotNone(hire)
            self.assertEqual(len(hire["tasks"]), 4)
            self.assertEqual(hire["plan_version"], 1)
            payload = self._reply_payload("evt-no-key-reply", UNCERTAIN)
            payload["hire_id"] = body["hire_id"]
            status, ack = submit_event(self.store, payload)
            self.assertEqual(status, 202)
            self.assertEqual(ack["status"], "processing")
            self.store.wait_for_event("evt-no-key-reply")
            after = self.store.load_hire(body["hire_id"])
            failed = self._event(after, "evt-no-key-reply")
            self.assertEqual(failed["state"], "failed")
            self.assertEqual(failed["failure"]["code"], "model_failure")
            self.assertEqual(failed["failure"]["message"], MODEL_FAILURE)
            self.assertEqual(after["tasks"], hire["tasks"])
            self.assertEqual(after["plan_version"], 1)
            self.assertEqual(after["failure"]["code"], "model_failure")
            self.assertFalse(after["messages"][-1]["verified"])
            self.assertEqual(after["messages"][-1]["body"], UNCERTAIN)
            self.assertEqual(self._follow_ups(after), 0)
        finally:
            if previous is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = previous

    def test_runtime_env_does_not_override(self) -> None:
        previous = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "preset-not-a-secret"
        try:
            load_runtime_env()
            self.assertEqual(os.environ.get("GEMINI_API_KEY"), "preset-not-a-secret")
        finally:
            if previous is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = previous

    def _boom(self, _event, _case):
        self.calls += 1
        raise AssertionError("the model must not be called")

    def _reply_payload(self, event_id: str, body: str) -> dict:
        return {
            "event_id": event_id,
            "event_type": "reply",
            "hire_id": self.hire_id,
            "actor_id": "actor-taylor-brooks",
            "actor_role": "it_fulfiller",
            "occurred_at": "2026-03-13T15:00:00-05:00",
            "body": body,
        }

    def _uncertain_draft(self, uncertainty: bool) -> dict:
        return {
            "claimed_fact": "March 19 laptop and a possible spare",
            "uncertainty": uncertainty,
            "date_candidates": ["2026-03-19"],
            "statements": [
                {
                    "device": "assigned_laptop",
                    "posture": "delivery_estimate",
                    "ready_date": "2026-03-19",
                    "excerpt": "The laptop slips to March 19.",
                },
                {
                    "device": "permitted_loaner",
                    "posture": "possibility",
                    "ready_date": None,
                    "excerpt": "A spare might be free on start day.",
                },
            ],
        }

    def _hire(self) -> dict:
        hire = self.store.load_hire(self.hire_id)
        self.assertIsNotNone(hire)
        return hire

    def _equipment(self, hire: dict) -> dict:
        for task in hire["tasks"]:
            if task["name"] == "Equipment readiness":
                return task
        self.fail("equipment task missing")

    def _follow_ups(self, hire: dict) -> int:
        return sum(1 for message in hire["messages"] if isinstance(message, dict) and message.get("kind") == "follow_up")

    def _event(self, hire: dict, event_id: str) -> dict:
        for event in hire["events"]:
            if event["event_id"] == event_id:
                return event
        self.fail(event_id)


if __name__ == "__main__":
    unittest.main()
