const API = "";

const RILEY_FACTS =
  "Riley Chen, start 2026-03-16, role Customer Support Representative, office Austin, manager Morgan Hale";

const RILEY_BODY = {
  employee_name: "Riley Chen",
  start_date: "2026-03-16",
  role: "Customer Support Representative",
  office: "Austin",
  manager_name: "Morgan Hale",
};

const WORDS = {
  needs_attention: "Needs attention",
  ready: "Ready",
  pending: "Pending",
  complete: "Complete",
  confirmed: "Confirmed",
  unconfirmed: "Unconfirmed",
  blocked: "Blocked",
};

const LOST_CONTACT =
  "The page lost contact with the API. The outcome of this event is unknown. It is not recorded as a failed event. Retry sends the same event again.";

const POLL_TIMEOUT =
  "The page stopped waiting after 60 seconds. The outcome of this event is unknown. It is not recorded as a failed event. Retry sends the same event again.";

const JORDAN_BODY = {
  employee_name: "Jordan Lee",
  start_date: "2026-03-02",
  role: "",
  office: "Austin",
  manager_name: "Sam Ortiz",
};

const JORDAN_FACTS =
  "Jordan Lee, start 2026-03-02, role blank, office Austin, manager Sam Ortiz";

const ACTORS = {
  "actor-alex-rivera": "hr_coordinator",
  "actor-taylor-brooks": "it_fulfiller",
  "actor-sam-ortiz": "hiring_manager",
  "actor-morgan-hale": "hiring_manager",
  "actor-jordan-lee": "new_hire",
  "actor-riley-chen": "new_hire",
};

const TRACKED = new Set([
  "reply",
  "policy_question",
  "start_date_change",
  "deadline_reached",
  "hr_decision",
  "task_update",
]);

const eventTypeSelect = document.querySelector("#event-type");
const intakeFields = document.querySelector("#intake-fields");
const replyFields = document.querySelector("#reply-fields");
const senderSelect = document.querySelector("#sender");
const hireIdInput = document.querySelector("#hire-id");
const replyEventInput = document.querySelector("#reply-event-id");
const occurredInput = document.querySelector("#occurred-at");
const replyBody = document.querySelector("#reply-body");
const replyBodyName = document.querySelector("#reply-body-name");
const hrFields = document.querySelector("#hr-fields");
const taskFields = document.querySelector("#task-fields");
const taskName = document.querySelector("#task-name");
const taskAction = document.querySelector("#task-action");
const decisionType = document.querySelector("#decision-type");
const planVersionInput = document.querySelector("#plan-version");
const replyError = document.querySelector("#reply-error");
const scenarioSelect = document.querySelector("#scenario");
const scenarioError = document.querySelector("#scenario-error");
const scenarioFacts = document.querySelector("#scenario-facts");
const runButton = document.querySelector("#run");
const resetButton = document.querySelector("#reset");
const retryButton = document.querySelector("#retry");
const crewStatus = document.querySelector("#crew-status");
const demoLock = document.querySelector("#demo-lock");
const demoTokenInput = document.querySelector("#demo-token");
let demoToken = sessionStorage.getItem("demo-token") || "";
if (demoTokenInput) {
  demoTokenInput.value = demoToken;
  demoTokenInput.addEventListener("input", () => {
    demoToken = demoTokenInput.value.trim();
    sessionStorage.setItem("demo-token", demoToken);
  });
}
const statusDot = document.querySelector("#status-dot");
const statusDetail = document.querySelector("#status-detail");
const inlineError = document.querySelector("#inline-error");
const lastUpdated = document.querySelector("#last-updated");
const results = document.querySelector("#results");
const actionForm = document.querySelector("#action-form");
const startDateInput = document.querySelector("#start-date");
const startDateLabel = document.querySelector("#start-date-label");
const policyNote = document.querySelector("#policy-note");
const replyGuide = document.querySelector("#reply-guide");
const idWarning = document.querySelector("#id-warning");
const newEventButton = document.querySelector("#new-event");
const copyEventButton = document.querySelector("#copy-event");
const copyHireButton = document.querySelector("#copy-hire");
const scenarioClock = document.querySelector("#scenario-clock");
const statusLine = document.querySelector("#status-line");
const attention = document.querySelector("#attention");
const completion = document.querySelector("#completion");
const approveDialog = document.querySelector("#approve-dialog");
const approveCopy = document.querySelector("#approve-copy");
const approveConfirm = document.querySelector("#approve-confirm");
const approveCancel = document.querySelector("#approve-cancel");
const tabs = [...document.querySelectorAll("[role=tab]")];
const panels = {
  tasks: document.querySelector("#panel-tasks"),
  activity: document.querySelector("#panel-activity"),
  policy: document.querySelector("#panel-policy"),
  decisions: document.querySelector("#panel-decisions"),
};
let activeTab = "tasks";
let lastSubmitted = null;
let approveReady = false;

let machine = "idle";
let failedSnapshot = null;
let lastVerified = null;
let visibleError = null;
let validationError = false;
let updatedAt = null;
let statusText = "";
let savedEventId = null;
let recordedHireId = null;
let replayNote = false;
let replyValidation = "";

scenarioSelect.addEventListener("change", () => {
  if (scenarioSelect.value) {
    validationError = false;
  }
  render();
});

eventTypeSelect.addEventListener("change", () => {
  const defaults = {
    intake: "actor-alex-rivera",
    reply: "actor-taylor-brooks",
    policy_question: "actor-riley-chen",
    start_date_change: "actor-alex-rivera",
    deadline_reached: "actor-alex-rivera",
    hr_decision: "actor-alex-rivera",
    task_update: "actor-jordan-lee",
  };
  if (defaults[eventTypeSelect.value]) {
    senderSelect.value = defaults[eventTypeSelect.value];
  }
  if (TRACKED.has(eventTypeSelect.value)) {
    if (!hireIdInput.value.trim() && lastVerified) {
      hireIdInput.value = lastVerified.hire_id;
    }
    if (!replyEventInput.value.trim()) {
      replyEventInput.value = crypto.randomUUID();
    }
  }
  replyValidation = "";
  render();
});

actionForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (machine === "running") {
    return;
  }
  if (
    eventTypeSelect.value === "hr_decision" &&
    decisionType.value === "approve_held_plan" &&
    !approveReady
  ) {
    const hire = hireIdInput.value.trim() || "this hire";
    approveCopy.textContent = `Approve the held plan for ${hire} at plan version ${planVersionInput.value}. This records HR approval. It does not confirm missing evidence.`;
    approveDialog.showModal();
    return;
  }
  approveReady = false;
  if (TRACKED.has(eventTypeSelect.value)) {
    const missing = missingReplyField();
    if (missing) {
      replyValidation = `Enter the ${missing.name}.`;
      render();
      missing.focus();
      return;
    }
    beginTracked(trackedSnapshot());
    return;
  }
  const scenarioId = scenarioSelect.value;
  if (!scenarioId) {
    validationError = true;
    render();
    scenarioSelect.focus();
    return;
  }
  begin(snapshotFor(scenarioId));
});

resetButton.addEventListener("click", () => {
  if (machine === "running") {
    return;
  }
  machine = "idle";
  failedSnapshot = null;
  visibleError = null;
  validationError = false;
  replayNote = false;
  statusText = "";
  scenarioSelect.value = "";
  eventTypeSelect.value = "intake";
  replyBody.value = "";
  savedEventId = null;
  lastSubmitted = null;
  updatedAt = new Date();
  render();
});

newEventButton.addEventListener("click", () => {
  if (machine === "running") return;
  replyEventInput.value = crypto.randomUUID();
  render();
});

for (const guide of [replyGuide, policyNote]) {
  guide.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button || machine === "running") {
      return;
    }
    event.preventDefault();
    const before = {
      eventId: replyEventInput.value,
      sender: senderSelect.value,
      hireId: hireIdInput.value,
      occurred: occurredInput.value,
    };
    replyBody.value = button.textContent;
    replyEventInput.value = before.eventId;
    senderSelect.value = before.sender;
    hireIdInput.value = before.hireId;
    occurredInput.value = before.occurred;
    render();
  });
}

copyEventButton.addEventListener("click", () => copyText(replyEventInput.value));
copyHireButton.addEventListener("click", () => copyText(lastVerified?.hire_id || hireIdInput.value));

approveCancel.addEventListener("click", () => approveDialog.close());
approveConfirm.addEventListener("click", () => {
  approveReady = true;
  approveDialog.close();
  actionForm.requestSubmit();
});

for (const tab of tabs) {
  tab.addEventListener("click", () => selectTab(tab.id.replace("tab-", "")));
  tab.addEventListener("keydown", (event) => {
    const keys = ["ArrowRight", "ArrowLeft", "Home", "End"];
    if (!keys.includes(event.key)) return;
    event.preventDefault();
    const index = tabs.indexOf(tab);
    const next = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : event.key === "ArrowRight" ? (index + 1) % tabs.length : (index - 1 + tabs.length) % tabs.length;
    selectTab(tabs[next].id.replace("tab-", ""));
    tabs[next].focus();
  });
}

function selectTab(name) {
  activeTab = name;
  for (const tab of tabs) {
    const selected = tab.id === `tab-${name}`;
    tab.setAttribute("aria-selected", selected ? "true" : "false");
    tab.tabIndex = selected ? 0 : -1;
  }
  for (const [key, panel] of Object.entries(panels)) {
    panel.hidden = key !== name;
  }
}

function copyText(value) {
  if (!value) return;
  navigator.clipboard?.writeText(value).catch(() => {});
}

retryButton.addEventListener("click", () => {
  if (machine !== "idle" || !failedSnapshot || !visibleError) {
    return;
  }
  const again = cloneSnapshot(failedSnapshot);
  if (TRACKED.has(again.kind)) {
    beginTracked(again);
    return;
  }
  begin(again);
});

function snapshotFor(scenarioId) {
  if (!savedEventId) {
    savedEventId = crypto.randomUUID();
  }
  return {
    scenario_id: scenarioId,
    event_id: savedEventId,
    body: structuredClone(scenarioId === "jordan-blank" ? JORDAN_BODY : RILEY_BODY),
    occurred_at:
      scenarioId === "jordan-blank" ? "2026-02-27T09:00:00-06:00" : "2026-03-13T09:00:00-05:00",
  };
}

function cloneSnapshot(snapshot) {
  return structuredClone(snapshot);
}

function missingReplyField() {
  const labels = {
    policy_question: "question",
    start_date_change: "new start date",
    hr_decision: "rationale",
  };
  const textName = labels[eventTypeSelect.value] ?? "message";
  const fields = [
    [hireIdInput, "hire id"],
    [replyEventInput, "event id"],
    [occurredInput, "occurred at"],
  ];
  if (eventTypeSelect.value === "start_date_change") {
    fields.push([startDateInput, textName]);
  } else if (eventTypeSelect.value !== "deadline_reached" && eventTypeSelect.value !== "task_update") {
    fields.push([replyBody, textName]);
  }
  for (const [field, name] of fields) {
    if (!field.value.trim()) {
      return { focus: () => field.focus(), name };
    }
  }
  return null;
}

function trackedSnapshot() {
  const actorId = senderSelect.value;
  const kind = eventTypeSelect.value;
  let body = replyBody.value.trim();
  if (kind === "hr_decision") {
    body = {
      decision_type: decisionType.value,
      rationale: replyBody.value.trim(),
      plan_version: Number(planVersionInput.value),
    };
  }
  if (kind === "task_update") {
    body = { task: taskName.value, action: taskAction.value };
  }
  if (kind === "start_date_change") {
    body = startDateInput.value;
  }
  return {
    kind,
    event_id: replyEventInput.value.trim(),
    hire_id: hireIdInput.value.trim(),
    actor_id: actorId,
    actor_role: ACTORS[actorId],
    occurred_at: occurredInput.value.trim(),
    body,
  };
}

async function begin(snapshot) {
  const frozen = cloneSnapshot(snapshot);
  machine = "running";
  validationError = false;
  visibleError = null;
  replayNote = false;
  statusText = "Processing event";
  render();
  document.body.dataset.submittedScenario = frozen.scenario_id;
  document.body.dataset.eventId = frozen.event_id;

  let response;
  try {
    response = await fetch(`${API}/events`, {
      method: "POST",
      headers: eventHeaders(),
      body: JSON.stringify({
        event_id: frozen.event_id,
        event_type: "intake",
        actor_id: "actor-alex-rivera",
        actor_role: "hr_coordinator",
        occurred_at: frozen.occurred_at,
        body: frozen.body,
      }),
      signal: AbortSignal.timeout(60000),
    });
  } catch {
    fail(frozen, LOST_CONTACT);
    return;
  }

  const ack = await readJson(response);
  if (!response.ok) {
    fail(frozen, refusalText(ack));
    return;
  }
  if (ack.event_id !== frozen.event_id || typeof ack.hire_id !== "string" || !ack.hire_id) {
    fail(frozen, LOST_CONTACT);
    return;
  }

  statusText = `Accepted. Event ${ack.event_id}. Hire ${ack.hire_id}.`;
  render();

  let hireResponse;
  try {
    hireResponse = await fetch(`${API}/hires/${encodeURIComponent(ack.hire_id)}`, {
      signal: AbortSignal.timeout(60000),
    });
  } catch {
    fail(frozen, LOST_CONTACT);
    return;
  }
  const hire = await readJson(hireResponse);
  if (!hireResponse.ok || hire.hire_id !== ack.hire_id) {
    fail(frozen, "The intake was accepted, but the hire could not be read. Retry sends the same event again.");
    return;
  }
  if (hire.failure) {
    const failureText = hire.failure.message || "The hire has a failure recorded.";
    fail(frozen, failureText);
    return;
  }

  replayNote = recordedHireId === hire.hire_id;
  recordedHireId = hire.hire_id;
  lastVerified = hire;
  if (!hireIdInput.value.trim()) {
    hireIdInput.value = hire.hire_id;
  }
  machine = "done";
  failedSnapshot = null;
  visibleError = null;
  statusText = "Event complete";
  lastSubmitted = cloneSnapshot(frozen);
  updatedAt = new Date();
  render();
}

async function beginTracked(snapshot) {
  const frozen = cloneSnapshot(snapshot);
  const prior = lastVerified;
  const alreadyComplete = Boolean(
    prior && (prior.events ?? []).some((event) => event.event_id === frozen.event_id && event.state === "complete"),
  );
  machine = "running";
  replyValidation = "";
  visibleError = null;
  replayNote = false;
  statusText = "Processing event";
  lastSubmitted = cloneSnapshot(frozen);
  render();
  document.body.dataset.eventId = frozen.event_id;

  let response;
  try {
    response = await fetch(`${API}/events`, {
      method: "POST",
      headers: eventHeaders(),
      body: JSON.stringify({
        event_id: frozen.event_id,
        event_type: frozen.kind,
        hire_id: frozen.hire_id,
        actor_id: frozen.actor_id,
        actor_role: frozen.actor_role,
        occurred_at: frozen.occurred_at,
        body: frozen.body,
      }),
      signal: AbortSignal.timeout(60000),
    });
  } catch {
    fail(frozen, LOST_CONTACT);
    return;
  }

  const ack = await readJson(response);
  if (!response.ok) {
    fail(frozen, refusalText(ack));
    return;
  }
  if (ack.event_id !== frozen.event_id || ack.hire_id !== frozen.hire_id) {
    fail(frozen, LOST_CONTACT);
    return;
  }

  statusText = `Accepted. Event ${ack.event_id}. Hire ${ack.hire_id}. A result or a visible failure is expected within 60 seconds.`;
  render();

  let polled;
  try {
    polled = await pollEvent(ack.hire_id, ack.event_id);
  } catch {
    fail(frozen, LOST_CONTACT);
    return;
  }
  if (polled.timedOut) {
    fail(frozen, POLL_TIMEOUT);
    return;
  }
  const found = (polled.hire.events ?? []).find((event) => event.event_id === ack.event_id);
  if (found && found.state === "failed") {
    lastVerified = polled.hire;
    const code = found.failure && found.failure.code ? found.failure.code : "model_failure";
    const message = found.failure && found.failure.message ? found.failure.message : "The event failed.";
    const alreadySaid = message.includes("No new verified fact was written.");
    const suffix = frozen.kind === "policy_question" || alreadySaid ? "" : " No new verified fact was written.";
    fail(frozen, `${code}: ${message}${suffix}`);
    return;
  }

  replayNote = alreadyComplete;
  recordedHireId = polled.hire.hire_id;
  lastVerified = polled.hire;
  machine = "done";
  failedSnapshot = null;
  visibleError = null;
  statusText = "Event complete";
  updatedAt = new Date();
  render();
}

async function pollEvent(hireId, eventId) {
  const deadline = Date.now() + 60000;
  while (Date.now() < deadline) {
    const response = await fetch(`${API}/hires/${encodeURIComponent(hireId)}`, {
      signal: AbortSignal.timeout(10000),
    });
    const hire = await readJson(response);
    if (!response.ok) {
      throw new Error("hire");
    }
    const found = (hire.events ?? []).find((event) => event.event_id === eventId);
    if (found && (found.state === "complete" || found.state === "failed")) {
      return { hire, timedOut: false };
    }
    statusText = `Processing event ${eventId}. The case on screen is the last verified case.`;
    render();
    await delay(500);
  }
  return { hire: null, timedOut: true };
}

function delay(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function fail(snapshot, message) {
  machine = "idle";
  failedSnapshot = cloneSnapshot(snapshot);
  visibleError = message;
  replayNote = false;
  statusText = "";
  updatedAt = new Date();
  render();
}

function eventHeaders() {
  const headers = { "Content-Type": "application/json" };
  if (demoToken) {
    headers["X-Demo-Token"] = demoToken;
  }
  return headers;
}

function refusalText(body) {
  if (body.code === "event_mismatch") {
    return "event_mismatch: This event id was already used with different contents. The new contents were not applied. No second hire was created.";
  }
  if (body.code === "conflict") {
    const id = body.event_id ? ` Event ${body.event_id}.` : "";
    return `conflict: One event is already running. This submission was not started.${id}`;
  }
  if (body.code === "unreadable_input") {
    const message = body.message || "The intake could not be read.";
    return `unreadable_input: ${message} No new verified fact was written.`;
  }
  if (body.code && body.message) {
    return `${body.code}: ${body.message}`;
  }
  if (body.message) {
    return body.message;
  }
  return "The intake API refused this event.";
}

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function render() {
  const running = machine === "running";
  const showRetry = machine === "idle" && failedSnapshot !== null && visibleError !== null;
  const kind = eventTypeSelect.value;
  const label = statusLabel();

  crewStatus.textContent = label;
  statusLine.textContent = label;
  statusDetail.textContent = statusText === label ? "" : statusText;
  inlineError.hidden = !visibleError;
  inlineError.textContent = visibleError ?? "";
  lastUpdated.textContent = updatedAt
    ? `Last received: ${updatedAt.toLocaleString()}`
    : "Last received: not yet";
  scenarioClock.textContent = `Scenario clock: ${occurredInput.value || "not set"} · Austin time`;

  eventTypeSelect.disabled = running;
  const tracked = TRACKED.has(kind);
  intakeFields.hidden = kind !== "intake";
  replyFields.hidden = !tracked;
  hrFields.hidden = kind !== "hr_decision";
  taskFields.hidden = kind !== "task_update";
  const hideBody = kind === "intake" || kind === "task_update" || kind === "start_date_change";
  replyBody.hidden = hideBody;
  document.querySelector("#reply-body-label").hidden = hideBody;
  startDateLabel.hidden = kind !== "start_date_change";
  policyNote.hidden = kind !== "policy_question";
  replyGuide.hidden = kind !== "reply";
  const names = {
    policy_question: "Question",
    hr_decision: "Rationale",
    deadline_reached: "Note",
  };
  replyBodyName.textContent = names[kind] ?? "Message";
  const submitLabels = {
    intake: "Create intake",
    reply: "Send reply",
    policy_question: "Ask question",
    start_date_change: "Update start date",
    deadline_reached: "Check deadlines",
    hr_decision: "Record decision",
    task_update: "Record status",
  };
  runButton.textContent = submitLabels[kind] ?? "Submit";
  scenarioSelect.disabled = running;
  senderSelect.disabled = running;
  hireIdInput.disabled = running;
  replyEventInput.disabled = running;
  occurredInput.disabled = running;
  replyBody.disabled = running;
  startDateInput.disabled = running;
  runButton.disabled = running;
  for (const button of document.querySelectorAll(".guide button")) {
    button.disabled = running;
  }
  resetButton.disabled = running;
  newEventButton.disabled = running;
  retryButton.hidden = !showRetry;
  retryButton.disabled = running || !showRetry;
  idWarning.hidden = !editedSubmittedId();

  if (validationError) {
    scenarioError.hidden = false;
    scenarioSelect.setAttribute("aria-invalid", "true");
  } else {
    scenarioError.hidden = true;
    scenarioSelect.removeAttribute("aria-invalid");
  }
  replyError.hidden = !replyValidation;
  replyError.textContent = replyValidation;
  const facts = { "riley-complete": RILEY_FACTS, "jordan-blank": JORDAN_FACTS };
  scenarioFacts.hidden = !facts[scenarioSelect.value];
  scenarioFacts.textContent = facts[scenarioSelect.value] ?? "";
  renderCase();
}

function statusLabel() {
  if (visibleError && visibleError.includes("lost contact")) {
    return "Connection lost — outcome unknown";
  }
  if (visibleError && visibleError.includes("stopped waiting")) {
    return "Still waiting — outcome unknown";
  }
  if (visibleError) {
    return "Event failed";
  }
  if (machine === "running") {
    return "Processing event";
  }
  if (machine === "done" && replayNote) {
    return "Already processed. No additional work added.";
  }
  if (machine === "done") {
    return "Event complete";
  }
  return "Ready to submit";
}

function editedSubmittedId() {
  if (!lastSubmitted || eventTypeSelect.value === "intake") {
    return false;
  }
  const current = trackedSnapshot();
  return current.event_id === lastSubmitted.event_id && JSON.stringify(current) !== JSON.stringify(lastSubmitted);
}

function renderCase() {
  const hire = lastVerified;
  const heading = document.querySelector("#hire-heading");
  const subtitle = document.querySelector("#hire-subtitle");
  const avatar = document.querySelector("#avatar");
  const badge = document.querySelector("#readiness-badge");
  const meta = document.querySelector("#hire-meta");
  if (!hire) {
    heading.textContent = "No case loaded";
    subtitle.textContent = "Start an intake to create a fictional case.";
    avatar.textContent = "—";
    badge.hidden = true;
    meta.replaceChildren();
    attention.hidden = true;
    panels.tasks.replaceChildren(emptyLine("No tasks yet."));
    panels.activity.replaceChildren(emptyLine("No activity yet."));
    panels.policy.replaceChildren(policyEmpty());
    panels.decisions.replaceChildren(emptyLine("No HR decision is recorded."));
    completion.hidden = true;
    return;
  }
  const name = hire.employee_name || "Unnamed hire";
  heading.textContent = name;
  subtitle.textContent = `${hire.role || "Role not recorded"} · ${hire.location || "—"}`;
  avatar.textContent = initials(name);
  badge.hidden = false;
  badge.textContent = WORDS[hire.readiness] ?? String(hire.readiness ?? "—");
  badge.className = `badge ${hire.readiness === "ready" ? "ok" : "warn"}`;
  meta.replaceChildren(
    metaItem("Start date", hire.start_date || "—"),
    metaItem("Hiring manager", hire.manager_name || "—"),
    metaItem("Plan", `${activationLabel(hire.activation)} · Version ${hire.plan_version ?? "None"}`),
    metaItem("Hire ID", hire.hire_id),
  );
  const reasons = hire.readiness_reasons ?? [];
  attention.hidden = reasons.length === 0;
  attention.replaceChildren();
  if (reasons.length > 0) {
    const title = document.createElement("h3");
    title.textContent = reasons.length === 1 ? "One item needs attention" : `${reasons.length} items need attention`;
    attention.append(title);
    for (const reason of reasons) {
      const lineItem = document.createElement("p");
      lineItem.textContent = reason;
      attention.append(lineItem);
    }
  }
  const happened = whatHappened(hire);
  completion.hidden = !happened;
  completion.replaceChildren();
  if (happened) {
    completion.append(happened);
    const view = document.createElement("button");
    view.type = "button";
    view.textContent = "View result";
    view.addEventListener("click", () => selectTab(resultTab()));
    completion.append(view);
  }
  panels.tasks.replaceChildren(...taskRows(hire));
  panels.activity.replaceChildren(...activityRows(hire));
  panels.policy.replaceChildren(policyPanel(hire));
  panels.decisions.replaceChildren(decisionPanel(hire));
}

function resultTab() {
  const kind = eventTypeSelect.value;
  if (kind === "policy_question") return "policy";
  if (kind === "hr_decision") return "decisions";
  return "tasks";
}

function emptyLine(text) {
  const p = document.createElement("p");
  p.className = "empty panel-body";
  p.textContent = text;
  return p;
}

function metaItem(term, value) {
  const wrap = document.createElement("div");
  const dt = document.createElement("dt");
  dt.textContent = term;
  const dd = document.createElement("dd");
  dd.textContent = value;
  wrap.append(dt, dd);
  return wrap;
}

function initials(name) {
  const parts = name.split(" ").filter(Boolean);
  return parts.slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "—";
}

function activationLabel(value) {
  return { active: "Active", proposed: "Proposed", held: "Held", review: "In review" }[value] ?? "—";
}

function taskRows(hire) {
  const tasks = hire.tasks ?? [];
  if (tasks.length === 0) return [emptyLine("Zero tasks were created.")];
  return tasks.map((task) => {
    const article = document.createElement("article");
    article.className = "task";
    const top = document.createElement("div");
    top.className = "task-line";
    const title = document.createElement("h3");
    title.textContent = task.name;
    const chip = document.createElement("span");
    chip.className = `chip ${task.readiness === "blocked" ? "bad" : task.readiness === "confirmed" || task.execution_status === "complete" ? "ok" : "warn"}`;
    chip.textContent = WORDS[task.readiness] ?? String(task.readiness);
    top.append(title, chip);
    const owner = document.createElement("p");
    owner.className = "task-meta";
    owner.textContent = `${task.owner || "—"} · Due ${task.due_date || "—"}`;
    const state = document.createElement("p");
    state.className = "task-meta";
    state.textContent = `Execution ${WORDS[task.execution_status] ?? task.execution_status} · Readiness ${WORDS[task.readiness] ?? task.readiness}`;
    const flags = document.createElement("p");
    flags.className = "task-meta";
    flags.textContent = `Overdue: ${task.overdue ? "yes" : "no"} · Escalated: ${task.escalated ? "yes" : "no"}`;
    const evidence = document.createElement("p");
    evidence.className = "task-meta";
    const refs = Array.isArray(task.evidence_refs) && task.evidence_refs.length ? task.evidence_refs.join(", ") : "None recorded";
    evidence.textContent = `Evidence: ${refs}`;
    const reason = blockedTaskReason(hire, task);
    article.append(top, owner, state, flags, evidence);
    if (reason) {
      const extra = document.createElement("p");
      extra.textContent = reason;
      article.append(extra);
    }
    return article;
  });
}

function activityRows(hire) {
  const messages = hire.messages ?? [];
  if (messages.length === 0) return [emptyLine("No activity yet.")];
  return messages.map((message) => {
    const article = document.createElement("article");
    article.className = "event";
    const title = document.createElement("h3");
    if (typeof message === "string") {
      title.textContent = message;
      article.append(title);
      return article;
    }
    title.textContent = message.kind || "Message";
    const body = document.createElement("p");
    body.textContent = message.body || "";
    const who = document.createElement("p");
    who.textContent = message.actor_id || "No actor recorded";
    article.append(title, who, body);
    if (message.deadline) {
      const due = document.createElement("p");
      due.textContent = `Deadline ${message.deadline}`;
      article.append(due);
    }
    if (message.citation) {
      const cite = document.createElement("p");
      cite.textContent = `Citation ${message.citation}`;
      article.append(cite);
    }
    return article;
  });
}

function policyEmpty() {
  const wrap = document.createElement("div");
  wrap.className = "panel-body";
  const title = document.createElement("h3");
  title.textContent = "No policy questions yet.";
  const note = document.createElement("p");
  note.textContent = "Supported question patterns are limited. A published answer is the exact approved passage and its citation. It does not confirm equipment.";
  wrap.append(title, note);
  return wrap;
}

function policyPanel(hire) {
  const questions = (hire.messages ?? []).filter((message) => message && message.kind === "policy_question");
  if (questions.length === 0) return policyEmpty();
  const wrap = document.createElement("div");
  for (const question of questions) {
    const card = document.createElement("article");
    card.className = "policy-card";
    const asked = document.createElement("h3");
    asked.textContent = question.body || "Question";
    card.append(asked);
    const related = (hire.messages ?? []).filter((message) => message && message.event_id === question.event_id && message.kind !== "policy_question");
    const lines = policyLines(related);
    if (lines) card.append(lines);
    else {
      const none = document.createElement("p");
      none.textContent = "No policy answer was published.";
      card.append(none);
    }
    wrap.append(card);
  }
  const limit = document.createElement("p");
  limit.className = "panel-body";
  limit.textContent = "Supported question patterns are limited.";
  wrap.append(limit);
  return wrap;
}

function decisionPanel(hire) {
  const wrap = document.createElement("div");
  wrap.className = "panel-body";
  const state = document.createElement("h3");
  state.textContent = `Plan is ${activationLabel(hire.activation).toLowerCase()}.`;
  const note = document.createElement("p");
  note.textContent = hire.activation === "active" && !(hire.decisions ?? []).some((item) => item.decision_type)
    ? "This case did not require an approval hold. HR approval does not confirm missing evidence."
    : "HR approval does not confirm missing evidence.";
  wrap.append(state, note);
  const decisions = (hire.decisions ?? []).filter((item) => item && item.decision_type);
  if (decisions.length === 0 && hire.activation !== "proposed" && hire.activation !== "held") {
    return wrap;
  }
  if (hire.activation === "proposed") {
    const pending = document.createElement("p");
    pending.textContent = "Proposed plan. It is not active until HR approves it.";
    wrap.append(pending);
  }
  for (const decision of decisions) {
    const card = document.createElement("article");
    card.className = "decision";
    const title = document.createElement("h3");
    title.textContent = decision.decision_type;
    const who = document.createElement("p");
    who.textContent = `${decision.actor_id || "—"} · plan version ${decision.plan_version ?? "—"}`;
    const rationale = document.createElement("p");
    rationale.textContent = decision.rationale || decision.rule_result || "";
    card.append(title, who, rationale);
    if (decision.needs_review) {
      const flag = document.createElement("p");
      flag.textContent = "Needs review";
      card.append(flag);
    }
    wrap.append(card);
  }
  return wrap;
}

function whatHappened(hire) {
  const lines = Array.isArray(hire.case_summary) ? hire.case_summary : [];
  if (lines.length === 0) {
    return null;
  }
  const block = document.createElement("div");
  const heading = document.createElement("p");
  heading.className = "case-label";
  heading.textContent = "What happened";
  block.append(heading);
  for (const text of lines) {
    const line = document.createElement("p");
    line.textContent = text;
    block.append(line);
  }
  return block;
}

function policyLines(messages) {
  const answers = messages.filter((message) => message.kind === "policy_answer");
  const referral = messages.some((message) => message.kind === "policy_referral");
  const review = messages.some((message) => message.kind === "policy_review");
  if (answers.length === 0 && !referral && !review) {
    return null;
  }
  const block = document.createDocumentFragment();
  if (referral) {
    const line = document.createElement("p");
    line.textContent = "Outside the pack. Routed to HR. No policy answer was published.";
    block.append(line);
  }
  if (review) {
    const line = document.createElement("p");
    line.textContent = "Manual review. No policy conclusion was published.";
    block.append(line);
  }
  for (const answer of answers) {
    const line = document.createElement("p");
    line.textContent = `${answer.citation}: ${answer.body}`;
    block.append(line);
  }
  return block;
}

function caseList(hire) {
  const dl = document.createElement("dl");
  addPair(dl, "Activation", hire.activation ?? "active");
  addPair(dl, "Readiness", WORDS[hire.readiness] ?? String(hire.readiness));
  addReasons(dl, hire.readiness_reasons ?? []);
  addPair(dl, "Start date", hire.start_date);
  addPair(dl, "Role", hire.role);
  addPair(dl, "Location", hire.location);
  addTasks(dl, hire);
  addPair(dl, "Hire id", hire.hire_id);
  addPair(dl, "Event id", document.body.dataset.eventId ?? "");
  addPair(dl, "Plan version", hire.plan_version == null ? "None" : String(hire.plan_version));
  if (hire.failure) {
    addPair(dl, "Failure", hire.failure.message || JSON.stringify(hire.failure));
  }
  return dl;
}

function addPair(dl, term, value) {
  const dt = document.createElement("dt");
  dt.textContent = term;
  const dd = document.createElement("dd");
  dd.textContent = value;
  dl.append(dt, dd);
}

function addReasons(dl, reasons) {
  const dt = document.createElement("dt");
  dt.textContent = "What needs attention";
  const dd = document.createElement("dd");
  if (reasons.length === 0) {
    dd.textContent = "Nothing needs attention.";
  } else {
    const list = document.createElement("ul");
    for (const reason of reasons) {
      const item = document.createElement("li");
      item.textContent = reason;
      list.append(item);
    }
    dd.append(list);
  }
  dl.append(dt, dd);
}

function addTasks(dl, hire) {
  const dt = document.createElement("dt");
  dt.textContent = "Tasks";
  const dd = document.createElement("dd");
  const tasks = hire.tasks ?? [];
  if (tasks.length === 0) {
    dd.textContent = "Zero tasks were created.";
    dl.append(dt, dd);
    return;
  }
  const list = document.createElement("ul");
  list.className = "tasks";
  for (const task of tasks) {
    const item = document.createElement("li");
    const evidence = Array.isArray(task.evidence_refs) && task.evidence_refs.length > 0
      ? task.evidence_refs.join(", ")
      : "None recorded";
    const rows = [
      line("Task", task.name),
      line("Owner", task.owner),
      line("Execution", WORDS[task.execution_status] ?? String(task.execution_status)),
      line("Readiness", WORDS[task.readiness] ?? String(task.readiness)),
    ];
    const reason = blockedTaskReason(hire, task);
    if (reason) {
      rows.push(line("Reason", reason));
    }
    rows.push(
      line("Due", task.due_date),
      line("Overdue", task.overdue ? "yes" : "no"),
      line("Escalated", task.escalated ? "yes" : "no"),
      line("Evidence", evidence),
    );
    item.append(...rows);
    list.append(item);
  }
  dd.append(list);
  dl.append(dt, dd);
}

function blockedTaskReason(hire, task) {
  if (!task || task.readiness !== "blocked") {
    return "";
  }
  const reasons = (hire.readiness_reasons ?? []).filter((reason) => typeof reason === "string" && reason.trim());
  const otherNames = (hire.tasks ?? [])
    .filter((other) => other && other.name && other.name !== task.name)
    .map((other) => other.name.toLowerCase());
  const own = reasons.filter((reason) => {
    const text = reason.toLowerCase();
    return !otherNames.some((name) => text.includes(name));
  });
  return own.join(" ");
}

function followUpMessages(hire) {
  return (hire.messages ?? []).filter(
    (message) => message && (message.kind === "follow_up" || message.kind === "role_follow_up"),
  );
}

function line(name, value) {
  const p = document.createElement("p");
  const strong = document.createElement("strong");
  strong.textContent = `${name}: `;
  p.append(strong, document.createTextNode(value ?? ""));
  return p;
}

render();

fetch(`${API}/health`)
  .then((response) => response.json())
  .then((body) => {
    if (body && body.demo_lock && demoLock) {
      demoLock.hidden = false;
    }
  })
  .catch(() => {});
