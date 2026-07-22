# Report — Step 1: implement a strict managed SSH-store reader

Date: 2026-07-22
Scope: `nctl` (submodule)
Status: **complete** (focused: 46 pass / full suite: 929 pass)

## Goal (plan.md Step 1)

Close outstanding problem #1: `entries_for_lookup_name` and
`_lines_excluding_lookup_name` each caught `SshTrustError` per line and
silently skipped it, so a malformed line in the nctl-managed known_hosts
store produced an empty lookup result (`unenrolled`) instead of the
promised `ssh_store_read_failed`, and corruption was indistinguishable from
a genuinely missing enrollment.

## Changes

### 1. `nctl_core/ssh_enroll.py` — one strict store-loading boundary

- Added `ManagedSshStore` (`raw_lines`, `entries`, `obsolete_entries`,
  `entries_for(lookup_name)`) and `ObsoleteEntry`.
- Added `load_managed_ssh_store(path) -> ManagedSshStore`:
  - an absent file is a valid empty store;
  - blank lines and `#` comments are skipped;
  - every other line is parsed with `parse_known_hosts_line` — its
    `SshTrustError` (malformed field count, unknown key type, invalid
    base64) is re-raised as `SshStoreReadError` with `path:lineno` context,
    not swallowed;
  - `@cert-authority`/`@revoked` marker lines are rejected (nctl never
    writes them into the managed store, unlike ordinary known_hosts usage);
  - a parsed entry with more than one name field, or a hashed (`|1|...`)
    name, is rejected;
  - a name matching `nctl-node-<uuid>` becomes a current `ManagedEntry`;
  - a name matching `[nctl-node-<uuid>]:<port>` with `port` in `1..65535`
    becomes a separate `ObsoleteEntry` (migration residue — never
    satisfies `entries_for`, i.e. never authorizes a connection);
  - any other name (an endpoint name, IP, or out-of-range obsolete port)
    fails the whole store as `SshStoreReadError`.
- Removed the old per-line `try/except SshTrustError: continue` from
  `entries_for_lookup_name` and `_lines_excluding_lookup_name`;
  `entries_for_lookup_name` is deleted entirely (superseded by
  `ManagedSshStore.entries_for`), and `_lines_excluding_lookup_name` no
  longer suppresses parser errors — it only runs on `raw_lines` already
  proven parseable by a prior `load_managed_ssh_store` call, so a remaining
  bare `parse_known_hosts_line` call there is now documented as always
  succeeding rather than defensively swallowed.
- `build_ssh_enroll` now calls `load_managed_ssh_store` (replacing
  `read_raw_lines` + `entries_for_lookup_name`) and still maps
  `SshStoreReadError` to the existing `ssh_store_read_failed` envelope
  error with no write.

### 2. `nctl_core/reconcile/ssh_preflight.py`

`check_ssh_enrollment`, `verify_offered_keys`, and
`verify_resolved_ssh_targets` all switched from
`read_raw_lines(...)` + `entries_for_lookup_name(raw_lines, lookup_name)`
to `load_managed_ssh_store(...)` + `store.entries_for(lookup_name)`. Each
already ran once per call (not per host), so this is a drop-in replacement:
`SshStoreReadError` is raised at the same point in the same uncaught form
these functions already left to their callers (the round-safety of that
propagation is Step 2's scope, not changed here).

### 3. `nctl_core/inventory_trust.py`

`check_inventory_ssh_preflight` switched the same way.

## Test changes

- `tests/test_ssh_enroll.py`: 12 new tests on `load_managed_ssh_store` —
  absent file is an empty store; valid comments plus multiple
  aliases/key-types remain readable; a valid obsolete `[alias]:port` entry
  is recognized separately and never satisfies `entries_for`; 8
  parametrized malformed/unsupported line forms (short field count, unknown
  key type, invalid base64, marker, hashed name, endpoint-keyed name,
  out-of-range obsolete port, multiple names) each raise
  `SshStoreReadError`; invalid UTF-8 raises `SshStoreReadError`; one
  malformed unrelated line fails a store that also contains a valid entry;
  a corrupt store blocks `build_ssh_enroll` apply and leaves the original
  bytes untouched.
- `tests/test_dnsmasq_apply.py`: 1 new test — a syntactically malformed
  store *line* (endpoint-keyed name, not an I/O failure) reaches
  `build_dnsmasq_apply` as `ssh_store_read_failed` and invokes no
  `ansible-playbook` call, alongside the pre-existing invalid-UTF-8 case.

## Verification

```
$ uv run pytest -q tests/test_ssh_enroll.py tests/test_ssh_trust.py tests/test_dnsmasq_apply.py \
    tests/test_ssh_preflight.py tests/test_inventory_trust.py
134 passed in 0.47s   # before adding new tests, confirming no regression

$ uv run pytest -q tests/test_ssh_enroll.py
45 passed in 0.43s    # after adding new tests

$ uv run pytest -q tests
929 passed, 1 warning in 5.94s   # full suite (baseline 914 + 15 net new)
```

`grep -rn entries_for_lookup_name` outside test comments/history: no
remaining references — every call site now goes through
`ManagedSshStore.entries_for`.

Lint/type check: `nctl/pyproject.toml`'s `[dependency-groups] dev` still
has no ruff/mypy or similar installed, so none was run (same as every prior
`fix_sshkey*` step).

## Step 1 exit criteria

- [x] No managed-store parser catches and skips corruption —
  `entries_for_lookup_name`/`_lines_excluding_lookup_name`'s suppression is
  gone; the one loader (`load_managed_ssh_store`) raises on every malformed
  or unsupported line.
- [x] Missing enrollment and invalid store are distinguishable everywhere —
  an absent file is `ManagedSshStore()` (empty, `unenrolled` downstream); a
  present-but-corrupt file raises `SshStoreReadError` (`ssh_store_read_failed`
  downstream at every existing call site).
- [x] Valid existing bare-alias stores remain byte-compatible — all
  pre-existing `ssh_enroll` write/read/replace tests pass unmodified,
  including exact-byte assertions on obsolete-entry purge and comment
  preservation.

## Handoff to Step 2

`observation.py:151`'s defense-in-depth `check_ssh_enrollment` call inside
`run_observation` is still uncaught — a store failure there (now including
a syntactically corrupt store, not just an I/O error, since
`load_managed_ssh_store` covers both) can still raise past
`_run_observation_action`, which only catches `ValueError`. Step 2 adds the
private action-outcome/terminal-error boundary and the round-retention
behavior for this and the other observation-time store-failure paths
described in Outstanding problem #2.
