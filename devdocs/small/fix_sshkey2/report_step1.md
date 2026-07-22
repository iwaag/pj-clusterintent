# Report — Step 1: correct SSH identity helpers and configuration paths

Date: 2026-07-22
Scope: `nctl` (submodule)
Status: **complete** (focused: 61 pass / full suite: 830 pass)

## Goal (plan.md Step 1)

Fix bug #1: `derive_lookup_name(alias, port)` produced `[alias]:port` for a
non-default port, but the real OpenSSH connection ignores `ansible_port`
entirely once `HostKeyAlias` is set, so enrollment/preflight and the real
connection looked up different names. Split the managed-store lookup and the
legacy-promotion lookup into separate APIs, and resolve `[ssh]` relative
paths against the config file's directory instead of the process cwd
(bug #5).

## Changes

### 1. `nctl_core/ssh_trust.py`
- Removed `derive_lookup_name(alias, port)`.
- Added `managed_lookup_name(alias)`: always returns the bare alias (no port
  argument). The managed store never depends on `ansible_port`.
- Added `legacy_lookup_name(effective_host, effective_port, host_key_alias)`:
  if an effective `HostKeyAlias` is present, returns it verbatim (no port
  suffix); otherwise the bare host on port 22, or `[host]:port` otherwise
  (matches portable OpenSSH's `get_hostfile_hostname_ipaddr()`).
- Added `EffectiveSshConfig` / `parse_effective_ssh_config(output)`: a pure
  parser for `ssh -G` output extracting `hostname` / `port` / `hostkeyalias`
  / `userknownhostsfile` (possibly multiple). Not yet wired into
  `ssh_enroll.py`'s real probe (planned for Step 2's port-aware
  `--from-known-hosts`).

### 2. `nctl_core/config.py`
- Added `resolve_local_path(path, config_dir)` (three rules: expand `~` →
  keep an absolute path absolute → resolve a relative path against
  `config_dir`).
- `SshConfig.resolved_known_hosts_file()` / `resolved_lock_path()` now take a
  `config_dir: Path` argument (matches the existing `AnsibleConfig` pattern).
- Added `Config.resolved_ssh_known_hosts_file()` / `resolved_ssh_lock_path()`
  as the single call site that supplies `self.source_path.parent`. Updated
  every caller (`observation.py`, `hosts_intent_render.py`,
  `production_render.py`, `ssh_enroll.py`, `reconcile/ssh_preflight.py`) to
  use these.
- `Config.load()` now `.resolve()`s the path returned by `find_config()`, so
  `source_path` is always absolute (the precondition for cwd-independent
  resolution).

### 3. `nctl_core/reconcile/ssh_preflight.py`
- Removed the `override.ansible_port`-based lookup-name computation from
  `_resolve_alias_and_lookup_name()`; it now uses `managed_lookup_name(alias)`.
  Fixes both `check_ssh_enrollment` and `verify_offered_keys`, which
  previously looked up `[alias]:port` for a non-default-port node in the
  managed store.

### 4. `nctl_core/ssh_enroll.py` (minimal follow-up to keep it compiling)
- Replaced the `derive_lookup_name(alias, port)` call with
  `managed_lookup_name(alias)`. The managed store's read/write key is now
  always the bare alias (this also satisfies part of Step 2 ahead of time).
- `--from-known-hosts` legacy search (`find_legacy_trusted_keys` /
  `SshProbeRunner.known_hosts_files_for`) is still the old, portless
  `ssh -G host` version; Step 2 wires it to `parse_effective_ssh_config` /
  `legacy_lookup_name`.

### 5. `example.nctl.toml`
- Documented the relative-path resolution rule (config-file-relative,
  cwd-independent) in the `[ssh]` section comment.

## Test changes

### `nctl/tests/test_ssh_trust.py`
- Removed the 3 `derive_lookup_name` tests.
- Added 17 tests covering `managed_lookup_name` (bare alias, rejects empty),
  `legacy_lookup_name` (port 22 / non-default, effective `HostKeyAlias`
  takes priority, rejects empty host / invalid port), and
  `parse_effective_ssh_config` (extracts all fields, defaults when
  `HostKeyAlias` absent, ignores blank/malformed lines).

### `nctl/tests/test_config.py`
- Updated `cfg.ssh.resolved_known_hosts_file()` calls to
  `cfg.resolved_ssh_known_hosts_file()`.
- Added tests: relative paths resolve against the config file directory
  (independent of cwd), absolute paths stay absolute, paths containing
  spaces, and `Config.source_path` is absolute even for a relative
  `--config` argument.

### `nctl/tests/test_ssh_enroll.py` / `test_ssh_preflight.py`
- Updated `cfg.ssh.resolved_known_hosts_file()` calls.
- Rewrote 2 non-default-port tests from the old, buggy expectation
  (bracketed `[alias]:2222` written to the store) to the corrected
  expectation (always the bare alias).

### `nctl/tests/test_hosts_intent_render.py`
- Updated the fake `Config`'s
  `ssh=SimpleNamespace(resolved_known_hosts_file=...)` to a top-level
  `resolved_ssh_known_hosts_file=...` attribute.

## Verification

```
$ uv run --project nctl pytest -q nctl/tests/test_ssh_trust.py nctl/tests/test_config.py
61 passed in 0.08s

$ uv run --project nctl pytest -q nctl/tests
830 passed, 1 warning in 5.50s
```

Lint/type check: `nctl/pyproject.toml`'s `[dependency-groups] dev` does not
include ruff/mypy or similar, and none is installed as a project dependency,
so none was run (recorded again at Step 5).

## Step 1 exit criteria

- [x] No managed-store generation/lookup code produces `[nctl-node-...]:port`
  (both `ssh_enroll.py`'s write path and `ssh_preflight.py`'s query path go
  through `managed_lookup_name`).
- [x] No call site of the old, argument-less SSH path resolver remains
  (`grep -rn "cfg\.ssh\.resolved_known_hosts_file()\|cfg\.ssh\.resolved_lock_path()"`
  returns 0 hits under `src/`).
- [x] All focused tests pass.

## Handoff to Step 2

- Wire `ssh_enroll.py`'s `--from-known-hosts` to `parse_effective_ssh_config` /
  `legacy_lookup_name` for a port-aware legacy promotion search. Replace
  `SshProbeRunner.known_hosts_files_for` (host only) with `effective_config`
  (host, port).
- Implement explicit removal of the obsolete `[alias]:port` entry (only after
  a freshly re-verified enrollment) in Step 2.
