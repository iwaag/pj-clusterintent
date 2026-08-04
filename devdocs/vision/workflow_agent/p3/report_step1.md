# Phase 3 — Step 1: first real request through plan → executor → report

Date: 2026-08-04. Executes Step 1 of [`plan.md`](plan.md).

## What was chosen as the real request

The plan's default: diagnose the three still-unexplained drifting services
from `nctl drift --json` — `swarmui`/`comfyui` (`service_missing` on agpc)
and `prometheus` (`service_observed_on_wrong_node` +
`service_has_no_active_placement`). Re-confirmed live at planning time
(summary `{"drifting": 4, "converged": 13, "unknown": 2}`, unchanged since
the Phase 2 completed run), so this is genuinely wanted diagnosis, not a
manufactured target.

## Planning-time investigation (main session, unbounded per design hint)

Done in this session before writing the plan, per the division of labor the
roadmap fixes (open-ended exploration on the planning side, bounded
confirmation on the executor side):

- `nctl drift --json` detail: swarmui/comfyui desired on agpc
  (deployment_profile `swarmui`/`comfyui`, both `observe_only` in
  `ansible_agdev/vars/deployment_profiles.yml`), observed missing at
  2026-08-03T13:49:41Z; prometheus observed `active` via `systemd` on agpc's
  device while desired has no active placement for it.
- Read-only ansible ad-hoc against agpc (allowed without pause per this
  phase's plan preamble: read-only diagnostics; the localenv memo's human
  note gates *direct* SSH, and contract §2's marker gates SSH/Ansible
  *mutations*):
  - `systemctl list-units --all 'swarmui*' 'comfyui*' 'prometheus*'`: **no
    swarmui/comfyui units exist at all** (not even unit files); no exact
    `prometheus.service`; `prometheus-node-exporter.service` is active.
  - `pgrep -af -i 'swarmui|comfyui'`: **both services are actually
    running** as plain user processes under `/home/eiji/StabilityMatrix/`
    (SwarmUI as a dotnet process, ComfyUI as a venv python process, port
    7821).
  - `docker ps`: only `portainer3` — neither service is a container.
- Observer code (`nodeutils/nodeutils_collect.py`): systemd observation
  matches units against `IMPORTANT_SERVICE_NAMES` + config probe hints by
  **substring** (`important_service_name_from_systemd`, ~line 929:
  `service_name.lower() in haystack`); `"prometheus"` is in
  `IMPORTANT_SERVICE_NAMES`, so `prometheus-node-exporter.service` matches
  and is reported as service `prometheus`. There is no process-based
  detection for swarmui/comfyui (only docker, system systemd units, and a
  narrow node-agent/ollama user-service probe).

Diagnosis hypotheses formed: **H1/H2** — swarmui/comfyui run as
StabilityMatrix user processes invisible to the observer, so
`service_missing` is an observation-capability gap, not real absence;
**H3** — the `prometheus` finding is a substring-match false positive on
`prometheus-node-exporter.service`; no real prometheus server exists on
agpc.

## The plan artifact and executor run

- Plan ID: `2026-08-04_swarmui-comfyui-prometheus-drift-diagnosis`
  (`.local/evidence/workflow-plans/<id>/plan.md`), written per the
  workflow-planning manual: read-only confirmation of H1–H3 as three
  bounded steps with expected outputs enumerated inline, plus a no-command
  assessment step; every deviation from the enumerated expectations is a
  stop condition. Step 1 pre-filters `drift --json` through a bounded
  `python3 -c` summarizer (the Phase 2 context-pressure hint, applied). No
  approval-marked steps (nothing mutates; read-only ansible is not in
  contract §2's marked class). Every command line was verified runnable
  from the repo root at planning time.
- Lint: passed (`--lint-only`).
- Execution: `python3 executor/executor.py
  2026-08-04_swarmui-comfyui-prometheus-drift-diagnosis` →
  `harness_outcome: model-finished`, 4 turns, 3 commands, ~25 s
  (12:05:48–12:06:13Z). The transcript shows **exactly the plan's three
  commands, verbatim, in order** — no substitution, no improvisation, no
  unplanned investigation.
- Report (`report.md` in the plan directory): `## status` completed; all
  three hypotheses **CONFIRMED** with the exact evidence lines quoted
  (process listing for H1/H2, unit listing for H3); explicitly states no
  remediation was performed and that choosing a fix is a new planning
  cycle. Success-evidence checks all visibly matched, so "completed" is
  evidence-backed.

## Defects observed and fixes made

- **No protocol-side fix was needed.** The only imperfection was the known
  Phase 2 v1 gap recurring: the model emitted two lines of scratch
  narration ("Step 3 passed — … Now composing the assessment.") above the
  `## status` skeleton. The report is fully usable read from `## status`
  down; per this phase's plan ("fix only when a real run forces it") this
  does not force a fix, so none was made. No contract, manual, prompt, or
  harness edit in this step; no rerun needed.
- Cluster-side observations that belong to the episode → improvement path
  (time-separation split, not fixed here): the observer's substring
  matching and its blindness to plain user processes; these go into the
  Step 2 episode `report`.

## Diagnosis outcome (for the record)

All three drift findings are **observation defects, not deployment
defects**: swarmui/comfyui are running where desired but unobservable;
prometheus-on-agpc does not exist and is a name-matching false positive
(the `service_has_no_active_placement` warning is the same false
observation viewed from the placement side). Possible fixes (observer
process-probe for StabilityMatrix services, word-boundary/exact unit
matching for important-service names, or desired-state changes) are a
follow-on planning cycle — Step 3 decides whether one is wanted now.

## Evidence locations

- `.local/evidence/workflow-plans/2026-08-04_swarmui-comfyui-prometheus-drift-diagnosis/`
  — `plan.md` + `transcript.json` + `report.md` (Git-ignored, per
  contract §3).
- No `nctl` operation IDs (read-only run); no secrets in any artifact
  (checked: transcripts contain host/unit/process listings only).
