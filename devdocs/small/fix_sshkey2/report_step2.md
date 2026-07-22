# Report — Step 2: correct enrollment and obsolete malformed entries

Date: 2026-07-22
Scope: `nctl` (submodule)
Status: **complete** (focused: 42 pass / full suite: 840 pass)

## Goal (plan.md Step 2)

Finish what Step 1 started for `ssh_enroll.py`: make `--from-known-hosts`
port-aware (bug #1's last remaining call site), remove the obsolete
`[alias]:port` entry only after a freshly re-verified enrollment (never on
an unverified scan), convert managed-file I/O failures into structured
envelope errors instead of uncaught exceptions (bug not explicitly numbered
in plan.md but listed under "Implementation" item 5), and close the
Nautobot client on every code path (item 6).

## Changes

### `nctl_core/ssh_enroll.py`
- `SshProbeRunner.known_hosts_files_for(host)` → `effective_config(host, port)`:
  runs `ssh -G -p <port> <host>` (`_default_effective_config`) instead of a
  portless `ssh -G host`.
- `find_legacy_trusted_keys(probe, endpoint, port)` (port argument added):
  parses the probe's `ssh -G` output via `ssh_trust.parse_effective_ssh_config`,
  computes the search key via `ssh_trust.legacy_lookup_name` (effective
  `HostKeyAlias` if present, otherwise `[effective_host]:effective_port`),
  and searches each effective `UserKnownHostsFile` under that name --
  matching what a real OpenSSH connection would actually look up.
- Added `_obsolete_alias_port_lookup_name(alias, port)`: returns
  `[alias]:port` for a non-default port, `None` at port 22 (nothing obsolete
  to purge there).
- In the write path, after a verified enrollment/replacement, the obsolete
  bracketed name (if any) is excluded from the rewritten file in the same
  atomic write as the new bare-alias entry -- never on a plan-only run or an
  unverified scan, since both return before reaching the write.
- `read_raw_lines(path)` now wraps `OSError`/`UnicodeDecodeError` in a new
  `SshStoreReadError`; `build_ssh_enroll` catches it and reports
  `ssh_store_read_failed`.
- The write path's exception handling now also catches `ArtifactError`
  (`atomic_write_private` raises `ArtifactError`, a `RuntimeError` subclass,
  not `OSError` -- the previous `except OSError` never actually caught a
  real write failure) and reports `ssh_store_write_failed`.
- `build_ssh_enroll` now creates the `NautobotClient` in the outer function
  and delegates to a new `_build_ssh_enroll_with_client(...)` inside a
  `try/finally` that always calls `client.close()` -- covers the success
  path and every early-return failure path (unknown host, no mDNS endpoint,
  probe failure, unverified, conflict, lock contention, store read/write
  failure).

## Test changes (`nctl/tests/test_ssh_enroll.py`)

- `_probe()` fixture rebuilt around `effective_config(host, port)`, emitting
  `hostname`/`port`/`hostkeyalias`/`userknownhostsfile` lines the way real
  `ssh -G` output does; existing `--from-known-hosts` tests updated
  accordingly.
- `_patch_snapshot` now returns a fake Nautobot client with a real `close()`
  (plain `object()` would otherwise `AttributeError` under the new
  `finally: client.close()`).
- New tests (10):
  - `test_stale_bracketed_entry_is_not_considered_enrolled` -- a store
    containing only `[alias]:2222` is not treated as already enrolled
    (`action == "enroll"`, not `"noop"`).
  - `test_verified_reenrollment_removes_obsolete_bracketed_entry` -- a
    verified re-enrollment purges the obsolete bracketed entry in the same
    write, preserving comments and unrelated aliases.
  - `test_unverified_reenrollment_does_not_touch_obsolete_bracketed_entry` --
    an unverified scan performs no write at all, including no purge.
  - `test_port_22_never_computes_an_obsolete_bracketed_name` -- unit test on
    `_obsolete_alias_port_lookup_name`.
  - `test_from_known_hosts_promotion_uses_port_aware_effective_config` --
    promotion against a `[endpoint]:2222`-keyed legacy entry succeeds via the
    port-aware probe.
  - `test_from_known_hosts_promotion_honors_effective_host_key_alias` --
    promotion searches by the developer's own effective `HostKeyAlias`, not
    `[host]:port`, when one is configured.
  - `test_read_only_managed_file_returns_structured_error` -- an unreadable
    (chmod 0) managed file yields `ssh_store_read_failed`.
  - `test_unwritable_directory_returns_structured_error` -- destination
    parent is a plain file (not a directory), so the atomic write fails at
    the filesystem level; yields `ssh_store_write_failed`. (A directory
    `chmod` alone cannot exercise this: `_atomic_write` unconditionally
    `chmod`s its destination's parent to `0o700` as the owner, which
    succeeds regardless of the directory's prior mode.)
  - `test_nautobot_client_closed_on_success_and_error_paths` -- `close()` is
    called both on an early-return failure (`unknown_host`) and on a
    successful apply.
  - `test_idempotent_after_port_change_same_bare_alias_no_reenrollment_needed`
    -- enrolling at port 22, then re-running the identical fingerprint at
    port 2222, is a `noop` (same bare alias either way).

### `nctl/tests/test_ssh_preflight.py`, `nctl/tests/test_reconcile_executor.py`
- Updated fake `SshProbeRunner` construction from `known_hosts_files_for=`
  to `effective_config=` (both files only fake enrollment-adjacent
  fixtures; neither exercises `--from-known-hosts`, so a no-op stub
  `CompletedProcess` was sufficient).

## Verification

```
$ uv run --project nctl pytest -q nctl/tests/test_ssh_enroll.py nctl/tests/test_ssh_preflight.py
42 passed in 0.13s

$ uv run --project nctl pytest -q nctl/tests
840 passed, 1 warning in 5.21s
```

Lint/type check: still not run -- see Step 1 report (no ruff/mypy in
`nctl/pyproject.toml`'s dev group).

## Step 2 exit criteria

- [x] The real connection, enrollment plan, and managed-file inspection all
  use the same bare alias (`managed_lookup_name`, wired since Step 1;
  `--from-known-hosts` now separately uses `legacy_lookup_name` only for its
  own promotion search, never for the managed store).
- [x] No test conflates non-default-port legacy promotion with the
  managed-store key (`test_from_known_hosts_promotion_uses_port_aware_effective_config`
  and `test_stale_bracketed_entry_is_not_considered_enrolled` cover both
  sides explicitly).

## Handoff to Step 3

- `reconcile/ssh_preflight.py` still calls `read_raw_lines` without catching
  `SshStoreReadError`; not fixed here since it is outside Step 2's file list
  and preserves its pre-existing behavior (an uncaught read failure was
  already possible before this step, just as an `OSError`/`UnicodeDecodeError`
  instead of `SshStoreReadError`). Worth a look during Step 3/4 if it comes
  up again while touching that module for the production-render context and
  the dnsmasq trust gate.
- Step 3 begins binding production regeneration to preflight using the same
  generation context (`production_render.py`, `production/composer.py`,
  `reconcile/executor.py`, `reconcile/ssh_preflight.py`).
