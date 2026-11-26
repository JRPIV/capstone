"""Current-case sentences for the hire read. Stored messages stay unchanged."""

PROPOSED = "Proposed plan. It is not active until HR approves it."
APPROVED = "HR approved the held plan. The plan is active."
REFERRAL = "Outside the pack. Routed to HR. No policy answer was published."
REVIEW = "Manual review. No policy conclusion was published."


def case_summary(hire: dict) -> list[str]:
    lines: list[str] = []
    activation = hire.get("activation")
    decisions = hire.get("decisions") or []
    if activation == "proposed":
        lines.append(PROPOSED)
    elif activation == "active" and any(
        isinstance(item, dict) and item.get("rule_result") == "approve_held_plan" for item in decisions
    ):
        lines.append(APPROVED)
    latest = _latest_complete_event_id(hire.get("events") or [])
    messages = [
        message
        for message in hire.get("messages") or []
        if isinstance(message, dict) and message.get("event_id") == latest
    ]
    lines.extend(_policy_lines(messages))
    return lines


def _latest_complete_event_id(events: list) -> str | None:
    for event in reversed(events):
        if isinstance(event, dict) and event.get("state") == "complete":
            return event.get("event_id")
    return None


def _policy_lines(messages: list) -> list[str]:
    lines: list[str] = []
    if any(message.get("kind") == "policy_referral" for message in messages):
        lines.append(REFERRAL)
    if any(message.get("kind") == "policy_review" for message in messages):
        lines.append(REVIEW)
    for message in messages:
        if message.get("kind") == "policy_answer":
            lines.append(f"{message.get('citation')}: {message.get('body')}")
    return lines
