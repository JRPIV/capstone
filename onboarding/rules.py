"""Intake rules. Python decides. No model call and no case write."""

import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


AUSTIN = ZoneInfo("America/Chicago")
DEADLINE_TIME = time(17, 0)
SUPPORTED_PHRASE = "customer support representative"
CSR_WORD = re.compile(r"\bcsr\b", re.IGNORECASE)

UNREADABLE_MESSAGE = "The intake could not be read, so no plan was written."

POLICY_REASON = "Policy acknowledgment is not complete."
EQUIPMENT_REASON = "Equipment is not confirmed."
MEETING_REASON = "The first-day meeting is not confirmed."
BLANK_ROLE_REASON = "The role was not on the intake."
REVIEW_REASON = "This role or location is not supported and is waiting for HR review."


def assess_intake(event: dict) -> dict:
    """Return either an error outcome or a hire the application may store."""
    checked = _readable_event(event)
    if checked is not None:
        return _unreadable()
    body = event["body"]
    occurred = _parse_occurred_at(event["occurred_at"])
    if occurred is None:
        return _unreadable()
    facts = _intake_facts(body)
    if facts is None:
        return _unreadable()

    role_kind = _role_kind(facts["role"])
    office_supported = facts["office"].casefold() == "austin"
    if not office_supported or role_kind == "unsupported":
        return _review_hire(facts, occurred, event)
    if role_kind == "blank":
        return _held_hire(facts, occurred, event)
    return _active_hire(facts, occurred, event)


def _readable_event(event: dict) -> str | None:
    if not isinstance(event.get("actor_id"), str) or not event["actor_id"].strip():
        return "actor"
    if event.get("actor_role") not in {
        "hr_coordinator",
        "hiring_manager",
        "it_fulfiller",
        "new_hire",
    }:
        return "role"
    if not isinstance(event.get("occurred_at"), str) or not event["occurred_at"].strip():
        return "time"
    if not isinstance(event.get("body"), dict):
        return "body"
    return None


def _intake_facts(body: dict) -> dict | None:
    name = _text(body.get("employee_name"))
    manager = _text(body.get("manager_name"))
    office = _text(body.get("office"))
    start_raw = _text(body.get("start_date"))
    if name is None or manager is None or office is None or start_raw is None:
        return None
    try:
        start = date.fromisoformat(start_raw)
    except ValueError:
        return None
    role = body.get("role", "")
    if role is None:
        role = ""
    if not isinstance(role, str):
        return None
    return {
        "employee_name": name,
        "manager_name": manager,
        "office": office,
        "start_date": start,
        "role": role.strip(),
    }


def _role_kind(role: str) -> str:
    if role == "":
        return "blank"
    folded = role.casefold()
    if folded == SUPPORTED_PHRASE or folded == "csr":
        return "supported"
    if SUPPORTED_PHRASE in folded or CSR_WORD.search(role):
        return "supported"
    return "unsupported"


def proposed_tasks(employee_name: str, manager_name: str, start: date, occurred: datetime) -> list:
    """The four Appendix A tasks for a supported Austin CSR plan."""
    policy_due = _shift_business_days(start, -2)
    training_due = _shift_business_days(start, 5)
    return [
        _task(
            "Policy acknowledgment",
            f"{employee_name}, new hire",
            policy_due,
            _overdue(policy_due, occurred, start_of_work=False),
        ),
        _task(
            "Equipment readiness",
            "Taylor Brooks, IT fulfiller",
            start,
            _overdue(start, occurred, start_of_work=True),
        ),
        _task(
            "First-day meeting",
            f"{manager_name}, hiring manager",
            start,
            _overdue(start, occurred, start_of_work=False),
        ),
        _task(
            "Customer-support tools orientation",
            f"{manager_name}, hiring manager",
            training_due,
            _overdue(training_due, occurred, start_of_work=False),
        ),
    ]


def _active_hire(facts: dict, occurred: datetime, event: dict) -> dict:
    tasks = proposed_tasks(facts["employee_name"], facts["manager_name"], facts["start_date"], occurred)
    version = _version(event, 1, "active_plan")
    return _hire(
        facts,
        plan_version=1,
        readiness="needs_attention",
        reasons=[POLICY_REASON, EQUIPMENT_REASON, MEETING_REASON],
        tasks=tasks,
        messages=[],
        versions=[version],
        activation="active",
    )


def _held_hire(facts: dict, occurred: datetime, event: dict) -> dict:
    del occurred
    message = f"Ask {facts['manager_name']} to confirm the role."
    version = _version(event, None, "held_for_missing_role")
    return _hire(
        facts,
        plan_version=None,
        readiness="needs_attention",
        reasons=[BLANK_ROLE_REASON],
        tasks=[],
        messages=[message],
        versions=[version],
        activation="held",
    )


def _review_hire(facts: dict, occurred: datetime, event: dict) -> dict:
    del occurred
    version = _version(event, None, "hr_review_unsupported")
    return _hire(
        facts,
        plan_version=None,
        readiness="needs_attention",
        reasons=[REVIEW_REASON],
        tasks=[],
        messages=["This role or location is waiting for HR review. No tasks were created."],
        versions=[version],
        activation="review",
    )


def _hire(facts, plan_version, readiness, reasons, tasks, messages, versions, activation) -> dict:
    return {
        "ok": True,
        "hire": {
            "employee_name": facts["employee_name"],
            "start_date": facts["start_date"].isoformat(),
            "role": facts["role"],
            "location": facts["office"],
            "manager_name": facts["manager_name"],
            "plan_version": plan_version,
            "readiness": readiness,
            "readiness_reasons": reasons,
            "failure": None,
            "activation": activation,
        },
        "tasks": tasks,
        "messages": messages,
        "versions": versions,
    }


def _task(name: str, owner: str, due: date, overdue: bool) -> dict:
    return {
        "name": name,
        "owner": owner,
        "execution_status": "pending",
        "readiness": "unconfirmed",
        "due_date": due.isoformat(),
        "evidence_refs": [],
        "overdue": overdue,
        "escalated": False,
    }


def _version(event: dict, plan_version: int | None, rule_result: str) -> dict:
    return {
        "plan_version": plan_version,
        "event_id": event["event_id"],
        "actor_id": event["actor_id"].strip(),
        "occurred_at": event["occurred_at"].strip(),
        "route": "intake",
        "proposal": None,
        "rule_result": rule_result,
        "evidence_refs": [],
    }


def _unreadable() -> dict:
    return {
        "ok": False,
        "error": {
            "code": "unreadable_input",
            "message": UNREADABLE_MESSAGE,
        },
    }


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped


def _parse_occurred_at(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=AUSTIN)
    return parsed.astimezone(AUSTIN)


def _shift_business_days(start: date, offset: int) -> date:
    if offset == 0:
        return start
    step = 1 if offset > 0 else -1
    remaining = abs(offset)
    cursor = start
    while remaining:
        cursor += timedelta(days=step)
        if cursor.weekday() < 5:
            remaining -= 1
    return cursor


def _overdue(due: date, occurred: datetime, start_of_work: bool) -> bool:
    if start_of_work:
        return occurred.date() > due
    deadline = datetime.combine(due, DEADLINE_TIME, tzinfo=AUSTIN)
    return occurred >= deadline
