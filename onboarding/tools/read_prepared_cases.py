"""Local mock of the four prepared cases. No network and no write."""

import json

PREPARED_CASES = {
    "riley-complete": {
        "hire_id": "H-002",
        "plan_version": 1,
        "plan_label": "active",
        "outcome_line": "Active plan. Four tasks created. No approval hold.",
        "readiness_label": "Needs attention",
        "attention_reasons": [
            "Policy acknowledgment is overdue and incomplete.",
            "No device is confirmed for the start.",
            "The first-day meeting is not confirmed.",
        ],
        "next_owner": "Riley Chen",
        "next_action": "Record the policy acknowledgment.",
        "messages": [],
        "failure": None,
        "tasks": [
            {
                "name": "Policy acknowledgment",
                "owner": "Riley Chen, new hire",
                "due": "2026-03-12",
                "execution": "pending",
                "readiness": "unconfirmed",
                "evidence": "Unverified. Overdue.",
            },
            {
                "name": "Equipment readiness",
                "owner": "Taylor Brooks, IT fulfiller",
                "due": "2026-03-16",
                "execution": "pending",
                "readiness": "unconfirmed",
                "evidence": "Unverified.",
            },
            {
                "name": "First-day meeting",
                "owner": "Morgan Hale, hiring manager",
                "due": "2026-03-16",
                "execution": "pending",
                "readiness": "unconfirmed",
                "evidence": "Unverified.",
            },
            {
                "name": "Customer-support tools orientation",
                "owner": "Morgan Hale, hiring manager",
                "due": "2026-03-23",
                "execution": "pending",
                "readiness": "unconfirmed",
                "evidence": "Unverified.",
            },
        ],
    },
    "jordan-blank": {
        "hire_id": "H-001",
        "plan_version": 1,
        "plan_label": "none",
        "outcome_line": "One request went to Sam Ortiz. No tasks were created.",
        "readiness_label": "Needs attention",
        "attention_reasons": ["The role was not on the intake."],
        "next_owner": "Sam Ortiz",
        "next_action": "Confirm the role.",
        "messages": ["Ask Sam to confirm the role."],
        "failure": None,
        "tasks": [],
    },
    "jordan-proposed": {
        "hire_id": "H-001",
        "plan_version": 1,
        "plan_label": "proposed",
        "outcome_line": "Proposed plan. Not active until HR approval.",
        "readiness_label": "Needs attention",
        "attention_reasons": [
            "The plan is proposed and is not active.",
            "Policy acknowledgment is overdue and incomplete.",
            "No device is confirmed for the start.",
            "The first-day meeting is not confirmed.",
        ],
        "next_owner": "Alex Rivera",
        "next_action": "Await HR approval.",
        "messages": [],
        "failure": None,
        "tasks": [
            {
                "name": "Policy acknowledgment",
                "owner": "Jordan Lee, new hire",
                "due": "2026-02-26",
                "execution": "pending",
                "readiness": "unconfirmed",
                "evidence": "Unverified. Overdue.",
            },
            {
                "name": "Equipment readiness",
                "owner": "Taylor Brooks, IT fulfiller",
                "due": "2026-03-02",
                "execution": "pending",
                "readiness": "unconfirmed",
                "evidence": "Unverified.",
            },
            {
                "name": "First-day meeting",
                "owner": "Sam Ortiz, hiring manager",
                "due": "2026-03-02",
                "execution": "pending",
                "readiness": "unconfirmed",
                "evidence": "Unverified.",
            },
            {
                "name": "Customer-support tools orientation",
                "owner": "Sam Ortiz, hiring manager",
                "due": "2026-03-09",
                "execution": "pending",
                "readiness": "unconfirmed",
                "evidence": "Unverified.",
            },
        ],
    },
    "stub-failure": {
        "status": "error",
        "message": "No new verified fact was written.",
        "case": None,
    },
}

REQUIRED_SENTENCES = (
    "Active plan. Four tasks created. No approval hold.",
    "One request went to Sam Ortiz. No tasks were created.",
    "Proposed plan. Not active until HR approval.",
    "No new verified fact was written.",
)

FAILURE_SENTENCE = "No new verified fact was written."

tool_called = False


def reset_tool_called() -> None:
    global tool_called
    tool_called = False


def tool_was_called() -> bool:
    return tool_called


def prepared_cases_json() -> str:
    global tool_called
    tool_called = True
    return json.dumps(PREPARED_CASES, indent=2)


def report_has_required_sentences(text: str) -> bool:
    cursor = 0
    for sentence in REQUIRED_SENTENCES:
        found = text.find(sentence, cursor)
        if found < 0:
            return False
        cursor = found + len(sentence)
    return True
