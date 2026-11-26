"""Python chooses the path. The model does not choose the next step."""

import json
import threading

from onboarding.case_summary import case_summary
from onboarding.demo_guard import allow_model_call
from onboarding.equipment import (
    MODEL_FAILURE,
    ProviderFailure,
    apply_reply,
    keep_message,
)
from onboarding.plan import (
    TASK_ACTIONS,
    apply_deadline,
    apply_hr_decision,
    apply_role_reply,
    apply_start_change,
    apply_task_update,
)
from onboarding.policy import settle
from onboarding.policy_pack import PASSAGES, detect
from onboarding.rules import assess_intake
from onboarding.simulator import find_identity, is_equipment_owner
from onboarding.store import CaseStore


ROLES = {"hr_coordinator", "hiring_manager", "it_fulfiller", "new_hire"}
UNREADABLE_MESSAGE = "The intake could not be read, so no plan was written."
REPLY_UNREADABLE = "The reply could not be read. No verified fact was changed."
POLICY_UNREADABLE = "The policy question could not be read. No policy conclusion was written."
UNSUPPORTED_SENDER = "This sender is not a configured simulator identity."


def submit_event(store: CaseStore, payload: object, reader=None, answerer=None) -> tuple[int, dict]:
    if not isinstance(payload, dict):
        return 400, {"code": "unreadable_input", "message": UNREADABLE_MESSAGE}
    event_type = payload.get("event_type")
    event_id = payload.get("event_id")
    if event_type == "reply":
        return _submit_reply(store, payload, reader)
    if event_type == "policy_question":
        return _submit_policy(store, payload, answerer)
    if event_type == "hr_decision":
        return _submit_hr(store, payload)
    if event_type == "start_date_change":
        return _submit_start(store, payload)
    if event_type == "deadline_reached":
        return _submit_deadline(store, payload)
    if event_type == "task_update":
        return _submit_task(store, payload)
    if event_type != "intake":
        return _unreadable(event_id, UNREADABLE_MESSAGE)
    if not isinstance(event_id, str) or not event_id.strip():
        return _unreadable(None, UNREADABLE_MESSAGE)

    event = _intake_event(payload, event_id.strip())
    attempt = store.begin_attempt(event)
    if attempt["action"] == "reply":
        return attempt["status"], attempt["body"]
    try:
        outcome = assess_intake(event)
        finished = store.finish_attempt(event, outcome)
    except Exception:
        store.abort_attempt(event["event_id"])
        raise
    return finished["status"], finished["body"]


def read_hire(store: CaseStore, hire_id: str) -> tuple[int, dict]:
    hire = store.load_hire(hire_id)
    if hire is None:
        return 404, {"message": "No hire is stored for this id.", "hire_id": hire_id}
    shown = dict(hire)
    shown["case_summary"] = case_summary(shown)
    return 200, shown


def health(store: CaseStore) -> tuple[int, dict]:
    if store.ping():
        return 200, {"status": "ok"}
    return 503, {"status": "unavailable"}


def _submit_reply(store: CaseStore, payload: dict, reader) -> tuple[int, dict]:
    event_id = payload.get("event_id")
    checked = _reply_event(payload)
    if checked is None:
        return _unreadable(event_id, REPLY_UNREADABLE)
    event, hire_id = checked
    if store.load_hire(hire_id) is None:
        body = {
            "message": "No hire is stored for this id.",
            "event_id": event["event_id"],
            "hire_id": hire_id,
        }
        return 404, body
    person = find_identity(event["actor_id"], event["actor_role"])
    if person is None:
        return 400, {
            "code": "unsupported",
            "message": UNSUPPORTED_SENDER,
            "event_id": event["event_id"],
            "hire_id": hire_id,
        }
    attempt = store.begin_attempt(event)
    if attempt["action"] == "reply":
        return attempt["status"], attempt["body"]
    context = store.reply_context(hire_id)
    if context.get("activation") == "held":
        store.finish_reply(event["event_id"], apply_role_reply(context, event))
        return 202, {"event_id": event["event_id"], "hire_id": hire_id, "status": "processing"}
    if not is_equipment_owner(person):
        store.finish_reply(
            event["event_id"],
            keep_message(event, "sender_cannot_establish_equipment", context["plan_version"]),
        )
        return 202, {"event_id": event["event_id"], "hire_id": hire_id, "status": "processing"}
    if reader is None and not allow_model_call():
        store.abort_attempt(event["event_id"])
        return 429, _limited(event)
    chosen = reader if reader is not None else _crew_reader
    threading.Thread(
        target=_read_and_commit,
        args=(store, event, context, chosen),
        daemon=True,
    ).start()
    return 202, {"event_id": event["event_id"], "hire_id": hire_id, "status": "processing"}


def _read_and_commit(store: CaseStore, event: dict, context: dict, reader) -> None:
    try:
        draft = reader(event, context)
        outcome = apply_reply(context, event, draft)
    except ProviderFailure:
        outcome = None
    except Exception:
        outcome = None
    if outcome is None or not outcome["ok"]:
        failure = {"code": "model_failure", "message": MODEL_FAILURE}
        message = {
            "event_id": event["event_id"],
            "kind": "reply",
            "body": event["body"],
            "actor_id": event["actor_id"],
            "verified": False,
        }
        if outcome is not None and not outcome["ok"]:
            message = outcome["message"]
        store.fail_reply(event["event_id"], failure, message)
        return
    store.finish_reply(event["event_id"], outcome)


def _submit_policy(store: CaseStore, payload: dict, answerer) -> tuple[int, dict]:
    event_id = payload.get("event_id")
    checked = _tracked_event(payload, "policy_question")
    if checked is None:
        return _unreadable(event_id, POLICY_UNREADABLE)
    event, hire_id = checked
    if store.load_hire(hire_id) is None:
        return 404, {
            "message": "No hire is stored for this id.",
            "event_id": event["event_id"],
            "hire_id": hire_id,
        }
    if find_identity(event["actor_id"], event["actor_role"]) is None:
        return 400, {
            "code": "unsupported",
            "message": UNSUPPORTED_SENDER,
            "event_id": event["event_id"],
            "hire_id": hire_id,
        }
    attempt = store.begin_attempt(event)
    if attempt["action"] == "reply":
        return attempt["status"], attempt["body"]
    hire = store.load_hire(hire_id)
    classification = detect(event["body"])
    if not classification["call_model"]:
        store.finish_reply(event["event_id"], settle(event, hire["plan_version"]))
        return 202, {"event_id": event["event_id"], "hire_id": hire_id, "status": "processing"}
    if answerer is None and not allow_model_call():
        store.abort_attempt(event["event_id"])
        return 429, _limited(event)
    chosen = answerer if answerer is not None else _crew_answerer
    passages = [{"id": passage_id, "text": PASSAGES[passage_id]} for passage_id in classification["candidates"]]
    threading.Thread(
        target=_answer_and_commit,
        args=(store, event, hire["plan_version"], passages, chosen),
        daemon=True,
    ).start()
    return 202, {"event_id": event["event_id"], "hire_id": hire_id, "status": "processing"}


def _answer_and_commit(store: CaseStore, event: dict, plan_version: int | None, passages: list, answerer) -> None:
    from onboarding.policy import POLICY_MODEL_FAILURE

    try:
        proposal = answerer(event["body"], passages)
        outcome = settle(event, plan_version, proposal)
    except ProviderFailure:
        outcome = None
    except Exception:
        outcome = None
    if outcome is None or not outcome["ok"]:
        failure = {"code": "model_failure", "message": POLICY_MODEL_FAILURE}
        message = {
            "event_id": event["event_id"],
            "kind": "policy_question",
            "body": event["body"],
            "actor_id": event["actor_id"],
            "verified": False,
        }
        if outcome is not None and not outcome["ok"]:
            message = outcome["message"]
            failure = outcome["failure"]
        store.fail_reply(event["event_id"], failure, message)
        return
    store.finish_reply(event["event_id"], outcome)


def _submit_hr(store: CaseStore, payload: dict) -> tuple[int, dict]:
    event_id = payload.get("event_id")
    checked = _decision_event(payload)
    if checked is None:
        return _unreadable(event_id, "The HR decision could not be read. No plan was changed.")
    event, hire_id = checked
    hire = store.reply_context(hire_id)
    if hire is None:
        return 404, {"message": "No hire is stored for this id.", "event_id": event["event_id"], "hire_id": hire_id}
    if event["actor_id"] != "actor-alex-rivera" or event["actor_role"] != "hr_coordinator":
        return _unsupported(event, "Only the HR coordinator can record this decision.")
    body = event["body"]
    if body["plan_version"] != hire["plan_version"]:
        return _unsupported(event, "The plan version does not match the current case.")
    if body["decision_type"] == "approve_held_plan" and hire.get("activation") != "proposed":
        return _unsupported(event, "There is no proposed plan to approve.")
    if body["decision_type"] == "escalation_disposition" and hire.get("activation") not in {"active", "proposed"}:
        return _unsupported(event, "There is no plan for this disposition.")
    return _reserve_and_finish(store, event, apply_hr_decision(hire, event))


def _submit_start(store: CaseStore, payload: dict) -> tuple[int, dict]:
    event_id = payload.get("event_id")
    checked = _tracked_event(payload, "start_date_change")
    if checked is None:
        return _unreadable(event_id, "The start date could not be read. No plan was changed.")
    event, hire_id = checked
    try:
        from datetime import date

        date.fromisoformat(event["body"])
    except ValueError:
        return _unreadable(event["event_id"], "The start date could not be read. No plan was changed.")
    hire = store.reply_context(hire_id)
    if hire is None:
        return 404, {"message": "No hire is stored for this id.", "event_id": event["event_id"], "hire_id": hire_id}
    if event["actor_id"] != "actor-alex-rivera" or event["actor_role"] != "hr_coordinator":
        return _unsupported(event, "Only the HR coordinator can change the start date.")
    if hire.get("activation") != "active":
        return _unsupported(event, "The plan is not active.")
    return _reserve_and_finish(store, event, apply_start_change(hire, event))


def _submit_task(store: CaseStore, payload: dict) -> tuple[int, dict]:
    event_id = payload.get("event_id")
    checked = _task_event(payload)
    if checked is None:
        return _unreadable(event_id, "The task update could not be read. No task was changed.")
    event, hire_id = checked
    hire = store.reply_context(hire_id)
    if hire is None:
        return 404, {"message": "No hire is stored for this id.", "event_id": event["event_id"], "hire_id": hire_id}
    return _reserve_and_finish(store, event, apply_task_update(hire, event))


def _task_event(payload: dict) -> tuple[dict, str] | None:
    body = payload.get("body")
    if not isinstance(body, dict):
        return None
    task = body.get("task")
    action = body.get("action")
    if task not in TASK_ACTIONS or action not in TASK_ACTIONS[task]:
        return None
    cloned = dict(payload)
    cloned["body"] = {"task": task, "action": action}
    return _tracked_event(cloned, "task_update")


def _submit_deadline(store: CaseStore, payload: dict) -> tuple[int, dict]:
    event_id = payload.get("event_id")
    checked = _tracked_event(payload, "deadline_reached", allow_empty=True)
    if checked is None:
        return _unreadable(event_id, "The deadline event could not be read. No plan was changed.")
    event, hire_id = checked
    hire = store.reply_context(hire_id)
    if hire is None:
        return 404, {"message": "No hire is stored for this id.", "event_id": event["event_id"], "hire_id": hire_id}
    return _reserve_and_finish(store, event, apply_deadline(hire, event))


def _reserve_and_finish(store: CaseStore, event: dict, outcome: dict) -> tuple[int, dict]:
    attempt = store.begin_attempt(event)
    if attempt["action"] == "reply":
        return attempt["status"], attempt["body"]
    store.finish_reply(event["event_id"], outcome)
    return 202, {"event_id": event["event_id"], "hire_id": event["hire_id"], "status": "processing"}


def _limited(event: dict) -> dict:
    return {
        "code": "demo_limit",
        "message": "The demonstration has reached its model-call limit for this hour. No model call was made.",
        "event_id": event["event_id"],
        "hire_id": event["hire_id"],
    }


def _unsupported(event: dict, message: str) -> tuple[int, dict]:
    return 400, {
        "code": "unsupported",
        "message": message,
        "event_id": event["event_id"],
        "hire_id": event["hire_id"],
    }


def _crew_reader(event: dict, context: dict) -> dict:
    from onboarding.reply_crew import read_equipment_reply

    return read_equipment_reply(event, context)


def _crew_answerer(question: str, passages: list) -> dict:
    from onboarding.policy_crew import answer_policy_question

    return answer_policy_question(question, passages)


def _reply_event(payload: dict) -> tuple[dict, str] | None:
    return _tracked_event(payload, "reply")


def _decision_event(payload: dict) -> tuple[dict, str] | None:
    body = payload.get("body")
    if not isinstance(body, dict):
        return None
    decision_type = body.get("decision_type")
    rationale = body.get("rationale")
    plan_version = body.get("plan_version")
    if decision_type not in {"approve_held_plan", "escalation_disposition"}:
        return None
    if not isinstance(rationale, str) or not rationale.strip():
        return None
    if not isinstance(plan_version, int):
        return None
    recorded_body = {
        "decision_type": decision_type,
        "rationale": rationale.strip(),
        "plan_version": plan_version,
    }
    cloned = dict(payload)
    cloned["body"] = recorded_body
    return _tracked_event(cloned, "hr_decision")


def _tracked_event(payload: dict, event_type: str, allow_empty: bool = False) -> tuple[dict, str] | None:
    event_id = payload.get("event_id")
    hire_id = payload.get("hire_id")
    actor_id = payload.get("actor_id")
    actor_role = payload.get("actor_role")
    occurred_at = payload.get("occurred_at")
    body = payload.get("body")
    if not isinstance(event_id, str) or not event_id.strip():
        return None
    if not isinstance(hire_id, str) or not hire_id.strip():
        return None
    if not isinstance(actor_id, str) or not actor_id.strip():
        return None
    if actor_role not in ROLES:
        return None
    if not isinstance(occurred_at, str) or not occurred_at.strip():
        return None
    try:
        from onboarding.equipment import _parse_time

        _parse_time(occurred_at)
    except ValueError:
        return None
    if isinstance(body, dict):
        normalized_body = body
    elif isinstance(body, str) and (body.strip() or allow_empty):
        normalized_body = body.strip()
    else:
        return None
    event_id = event_id.strip()
    hire_id = hire_id.strip()
    actor_id = actor_id.strip()
    occurred_at = occurred_at.strip()
    body = normalized_body
    recorded = {
        "event_type": event_type,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "occurred_at": occurred_at,
        "body": body,
        "hire_id": hire_id,
    }
    event = {
        "event_id": event_id,
        "event_type": event_type,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "occurred_at": occurred_at,
        "hire_id": hire_id,
        "body": body,
        "body_json": json.dumps(body),
        "contents_key": json.dumps(recorded, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
    }
    return event, hire_id


def _intake_event(payload: dict, event_id: str) -> dict:
    body = payload.get("body")
    actor_id = payload.get("actor_id")
    actor_role = payload.get("actor_role")
    occurred_at = payload.get("occurred_at")
    recorded = {
        "event_type": "intake",
        "actor_id": actor_id.strip() if isinstance(actor_id, str) else actor_id,
        "actor_role": actor_role,
        "occurred_at": occurred_at.strip() if isinstance(occurred_at, str) else occurred_at,
        "body": _normalize(body),
    }
    return {
        "event_id": event_id,
        "event_type": "intake",
        "actor_id": actor_id if isinstance(actor_id, str) else "",
        "actor_role": actor_role if isinstance(actor_role, str) else "",
        "occurred_at": occurred_at if isinstance(occurred_at, str) else "",
        "body": body,
        "body_json": json.dumps(body, sort_keys=True)
        if isinstance(body, (dict, list, str, int, float, bool)) or body is None
        else json.dumps(str(body)),
        "contents_key": json.dumps(recorded, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
    }


def _normalize(value: object) -> object:
    if isinstance(value, dict):
        return {key: _normalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, str):
        return value.strip()
    return value


def _unreadable(event_id: object, message: str) -> tuple[int, dict]:
    body = {"code": "unreadable_input", "message": message}
    if isinstance(event_id, str) and event_id.strip():
        body["event_id"] = event_id.strip()
    return 400, body
