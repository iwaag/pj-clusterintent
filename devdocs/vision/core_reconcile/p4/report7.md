# Phase 4 Report — Step 7 (`nctl reconcile`: bounded executor, verification, and dashboard)

Date: 2026-07-17. Implements [p4/plan.md](plan.md) Step 7. This is the seventh suggested commit
boundary and the largest so far: `nctl reconcile [HOST] [--yes] [--max-rounds N] [--json]` now
exists end to end, tying Step 5's planner and Step 6's ledger execution into one bounded operation
with its own lock, event log, plan/drift artifacts, and dashboard regeneration.

## What was built

### The round loop (`nctl_core/reconcile/executor.py`)

The 9 numbered steps in `p4/plan.md`'s "Apply mode execution per round" are deliberately collapsed:
each loop iteration starts by fetching one fresh full-cluster drift and building a plan for the
requested scope. If the plan has nothing left to do, that same drift *is* the final drift (nothing
was mutated, so nothing needs re-observing). Otherwise the round executes in three phases —
bootstrap/ledger actions (`observe_node`, `link_actual_node`, `reconcile_ipam`), a full production
inventory regeneration (always, even for host scope), then service/dnsmasq playbook actions — and
the loop continues; the *next* iteration's fresh fetch becomes round N's "after" drift, so the same
full-cluster payload is never computed twice for one round.

Terminal states match the plan exactly: `planned` (dry-plan mode), `already_converged` /
`converged` (empty plan, round 0 vs. later), `manual_intervention_required` (plan has
manual_review/unsupported findings — stops before any mutation), `non_converged` (unchanged drift
fingerprint between rounds, or `max_rounds` exhausted), `failed` (fetch/config/lock/interruption
errors). `ok` is derived from this state vocabulary directly rather than from `Envelope.build`'s
default "no errors" rule, since `manual_intervention_required`/`non_converged` are failures with no
`EnvelopeError` of their own (the plan's manual/unsupported records are the reason).

Per-action execution dispatches by `reconciler_id`:

- `observe_node` → `nctl_core.observation.run_observation` (Steps 2/4's pipeline, unchanged);
- `link_actual_node` → Step 6's `execute_link_actual_node`;
- `reconcile_ipam` → Step 6's `execute_reconcile_ipam`, conflicts/skips recorded in the action
  detail rather than hidden;
- `service_profile` → runs the resolved playbook(s) via `AnsibleRunner` with `--limit` over the
  action's `host_slugs`, grouping hosts by resolved playbook path (supporting the `playbook_by_os`
  variant by looking up each host's node operational config `expected_host_os`/`declared_host_os`);
- `dnsmasq_config` → calls `nctl_core.dnsmasq_apply.build_dnsmasq_apply(cfg, apply_changes=True)`
  directly — Decision 7's "existing dnsmasq render/deploy logic is factored into a reusable action"
  was already true as of Phase 1 Step 1, so this action is a one-line call, not new logic.

A successful actuating action emits both `action_completed` and `actuation_completed` (Step 4's
exact event contract: `target_slugs`, `claimed_diff_codes`, `requires_observation`, `success`) so
the `converging` status rule has real events to read, not just the plan's static metadata. After the
service/dnsmasq phase, every target named by a `requires_observation=True` action gets one more
observation pass (Decision 8's "any host actuation requiring observation is followed by a newer
successfully ingested report") — distinct from the bootstrap `observe_node` action, logged as
`post_actuation_observation`.

Independent-target failure: actions execute in a flat loop and one action's failure (a non-success
result) never stops the remaining actions in the same round — matching Decision 1's "Independent
targets continue after another target fails."

### Dashboard reuse without a second drift read

`dashboard_render.py` gained `render_dashboard_from_drift(cfg, drift_envelope, ...)`, extracted from
`build_dashboard` (which now just feeds it a freshly computed or `--from`-loaded envelope — existing
`nctl dashboard` behavior is unchanged and its tests pass unmodified). The reconcile executor calls
this directly with its own final full-cluster drift payload on every apply terminal path that has
one, so the dashboard and the reconcile result are guaranteed to agree — `build_drift` is never
called a second time. A dashboard/write-back failure degrades to a `warning` event and
`data.dashboard.errors`; it never overwrites the reconcile terminal `state`.

`drift_render.py` gained `fetch_and_compute_drift` (fetch + `compute_drift`, returning the raw
`SourceSnapshot` alongside the `DriftResult`) and `render_drift_data` (the `DriftData` rendering
step), factored out of `build_drift` so the executor can get the snapshot it needs for planning
without duplicating the fetch/compute logic or the rendering shape.

### Lock (`nctl_core/reconcile/lock.py`)

`acquire_reconcile_lock` is a plain non-blocking `flock` on `[reconcile].lock_path`, released
automatically on process exit — enough for Phase 4's "only one mutating reconcile at a time" rule
without a server-side lock (Phase 5). Contention raises `ReconcileLockError`, mapped to the
`reconcile_lock_contention` terminal failure before any drift fetch or planning happens.

### Interruption

A small `_InterruptFlag` context manager installs SIGINT/SIGTERM handlers around the apply path
(best-effort: failing to install on a non-main thread is swallowed, matching the "handle where
possible" requirement) and is checked before each round and before each action; on interruption the
loop stops without starting another action and the run reports `state=failed` with an `interrupted`
error, restoring the previous signal handlers on exit either way.

### CLI

`nctl reconcile [HOST] [--yes] [--max-rounds N] [--json]` in `cli/main.py`. `--max-rounds` is
bounded to `1..10` by Typer itself (a bad value is a usage error, exit 2, before any command logic
runs). An `unknown_host` plan/scope error also exits 2 (an argument error, not a run failure);
Configuration/argument errors otherwise retain the existing `_load_config` exit-2 path. Plan mode
exits 0 whenever planning itself succeeds (state `planned`); apply mode exits 0 only for
`already_converged`/`converged`.

## Tests

`tests/test_reconcile_executor.py` (11 tests) and `tests/test_reconcile_lock.py` (4 tests), plus the
`dashboard_render.py` refactor re-verified against its existing 18 tests unchanged. The executor
tests fake every side-effecting dependency by monkeypatching the names imported into
`nctl_core.reconcile.executor` (`fetch_and_compute_drift`, `execute_link_actual_node`,
`execute_reconcile_ipam`, `run_observation`, `AnsibleRunner.run`, `build_production_render`,
`load_deployment_profiles`/`load_profile_reconciliation`, `render_dashboard_from_drift`) rather than
touching real Ansible/Nautobot, covering:

- plan mode never mutates (`execute_link_actual_node` is never called) and reports `planned`;
- already-converged (empty plan, no rounds executed);
- manual review blocks before any mutation (`AnsibleRunner` is never constructed);
- no-progress stop (identical fingerprint across rounds) vs. max-rounds-reached (a different code
  each round so it never trips the no-progress check, exhausting the round budget instead) —
  distinct stop reasons (`no_progress` vs. `max_rounds_reached`), distinct round counts;
- lock contention (held by the test itself) fails before any drift fetch;
- interruption before a round starts reports `failed`/`interrupted` with zero rounds executed;
- a `link_actual_node` action executes against a snapshot with a real unique candidate and the next
  round's drift shows `converged`;
- two independent `service_profile` actions on the same round, one whose fake Ansible run exits 0
  and one that exits 1 — both results are recorded, the failure doesn't block the success, and the
  operation continues (non-converged, since the failing service's drift never resolves in the fed
  rounds);
- dashboard failure is recorded as a `warning` event without changing the terminal `state`.

Verification:

- `cd nctl && uv run pytest -q` — **420 passed** (up from 405 before this boundary);
- `cd nctl && python3 -m compileall -q src tests` — passed;
- an AST-based unused-import scan over the new/changed modules found nothing beyond the expected
  `from __future__ import annotations` false positive;
- manual CLI smoke test against the real local `nctl.toml`: `nctl reconcile --json` and
  `nctl reconcile ghost-host --json` both produced well-formed `nctl.reconcile.v1` envelopes and
  exit code 1 on the already-known live `nautobot_fetch_failed` (403) from Step 3, with a correctly
  written event log (`started` → `finished`) each time; `nctl reconcile --max-rounds 20` correctly
  fails as a Typer usage error (exit 2) before any command logic runs. Scratch operation
  directories/event logs created by this smoke test were deleted afterward;
- `git diff --check` (parent and nctl) — passed.

## Deliberate non-work

- no live end-to-end proof of a real actuation round against Nautobot/Ansible — Step 9's live
  rollout is where the already-known local-token 403 (recorded in Steps 3 and 6) gets resolved and
  a real happy path is exercised;
- no per-endpoint IPAM evidence refinement beyond what Step 6 already implemented;
- `new_node_baseline` is still registered metadata only (Step 5); nothing in Step 7 invokes it yet
  procedurally after a fresh node link, since no current desired-state fixture exercises that path
  and the plan explicitly scopes it as a later refinement ("a future collector/comparator can
  promote it");
- no cutover of the old Ansible collect/ingest entry points or Makefile targets — Step 8;
- no nauto or nintent changes in this boundary;
- no commit, push, or Nautobot deployment.

## Files changed in this boundary

nctl:

- added `src/nctl_core/reconcile/executor.py`, `src/nctl_core/reconcile/lock.py`;
- updated `src/nctl_core/drift_render.py` (`fetch_and_compute_drift`, `render_drift_data`),
  `src/nctl_core/dashboard_render.py` (`render_dashboard_from_drift`), `src/nctl_core/cli/main.py`
  (`reconcile` command);
- added `tests/test_reconcile_executor.py`, `tests/test_reconcile_lock.py`.

Parent repository:

- added this report. No commit was created.
