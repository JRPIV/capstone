"""Equipment ledger. The draft is a proposal. Python writes the case."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


AUSTIN = ZoneInfo("America/Chicago")
DEADLINE_TIME = time(17, 0)
DEVICES = ("assigned_laptop", "permitted_loaner")
POSTURES = {
    "explicit_commitment",
    "possibility",
    "delivery_estimate",
    "denial",
    "revocation",
    "unclassified",
}
EQUIPMENT_TASK = "Equipment readiness"
EQUIPMENT_REASON = "Equipment is not confirmed."
BLOCKED_REASON = "No permitted device is available by the start date."
POLICY_REASON = "Policy acknowledgment is not complete."
MEETING_REASON = "The first-day meeting is not confirmed."
MODEL_FAILURE = "The equipment reply could not be read. No new verified fact was written."


class ProviderFailure(Exception):
    """The provider call failed. The message is not shown to the client."""


def follow_up_deadline(occurred_at: str) -> str:
    """5:00 p.m. Austin time, rolling Saturday, Sunday, and times at or after 5 p.m. forward."""
    local = _parse_time(occurred_at).astimezone(AUSTIN)
    day = local.date()
    if day.weekday() >= 5 or local.time() >= DEADLINE_TIME:
        day = day + timedelta(days=1)
        while day.weekday() >= 5:
            day += timedelta(days=1)
    deadline = datetime.combine(day, DEADLINE_TIME, tzinfo=AUSTIN)
    return deadline.isoformat()


def apply_reply(case: dict, event: dict, draft: object) -> dict:
    """Turn one authorized draft into a case update, or an ungrounded failure."""
    grounded = _ground(event["body"], draft)
    if grounded is None:
        return _failure(event)
    return _decide(case, event, grounded)


def _ground(body: object, draft: object) -> dict | None:
    if not isinstance(body, str) or not isinstance(draft, dict):
        return None
    statements = draft.get("statements")
    candidates = draft.get("date_candidates")
    if not isinstance(statements, list) or not isinstance(candidates, list):
        return None
    candidate_set = set()
    for candidate in candidates:
        if not isinstance(candidate, str) or _parse_date(candidate) is None:
            return None
        candidate_set.add(candidate)
    supported = []
    for item in statements:
        accepted = _accept_statement(body, item, candidate_set)
        if accepted is not None:
            supported.append(accepted)
    if not supported:
        return None
    by_device: dict[str, dict | None] = {}
    contradicted = []
    for statement in supported:
        device = statement["device"]
        if device not in DEVICES:
            continue
        current = by_device.get(device, "missing")
        if current == "missing":
            by_device[device] = statement
            continue
        if current is None:
            continue
        if current["posture"] != statement["posture"] or current["ready_date"] != statement["ready_date"]:
            by_device[device] = None
            contradicted.append(device)
    return {
        "by_device": by_device,
        "contradicted": contradicted,
        "proposal": {
            "claimed_fact": draft.get("claimed_fact"),
            "uncertainty": draft.get("uncertainty"),
            "date_candidates": list(candidates),
            "statements": supported,
        },
    }


def _accept_statement(body: str, item: object, candidates: set[str]) -> dict | None:
    if not isinstance(item, dict):
        return None
    device = item.get("device")
    posture = item.get("posture")
    excerpt = item.get("excerpt")
    ready = item.get("ready_date")
    if device not in {"assigned_laptop", "permitted_loaner", "unspecified"}:
        return None
    if posture not in POSTURES:
        return None
    if not isinstance(excerpt, str) or not excerpt or excerpt not in body:
        return None
    if ready is not None:
        if not isinstance(ready, str) or ready not in candidates or _parse_date(ready) is None:
            return None
    return {
        "device": device,
        "posture": posture,
        "ready_date": ready,
        "excerpt": excerpt,
    }


def _decide(case: dict, event: dict, grounded: dict) -> dict:
    start = date.fromisoformat(case["start_date"])
    body = event["body"].strip()
    tasks = [_copy_task(task) for task in case["tasks"]]
    equipment = next((task for task in tasks if task["name"] == EQUIPMENT_TASK), None)
    ledger = _copy_ledger(case.get("ledger"))
    follow_ups = int(case.get("follow_ups") or 0)
    round_bodies = list(case.get("round_bodies") or [])
    was_escalated = bool(equipment and equipment.get("escalated"))
    previous_readiness = equipment["readiness"] if equipment is not None else None
    plan_version = case["plan_version"]
    messages = [_reply_message(event, verified=True)]
    rule = "insufficient"

    if body in round_bodies:
        return _commit(
            case,
            event,
            tasks,
            ledger,
            follow_ups,
            round_bodies,
            messages,
            plan_version,
            "unchanged_reply",
            grounded["proposal"],
            follow_up=None,
        )

    for device, statement in grounded["by_device"].items():
        if statement is None:
            continue
        ledger[device] = _next_state(ledger[device], statement, start)

    confirmed = _confirmed(ledger, start)
    blocked = _both_unavailable(ledger, start)
    if confirmed:
        rule = "confirmed"
        follow_ups = 0
    elif blocked:
        rule = "contextual_denial"
    elif was_escalated or follow_ups >= 1:
        rule = "escalated"
    else:
        rule = "follow_up"
        follow_ups = 1
    if equipment is not None:
        if confirmed:
            equipment["readiness"] = "confirmed"
            equipment["escalated"] = False
        elif blocked:
            equipment["readiness"] = "blocked"
            equipment["escalated"] = True
        else:
            equipment["readiness"] = "unconfirmed"
            if rule == "escalated":
                equipment["escalated"] = True
        if rule in {"confirmed", "contextual_denial"} and event["event_id"] not in equipment["evidence_refs"]:
            equipment["evidence_refs"].append(event["event_id"])

    follow_up = None
    if rule == "follow_up" and equipment is not None:
        deadline = follow_up_deadline(event["occurred_at"])
        follow_up = {
            "event_id": event["event_id"],
            "kind": "follow_up",
            "body": (
                "Confirm an assigned laptop or a permitted loaner with a ready date "
                f"on or before {case['start_date']}. This request cites P2. Reply by {deadline}."
            ),
            "deadline": deadline,
            "actor_id": "actor-taylor-brooks",
            "verified": True,
        }
        messages.append(follow_up)

    round_bodies.append(body)
    if (
        equipment is not None
        and isinstance(plan_version, int)
        and (
            equipment["readiness"] != previous_readiness
            or bool(equipment["escalated"]) != was_escalated
        )
    ):
        plan_version += 1
        material = True
    else:
        material = False
    return _commit(
        case,
        event,
        tasks,
        ledger,
        follow_ups,
        round_bodies,
        messages,
        plan_version,
        rule,
        grounded["proposal"],
        follow_up,
        material,
    )


def _next_state(current: dict, statement: dict, start: date) -> dict:
    posture = statement["posture"]
    ready = statement["ready_date"]
    if posture in {"unspecified", "unclassified"}:
        return current
    if posture == "explicit_commitment":
        ready_on = _parse_date(ready) if ready else None
        if ready_on is not None and ready_on <= start and current["state"] != "revoked":
            return {"state": "committed", "ready_date": ready}
        if ready_on is not None and ready_on > start and current["state"] != "committed":
            return {"state": "estimate", "ready_date": ready}
        return current
    if posture == "possibility":
        if current["state"] == "committed":
            return current
        return {"state": "possible", "ready_date": None}
    if posture == "delivery_estimate":
        if current["state"] == "committed" or ready is None:
            return current
        return {"state": "estimate", "ready_date": ready}
    if posture == "denial":
        return {"state": "denied", "ready_date": None}
    if posture == "revocation":
        return {"state": "revoked", "ready_date": None}
    return current


def _confirmed(ledger: dict, start: date) -> bool:
    for device in DEVICES:
        state = ledger[device]
        ready = _parse_date(state["ready_date"]) if state["ready_date"] else None
        if state["state"] == "committed" and ready is not None and ready <= start:
            return True
    return False


def _both_unavailable(ledger: dict, start: date) -> bool:
    return all(_unavailable(ledger[device], start) for device in DEVICES)


def _unavailable(state: dict, start: date) -> bool:
    if state["state"] in {"denied", "revoked"}:
        return True
    ready = _parse_date(state["ready_date"]) if state["ready_date"] else None
    return state["state"] == "estimate" and ready is not None and ready > start


def _commit(
    case,
    event,
    tasks,
    ledger,
    follow_ups,
    round_bodies,
    messages,
    plan_version,
    rule,
    proposal,
    follow_up,
    material=False,
) -> dict:
    reasons = _reasons(tasks)
    readiness = "ready" if not reasons else "needs_attention"
    decision = {
        "event_id": event["event_id"],
        "hire_id": event["hire_id"],
        "actor_id": event["actor_id"],
        "occurred_at": event["occurred_at"],
        "route": "reply_reader",
        "proposal": proposal,
        "rule_result": rule,
        "evidence_refs": [event["event_id"]] if rule in {"confirmed", "contextual_denial"} else [],
        "plan_version": plan_version,
    }
    version = {
        "plan_version": plan_version,
        "event_id": event["event_id"],
        "actor_id": event["actor_id"],
        "occurred_at": event["occurred_at"],
        "route": "reply_reader",
        "proposal": proposal,
        "rule_result": rule,
        "evidence_refs": decision["evidence_refs"],
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
        "ledger": ledger,
        "follow_ups": follow_ups,
        "round_bodies": round_bodies,
        "failure": None,
        "follow_up": follow_up,
        "flag_reviews": material,
    }


def keep_message(event: dict, rule: str, plan_version: int | None) -> dict:
    """Store a reply that cannot change equipment. No model result is applied."""
    return {
        "ok": True,
        "tasks": None,
        "messages": [_reply_message(event, verified=True)],
        "decision": {
            "event_id": event["event_id"],
            "hire_id": event["hire_id"],
            "actor_id": event["actor_id"],
            "occurred_at": event["occurred_at"],
            "route": "reply_reader",
            "proposal": None,
            "rule_result": rule,
            "evidence_refs": [],
            "plan_version": plan_version,
        },
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


def _failure(event: dict) -> dict:
    return {
        "ok": False,
        "failure": {"code": "model_failure", "message": MODEL_FAILURE},
        "message": _reply_message(event, verified=False),
    }


def _reply_message(event: dict, verified: bool) -> dict:
    return {
        "event_id": event["event_id"],
        "kind": "reply",
        "body": event["body"],
        "actor_id": event["actor_id"],
        "verified": verified,
    }


def _reasons(tasks: list) -> list:
    reasons = []
    for task in tasks:
        if task["name"] == "Policy acknowledgment" and task["execution_status"] != "complete":
            reasons.append(POLICY_REASON)
        elif task["name"] == EQUIPMENT_TASK and task["readiness"] == "blocked":
            reasons.append(BLOCKED_REASON)
        elif task["name"] == EQUIPMENT_TASK and task["readiness"] != "confirmed":
            reasons.append(EQUIPMENT_REASON)
        elif task["name"] == "First-day meeting" and task["readiness"] != "confirmed":
            reasons.append(MEETING_REASON)
    return reasons


def _copy_task(task: dict) -> dict:
    copied = dict(task)
    copied["evidence_refs"] = list(task.get("evidence_refs") or [])
    return copied


def _copy_ledger(ledger: dict | None) -> dict:
    base = {device: {"state": "unknown", "ready_date": None} for device in DEVICES}
    for device in DEVICES:
        if ledger and device in ledger:
            base[device] = {
                "state": ledger[device]["state"],
                "ready_date": ledger[device]["ready_date"],
            }
    return base


def _parse_date(value: str | None) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.strip())
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=AUSTIN)
    return parsed
