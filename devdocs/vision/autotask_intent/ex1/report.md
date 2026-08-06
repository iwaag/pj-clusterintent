# autotask_intent ex1 — `cron_registered` check kind

Status: **implemented, not deployed** — code, tests, and braindump backing
are complete; the live agstudio proof is pending exactly two operator-gated
steps (nodeutils push, crontab registration), listed at the end. This
report will be updated to `complete` after the live rounds run.

## Why this exists (build-on-consumer)

The main plan's final report deferred a `cron_registered` check kind
"until a placement actually needs it" (deferred item 1) and left the demo
crontab unregistered (deferred item 3). The consumer has now appeared: the
user judged that `heartbeat-cron` reading `converged` on script existence
alone — while the real desire (a heartbeat every 10 minutes) is not
running — is exactly the kind of invisible drift this system exists to
surface. Registration proof is the natural ceiling: it stays in the
state-proof family with `file_exists` and deliberately does **not** cross
into activity/freshness observation (deferred item 2 remains out of scope).

## Braindump backing (was missing)

None of the autotask_intent braindumps had been registered in nintent —
the episode used flat files only, so `heartbeat-cron` was a desired state
with no braindump backing. Fixed:

- `braindump/braindump3.txt` (existence-proof desire) registered verbatim,
  `user_direct`, BrainDumpDocument `274c7ade-f667-4e1f-b0f4-84b0d615e80c`.
- `braindump/braindump4.txt` (new: extend the desire to registration
  proof) written and registered, `agent_transcribed`, BrainDumpDocument
  `a6e26e59-b8a1-4cde-8bbc-82512f90b18b`.

DesiredService↔braindump linkage is textual by design (the braindump diary
has no import path into drift/reconcile), so both titles name the
`heartbeat-cron` slug.

## What was built

- **nctl** (`0dcc477`): `CronRegisteredCheckSpec` joins the discriminated
  check union with `file_exists`' exact path rules (shared
  `_validate_single_path_source` / `_resolve_check_path` helpers — one
  owner for path semantics). `resolve_check_hints` renders it as a fully
  resolved `{kind, path}` row. Drift: a new
  `EXISTENCE_PROOF_CHECK_KINDS = {file_exists, cron_registered}` set; any
  such check row whose status is not `present` (including `error`) is
  `service_missing`, even beside richer running-state evidence.
- **nodeutils** (`97d436b`): `crontab_registration_status()` runs
  `crontab -l` for the login user and proves whether any non-comment line
  references the hinted script path (expanded or original `~`-relative
  spelling — POSIX sh tilde-expands both). Fail truthfully: empty crontab
  ("no crontab for <user>") is `missing`; an unusable crontab tool
  (absent binary, timeout, other nonzero exit) is `error`, never proof
  either way. Check-created entries now record
  `source: check:<sorted proof kinds joined by +>` —
  `check:file_exists` outputs are byte-identical to before, so existing
  placements observe no change.
- **profile** (`ansible_agdev` `b488c0d`): `cron_task` reconciliation
  declares both proofs from the one `script_path` config key:
  `file_exists` + `cron_registered`. Existence alone no longer converges a
  `cron_task` placement.

Contract notes: the byte-frozen `deployment_profiles.<name>` half is
untouched (only `deployment_profile_reconciliation` changed, which is
outside the digest); no nintent model/API change anywhere — the `checks`
list rides through ingest as before.

## Test gates (README_DEV matrix)

- nctl ordinary: **1282 passed** (1275 → 1282). New: spec parse/validation
  parity tests, hint-rendering test, and the control-loop test extended to
  four rounds — missing script → **script present but unregistered →
  still `service_missing`** → registered → satisfied with no planned
  action; plus an `error`-status fail-closed round. The unknown-kind
  rejection test was repointed (its bogus-kind fixture was literally
  `cron_registered`).
- nodeutils ordinary: **89 passed** (84 → 89). New: registration
  present/missing through `normalize_observed_services`, `~` expansion
  with raw-spelling needle, comment-line exclusion, and the truthful
  missing/error distinction; cron proof never downgrades a richer running
  detection.

## Live proof plan (pending, agstudio)

Current real state: `~/mycron/heartbeat.sh` exists on agstudio (Step 4),
crontab is **not** registered — the exact negative fixture the new check
must expose.

1. Push `nodeutils` `97d436b` to GitHub (operator: nodeutils deploys by
   clone-at-pin; pushes are the user's step by policy). Superproject
   gitlink update rides in this ex1 commit.
2. `nctl reconcile agstudio --refresh-observation` → expect
   `heartbeat-cron` **drifting**, gap `service_missing`, checks
   `[{file_exists: present}, {cron_registered: missing}]`, planner still
   inventing no action (observe_only).
3. Register (user-confirmed SSH):
   `*/10 * * * * ~/mycron/heartbeat.sh >> ~/mycron/heartbeat.log 2>&1`
4. Fresh reconcile → expect `converged`; repeat dry reconcile → `actions: []`.

## Self-report

WorkflowEpisode: to be created when the live rounds close this episode.
