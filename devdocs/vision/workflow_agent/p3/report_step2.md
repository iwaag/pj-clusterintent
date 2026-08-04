# Phase 3 — Step 2: WorkflowEpisode for the first real run

Date: 2026-08-04. Executes Step 2 of [`plan.md`](plan.md).

## Episode created

- ID: `2f2d3de6-039a-4a36-a6a6-152da8a92d51`, status `candidate` (left for
  the human survey step — not self-selected or self-resolved, per the
  workflow-improvement manual).
- Title: "workflow-agent first real run: swarmui/comfyui/prometheus drift
  diagnosis (observation defects, not deployment)".
- `references.workflow_plan_id` =
  `2026-08-04_swarmui-comfyui-prometheus-drift-diagnosis` (contract §3
  convention key; no operation IDs — the run was read-only, and no local
  path is referenced).
- `report` namespace answers the roadmap's one evaluation question
  explicitly: **neither** a planning defect nor a faithful-execution stop —
  the run completed with success evidence visibly matched; the only
  protocol imperfection was the known cosmetic scratch-narration gap. It
  also records the diagnosis and the two cluster-side improvement
  candidates (observer blindness to plain user processes; substring
  matching mapping `prometheus-node-exporter.service` to `prometheus`) for
  a later, separate workflow-improvement session — recorded, not fixed,
  per the time-separation split.
- Verified via `nctl workflow-episode show
  2f2d3de6-039a-4a36-a6a6-152da8a92d51 --json`: status `candidate`,
  references and report round-trip intact. (GUI verification needs a
  browser session — known limitation; the JSON read is the agreed
  substitute.)

This is the first row in the previously-empty WorkflowEpisode store.

## One API-shape lesson (no fix needed)

The phase plan's hint sketched the `report` namespace as "free text"; the
API validates each namespace as a **JSON object**
(`invalid_namespace_type: report must be a JSON object`). First create
attempt with a string `report` was rejected; resubmitted with a structured
object (`summary` / `diagnosis` / `planning_defect_or_execution_stop` /
`improvement_candidates` / `note`). This matches the existing
workflow-improvement convention (`write … --data '{"summary": …}'` —
free-form JSON *object*, not free-form text), so nothing needs amending in
the contract or manuals; noting it here so the next episode author doesn't
repeat the 400.

## Backfill decision

**Forward-only.** Episodes are recorded for runs from this scheme onward;
pre-scheme work (notably the agscratch1 retirement discovered episodeless
by the Phase 2 stop-run) is **not** backfilled. Reasons: a backfilled
`report` would be a reconstruction, violating the "report is written once
at the end of the operating session" convention in spirit; and policy
already warns against depending on the old
`.local/evidence/workflow-episodes/` directories. The decision is recorded
here explicitly, as the phase plan requires.
