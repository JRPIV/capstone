"""Held-plan approval, start-date changes, and deadlines. Python writes the case."""

from datetime import date

from onboarding.equipment import (
    _both_unavailable,
    _confirmed,
    _copy_ledger,
    _copy_task,
    _parse_date,
    _parse_time,
    _reasons,
    follow_up_deadline,
)
from onboarding.rules import _overdue, _role_kind, _shift_business_days, proposed_tasks
from onboarding.simulator import ROSTER


HR_ID = "actor-alex-rivera"
SUPPORTED_ROLE = "Customer Support Representative"


def manager_identity(manager_name: str) -> dict | None:
    person = find_identity_by_name(manager_name)
    if person is None or person["actor_role"] != "hiring_manager":
        return None
    return person


def find_identity_by_name(name: str) -> dict | None:
    for person in ROSTER:
        if person["name"] == name:
            return person
    return None


def apply_role_reply(case: dict, event: dict) -> dict:
    """A held hire. No model call and no invented role."""
    manager = manager_identity(case["manager_name"])
    is_manager = (
        manager is not None
        and event["actor_id"] == manager["actor_id"]
        and event["actor_role"] == manager["actor_role"]
    )
    supported = _role_kind(event["body"]) == "supported"
    prior = [
        message
        for message in case["messages"]
        if isinstance(message, dict) and message.get("kind") == "role_follow_up"
    ]
    stored = _note(event, "reply", event["body"])
    if is_manager and supported:
        start = date.fromisoformat(case["start_date"])
        tasks = proposed_tasks(
            case["employee_name"],
            case["manager_name"],
            start,
            _parse_time(event["occurred_at"]),
        )
        reasons = _reasons(tasks)
        return _update(
            case,
            event,
            tasks=tasks,
            messages=[stored],
            rule="proposed_plan",
            plan_version=1,
            readiness="needs_attention",
            reasons=reasons,
            activation="proposed",
            role=SUPPORTED_ROLE,
            version_rule="proposed_plan",
        )
    if is_manager and not prior:
        deadline = follow_up_deadline(event["occurred_at"])
        follow = _note(
            event,
            "role_follow_up",
            "Confirm whether the role is Customer Support Representative. "
            f"Reply by {deadline}.",
        )
        follow["deadline"] = deadline
        follow["subject"] = "role"
        return _message_only(case, event, [stored, follow], "role_follow_up")
    if is_manager:
        notice = _note(
            event,
            "escalation",
            "The role was not established. The case is escalated to HR.",
        )
        return _message_only(case, event, [stored, notice], "role_escalated")
    return _message_only(case, event, [stored], "sender_cannot_establish_role")


def apply_hr_decision(case: dict, event: dict) -> dict:
    body = event["body"]
    decision_type = body["decision_type"]
    rationale = body["rationale"]
    if decision_type == "approve_held_plan":
        tasks = [_copy_task(task) for task in case["tasks"]]
        new_version = int(case["plan_version"]) + 1
        return _update(
            case,
            event,
            tasks=tasks,
            messages=[_note(event, "hr_decision", rationale)],
            rule="approve_held_plan",
            plan_version=new_version,
            readiness=case["readiness"],
            reasons=list(case["readiness_reasons"]),
            activation="active",
            version_rule="approve_held_plan",
            decision_type=decision_type,
            rationale=rationale,
            flag_reviews=True,
        )
    return _message_only(
        case,
        event,
        [_note(event, "hr_decision", rationale)],
        "escalation_disposition",
        decision_type="escalation_disposition",
        rationale=rationale,
    )


def apply_start_change(case: dict, event: dict) -> dict:
    new_start = date.fromisoformat(event["body"])
    occurred = _parse_time(event["occurred_at"])
    tasks = []
    for task in case["tasks"]:
        copied = _copy_task(task)
        if copied["execution_status"] == "complete":
            tasks.append(copied)
            continue
        name = copied["name"]
        if name == "Policy acknowledgment":
            due = _shift_business_days(new_start, -2)
            start_of_work = False
        elif name == "Customer-support tools orientation":
            due = _shift_business_days(new_start, 5)
            start_of_work = False
        else:
            due = new_start
            start_of_work = name == "Equipment readiness"
        copied["due_date"] = due.isoformat()
        copied["overdue"] = _overdue(due, occurred, start_of_work)
        if name == "First-day meeting":
            copied["readiness"] = "unconfirmed"
            copied["evidence_refs"] = []
        tasks.append(copied)
    ledger = _copy_ledger(case.get("ledger"))
    equipment = next(task for task in tasks if task["name"] == "Equipment readiness")
    if equipment["execution_status"] != "complete":
        if _confirmed(ledger, new_start):
            equipment["readiness"] = "confirmed"
            equipment["escalated"] = False
        elif _commitment_misses(ledger, new_start) or _both_unavailable(ledger, new_start):
            equipment["readiness"] = "blocked"
            equipment["escalated"] = True
        else:
            equipment["readiness"] = "unconfirmed"
    messages = [_note(event, "start_date_change", event["body"])]
    meeting = next(task for task in tasks if task["name"] == "First-day meeting")
    if meeting["execution_status"] != "complete":
        follow = _note(
            event,
            "follow_up",
            f"Confirm the first-day meeting for {new_start.isoformat()}.",
        )
        follow["subject"] = "meeting"
        follow["deadline"] = follow_up_deadline(event["occurred_at"])
        messages.append(follow)
    reasons = _reasons(tasks)
    return _update(
        case,
        event,
        tasks=tasks,
        messages=messages,
        rule="start_date_change",
        plan_version=int(case["plan_version"]) + 1,
        readiness="ready" if not reasons else "needs_attention",
        reasons=reasons,
        activation="active",
        version_rule="start_date_change",
        flag_reviews=True,
        start_date=new_start.isoformat(),
        ledger=ledger,
    )


TASK_NAMES = {
    "policy_acknowledgment": "Policy acknowledgment",
    "first_day_meeting": "First-day meeting",
    "training": "Customer-support tools orientation",
}
TASK_ACTIONS = {
    "policy_acknowledgment": {"acknowledge"},
    "first_day_meeting": {"confirm", "held"},
    "training": {"assigned", "complete"},
}


def apply_task_update(case: dict, event: dict) -> dict:
    """Record an authorized task fact. A wrong sender changes nothing else."""
    body = event["body"]
    task_name = TASK_NAMES[body["task"]]
    action = body["action"]
    stored = _note(event, "task_update", f"{body['task']}:{action}")
    authorized = _task_sender(case, event, body["task"])
    if case.get("activation") != "active" or not authorized:
        return _message_only(case, event, [stored], "task_update_retained")
    tasks = [_copy_task(task) for task in case["tasks"]]
    target = next(task for task in tasks if task["name"] == task_name)
    if event["event_id"] not in target["evidence_refs"]:
        target["evidence_refs"].append(event["event_id"])
    if action == "acknowledge":
        target["execution_status"] = "complete"
        target["readiness"] = "confirmed"
    elif action == "confirm":
        target["readiness"] = "confirmed"
        target["escalated"] = False
    elif action in {"held", "complete"}:
        target["execution_status"] = "complete"
        target["readiness"] = "confirmed"
        target["escalated"] = False
    elif action == "assigned":
        target["readiness"] = "confirmed"
    reasons = _reasons(tasks)
    return _update(
        case,
        event,
        tasks=tasks,
        messages=[stored],
        rule=f"task_{action}",
        plan_version=int(case["plan_version"]) + 1,
        readiness="ready" if not reasons else "needs_attention",
        reasons=reasons,
        activation="active",
        version_rule=f"task_{action}",
        flag_reviews=True,
    )


def _task_sender(case: dict, event: dict, task: str) -> bool:
    if task == "policy_acknowledgment":
        person = find_identity_by_name(case["employee_name"])
        return (
            person is not None
            and person["actor_role"] == "new_hire"
            and event["actor_id"] == person["actor_id"]
            and event["actor_role"] == "new_hire"
        )
    manager = manager_identity(case["manager_name"])
    return (
        manager is not None
        and event["actor_id"] == manager["actor_id"]
        and event["actor_role"] == manager["actor_role"]
    )


def apply_deadline(case: dict, event: dict) -> dict:
    occurred = _parse_time(event["occurred_at"])
    tasks = [_copy_task(task) for task in case["tasks"]]
    messages = [_note(event, "deadline", event["body"])]
    changed = False
    for message in case["messages"]:
        if not isinstance(message, dict) or not message.get("deadline"):
            continue
        if occurred < _parse_time(message["deadline"]):
            continue
        body = str(message.get("body", ""))
        if "cites P2" in body:
            equipment = next((task for task in tasks if task["name"] == "Equipment readiness"), None)
            if equipment and equipment["readiness"] == "unconfirmed" and not equipment["escalated"]:
                equipment["escalated"] = True
                changed = True
        if message.get("kind") == "role_follow_up" and case.get("activation") == "held":
            if not any(item.get("kind") == "escalation" for item in messages):
                messages.append(
                    _note(event, "escalation", "The role request reached its deadline. The case is escalated to HR.")
                )
                changed = True
        if message.get("subject") == "meeting":
            meeting = next((task for task in tasks if task["name"] == "First-day meeting"), None)
            if meeting and meeting["readiness"] != "confirmed" and not meeting["escalated"]:
                meeting["escalated"] = True
                changed = True
    if not changed or not tasks or not isinstance(case.get("plan_version"), int):
        return _message_only(case, event, messages, "deadline_reached")
    reasons = _reasons(tasks)
    return _update(
        case,
        event,
        tasks=tasks,
        messages=messages,
        rule="deadline_escalated",
        plan_version=int(case["plan_version"]) + 1,
        readiness="ready" if not reasons else "needs_attention",
        reasons=reasons,
        activation=case.get("activation") or "active",
        version_rule="deadline_escalated",
        flag_reviews=True,
    )


def _commitment_misses(ledger: dict, start: date) -> bool:
    if _confirmed(ledger, start):
        return False
    for state in ledger.values():
        ready = _parse_date(state["ready_date"]) if state["ready_date"] else None
        if state["state"] == "committed" and ready is not None and ready > start:
            return True
    return False


def _update(
    case,
    event,
    tasks,
    messages,
    rule,
    plan_version,
    readiness,
    reasons,
    activation,
    version_rule,
    decision_type=None,
    rationale=None,
    flag_reviews=False,
    start_date=None,
    role=None,
    ledger=None,
) -> dict:
    decision = _decision(event, rule, plan_version, decision_type, rationale)
    version = {
        "plan_version": plan_version,
        "event_id": event["event_id"],
        "actor_id": event["actor_id"],
        "occurred_at": event["occurred_at"],
        "route": "plan",
        "proposal": None,
        "rule_result": version_rule,
        "evidence_refs": [],
    }
    return {
        "ok": True,
        "tasks": tasks,
        "messages": messages,
        "decision": decision,
        "version": version,
        "plan_version": plan_version,
        "readiness": readiness,
        "readiness_reasons": reasons,
        "ledger": ledger if ledger is not None else _copy_ledger(case.get("ledger")),
        "follow_ups": case.get("follow_ups", 0),
        "round_bodies": list(case.get("round_bodies") or []),
        "failure": None,
        "follow_up": None,
        "activation": activation,
        "flag_reviews": flag_reviews,
        "start_date": start_date,
        "role": role,
    }


def _message_only(case, event, messages, rule, decision_type=None, rationale=None) -> dict:
    return {
        "ok": True,
        "tasks": None,
        "messages": messages,
        "decision": _decision(event, rule, case.get("plan_version"), decision_type, rationale),
        "version": None,
        "plan_version": None,
        "readiness": None,
        "readiness_reasons": None,
        "ledger": None,
        "follow_ups": None,
        "round_bodies": None,
        "failure": None,
        "follow_up": None,
    }


def _decision(event, rule, plan_version, decision_type, rationale) -> dict:
    return {
        "event_id": event["event_id"],
        "hire_id": event["hire_id"],
        "actor_id": event["actor_id"],
        "occurred_at": event["occurred_at"],
        "route": "plan",
        "proposal": None,
        "rule_result": rule,
        "evidence_refs": [],
        "plan_version": plan_version,
        "decision_type": decision_type,
        "rationale": rationale,
        "needs_review": False,
    }


def _note(event: dict, kind: str, body: str) -> dict:
    return {
        "event_id": event["event_id"],
        "kind": kind,
        "body": body,
        "actor_id": event["actor_id"],
        "verified": True,
    }
