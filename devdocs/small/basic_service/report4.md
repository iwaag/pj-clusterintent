# Step 4 report — dnsmasq action installs the daemon

## Change

`nctl/src/nctl_core/dnsmasq_apply.py::build_dnsmasq_apply`: before invoking
`deploy_dnsmasq_records.yml`, runs `playbooks/bootstrap/setup_dnsmasq.yml` against the same
inventory/group and the same check/diff-vs-apply mode, via the same `AnsibleRunner` (so both
playbook runs share one operation, one artifact directory, and one timeout budget). A setup
failure aborts before the records deploy — `_failure(...)` returns immediately, `data.ansible`
stays `None`, and the deploy playbook never runs.

- New `SETUP_PLAYBOOK = Path("playbooks/bootstrap/setup_dnsmasq.yml")` constant; `_validate_paths`
  now checks it exists alongside `DEPLOY_PLAYBOOK`.
- `DnsmasqApplyData` gained `setup: AnsibleRunResult | None = None`, populated by the setup run's
  own `ansible/dnsmasq-setup` artifact stem (the records deploy keeps its existing `ansible/dnsmasq`
  stem, now in `data.ansible`).
- New failure codes: `ansible_setup_failed` (apply mode) / `ansible_setup_dry_run_failed`
  (dry-run mode), mirroring the existing `ansible_apply_failed`/`ansible_dry_run_failed` for the
  records-deploy phase.
- New events (documented in `docs/event-log.md` and `docs/compatibility.md`): `setup_started` /
  `setup_completed` (apply mode, mirroring the existing `apply_started`/`apply_completed`
  asymmetry — no `dry_run`-mode "started" event) and `setup_dry_run_completed` (dry-run mode,
  mirroring the existing bare `dry_run_completed`). The records-deploy phase's own
  `dry_run_completed`/`apply_started`/`apply_completed` events are unchanged.
- The reconcile executor (`reconcile/executor.py`'s `dnsmasq_config` → `build_dnsmasq_apply`
  mapping) needed no change — it already just calls `build_dnsmasq_apply(cfg, apply_changes=True)`
  and inherits the two-phase run.
- `render_dnsmasq_apply_text` now prints both phases' Ansible stdout/stderr under
  `-- daemon setup --` / `-- records deploy --` headers.

## Schema versioning — did **not** bump `nctl.apply.dnsmasq.v1`

The plan text suggested bumping the envelope schema for this change. Adding a field to an
envelope's `data` payload is explicitly *not* a breaking change under this project's own frozen
compatibility policy (`nctl/docs/compatibility.md` §3: "Each command's `data` payload is frozen at
its current field set and may only gain fields" — a real bump is reserved for
renames/removals, minted as a new `.v2` kept *alongside* `v1` for a deprecation window, never by
swapping `v1` in place). `setup` is purely additive, so `APPLY_DNSMASQ_SCHEMA` stays
`"nctl.apply.dnsmasq.v1"`; `tests/test_compatibility_snapshots.py`'s
`FROZEN_DATA_FIELDS["nctl.apply.dnsmasq.v1"]` needed no change (its check is "the frozen field set
is a subset of the model's actual fields" — a floor, not a ceiling). Added the three new event
names to `FROZEN_EVENT_VOCABULARY` since they're now part of the frozen-going-forward vocabulary.

## Tests

`nctl/tests/test_dnsmasq_apply.py`:
- `_config` fixture now creates `playbooks/bootstrap/setup_dnsmasq.yml` alongside the existing
  deploy playbook (both are required by `_validate_paths` now).
- `test_dry_run_renders_artifact_invokes_check_diff_and_emits_events`: asserts both the setup and
  deploy `ansible-playbook` calls got `--check --diff`, and the event sequence includes
  `setup_dry_run_completed` before `dry_run_completed`.
- `test_yes_runs_real_apply_without_check_flags`: asserts neither call got `--check`/`--diff`, and
  the event sequence is `started, rendered, setup_started, setup_completed, apply_started,
  apply_completed, finished`.
- `test_ansible_failure_is_returned_with_exit_code_and_recap`: updated so the fake setup run
  succeeds and only the deploy run fails, preserving the original "records deploy failure" case.
- New `test_setup_failure_aborts_before_records_deploy`: fake setup run fails; asserts
  `ansible_setup_dry_run_failed`, `data.ansible is None`, and only 2 subprocess calls happened
  (inventory + setup — no deploy call).

## Verification

```
uv run pytest -q
```
509 passed (full nctl suite, no regressions; +1 for the new setup-failure test).
