# autotask_intent — Step 4 Report: End-to-end live demo, braindump to converged

Status: **complete** (all plan.md Step 4 acceptance criteria exercised live).

Target node: **agstudio** — changed from the plan's `agpc` example by the
user when confirming live actions for this session (recorded in
`braindump/braindump3.txt`). The user also confirmed the nodeutils push;
observation deployed the exact pinned commit
`efb790f07a6e83176b24add6888c1cc1fdd48d2b`, recorded in the operation
evidence.

## What was done, in order

1. **Braindump** (`braindump/braindump3.txt`): a conversational wish for a
   10-minute heartbeat cron task; the clusterintent contract derived from it
   is only that `~/mycron/heartbeat.sh` exists on the node.
2. **Desired state** via `.local/desired-state.yaml`:
   `DesiredService heartbeat-cron` + placement `heartbeat-cron-agstudio`
   (profile `cron_task`, `config: {script_path: ~/mycron/heartbeat.sh}`).
   The earlier agpc placement from Step 3 was moved with a previewed
   `delete + create` batch (`dry_run: {create: 1, delete: 1}` →
   `committed` identically). `~` expansion owner: observation time
   (nodeutils), per report3.
3. **Negative first** (README_DEV lesson 1 — prove the check ran):
   - Dry `nctl reconcile agstudio --refresh-observation`
     (op `01KZC3R1P88TR4GKC813X9SMDA`): plans exactly one `observe_node`
     action; `cron_task`'s `service_missing` is `unsupported`
     ("observe_only; no actuation is available") — no invented action.
   - Apply (op `01KZC3R7GYBH3CP0CY5QB6WJSF`): fresh live observation; the
     dump's `observed_services["heartbeat-cron"]` is
     `{state: missing, source: check:file_exists, checks: [{kind:
     file_exists, path: /Users/eiji/mycron/heartbeat.sh, status: missing}]}`
     — positive evidence the check executed and expanded `~` on the target.
     Final drift: `heartbeat-cron: service_missing (error)`. Run state
     `manual_intervention_required` / `ok: False` is the correct safe stop
     for drift with no automatable action.
   - Bonus regression evidence: the migrated `ollama` http check ran from
     hints on the same round (`checks: [{kind: http, status: 200}]`,
     `state: active`, `source: http_probe`) — the Step 2 deletion of
     name-keyed specs is live-proven, not just unit-tested.
4. **Script placement** (disposable, exact scope): Ansible ad-hoc from
   `ansible_agdev/` — `file state=directory ~/mycron` + `copy` of the
   2-line date-append `heartbeat.sh` (mode 0755) to agstudio only.
   (crontab registration is the plan's explicit nice-to-have; not done, not
   asserted — recorded as deferred in Step 5.)
5. **Convergence round** (op `01KZC3TR5PGANVD4MZCW4SQRDG`):
   `nctl reconcile agstudio --refresh-observation --yes` → state
   **converged**, `ok: True`. Fresh dump:
   `{state: present, source: check:file_exists, checks: [{... status:
   present}]}`; final drift for `heartbeat-cron`: `converged`, no diffs.
6. **No repeat action** (op `01KZC3VR3JMB69YJJXQ60P63JG`): a repeat dry
   `nctl reconcile agstudio` plans `actions: []`.

## Acceptance mapping (plan Step 4.5)

- Final drift for the placement converged: **yes** (round-00
  `drift-final.json`, op `01KZC3TR5PGANVD4MZCW4SQRDG`).
- Operation evidence records the observation: **yes** — probe hints
  (`probe-config/agstudio.yaml` carries the resolved `file_exists` check),
  retrieved report, ingest summary, and the pinned nodeutils SHA, all under
  `~/.local/state/nctl/events/<operation_id>/`.
- Repeat reconcile plans nothing: **yes** (`actions: []`).

## Unrelated cluster drift (kept distinct from the feature under test)

`dnsmasq`/`node-agent` `service_observation_stale` (+ one cascading
`binding_unknown`) remained during the negative round: their observations
live on nodes outside this scoped run and had aged past 24 h. The agstudio
rounds refreshed agstudio-hosted services (ollama et al. converged); the
remaining staleness is routine cluster hygiene, not autotask_intent drift.
