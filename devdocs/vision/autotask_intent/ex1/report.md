# autotask_intent ex1 — `cron_registered` check kind

Status: **complete** — code, tests, braindump backing, and the live
agstudio proof (negative round → crontab registration → converged →
no-repeat) all ran; exact evidence below.

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

## Live proof (agstudio, nodeutils pin `97d436b8`)

Starting state was the exact negative fixture the new check must expose:
`~/mycron/heartbeat.sh` on disk (Step 4), crontab unregistered.

- **Negative round** (op `01KZC87DV1AAZYDCRR2PPNDH92`, fresh observation
  after the operator pushed nodeutils `97d436b`): observed entry
  `{state: missing, source: check:cron_registered+file_exists, checks:
  [{file_exists, /Users/eiji/mycron/heartbeat.sh, present},
  {cron_registered, /Users/eiji/mycron/heartbeat.sh, missing}]}` →
  `heartbeat-cron` drifting, gap `service_missing`, planner invented no
  action (observe_only stays `manual_intervention_required`). Existence
  proof alone no longer converges — the exact false convergence braindump4
  complains about is now visible drift.
- **Registration** (user-approved SSH, `~/.ssh/ansible_key`): appended
  `*/10 * * * * ~/mycron/heartbeat.sh >> ~/mycron/heartbeat.log 2>&1` to
  the login user's crontab.
- **Positive round** (op `01KZC8BN0DFKN0QVDPSMB0TKJB`, fresh observation):
  observed entry identical shape, both checks `present`, `state: present`
  → agstudio scope `converged` (drifting count 1 → 0).
- **No repeat** (op `01KZC8CKP29PHW0ZQ3P3BWBV59`, dry reconcile):
  `actions: []`.

The `~`-relative crontab spelling was matched via the raw-needle path
(hint path `~/mycron/heartbeat.sh`, crontab line `~`-relative, observed
check path expanded) — the exact spelling pair the nodeutils tests pin.

## Self-report

WorkflowEpisode `306cba41-1f06-4f8d-90bc-a4ba87bbf38e` (tags `routine`,
outcome `completed`) referencing the three operations above and both
braindump registrations.
