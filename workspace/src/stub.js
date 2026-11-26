/**
 * Sprint 3 temporary adapters. They do not replace the SAD section 4
 * submit-event and hire-read contracts. No network and no model call.
 */

const ERROR_PAYLOAD = {
  status: "error",
  message: "No new verified fact was written.",
  case: null,
};

const CASES = {
  "riley-complete": {
    hire_id: "H-002",
    plan_version: 1,
    plan_label: "active",
    outcome_line: "Active plan. Four tasks created. No approval hold.",
    readiness_label: "Needs attention",
    attention_reasons: [
      "Policy acknowledgment is overdue and incomplete.",
      "No device is confirmed for the start.",
      "The first-day meeting is not confirmed.",
    ],
    next_owner: "Riley Chen",
    next_action: "Record the policy acknowledgment.",
    messages: [],
    failure: null,
    tasks: [
      {
        name: "Policy acknowledgment",
        owner: "Riley Chen, new hire",
        due: "2026-03-12",
        execution: "pending",
        readiness: "unconfirmed",
        evidence: "Unverified. Overdue.",
      },
      {
        name: "Equipment readiness",
        owner: "Taylor Brooks, IT fulfiller",
        due: "2026-03-16",
        execution: "pending",
        readiness: "unconfirmed",
        evidence: "Unverified.",
      },
      {
        name: "First-day meeting",
        owner: "Morgan Hale, hiring manager",
        due: "2026-03-16",
        execution: "pending",
        readiness: "unconfirmed",
        evidence: "Unverified.",
      },
      {
        name: "Customer-support tools orientation",
        owner: "Morgan Hale, hiring manager",
        due: "2026-03-23",
        execution: "pending",
        readiness: "unconfirmed",
        evidence: "Unverified.",
      },
    ],
  },
  "jordan-blank": {
    hire_id: "H-001",
    plan_version: 1,
    plan_label: "none",
    outcome_line: "One request went to Sam Ortiz. No tasks were created.",
    readiness_label: "Needs attention",
    attention_reasons: ["The role was not on the intake."],
    next_owner: "Sam Ortiz",
    next_action: "Confirm the role.",
    messages: ["Ask Sam to confirm the role."],
    failure: null,
    tasks: [],
  },
  "jordan-proposed": {
    hire_id: "H-001",
    plan_version: 1,
    plan_label: "proposed",
    outcome_line: "Proposed plan. Not active until HR approval.",
    readiness_label: "Needs attention",
    attention_reasons: [
      "The plan is proposed and is not active.",
      "Policy acknowledgment is overdue and incomplete.",
      "No device is confirmed for the start.",
      "The first-day meeting is not confirmed.",
    ],
    next_owner: "Alex Rivera",
    next_action: "Await HR approval.",
    messages: [],
    failure: null,
    tasks: [
      {
        name: "Policy acknowledgment",
        owner: "Jordan Lee, new hire",
        due: "2026-02-26",
        execution: "pending",
        readiness: "unconfirmed",
        evidence: "Unverified. Overdue.",
      },
      {
        name: "Equipment readiness",
        owner: "Taylor Brooks, IT fulfiller",
        due: "2026-03-02",
        execution: "pending",
        readiness: "unconfirmed",
        evidence: "Unverified.",
      },
      {
        name: "First-day meeting",
        owner: "Sam Ortiz, hiring manager",
        due: "2026-03-02",
        execution: "pending",
        readiness: "unconfirmed",
        evidence: "Unverified.",
      },
      {
        name: "Customer-support tools orientation",
        owner: "Sam Ortiz, hiring manager",
        due: "2026-03-09",
        execution: "pending",
        readiness: "unconfirmed",
        evidence: "Unverified.",
      },
    ],
  },
};

let rememberedScenarioId = null;

export function startRun(snapshot) {
  rememberedScenarioId = snapshot.scenario_id;
  return Promise.resolve({
    run_id: "run-stub-1",
    scenario_id: snapshot.scenario_id,
    accepted: true,
  });
}

export function getRunStatus(runId) {
  if (runId !== "run-stub-1" || !Object.hasOwn(CASES, rememberedScenarioId)) {
    return Promise.resolve(structuredClone(ERROR_PAYLOAD));
  }
  return Promise.resolve({
    status: "case",
    case: structuredClone(CASES[rememberedScenarioId]),
  });
}

export function forgetLastScenario() {
  rememberedScenarioId = null;
}
