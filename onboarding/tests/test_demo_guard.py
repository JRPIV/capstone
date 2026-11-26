"""Shared-demo token and model budget. No provider call."""

import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

from onboarding import server
from onboarding.demo_guard import ModelBudget, budget, token_ok
from onboarding.router import submit_event
from onboarding.store import CaseStore


INTAKE = {
    "event_id": "demo-intake",
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


class DemoGuardTests(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("DEMO_ACCESS_TOKEN", None)
        os.environ.pop("DEMO_MODEL_CALLS_PER_HOUR", None)
        budget.clear()

    def test_local_run_without_a_token_stays_open(self) -> None:
        os.environ.pop("DEMO_ACCESS_TOKEN", None)
        self.assertTrue(token_ok(None))
        gate = ModelBudget()
        self.assertTrue(gate.allow())

    def test_shared_host_rejects_a_missing_token_and_stops_at_the_hourly_limit(self) -> None:
        os.environ["DEMO_ACCESS_TOKEN"] = "gate-test"
        os.environ["DEMO_MODEL_CALLS_PER_HOUR"] = "1"
        self.assertFalse(token_ok(None))
        self.assertFalse(token_ok("wrong"))
        self.assertTrue(token_ok("gate-test"))
        gate = ModelBudget()
        self.assertTrue(gate.allow())
        self.assertFalse(gate.allow())

    def test_http_lock_blocks_a_write_until_the_token_is_sent(self) -> None:
        os.environ["DEMO_ACCESS_TOKEN"] = "gate-test"
        with TemporaryDirectory() as directory:
            store = CaseStore(Path(directory) / "case.sqlite")
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), server._handler(store))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            port = httpd.server_address[1]
            try:
                health = _json("GET", f"http://127.0.0.1:{port}/health")
                self.assertEqual(health["status"], "ok")
                self.assertTrue(health["demo_lock"])
                denied = _status("POST", f"http://127.0.0.1:{port}/events", INTAKE)
                self.assertEqual(denied, 401)
                accepted = _status(
                    "POST",
                    f"http://127.0.0.1:{port}/events",
                    INTAKE,
                    {"X-Demo-Token": "gate-test"},
                )
                self.assertEqual(accepted, 202)
            finally:
                httpd.shutdown()
                store.close()

    def test_model_limit_returns_before_a_provider_call(self) -> None:
        os.environ["DEMO_ACCESS_TOKEN"] = "gate-test"
        os.environ["DEMO_MODEL_CALLS_PER_HOUR"] = "0"
        with TemporaryDirectory() as directory:
            store = CaseStore(Path(directory) / "case.sqlite")
            status, body = submit_event(store, INTAKE)
            self.assertEqual(status, 202, body)
            question = {
                "event_id": "demo-policy",
                "event_type": "policy_question",
                "hire_id": body["hire_id"],
                "actor_id": "actor-riley-chen",
                "actor_role": "new_hire",
                "occurred_at": "2026-03-13T15:00:00-05:00",
                "body": "Can IT provide an approved loaner by the start date?",
            }
            status, limited = submit_event(store, question)
            self.assertEqual(status, 429, limited)
            self.assertEqual(limited["code"], "demo_limit")
            store.close()


def _json(method: str, url: str) -> dict:
    request = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def _status(method: str, url: str, payload: dict, headers: dict | None = None) -> int:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    for name, value in (headers or {}).items():
        request.add_header(name, value)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code
