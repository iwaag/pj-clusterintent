# Report — Step 1: close the SSH inventory and probe error contracts

Date: 2026-07-22
Scope: `nctl` (submodule)
Status: **complete** (focused: 126 pass / full suite: 886 pass)

## Goal (plan.md Step 1)

Close the gaps left by `fix_sshkey2`'s exact-field inventory check: reject
every inventory variable that can precede or replace the generated host-key
policy, validate `ansible_port` by type/range instead of coercing invalid
values to 22, and turn managed-store I/O failures and probe subprocess
failures into structured errors instead of uncaught exceptions/tracebacks.

## Changes

### 1. `nctl_core/inventory_trust.py`
- Added `FORBIDDEN_INVENTORY_SSH_VARS`: `ansible_ssh_args`,
  `ansible_ssh_extra_args`, `ansible_scp_extra_args`,
  `ansible_sftp_extra_args`, `ansible_ssh_executable`,
  `ansible_host_key_checking`, `ansible_ssh_host_key_checking`.
- `validate_inventory_trust_contract` now additionally rejects: any present
  forbidden variable (`ssh_policy_override_rejected`), a present
  `ansible_port` that is not an `int` in `1..65535` (bool excluded
  explicitly, since `bool` is an `int` subclass) (`ansible_port_invalid`),
  and a present `ansible_connection` other than exactly `"ssh"`
  (`ansible_connection_invalid`). These checks run after the existing
  alias/`ansible_ssh_common_args` equality checks, and always before
  `check_inventory_ssh_preflight` (managed-store read + keyscan) for the
  same host.
- `check_inventory_ssh_preflight`'s port extraction no longer coerces a
  bad value to 22 (there no longer is one reachable here -- upstream
  validation already rejected it); it now only supplies the port-22
  default when `ansible_port` is absent.

### 2. `nctl_core/ssh_enroll.py`
- `scan_offered_keys` now also wraps `OSError` (e.g. `ssh-keyscan` missing
  from `PATH`) as `SshTrustError`, alongside the existing
  `TimeoutExpired` handling.
- `find_legacy_trusted_keys` now wraps `probe.effective_config`'s
  `TimeoutExpired`/`OSError` and a nonzero `ssh -G` exit as `SshTrustError`,
  and wraps `probe.keygen_find`'s `TimeoutExpired`/`OSError` the same way
  (its own nonzero exit is a normal "no match" result and is left alone).

### 3. `nctl_core/dnsmasq_apply.py`
- `build_dnsmasq_apply` now catches `SshStoreReadError` around
  `check_inventory_ssh_preflight` and returns `ssh_store_read_failed`
  instead of letting a corrupt/unreadable managed known_hosts file crash
  the operation.

### 4. `nctl_core/reconcile/executor.py`
- `_ssh_scan_errors` now also maps `STATUS_UNENROLLED` to
  `ssh_host_key_unenrolled` (previously only mismatch/unreachable): a
  managed-store entry removed between the round-start enrollment gate and
  a later offered-key scan (mDNS gate or post-regeneration service scan)
  no longer falls through unrecognized.
- All four call sites that read the managed store through
  `check_ssh_enrollment`/`verify_offered_keys`
  (plan-only preflight, apply-mode pre-round enrollment gate, apply-mode
  pre-round mDNS scan, and the post-regeneration service scan inside
  `_execute_round`) now catch `SshStoreReadError` and stop the run with
  `ssh_store_read_failed` instead of propagating a raw exception out of
  `run_reconcile`.

## Test changes

- `tests/test_inventory_trust.py`: 7 new tests -- exact common args plus
  hostile `ansible_ssh_args` rejected; each of the 7 forbidden vars rejected
  individually; non-`ssh` `ansible_connection` rejected / bare `ssh`
  accepted; integer port accepted; string/bool/zero/negative/>65535/float
  ports all rejected.
- `tests/test_dnsmasq_apply.py`: 3 new tests -- integer `ansible_port: 2222`
  is scanned at 2222 (not 22); string `ansible_port: "2222"` is rejected by
  the trust contract before any keyscan call; a corrupt (invalid-UTF-8)
  managed store returns `ssh_store_read_failed` and invokes no
  `ansible-playbook` call.
- `tests/test_ssh_enroll.py`: extended `_probe()` with
  `effective_config_raises`/`effective_config_returncode`/
  `keygen_find_raises`; 4 new tests -- keyscan missing-executable,
  legacy-probe (`ssh -G`) timeout, missing-executable, and nonzero-exit all
  report `ssh_probe_failed`.
- `tests/test_reconcile_executor.py`: 2 new tests -- `_ssh_scan_errors`
  maps a `STATUS_UNENROLLED` entry to `ssh_host_key_unenrolled`; a corrupt
  managed store during `run_reconcile(apply_changes=True)` reports
  `ssh_store_read_failed` with `rounds == []` rather than crashing.

## Verification

```
$ uv run --project nctl pytest -q nctl/tests/test_inventory_trust.py nctl/tests/test_dnsmasq_apply.py \
    nctl/tests/test_ssh_enroll.py nctl/tests/test_reconcile_executor.py nctl/tests/test_ssh_preflight.py
126 passed in 0.77s

$ uv run --project nctl pytest -q nctl/tests
886 passed, 1 warning in 5.77s
```

Lint/type check: `nctl/pyproject.toml`'s `[dependency-groups] dev` does not
include ruff/mypy or similar, and none is installed as a project dependency,
so none was run (same as every prior `fix_sshkey*` step).

## Step 1 exit criteria

- [x] No supported inventory variable can precede or replace the generated
  host-key policy (`FORBIDDEN_INVENTORY_SSH_VARS` denylist +
  `ansible_connection` allowlist, checked for every host before any
  managed-file read or network access).
- [x] Invalid ports never silently become 22
  (`ansible_port_invalid` rejects any present non-integer/out-of-range
  value; `check_inventory_ssh_preflight`'s fallback to 22 now only fires
  when the variable is absent).
- [x] Trust-store/probe failures do not escape as tracebacks
  (`SshStoreReadError` caught at every reachable call site in
  `dnsmasq_apply.py` and `reconcile/executor.py`; every real probe function
  wraps `TimeoutExpired`/`OSError`/malformed-output/nonzero-exit as
  `SshTrustError`).

## Handoff to Step 2

- Step 2 replaces `resolve_production_routes(...)` +
  `verify_offered_keys(old_snapshot, ...)` with a single `ResolvedSshTarget`
  map carried in `ProductionRenderContext`, so the post-regeneration scan
  (the `verify_offered_keys` call inside `_execute_round` this step just
  added `SshStoreReadError` handling around) stops reading `ansible_port`
  from the round-start `snapshot.desired` operational overrides.
- Step 2 also introduces `RoundOutcome` so a failure after a successful
  mutation (including the new `ssh_store_read_failed` paths added here)
  retains the round's completed action evidence instead of returning
  `rounds: []` -- this step deliberately left `rounds: []` as the correct,
  honest result for a *pre-round* store-read failure (no action ran yet);
  Step 2 must distinguish that from a failure *after* actions already ran.
