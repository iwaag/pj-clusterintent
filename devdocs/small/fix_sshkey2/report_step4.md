# Report — Step 4: put standalone dnsmasq apply behind the same trust gate

Date: 2026-07-22
Scope: `nctl` (submodule)
Status: **complete** (focused: 116 pass / full suite: 856 pass)

## Goal (plan.md Step 4)

Fix bug #4: the arbitrary-inventory guard in `nctl apply dnsmasq` checked
only that the alias was non-empty and the node ID was a UUID, and only for
an explicit `--inventory` override -- the normally configured default
inventory bypassed the check entirely. Replace it with a structured
per-host validator applied to both inventory paths, plus an actual
offered-key preflight before Ansible starts.

## Changes

### `nctl_core/production/contract.py`
- Extracted `select_local_route(*, local_ip, local_dns_hostname,
  mdns_hostname, inventory_hostname)`: the `local_ip -> local_dns_hostname ->
  mdns_hostname -> inventory_hostname` priority chain `resolve_connection_variables`
  already used inline to compute `ansible_host` for the `local` connection
  path. `resolve_connection_variables` now calls this extracted function
  instead of repeating the chain -- byte-identical behavior, but the chain
  now has exactly one implementation the production composer and the new
  `inventory_trust` module both call.

### `nctl_core/inventory_trust.py` (new)
- `validate_inventory_trust_contract(host_vars, hostname, known_hosts_path)`:
  recomputes the expected alias and the *entire* `ansible_ssh_common_args`
  string from `nintent_desired_node_id` via `derive_host_key_alias`/
  `build_ansible_ssh_common_args`, and requires exact equality with the
  rendered host vars -- not "contains the right options." A non-empty alias
  that merely differs from the UUID-derived value, a missing
  `ansible_ssh_common_args`, or one with an extra policy-weakening option
  appended are all rejected the same way as a completely absent trust
  contract.
- `resolve_route_from_host_vars(host_vars, hostname)`: a bootstrap inventory
  exports `ansible_host` directly (used verbatim); a production inventory
  never does (the composer pops it), so this falls back to
  `select_local_route`/`tailscale_ip` fed from the *same*
  `connection_path`/`local_ip`/`local_dns_hostname`/`mdns_hostname`/
  `tailscale_ip` variables the composer derived it from and left in the
  rendered host vars. Returns `None` (never a guess) when neither
  representation resolves -- there is no general Jinja evaluator here, only
  this one supported generated-contract shape.
- `check_inventory_ssh_preflight(...)`: managed-store enrollment (bare
  alias) + a matching currently-offered key, mirroring
  `reconcile.ssh_preflight.verify_offered_keys`'s READY/UNENROLLED/MISMATCH/
  UNREACHABLE logic but reading `nintent_desired_node_id`/route out of
  already-rendered host vars instead of a `DesiredSnapshot` (this command
  has no live Nautobot fetch at all). Reuses `SshPreflightEntry` and the
  status constants from `reconcile.ssh_preflight` rather than redeclaring
  them.

### `nctl_core/dnsmasq_apply.py`
- Removed the old boolean `_has_valid_ssh_trust_vars()` and its
  `--inventory`-only branch.
- `build_dnsmasq_apply` gained a `probe: SshProbeRunner | None = None`
  parameter (defaults to `default_ssh_probe_runner()`), the injection
  boundary so tests never touch the real network or the developer's own
  known_hosts files.
- After computing `target_hosts` (unchanged), **every** run now: (1) runs
  `validate_inventory_trust_contract` for every target host regardless of
  whether the inventory is the configured default or `--inventory` --
  any contract violation fails closed with `dnsmasq_inventory_untrusted_host`
  before any Ansible process starts; (2) runs `check_inventory_ssh_preflight`
  and fails closed with a status-specific code
  (`ssh_host_key_unenrolled`/`ssh_host_key_mismatch`/`ssh_host_key_unreachable`)
  before any Ansible process starts. Both checks are pure/read-only; dry-run
  and apply mode run the identical preflight.
- Added `DnsmasqApplyData.ssh_preflight: list[dict]` recording each target
  host's slug/alias/status/detail, mirroring `ReconcileData.ssh_preflight`.

### `nctl_core/reconcile/executor.py`
- Threaded `ssh_probe: SshProbeRunner` through `_execute_action` and
  `_run_playbook_action` down to the `dnsmasq_config` action's
  `build_dnsmasq_apply(cfg, apply_changes=True, probe=ssh_probe)` call. Without
  this, reconcile's own `dnsmasq_config` actuation would silently construct a
  second, real `default_ssh_probe_runner()` alongside the executor's already-
  injected fake/real probe -- a redundant live SSH scan during every
  `dnsmasq_config` action, and a real-network call inside any test that
  exercises that action kind without realizing it needed a second mock.

## Test changes

### `nctl/tests/test_dnsmasq_apply.py`
- Added an `[ssh]` section to the shared `_config()` fixture (a
  configuration-relative known_hosts path under `tmp_path`, never the real
  user's home directory).
- `_inventory_payload()` now takes `cfg` and builds a fully valid trust
  contract by default (`_valid_host_vars`): correct alias, correct
  `ansible_ssh_common_args`, and a bootstrap-style `ansible_host`. Added
  `_write_managed_entry(cfg)` and `_good_probe(key_blob=...)` fixtures. Every
  previously-passing "happy path" test (dry-run, apply, ansible-failure,
  `--inventory` override x2, setup-failure) now supplies a matching managed
  entry and probe.
- `test_default_configured_inventory_is_not_subject_to_the_trust_var_guard`
  (asserted the *old, buggy* bypass) replaced by
  `test_default_configured_inventory_is_also_subject_to_the_trust_gate`
  (asserts the same untrusted payload now fails with
  `dnsmasq_inventory_untrusted_host`) plus
  `test_default_configured_inventory_with_a_valid_contract_and_matching_key_proceeds`
  (asserts a fully valid configured inventory still succeeds).
- New tests (10): unenrolled host rejected + zero `ansible-playbook` calls;
  mismatched offered key rejected + zero `ansible-playbook` calls;
  unreachable route (`no_resolvable_route`, no `ansible_host`/`connection_path`
  at all) rejected; production-style host vars (no `ansible_host`, only
  `connection_path`/`mdns_hostname`) resolve the route correctly and the
  keyscan target matches; a non-empty alias differing from the UUID-derived
  value is rejected; `ansible_ssh_common_args` with an appended
  policy-weakening option is rejected; a completely missing
  `ansible_ssh_common_args` is rejected; dry-run performs the identical
  preflight and leaves the known_hosts file byte-identical; the
  `ssh_preflight` summary is populated on success.

## Verification

```
$ uv run --project nctl pytest -q nctl/tests/test_dnsmasq_apply.py nctl/tests/test_reconcile_executor.py \
    nctl/tests/test_production_contract.py nctl/tests/test_production_composer.py
116 passed in 0.45s

$ uv run --project nctl pytest -q nctl/tests
856 passed, 1 warning in 5.56s
```

Lint/type check: still not run -- see Step 1 report.

## Step 4 exit criteria

- [x] Every `nctl apply dnsmasq` inventory path (configured default and
  `--inventory`) passes through the same validator, managed store check, and
  offered-key check.
- [x] A hand-written non-empty alias is not enough to pass the trust gate
  (`test_non_empty_alias_differing_from_uuid_derived_value_is_rejected`).

## Handoff to Step 5

- Documentation (`nctl/README.md`, `ansible_agdev/README.md`,
  `ansible_agdev/README_ADMIN.md`, `devdocs/small/fix_sshkey/report_verification.md`)
  still describes the pre-fix_sshkey2 contract in places and needs updating.
- Full automated verification (the complete focused-suite list plus the full
  `nctl/tests` run, `ansible-inventory --list`/`--host` against both
  generated inventories) and the two live verifications (non-default-port
  OpenSSH lookup; a real post-regeneration `agdnsmasq` service action) are
  still outstanding.
