"""Publication gate. Python stores passage text or no policy conclusion."""

from onboarding.policy_pack import OBLIGATION_PASSAGE, PASSAGES, detect


POLICY_MODEL_FAILURE = "The policy question could not be read. No policy conclusion was written."
OUTSIDE_THE_PACK = "outside the pack"
_LIVE_STATE = (
    "reserved for this hire",
    "equipment readiness is confirmed",
    "task is complete",
)


def settle(event: dict, plan_version: int | None, proposal: object | None = None) -> dict:
    """Finish one policy question without changing tasks, readiness, or plan version."""
    classification = detect(event["body"])
    if classification["call_model"]:
        parsed = _parse_proposal(proposal)
        if parsed is None:
            return _failed(event)
        return _gate(event, plan_version, classification, parsed)
    return _route_without_model(event, plan_version, classification)


def _route_without_model(event: dict, plan_version: int | None, classification: dict) -> dict:
    route = classification["route"]
    if route == "out_of_pack":
        return _complete(
            event,
            plan_version,
            "outside_the_pack",
            [_question(event, True), _notice(event, "policy_referral", OUTSIDE_THE_PACK)],
            classification,
            None,
        )
    return _complete(
        event,
        plan_version,
        "manual_review",
        [_question(event, True), _notice(event, "policy_review", "manual review")],
        classification,
        None,
    )


def _gate(event: dict, plan_version: int | None, classification: dict, proposal: dict) -> dict:
    if proposal["covered"] is False or not proposal["citations"]:
        return _manual(event, plan_version, classification, proposal)
    for citation, excerpt in zip(proposal["citations"], proposal["grounding"]):
        passage = PASSAGES.get(citation)
        if passage is None or citation not in classification["candidates"]:
            return _failed(event)
        if not excerpt or excerpt not in passage:
            return _failed(event)
    if any(_asserts_live_state(excerpt) for excerpt in proposal["grounding"]):
        return _manual(event, plan_version, classification, proposal)
    if not classification["obligations"] or not _fully_covered(classification):
        return _manual(event, plan_version, classification, proposal)
    published = []
    for citation in proposal["citations"]:
        if citation in published:
            continue
        if _covers_detected(citation, classification["obligations"]):
            published.append(citation)
    if not published:
        return _manual(event, plan_version, classification, proposal)
    messages = [_question(event, True)]
    for citation in published:
        messages.append(
            {
                "event_id": event["event_id"],
                "kind": "policy_answer",
                "body": PASSAGES[citation],
                "citation": citation,
                "actor_id": event["actor_id"],
                "verified": True,
            }
        )
    return _complete(event, plan_version, "published", messages, classification, proposal)


def _fully_covered(classification: dict) -> bool:
    candidates = set(classification["candidates"])
    return all(OBLIGATION_PASSAGE[item] in candidates for item in classification["obligations"])


def _covers_detected(citation: str, obligations: list[str]) -> bool:
    return any(OBLIGATION_PASSAGE[item] == citation for item in obligations)


def _asserts_live_state(excerpt: str) -> bool:
    folded = excerpt.casefold()
    return any(phrase in folded for phrase in _LIVE_STATE)


def _parse_proposal(proposal: object) -> dict | None:
    if not isinstance(proposal, dict):
        return None
    citations = proposal.get("citations")
    grounding = proposal.get("grounding")
    covered = proposal.get("covered")
    if not isinstance(covered, bool):
        return None
    if not isinstance(citations, list) or not isinstance(grounding, list):
        return None
    if len(citations) != len(grounding):
        return None
    if any(not isinstance(item, str) or not item.strip() for item in citations):
        return None
    if any(not isinstance(item, str) for item in grounding):
        return None
    return {
        "citations": [item.strip() for item in citations],
        "grounding": grounding,
        "covered": covered,
    }


def _manual(event: dict, plan_version: int | None, classification: dict, proposal: dict) -> dict:
    return _complete(
        event,
        plan_version,
        "manual_review",
        [_question(event, True), _notice(event, "policy_review", "manual review")],
        classification,
        proposal,
    )


def _complete(event, plan_version, rule, messages, classification, proposal) -> dict:
    stored_proposal = {
        "obligations": classification["obligations"],
        "candidates": classification["candidates"],
        "route": classification["route"],
        "model": proposal,
    }
    return {
        "ok": True,
        "tasks": None,
        "messages": messages,
        "decision": {
            "event_id": event["event_id"],
            "hire_id": event["hire_id"],
            "actor_id": event["actor_id"],
            "occurred_at": event["occurred_at"],
            "route": "policy_answerer" if classification["call_model"] else "policy_router",
            "proposal": stored_proposal,
            "rule_result": rule,
            "evidence_refs": [message["citation"] for message in messages if message.get("citation")],
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


def _failed(event: dict) -> dict:
    return {
        "ok": False,
        "failure": {"code": "model_failure", "message": POLICY_MODEL_FAILURE},
        "message": _question(event, False),
    }


def _question(event: dict, verified: bool) -> dict:
    return {
        "event_id": event["event_id"],
        "kind": "policy_question",
        "body": event["body"],
        "actor_id": event["actor_id"],
        "verified": verified,
    }


def _notice(event: dict, kind: str, body: str) -> dict:
    return {
        "event_id": event["event_id"],
        "kind": kind,
        "body": body,
        "actor_id": event["actor_id"],
        "verified": True,
        "reason": OUTSIDE_THE_PACK if kind == "policy_referral" else None,
    }
