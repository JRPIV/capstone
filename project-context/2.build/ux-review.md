# UX Review

## Context & Instructions

Rendered review of the Sprint 3 page against `project-context/2.build/frontend.md`, which the operator approved as a sprint exception to `project-context/1.define/ux.md`. The full UX contract stays in force for the MVP. This review does not treat that exception as a defect.

## Input Requirements

**UX specification**: `project-context/1.define/ux.md` (approved). Sprint page: `project-context/2.build/frontend.md`.
**PRD / stories**: `project-context/1.define/prd.md` Appendix A, D1 and D2 labels used by the fixtures.
**frontend.md**: `project-context/2.build/frontend.md`
**Renderer**: Cursor browser
**Viewports inspected**: 1920×1080 (primary exercise). 1024×768 (overflow check on the empty idle page only).

### 1. Scope

- **Exercised:** `/` of the static page. Idle with no scenario. Validation error. Running. Stub-failure error. Retry after the select changed. Riley active plan. Jordan held intake. Jordan proposed plan. Reset.
- **Not tested:** 1280×800. A full keyboard pass. Assistive technology. Contrast measured with a tool. Playwright snapshots. The full `ux.md` event form and resilience paths, which this sprint excludes.
- **Tool and viewports:** Cursor browser. 1920×1080 and 1024×768.
- **Evidence:** Observed in the browser session. No screenshot was committed to the repo.

### 2. Functional gate

| ID | Route | State | Viewport | Result | Evidence | Notes |
|----|-------|-------|----------|--------|----------|-------|
| F-001 | `/` | idle, empty | 1920×1080 | passed | Browser snapshot | Crew: idle. “No result yet. Run one event to see the case.” Retry hidden. |
| F-002 | `/` | validation | 1920×1080 | passed | Browser snapshot | Run with no scenario stays idle, shows “Choose a scenario.”, and focuses the select, which is marked invalid. |
| F-003 | `/` | running | 1920×1080 | passed | Browser snapshot | Crew: running. Run, Reset, and the select are disabled. Prior case, when one exists, is labeled “Last verified case”. |
| F-004 | `/` | done, Riley | 1920×1080 | passed | Results text | Verified case. Active plan. Needs attention. Four tasks. H-002. Not Ready. |
| F-005 | `/` | done, held | 1920×1080 | passed | Results text | “No tasks were created.” Plan: No plan. Stored message to Sam Ortiz. H-001. |
| F-006 | `/` | done, proposed | 1920×1080 | passed | Results text | “Proposed plan. Not active until HR approval.” Plan: Proposed. Four tasks. |
| F-007 | `/` | error, then Retry | 1920×1080 | passed | Page data | After a stub failure, changing the select to Riley and pressing Retry resubmitted `stub-failure`. Results did not become Riley’s plan. |
| F-008 | `/` | reset | 1920×1080 | passed | Browser snapshot | Select cleared. Results emptied. Crew: idle. Retry hidden. Last updated changed. |

### 3. Mechanical gate

| ID | Check | Tool | Result | Evidence | Notes |
|----|-------|------|--------|----------|-------|
| M-001 | Keyboard, primary task | Cursor browser key event | not tested | Tab did not move focus | The select received focus from a click. The tool’s Tab event left focus on the select, so the sequence was not confirmed. |
| M-002 | Visible focus | stylesheet read | not tested | `:focus-visible` rule is present | The ring was not observed, because the key event did not apply `:focus-visible`. |
| M-003 | Contrast spot check | source colors | not tested | `styles.css` uses the specified text pairs | No measured contrast check. |
| M-004 | Target size | computed style | passed | Select `min-height` 32px | The rule is `min-height: 2rem` on `select` and `button`. |
| M-005 | Automated a11y scan | none | not tested | — | No scanner was run. |
| M-006 | Visual regression | Playwright Test | not tested | — | See section 3b. |

### 3b. Visual regression

- **Command:** none
- **Browser channel and viewports:** not run
- **Snapshot directory:** none
- **Last baseline Audit:** none
- **Skip rationale:** The approved Sprint 3 spec limits the page to four files and no package manifest. A first Playwright baseline also waits until Human judgment has no open high-severity finding, or the operator accepts the findings. This review does not take that baseline.

### 4. Human judgment gate

The page is one column, in the order banner, Inputs, Run, Results. The stub sentence is visible under the crew line. Riley is not shown as Ready. The proposed plan is labeled not active. The held intake lists zero tasks.

| ID | Finding | Route | State | Viewport | User impact | Severity | Resolution | Evidence |
|----|---------|-------|-------|----------|-------------|----------|------------|----------|
| H-001 | None against the approved sprint spec | `/` | done | 1920×1080 | — | — | — | Browser session |

### 5. Findings

No open finding against the approved sprint spec. M-001, M-002, M-003, M-005, and M-006 are not tested. They are not passes.

### 6. Remaining limitations

- Keyboard traversal, the visible focus ring, and measured contrast were not confirmed in the browser.
- 1280×800 was not opened. 1024×768 was checked only for horizontal overflow on the empty page (`scrollWidth` 1024, no overflow).
- Playwright snapshots were not created.
- The page is the sprint exception. It does not implement the full `ux.md` form or the SAD submit-event client.

## Sources

- `project-context/1.define/ux.md`
- `project-context/2.build/frontend.md`
- `project-context/1.define/prd.md` Appendix A
- Cursor browser session on `http://127.0.0.1:8080/workspace/`

## Assumptions

- Divergence from the full `ux.md` state model and form is the operator-approved Sprint 3 exception, not a defect in this review.
- The temporary server that was used for the review served the repository root, so the page URL included `/workspace/`. The launch command in the operator reply serves the `workspace/` directory itself.

## Open Questions

None for this increment. A later keyboard pass can close M-001 and M-002.

## Audit

- **Persona ID:** frontend-eng
- **Action:** review-ui
- **Timestamp:** 2026-11-20T04:50:00Z
- **Renderer:** Cursor browser
- **Viewports:** 1920×1080 exercised. 1024×768 overflow check only.
- **Resolved project.mode:** greenfield (`aamad.config.yml`)
- **Prompt trace:** Omitted. The review records what the browser showed. It does not call the product model.
- **Visual regression:** not tested. The approved spec does not add a package manifest, and the first baseline waits for Human judgment.
