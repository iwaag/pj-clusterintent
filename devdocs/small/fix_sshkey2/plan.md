# fix_sshkey2 Implementation Plan: SSH trust contract hardening and exact-route verification

Date: 2026-07-22

## Goal

Permanently correct the implementation inconsistencies found during review while preserving the
core design introduced by `fix_sshkey`: a stable `HostKeyAlias` derived from the DesiredNode UUID.

After this change, the system must guarantee all of the following:

- The managed known_hosts store uses the same bare alias whether the SSH port is 22 or a
  non-default port.
- Enrollment, preflight, Ansible, and OpenSSH refer to the same file and the same trust key.
- After production inventory regeneration, preflight checks the endpoint resolved from the fresh
  snapshot used for that generation. It must not reuse the snapshot from the beginning of the
  round or fall back to mDNS.
- `nctl apply dnsmasq` validates the complete SSH trust contract and the currently offered key
  before starting Ansible, for both the configured inventory and `--inventory`.
- The live Phase 3 replay exercises a real service/dnsmasq action that requires SSH. An empty
  `ssh_preflight` result is not accepted as proof of this path.

Do not use short-term IP-specific known_hosts entries, `StrictHostKeyChecking=no`,
`accept-new`, or automatic enrollment from an unverified `ssh-keyscan` result.

## Background and unresolved issues

The previous plan, `devdocs/small/fix_sshkey/plan.md`, established the following contract in both
the bootstrap and production inventories:

```text
trust identity = nctl-node-<DesiredNode UUID>
route identity = ansible_host (mDNS, DNS, IP, or Tailscale)
```

The central design is correct, but the current implementation still has these problems:

1. `derive_lookup_name()` produces `[alias]:port` for a non-default port. When
   `HostKeyAlias` is configured, OpenSSH instead uses the alias itself as the known_hosts lookup
   name and does not append the connection port. Enrollment/preflight and the real SSH connection
   therefore look up different names.
2. Reconcile regenerates the production inventory from fresh data, but then calculates its
   post-regeneration preflight route from the snapshot captured at the beginning of the round.
   An IPAM or observation update in the same round can make the generated inventory and scanned
   endpoint disagree.
3. If a target slug is absent from an explicit production route map, the current
   `verify_offered_keys()` silently falls back to mDNS instead of failing because no production
   route was resolved.
4. The arbitrary-inventory guard in `nctl apply dnsmasq` checks only that the node ID is a UUID
   and the alias is non-empty. It does not validate the alias, `ansible_ssh_common_args`, the
   managed entry, or the offered key. The configured default inventory bypasses even this limited
   check.
5. Relative paths in `[ssh]` are not resolved relative to the configuration file. If nctl and
   Ansible run with different working directories, enrollment can write one file while OpenSSH
   reads another.
6. The existing live report did not execute an SSH-requiring action and its `ssh_preflight` list
   was empty. The production post-regeneration service/dnsmasq path has therefore not yet been
   proven on a live host.

Use `ssh_config(5)` and portable OpenSSH's `get_hostfile_hostname_ipaddr()` as the normative
references:

- <https://man.openbsd.org/ssh_config.5#HostKeyAlias>
- <https://github.com/openssh/openssh-portable/blob/master/sshconnect.c>

## Corrected contract

### 1. Separate managed trust lookup from legacy endpoint lookup

These operations both involve a known_hosts lookup name, but they have different semantics and
must not share one ambiguous helper.

| Purpose | Lookup name | Port behavior |
|---|---|---|
| nctl managed known_hosts | `nctl-node-<UUID>` | Always the bare alias; independent of port |
| Promotion from a normal legacy known_hosts file | Endpoint or effective `HostKeyAlias` | Follow `ssh -G`; use `[endpoint]:port` only for a non-default port when no alias is active |
| `ssh-keyscan` | Actual endpoint | Connect with `-p <ansible_port>` |

`ansible_port` controls the TCP connection and the legacy endpoint lookup. It must never affect
the managed alias key. Express this separation directly in the API:

- `derive_host_key_alias(node_id)` — returns the stable trust identity.
- `managed_lookup_name(alias)` — validates and returns the bare alias; it has no port argument.
- `legacy_lookup_name(effective_host, effective_port, host_key_alias)` — returns the lookup name
  used by a normal OpenSSH endpoint connection from effective `ssh -G` values.

Do not read an old, incorrectly generated `[nctl-node-<UUID>]:port` entry at runtime. On the next
explicit enrollment of a non-default-port node, require a newly verified source and remove only
the obsolete entry for that stable alias and current port inside the atomic update. Do not retain
a compatibility reader or dual lookup.

### 2. Resolve local SSH paths relative to the configuration file

Canonicalize `known_hosts_file` and `lock_path` once using these rules:

1. Expand `~`.
2. Keep an absolute path absolute.
3. Resolve a relative path against `cfg.source_path.parent`.

Pass the same absolute path to enrollment, inventory rendering, preflight, and dnsmasq apply.
Never embed a relative `UserKnownHostsFile` in an inventory. The meaning of the trust store must
not depend on the process working directory.

### 3. Use one generation context for production render and post-regeneration preflight

Bundle at least the following in the internal production-render result:

```text
ProductionRenderContext
  envelope / rendered inventory
  generation_id
  generated_at
  source_snapshot used for composition
  resolved SSH routes for included hosts
```

Do not fetch or derive the route map independently from the inventory. Build it from the same
`SourceSnapshot`, the same `NodeInput` objects, and the same
`try_resolve_operational_values()` / `resolve_effective_route()` results. The public CLI
envelope does not need to expose the full snapshot; keep it as internal executor context.

`_regenerate_production_inventory()` must return both its action result and this successful
context. If rendering, validation, or atomic installation fails, do not run any service action.

When an explicit route map is supplied for post-regeneration preflight, a missing slug means
`ssh_host_key_unreachable` / `no_resolvable_production_route`. mDNS selection is reserved for
bootstrap preflight and must not be a production fallback.

### 4. Validate the complete inventory trust contract

For every effective SSH target, validate all of the following:

- `nintent_desired_node_id` is a canonical UUID.
- `nctl_ssh_host_key_alias == derive_host_key_alias(node_id)`.
- `ansible_ssh_common_args == build_ansible_ssh_common_args(alias, resolved_path)`.
- No unmanaged SSH argument can subsequently weaken the host-key policy.
- The managed known_hosts file contains at least one valid entry under the bare alias.
- A key currently offered on the actual route and port exactly matches a managed key.

Apply this validation to both the configured inventory and `--inventory`. The latter is the
supported bootstrap-inventory path, so do not simply prohibit it. Reject old-schema, hand-written,
or partial trust variables, a different known_hosts path, and an incorrect alias with a structured
error before Ansible starts.

To resolve a route from production host vars, extract the existing
`local_ip -> local_dns_hostname -> mdns_hostname -> inventory_hostname` and Tailscale policy into
a pure helper shared by the production composer and inventory preflight. Do not build a general
Jinja evaluator. If the route cannot be determined from the supported generated contract, stop
with `no_resolvable_route`.

### 5. Preflight does not create authority; OpenSSH remains the final verifier

The preflight `ssh-keyscan` may only compare the current offer with a key that is already pinned.
It must never authorize a new key. The actual connection must continue to use:

```text
HostKeyAlias=nctl-node-<UUID>
UserKnownHostsFile=<absolute path resolved from the config file>
StrictHostKeyChecking=yes
CheckHostIP=no
UpdateHostKeys=no
```

## Non-goals

- Changing DNS/IP/mDNS/Tailscale route priority.
- SSH CAs, SSHFP, certificate distribution, or trust synchronization between controllers.
- TOFU from an unverified key, automatic rotation, or automatic replacement.
- Storing SSH readiness in nintent, Nautobot actual state, nodeutils, or drift classification.
- A runtime compatibility layer for the incorrect `[alias]:port` representation.
- A general inventory interpreter capable of evaluating arbitrary Jinja expressions.

## Step 1 — Correct SSH identity helpers and configuration paths

Files:

- `nctl/src/nctl_core/ssh_trust.py`
- `nctl/src/nctl_core/config.py`
- `nctl/src/nctl_core/hosts_intent_render.py`
- `nctl/src/nctl_core/production_render.py`
- `nctl/src/nctl_core/observation.py`
- `nctl/src/nctl_core/reconcile/ssh_preflight.py`
- Related tests and docstrings

Implementation:

1. Remove port-aware `derive_lookup_name(alias, port)` and replace it with a managed-alias-only
   helper.
2. Add a dedicated type/helper for legacy lookup. Run `ssh -G` with the explicit port and consume
   the effective `hostname`, `port`, `hostkeyalias`, and `userknownhostsfile` values.
3. Either require the config directory in the `SshConfig` path resolvers or place the single
   authoritative SSH path resolver on `Config`. Update every call site together.
4. Ensure an explicitly supplied relative `source_path` cannot leave the base directory
   ambiguous; make it absolute during load or inside the resolver.
5. Assert that `UserKnownHostsFile` embedded in an inventory is always absolute.

Tests:

- Ports 22 and 2222 produce the same managed bare alias.
- Legacy port 22 uses the endpoint; port 2222 uses `[endpoint]:2222`.
- The probe passes the equivalent of `ssh -G -p 2222` and honors an effective
  `HostKeyAlias`.
- Relative paths, `~`, absolute paths, and paths containing spaces.
- Enrollment, render, and preflight still use the same path after changing cwd following config
  load.
- Bootstrap and production inventory arguments contain the same absolute path.

Step 1 exit criteria:

- No managed-store generation or lookup code produces `[nctl-node-...]:port`.
- Search and tests confirm that no old no-argument SSH path resolver call site remains.
- All focused tests pass.

## Step 2 — Correct enrollment and obsolete malformed entries

Files:

- `nctl/src/nctl_core/ssh_enroll.py`
- `nctl/tests/test_ssh_enroll.py`
- `nctl/tests/test_ssh_trust.py`

Implementation:

1. Continue scanning the actual endpoint at `ansible_port`, but always read and write the managed
   store under the bare alias.
2. Make `--from-known-hosts` obtain the port-aware effective OpenSSH configuration and search
   plain or hashed entries using the correct legacy lookup name.
3. Preserve the re-scan and re-verification inside the write lock.
4. Only after an explicitly verified enrollment succeeds, remove the obsolete
   `[alias]:port` entry for the same stable alias/current port. Preserve all other nodes,
   comments, and unrelated entries.
5. Convert managed-file read, write, permission, and encoding failures into
   `ssh_store_read_failed` / `ssh_store_write_failed` envelopes instead of uncaught exceptions.
6. Close the Nautobot client on success, early return, and exception paths.

Tests:

- Port 2222 writes a bare alias, and the reported `lookup_name` is also bare.
- A plain or hashed legacy `[endpoint]:2222` entry can be promoted.
- A managed store containing only `[alias]:2222` is not considered enrolled at runtime.
- Only a fingerprint- or legacy-exact-key-backed re-enrollment removes the obsolete entry.
- An unverified scan, different legacy key, or incorrect fingerprint performs no write.
- A read-only file, unwritable directory, and atomic-write failure return structured errors.
- The same bare alias remains idempotent after a port change and does not require re-enrollment.

Step 2 exit criteria:

- The real connection, enrollment plan, and managed-file inspection all use the same bare alias.
- No test conflates non-default-port legacy promotion with the managed-store key.

## Step 3 — Atomically bind production regeneration to preflight

Files:

- `nctl/src/nctl_core/production_render.py`
- `nctl/src/nctl_core/production/composer.py`
- `nctl/src/nctl_core/reconcile/executor.py`
- `nctl/src/nctl_core/reconcile/ssh_preflight.py`
- Production and reconcile tests

Implementation:

1. Add an internal API that produces the production envelope and resolved route map together from
   an already fetched `SourceSnapshot`. Normal `nctl render production` must use the same API.
2. Have `_regenerate_production_inventory()` return render context only after generation, staged
   validation, and atomic installation all succeed.
3. If the regeneration action fails, or is in a state that cannot legitimately be skipped, stop
   post-regeneration scanning and every service action while retaining the failed generation
   action in the result.
4. Scan service targets using the route map from that render context. Do not pass the round-start
   snapshot.
5. If a slug is absent from the explicit production map, stop with
   `no_resolvable_production_route` instead of falling back to mDNS.
6. Distinguish `route_overrides is None` (bootstrap mDNS selection) from an explicit map,
   including an empty map. Prefer separate route-mode types so falsy values cannot change modes.
7. Record only slug, alias, scanned route, port, status, and public fingerprint in output/artifacts;
   never record credentials or raw key blobs.

Required regression tests:

- The round-start snapshot contains an old IP, while an IPAM action causes the render context to
  contain a new IP. Assert that keyscan calls only the new IP.
- A correct key on the new IP permits the service action; a correct key only on the old IP and a
  different key on the new IP blocks it.
- An empty production route map remains unreachable even when the snapshot has an mDNS endpoint;
  keyscan must not run.
- A production write or validation failure starts no service Ansible process.
- If one of two targets is missing from the route map, that target does not escape to mDNS.
- The generation-context route follows the production composer's existing connection priority.

Step 3 exit criteria:

- The executor no longer passes the round-start snapshot to post-regeneration scanning.
- The installed inventory and scanned route have the same generation ID and source context.
- A missing route, generation failure, or key mismatch stops before service actuation.

## Step 4 — Put standalone dnsmasq apply behind the same trust gate

Files:

- `nctl/src/nctl_core/dnsmasq_apply.py`
- `nctl/src/nctl_core/reconcile/ssh_preflight.py` or a new shared inventory-trust module
- `nctl/tests/test_dnsmasq_apply.py`
- Thin CLI wrapper tests

Implementation:

1. Replace the boolean-only `_has_valid_ssh_trust_vars()` check with a structured per-host
   validator.
2. Recompute the expected alias and `ansible_ssh_common_args` from the UUID and require exact
   equality with the effective host vars.
3. Pass both the configured inventory and `--inventory` through the same validation path.
4. Before starting Ansible, check for a managed bare-alias entry and scan the route/port resolved
   from the inventory for a matching offered key.
5. Use the pure route helper extracted in Step 3 for production selection. Normalize a bootstrap
   inventory's direct `ansible_host` into the same target type.
6. Add the `SshProbeRunner` injection boundary so tests never use the real network or the
   developer's known_hosts files.
7. Add an `ssh_preflight` summary to `DnsmasqApplyData`. Distinguish inventory-contract errors
   from `ssh_host_key_unenrolled`, `ssh_host_key_mismatch`, and
   `ssh_host_key_unreachable`.

Tests:

- Only a valid production inventory with a matching offered key proceeds to setup/deploy.
- A valid bootstrap `--inventory` proceeds over mDNS.
- A non-empty alias that differs from the UUID-derived value is rejected.
- Missing `ansible_ssh_common_args`, a different path, missing options, and policy-weakening
  options are rejected.
- A stale configured default inventory is also rejected.
- A missing managed entry, unresolvable route, or key mismatch invokes `AnsibleRunner` zero times.
- Dry-run performs the same read-only preflight and never mutates trust.
- An inventory/Jinja route that cannot be safely resolved fails instead of falling back.

Step 4 exit criteria:

- Every `nctl apply dnsmasq` inventory path passes through the same validator, managed store, and
  offered-key check.
- A hand-written non-empty alias is not enough to pass the trust gate.

## Step 5 — Documentation, full verification, and live Phase 3 proof

### Documentation

Update:

- `nctl/README.md`
- `ansible_agdev/README.md`
- `ansible_agdev/README_ADMIN.md`
- The production inventory contract documentation if needed
- `devdocs/small/fix_sshkey/report_verification.md`
- New `devdocs/small/fix_sshkey2/report_verification.md`

Preserve the facts and operation IDs in the previous report. Add a notice that its
post-regeneration service path was not exercised and is being re-verified by `fix_sshkey2`.
Correct completion claims that relied on an empty preflight. Record the new evidence in a
separate report instead of overwriting the history.

### Automated verification

Run focused suites after each step, followed by at least:

```text
uv run --project nctl pytest -q nctl/tests/test_ssh_trust.py nctl/tests/test_config.py
uv run --project nctl pytest -q nctl/tests/test_ssh_enroll.py nctl/tests/test_ssh_preflight.py
uv run --project nctl pytest -q nctl/tests/test_production_contract.py nctl/tests/test_production_composer.py nctl/tests/test_production_render.py
uv run --project nctl pytest -q nctl/tests/test_dnsmasq_apply.py nctl/tests/test_reconcile_executor.py
uv run --project nctl pytest -q nctl/tests
```

Also run the project's available standard lint and type checks. If a tool is not installed as a
project dependency, record why it was not run and do not report it as successful.

Generate both inventories through their existing atomic writers and use
`ansible-inventory --list` / `--host` to verify syntax, target membership, and trust variables.

### Live verification A — OpenSSH lookup on a non-default port

Without permanently changing the host configuration, create a non-default-port fixture using a
temporary localhost port forward to `agdnsmasq:22` or an equivalent safe mechanism.

1. Put the verified live-host key under the bare stable alias in a disposable managed known_hosts
   file.
2. Confirm that
   `ssh -p <non-default> -o HostKeyAlias=<bare alias> -o UserKnownHostsFile=<file>
   -o StrictHostKeyChecking=yes ...` succeeds.
3. Confirm that a disposable file containing only `[alias]:port` fails.
4. Confirm that nctl enrollment/preflight succeeds with the same bare alias.
5. Remove the fixture, port forward, and disposable files.

If a safe fixture cannot be created, do not mark this verification complete. Record the reason and
the requirements for an alternative fixture, then run it when the environment is available.

### Live verification B — service/dnsmasq action after production regeneration

Exercise the actual path against `agdnsmasq`:

1. Confirm the bare alias, fingerprint, permissions, and absolute path of the managed store. Do not
   add an IP-keyed entry to the normal known_hosts file.
2. Render the bootstrap and production inventories and confirm identical alias/common arguments
   while their routes differ.
3. Run a dry-run of `nctl apply dnsmasq --inventory <bootstrap>` and confirm the mDNS preflight.
4. Run a dry-run of `nctl apply dnsmasq` and confirm the production-route preflight.
5. Ensure the reconcile plan contains `dnsmasq_config` or an SSH-requiring
   `service_profile` action. If no legitimate drift already exists, obtain operator confirmation
   before creating a reversible, harmless test dnsmasq-record change through the normal
   desired-state interface, then restore and reconverge it afterward.
6. Run `nctl reconcile agdnsmasq --yes` and confirm from its operation artifacts that:
   - production inventory regeneration succeeded;
   - `ssh_preflight` is non-empty;
   - the scanned route equals the production route from the same generation, currently expected
     to be the reserved IP;
   - the fingerprint matches the managed key;
   - the service/dnsmasq Ansible action ran and succeeded; and
   - no host-key failure occurred and the scoped target reached the expected state.
7. If a test desired-state change was used, reverse it and reconcile again to restore the original
   state.
8. Repeat the same SSH-requiring plan with a disposable empty managed store. Confirm that apply
   stops with `ssh_host_key_unenrolled` before any mutating inventory, Nautobot, or playbook
   action.
9. Reproduce mismatch with a disposable store/route fixture without changing the live host key,
   and confirm that service actuation does not start.

Record:

- Commands, timestamps, commits, and operation IDs.
- Source/render generation ID and scanned route.
- Public SHA-256 fingerprints only; no raw key blob or credential.
- Action list, preflight list, Ansible recap, and final scoped state.
- Any temporary desired-state change and its restoration result.

## Implementation order and commit boundaries

Use this order so each commit passes its focused tests and later steps do not temporarily
duplicate an incorrect earlier contract:

1. `ssh identity/path contract` — Step 1.
2. `non-default-port enrollment` — Step 2.
3. `production render context and exact-route preflight` — Step 3.
4. `dnsmasq inventory trust preflight` — Step 4.
5. `docs and automated verification` — the first half of Step 5.
6. `live Phase 3 replay evidence` — live verification report only.

Do not mix root-repository changes with `nctl` or `ansible_agdev` submodule changes in one
submodule commit. Commit each submodule first, then update the root submodule pointers and devdocs.
Per the local environment policy, ask the user to push; do not push automatically.

## Rollback

- Roll back code by submodule commit.
- Do not rewrite the managed known_hosts store merely because code is rolled back. It is
  controller state outside the repository and may only be changed by explicit enrollment after
  verifying the live fingerprint.
- If an obsolete `[alias]:port` entry has been removed, do not restore the malformed entry during
  rollback. The bare alias is the correct OpenSSH contract for both port 22 and a non-default port.
- Reverse a live-verification desired-state change through the normal desired-state interface and
  confirm restoration with reconcile.

## Final exit criteria

- Real connections on port 22 and a non-default port both succeed using one managed entry under the
  same bare UUID alias.
- `[alias]:port` no longer appears in managed runtime lookup, enrollment output, or preflight.
- Only legacy known_hosts promotion uses the endpoint's non-default-port representation.
- Relative `[ssh]` paths resolve to one config-file-relative absolute path independent of cwd.
- Production generation and post-regeneration scanning use the same snapshot, generation, and
  route.
- A missing production route never falls back to mDNS and fails before service actuation.
- A production generation or atomic-install failure starts no service Ansible process.
- Both configured and override inventory paths in `nctl apply dnsmasq` validate the expected
  alias, strict SSH arguments, managed entry, and offered key before starting Ansible.
- Unknown, unenrolled, unreachable, mismatch, and invalid-inventory-contract cases produce distinct
  structured errors.
- The full nctl test suite passes.
- A live reconcile records a non-empty post-regeneration `ssh_preflight` and a real
  service/dnsmasq action, and reaches the expected scoped state without a one-off IP known_hosts
  workaround.
- The previous report's overbroad completion claims are corrected, and the new report preserves
  the evidence for the renewed proof.
