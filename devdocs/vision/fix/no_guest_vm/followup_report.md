# Follow-up report: closing the residual findings of report.md (G1–G3, F4)

Executed 2026-08-10 (JST), continuing the same working trees as
[`report.md`](report.md) (`nctl` submodule on `7782d72`, changes uncommitted).
Executor: Omni Agent (Claude Code, backend `claude-fable-5`).

**Outcome: complete.** All four residual findings from report.md §4 are fixed
in `nctl`, `uv run pytest -q` green (**1331 passed**, up from 1316), and the
two tombstone ledger rows left behind by the episode were removed live using
only supported commands (no ledger hand-edit, no direct hypervisor access —
the cluster was never contacted at all; every action this session was a
ledger/planner operation).

## G2 — prune no longer leaves unlinked VirtualMachine tombstones

Root cause chain: `drift/compute_evaluation.py` returned from the retired
branch without ever yielding `compute_instance_not_linked`, and
`plan_link_compute_realization` explicitly refused retired dispositions
("retired compute disposition forbids a realization link"). So a guest
destroyed while matched-by-vmid stayed unlinked, and the server-side prune
(`nintent .../operations/retirement_prune.py`), which by design accepts only
Desired-linked roots and never searches by vmid/name, could not collect the
row. nintent was deliberately **not** modified — its link-only validation is a
safety property worth keeping.

- `compute_evaluation.py`: the retired branch (retained / destroy_required /
  removal_complete) now yields `compute_instance_not_linked` whenever
  `instance_link_state == "absent"`.
- `reconcilers.py`: `plan_link_compute_realization` allows retired
  dispositions; all identity/ambiguity/`linked_to_other` guards unchanged.
- `planner.py`: a planned destroy gains a `dependencies` entry on the same
  guest's link action, so `topological_order` runs link → destroy (the
  alphabetical tie-break used to order destroy first).

The removal-complete variant is exactly the tombstone-cleanup shape:
re-declare the guest retired/absent, the plan is one link action, then prune
collects the now-linked row.

## G3 — active unrealized guests are no longer bootstrap-gated

`build_plan` now also excludes from guest-targeted observe actions any compute
instance with **no realized VirtualMachine and no realized Device** — a guest
that has never run sshd, whose observe action could only fail
`ssh_host_key_unenrolled` and kill the round. Its refresh routes to the
control node (`observe_node:compute-evidence`), same as the retired case. The
narrowing matters: a guest **with** a realized Device keeps its own observe
action (it exists and is enrolled; its facts are merely stale) — pinned by
`test_unrealized_guest_with_realized_device_keeps_its_own_observe_action`.

## F4 — orphaned `running` operations are detectable and closable

- `operations_index.py`: a running operation silent for >1h
  (`STALE_RUNNING_SECONDS`) is reported `stale` (`running (stale)` in
  `ops list`/`ops show`; `stale: true` in the envelopes). Nothing auto-closes.
- New `nctl ops close OPERATION_ID --reason TEXT [--force]`
  (`nctl.ops.close.v1`): appends one `finished` event (`ok: false`, message
  `abandoned: <reason>`, data `abandoned: true`) — append-only, refuses
  non-stale operations without `--force`, refuses finished/unknown ones.

## G1 — worker stall has an in-system detector

`nctl status` gained a worker check (read-only Nautobot REST, degrades
independently like the other checks):

- `celery-workers-running == 0` from `/api/status/` → error
  `celery_workers_not_running` (the redis_access failure mode; Job submission
  would 503).
- A PENDING JobResult older than 120s while a worker **is** registered →
  error `worker_queue_stalled`, with the restart hint. This is the §2
  signature this episode recorded — ping OK, kombu binding present, nothing
  consumed for ~28h — which `celery inspect ping` alone cannot see, and which
  recurred *after* redis_access's 2026-08-06 transport hardening.

Deliberately not done (unchanged from redis_access's scope decision, now with
a detector in place instead of nothing): no auto-restart machinery, no
healthcheck/compose rework, no topology change. Docker does not restart on
unhealthy anyway; the honest increment is detection plus the recorded manual
fix (`docker restart nautobot-nautobot-worker-1`).

## Tests

`uv run pytest -q` in `nctl/`: **1331 passed**. New/updated:

- `test_compute_evaluation.py`: retired-unlinked destroy shape and
  removal-complete tombstone shape both yield `compute_instance_not_linked`
  (the linked-retired suppressions of the existing tests still hold).
- `test_reconcile_planner.py`: link ordered before destroy via dependency;
  tombstone shape plans only the link; G3 suppression and its
  realized-Device narrowing.
- `test_operations_index.py` / `test_cli_ops.py`: stale derivation, close
  semantics (append, seq continuity, `not_stale`/`already_finished`/
  `unknown_operation` refusals, `--force`), CLI flow.
- `test_status.py`: worker-ok, workers=0, stalled-queue (message carries the
  restart hint), fresh-pending-is-fine; shared healthy-client fixture.
- Contract test: `nctl.status.v1` data fields now include `worker`.

## Live verification (scratch env)

- `nctl status`: `✓ worker  celery workers: 1, pending jobs: 0`.
- Tombstone cleanup, supported commands only
  (`.local/agdoomed-tombstone-cleanup.yaml`, preview then `--yes`):
  - `agdoomed2` (vmid 112): dry plan = exactly
    `link_compute_realization:agdoomed2` — the shape that planned *nothing*
    before the fix. Apply `01KZN89SZTHY3RHCEBTWVAGX17` → converged; prune
    `01KZN8A7D1S7FAQ3NTC0H42JMP` → pruned (4 Actual records, 3 Desired
    deletes).
  - `agdoomed3` (vmid 113): apply `01KZN8ADBJ0XGC4MYQR7RK2Z09` → converged;
    prune `01KZN8AKYX074FHS36MJGFAHDY` → pruned.
  - GraphQL confirms no `agdoomed*` VirtualMachine rows remain.
- `nctl ops list` flagged the episode's dead runs as stale; closed with
  recorded reasons: `01KZN5EJRRX0SGMSP07W9DT944` (the kill -9'd create,
  `--force` — under the 1h threshold but known dead), `01KZN09HN19FXQ3ZCA9P7Y449S`,
  `01KZMTTEEX0GENS5XMX0VN3DBZ`. Zero running operations remain.

## Notes

- Pre-existing, out of scope: the scratch ledger holds seven other
  `proxmox_presence: absent` VM rows with no Desired rows (`infra` 100,
  `agansible` 101, `agprome` 103, `aggrafana` 104, `agk3s` 105, `agnomad`
  106, `agkeadhcp` 107) — history predating this episode, same cleanup recipe
  available if ever wanted.
- Docs updated: `nctl/docs/reconcile.md` (G2/G3 planner behavior),
  `nctl/docs/add-and-retire-proxmox-lxc.md` (link-before-destroy, tombstone
  recipe), `nctl/docs/ops-upload-braindump.md` (stale + `ops close`),
  `nctl/README.md` (status worker check),
  `.claude/skills/retire-proxmox-lxc/SKILL.md` (a link action alongside the
  destroy is expected, not a deviation).

## Changed files (uncommitted, on top of report.md's set)

In `nctl/`: `src/nctl_core/drift/compute_evaluation.py`,
`src/nctl_core/reconcile/{planner,reconcilers}.py`,
`src/nctl_core/{operations_index,ops_render,status}.py`,
`src/nctl_core/cli/main.py`,
`tests/{test_compute_evaluation,test_reconcile_planner,test_operations_index,test_cli_ops,test_status,test_current_consumer_contracts}.py`,
`docs/{reconcile,add-and-retire-proxmox-lxc,ops-upload-braindump}.md`,
`README.md`.

In the superproject: `.claude/skills/retire-proxmox-lxc/SKILL.md`,
`devdocs/vision/fix/no_guest_vm/followup_report.md` (this report),
`.local/agdoomed-tombstone-cleanup.yaml` (git-ignored operator input).
