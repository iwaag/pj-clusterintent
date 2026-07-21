# fix_sshkey Implementation Plan: stable SSH trust across bootstrap and production endpoints

Goal: make SSH host-key verification follow the stable nintent node identity rather than the
current network spelling of that node. A node first reached as `<hostname>.local` must remain the
same trusted SSH host when nctl later connects through `<hostname>.home.arpa`, a DHCP reservation,
a static IP, or a Tailscale address. Unknown or changed keys must continue to fail closed; this
plan does not use `StrictHostKeyChecking=no`, `accept-new`, or an unverified `ssh-keyscan` result.

After this work is implemented, replay the Phase 3 `agdnsmasq` workflow from
`devdocs/big/braindump/p3/memo.py`. Do not apply the memo's one-off IP known_hosts workaround first:
the replay is intended to prove the permanent design.

## Current state (as of 2026-07-22)

The failure is reproducible and is caused by two correct but currently disconnected contracts:

- The bootstrap inventory emitted by `nctl_core.hosts_intent` uses the selected mDNS endpoint as
  `ansible_host`, e.g. `agdnsmasq.local`. The inventory also carries the stable
  `nintent_desired_node_id`.
- The production inventory carries `local_ip`, `local_dns_hostname`, and `mdns_hostname`, but
  `ansible_agdev/inventories/generated/group_vars/all/main.yml` deliberately resolves a local
  connection in the order `local_ip -> local_dns_hostname -> mdns_hostname -> inventory_hostname`.
  For `agdnsmasq` this selects `192.168.0.2` after observation/IPAM succeeds.
- OpenSSH normally indexes host keys by the connection name/address. It therefore does not infer
  that a key trusted for `agdnsmasq.local` is also the expected key for `192.168.0.2`.
- Operation `01KY2NZR048X0GKWYBN4DVENW5` successfully completed mDNS observation and IPAM
  reconciliation, then failed the production-inventory dnsmasq SSH connection with `Host key
  verification failed`. This is a controller trust/readiness problem, not desired-state drift or
  a dnsmasq placement problem.
- `nctl_core.ansible.AnsibleRunner` currently invokes Ansible without a managed SSH trust context.
  No nctl config, core operation, or CLI command owns host-key enrollment.
- Ansible host-key checking is still enabled by default. Keep that behavior. The missing piece is a
  stable lookup alias and an explicit way to populate the key stored under that alias.

OpenSSH's `HostKeyAlias` is the intended primitive: it substitutes a stable alias when looking up
or saving a key, independently of the hostname/IP used for the TCP connection. Ansible's builtin
SSH connection plugin applies `ansible_ssh_common_args` to ssh, scp, and sftp, so it can carry
`HostKeyAlias`, `UserKnownHostsFile`, and the strict verification options through every Ansible SSH
path used here.

External contract references:

- OpenSSH `ssh_config(5)`: `HostKeyAlias`, `UserKnownHostsFile`, `StrictHostKeyChecking`,
  `CheckHostIP`, and `UpdateHostKeys` — <https://man.openbsd.org/ssh_config.5>
- OpenSSH known_hosts file format — <https://man.openbsd.org/sshd.8#SSH_KNOWN_HOSTS_FILE_FORMAT>
- Ansible builtin SSH connection options, including `ansible_ssh_common_args` and default-enabled
  host-key checking —
  <https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/ssh_connection.html>

## Design decisions

### 1. Separate route identity from trust identity

- `ansible_host` remains the routable endpoint. Bootstrap continues to use mDNS. Production may
  continue to choose IP first under the current contract; changing that priority is not required
  to solve host-key identity.
- The SSH trust alias is derived only from the immutable DesiredNode UUID:

  ```text
  nctl-node-<nintent_desired_node_id>
  ```

  Example:

  ```text
  nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33
  ```

- Do not use the node slug, `.local` name, `.home.arpa` name, IP address, Nautobot Device ID, or
  MAC address as the trust identity. Slugs and endpoints may change; actual Device rows may be
  relinked or recreated. The DesiredNode ID represents the stable logical node slot already present
  in both bootstrap and production inventories.
- Reusing a DesiredNode for replacement hardware intentionally produces a key mismatch. Hardware
  replacement must use explicit re-enrollment; it must never silently inherit trust merely because
  it acquired the old IP or DNS name.
- The helper that derives the OpenSSH known_hosts lookup name must cover `ansible_port`. Tests must
  confirm the exact OpenSSH-compatible representation for both port 22 and a non-default port
  (normally the bracketed `[alias]:port` form for the latter) rather than assuming port 22 forever.

### 2. nctl owns a dedicated local trust store

- Add an optional strict `[ssh]` config section, backed by an `SshConfig` model in
  `nctl_core.config`:

  ```toml
  [ssh]
  known_hosts_file = "~/.local/state/nctl/ssh/known_hosts"
  keyscan_timeout_seconds = 10
  lock_path = "~/.local/state/nctl/ssh.lock"
  ```

- These defaults must work when the section is absent, as the other optional nctl config sections
  do. Paths are expanded by nctl; inventory generation receives the resolved known_hosts path.
- Create the parent directory with mode `0700` and the file with mode `0600`. Host public keys are
  not secrets, but this file is security-sensitive controller state whose integrity must not depend
  on repository permissions.
- Never commit the managed known_hosts file, copy it into an operation artifact, or write it to
  Nautobot/nintent. It is local controller trust state, not cluster desired state or nodeutils
  actual state.
- Preserve unrelated entries and comments when updating the file. Mutations are serialized by the
  configured lock, written through a private staged sibling, and atomically replaced. Do not use a
  broad `ssh-keygen -R`, truncate the file, or rewrite `~/.ssh/known_hosts`.
- The existing user/system known_hosts files are read-only trust sources during migration/enrollment
  and are never modified by nctl.

### 3. Every generated SSH host carries the same strict trust policy

For each `ssh_hosts` member, both bootstrap and production inventory generation add transparent
host variables equivalent to:

```yaml
nctl_ssh_host_key_alias: nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33
ansible_ssh_common_args: >-
  -o HostKeyAlias=nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33
  -o UserKnownHostsFile=/resolved/local/state/nctl/ssh/known_hosts
  -o StrictHostKeyChecking=yes
  -o CheckHostIP=no
  -o UpdateHostKeys=no
```

- Build this string in one nctl helper. Do not duplicate quoting/path rules in the bootstrap and
  production composers.
- `CheckHostIP=no` makes the selected route irrelevant to key lookup and prevents a second raw-IP
  identity from being introduced. `HostKeyAlias` remains the only per-node lookup identity.
- `UpdateHostKeys=no` prevents an ordinary unattended Ansible connection from mutating the managed
  trust store. Adding or rotating keys remains an explicit nctl operation.
- Do not disable the system global host-key database. The UUID-based alias is deliberately unique;
  the dedicated user file is the normal matching source, while system-wide revocation/CA policy
  should not be bypassed without a separate reason.
- Do not make these options depend on adjacent generated `group_vars`. The operation-scoped
  bootstrap inventory written under the event directory cannot discover those files reliably.
  Host vars ensure the same behavior for operation-scoped observation, a persisted
  `hosts_intent.yml`, production inventory, dnsmasq actuation, and direct Ansible diagnostics.
- `ansible_ssh_common_args` is controller-generated and closed; it must never be accepted from an
  arbitrary nintent text/config field.

This is a breaking contract update:

- bump the hosts-intent inventory schema from `4.0` to `5.0`;
- bump the production inventory schema from `2.0` to `3.0` because the closed host-variable set and
  rendered bytes change;
- update the paired validators, compatibility snapshots, reports, and docs together; and
- add no dual-schema reader or compatibility alias.

### 4. Enrollment is explicit and has a verified trust source

Add a local-only command:

```text
nctl ssh enroll HOST [--from-known-hosts | --fingerprint SHA256:...] [--replace] [--yes] [--json]
```

The command follows the nctl dry-plan/apply convention:

- Without `--yes`, resolve the exact DesiredNode slug and its selected bootstrap mDNS endpoint,
  collect the currently offered public keys, and show the node ID, endpoint, port, stable alias,
  currently managed fingerprints, offered fingerprints, eligible trust source, and proposed
  action. It performs no write.
- `ssh-keyscan` may be used to observe offered public keys, with a bounded timeout and argv-based
  subprocess execution. Its output is never sufficient on its own to mark a key trusted.
- `--from-known-hosts` is the migration/bootstrap path for this cluster. Resolve the effective
  OpenSSH user known_hosts files for the mDNS endpoint, including hashed host entries, and accept
  only an offered key whose exact key type/blob is already trusted for that endpoint. Use
  `ssh -G`/`ssh-keygen -F` or an equivalently tested mechanism; do not assume that the only source
  file is literally `~/.ssh/known_hosts`.
- `--fingerprint` is the clean path for a new machine with no prior entry. The supplied SHA-256
  fingerprint must have been obtained through a trusted channel such as the machine console,
  provisioning output, or an administrator-confirmed host public key. Enroll only an offered key
  whose computed fingerprint exactly matches. Make the option repeatable if multiple host-key
  algorithms are deliberately pinned.
- If neither a previously trusted exact key nor a supplied matching fingerprint is available, the
  command remains a read-only inspection and returns `host_key_unverified`; `--yes` does not turn
  an unverified scan into TOFU.
- Re-scan and re-check the selected key inside the write/lock boundary before committing it, so the
  plan cannot be applied to a different offered key unnoticed.
- An absent alias is enrolled. The same already-enrolled key is an idempotent no-op. A different
  key at an existing alias fails with `host_key_conflict`; replacement requires all of
  `--replace`, a verified source (`--from-known-hosts` or matching `--fingerprint`), and `--yes`.
- Store only the stable alias plus the verified key type/blob and a human-readable comment with the
  current slug. Do not store `.local`, `.home.arpa`, or current IP as additional matching names.
- Emit an `nctl.ssh.enroll.v1` envelope. Keep raw public-key blobs out of normal text output; JSON
  may include key type and SHA-256 fingerprint but does not need to expose the full blob.
- Do not expose enrollment through `nctl serve` in this change. It mutates trust on the local
  controller and needs a separate remote-authority design before becoming an HTTP operation.

### 5. Preflight before reconciliation writes; SSH remains the final verifier

- Add a read-only core check that determines whether every SSH-requiring node in the plan has at
  least one valid entry under its stable alias in the configured managed file. Missing entries
  produce `ssh_host_key_unenrolled` with the exact `nctl ssh enroll <slug>` remediation.
- In `nctl reconcile --yes`, run this enrollment preflight for the complete initial action plan
  before executing observation, Nautobot Jobs, inventory writes, or playbooks. Repeat it for each
  re-plan round before that round's writes, because later rounds may introduce a new SSH target.
  This prevents the current pattern where observation/IPAM writes succeed before a predictable
  missing-key failure is discovered.
- A no-`--yes` reconcile remains a zero-write dry plan. Include the local SSH readiness result in
  its output as a prerequisite/warning, but do not convert it into desired-vs-actual drift, a
  reconcile diff code, or a Nautobot status.
- Presence in the trust file is not proof that the current endpoint presents the key. Before the
  first mutating action in a round, compare the keys currently offered by every already-resolvable
  route that the round will use with the pinned managed keys. This is a read-only rejection check:
  a scan can prove a mismatch against an already trusted key, but can never authorize a new key.
  Fail before writes with `ssh_host_key_mismatch` or `ssh_host_key_unreachable` as appropriate.
- A route created only by an IPAM action may not be testable before that action. Re-run route
  verification after production inventory regeneration and before the first production playbook;
  do not attempt SSH actuation if the newly selected endpoint does not present the pinned key.
- OpenSSH with `StrictHostKeyChecking=yes` and `HostKeyAlias` remains the final verifier for the
  actual ssh/scp/sftp connection. Preflight improves atomicity and diagnostics; it does not replace
  OpenSSH verification.
- Standalone Ansible commands that use either generated inventory remain protected even when they
  bypass nctl: they receive the strict per-host variables and fail closed, although their error may
  be OpenSSH's generic `Host key verification failed` rather than nctl's structured error.

### 6. Keep SSH readiness outside convergence semantics

- Do not add SSH fingerprints, enrollment state, or key health to nintent models, nodeutils dumps,
  Nautobot actual state, `nctl drift`, service observation, or Alignment Reviews.
- Do not make missing local trust mean that a cluster node itself is drifting. It means this
  controller is not ready/authorized to actuate that node.
- Do not add SSH CA/certificate issuance, automatic rotation, multi-controller trust replication,
  DNS SSHFP, or secret-management machinery in this fix. Those may become worthwhile at larger
  scale, but a dedicated pinned-key store is the smallest complete solution for the current
  single-operator local cluster.

## Step 1 — configuration and pure SSH identity helpers

- `nctl/src/nctl_core/config.py`:
  - add strict `SshConfig` with the defaults above;
  - add path resolvers and bounds validation for the keyscan timeout; and
  - attach it to `Config` with a default instance.
- `nctl/example.nctl.toml` and config documentation: show the optional section and explain that the
  file is local trust state, not a credential or generated repo artifact.
- Add `nctl/src/nctl_core/ssh_trust.py` with pure/testable helpers for:
  - validating a DesiredNode UUID and deriving the alias;
  - deriving the lookup name for default/non-default ports;
  - computing OpenSSH-compatible SHA-256 fingerprints from public-key blobs;
  - building safely quoted `ansible_ssh_common_args` from an alias and resolved path;
  - parsing only valid known_hosts/keyscan lines without accepting markers or malformed keys as
    ordinary host keys; and
  - checking managed entries by exact alias/key type/blob.
- Tests in `nctl/tests/test_ssh_trust.py`: UUID/alias determinism, port handling, SHA-256 vectors,
  malformed lines, comments, duplicate keys, path quoting, strict option presence, and no endpoint
  name/address appearing in the trust alias.
- Extend `test_config.py` for defaults, overrides, path expansion, timeout bounds, and rejection of
  unknown `[ssh]` keys.

## Step 2 — explicit enrollment core and CLI

- Implement `build_ssh_enroll()` and text rendering in the core module (or a small adjacent
  `ssh_enroll.py` if keeping file parsing separate makes the boundary clearer). Keep Typer thin.
- Add an `ssh` Typer command group and `ssh enroll` wrapper to `nctl_core/cli/main.py`.
- Reuse the desired-state GraphQL reader to resolve one exact DesiredNode and the same deterministic
  mDNS endpoint-selection rule used by hosts-intent. Extract/reuse that selector rather than
  implementing a different bootstrap endpoint preference in the enrollment path.
- Introduce a narrow injected subprocess interface for `ssh-keyscan`, `ssh -G`, and `ssh-keygen -F`
  so tests never depend on the developer's real SSH files or network. Invoke argv directly, never
  through a shell.
- Implement dry plan, verified-source selection, locked/atomic write, idempotency, and explicit
  replacement rules from Design Decision 4.
- Record an operation/event artifact containing node/alias/fingerprint/outcome metadata if the
  existing operation framework is reused, but never copy the managed known_hosts file or full
  unredacted scan output into artifacts.
- Tests:
  - unverified scan cannot be applied, even with `--yes`;
  - matching explicit fingerprint can be applied;
  - matching plain and hashed legacy `.local` entries can be promoted;
  - a legacy entry that does not match the currently offered key fails;
  - existing identical entry is a no-op;
  - conflict fails without `--replace` and still fails with `--replace` but no verified source;
  - verified replacement changes only the exact alias entry;
  - permissions, atomic preservation, duplicate suppression, lock contention, timeouts, malformed
    command output, unknown node, node without mDNS, non-default port, text/JSON envelopes, and CLI
    exit codes.

## Step 3 — bootstrap inventory uses the stable alias

- Extend `export_hosts_intent()`/`_host_vars()` to receive the resolved managed known_hosts path and
  emit `nctl_ssh_host_key_alias` plus generated `ansible_ssh_common_args` for every eligible node.
- Bump `HOSTS_INTENT_SCHEMA_VERSION` to `5.0`; update the render envelope fixtures and schema/header
  assertions where applicable.
- Ensure `build_hosts_intent_render()` and `run_observation()` pass `cfg.ssh` values. This is
  essential for the operation-scoped `events/<operation>/bootstrap/hosts_intent.yml`, not only the
  persisted generated inventory.
- Tests in `test_hosts_intent.py`, `test_hosts_intent_render.py`, and `test_observation.py`:
  - aliases derive from node IDs and are unchanged when mDNS names change;
  - two different node IDs cannot share an alias;
  - the configured managed path and all strict options appear in host vars;
  - operation-scoped collection and slurp invocations receive the protected inventory; and
  - missing enrollment is reported before either Ansible subprocess is called.

## Step 4 — production inventory uses the identical alias

- Extend the production composition call with the resolved SSH trust settings. Add only the two
  controller-generated variables (`nctl_ssh_host_key_alias`, `ansible_ssh_common_args`) to the
  closed production host-variable contract.
- Bump production inventory schema to `3.0` and update:
  - `production/contract.py` validators and tests;
  - `production/composer.py` rendering/composition tests and determinism fixtures;
  - production render compatibility snapshots/reports; and
  - `ansible_agdev/docs/production_inventory_contract.md` and README sections.
- Assert that the same DesiredNode has byte-identical alias/trust arguments in bootstrap and
  production inventories even when `ansible_host` changes from `.local` to `.home.arpa`, IPv4,
  IPv6, or Tailscale.
- Remove any temptation to fix this by changing `local_ip -> DNS -> mDNS` selection order. Add a
  regression test where production deliberately selects an IP while the stable alias remains the
  mDNS-enrolled node alias.

## Step 5 — reconcile/apply preflight and structured failure

- Add an SSH requirement extractor for a `ReconcilePlan` that identifies only nodes used by
  observation or playbook actions. Ledger-only actions on unrelated nodes must not require SSH
  enrollment.
- Run whole-round enrollment and resolvable-route verification before action execution in
  `reconcile/executor.py`, and repeat after production regeneration when a route may have changed.
- Extend the reconcile output data/text with a controller-local `ssh_preflight` summary without
  adding it to drift or action classification. The dry plan should list `ready`, `unenrolled`,
  `mismatch`, and `unreachable` nodes clearly.
- `observation.py`, generic service playbook execution, and `dnsmasq_apply.py` retain their own
  narrow preflight guard as defense in depth and for standalone core/CLI entry points.
- When loading an arbitrary `--inventory` for `nctl apply dnsmasq`, require each target host to
  expose a valid `nintent_desired_node_id`/stable alias. Reject an old or hand-written inventory
  that cannot participate in the trust contract instead of silently falling back to endpoint-keyed
  verification.
- Tests cover:
  - `reconcile --yes` with an unenrolled required host invokes no observation, Nautobot Job,
    inventory mutation, or playbook;
  - dry-plan output remains zero-write and reports the same prerequisite;
  - ledger-only plans are not blocked by an unrelated unenrolled host;
  - a matching offered key permits execution;
  - a wrong host at a reserved IP is rejected before the playbook;
  - a route changed by IPAM is checked after regeneration;
  - missing/unreachable/mismatch errors remain distinct in JSON and text; and
  - dnsmasq bootstrap-inventory and production-inventory paths both enforce the same alias.

## Step 6 — operator documentation

- Update `nctl/README.md`, `ansible_agdev/README.md`, and `ansible_agdev/README_ADMIN.md` with the
  lifecycle:

  ```text
  discover by mDNS
    -> verify fingerprint / promote existing trusted .local key
    -> nctl ssh enroll
    -> observe and reconcile IPAM/DNS/DHCP
    -> connect by DNS/IP/Tailscale under the same HostKeyAlias
  ```

- Document hardware replacement/key rotation using `--replace` plus a newly verified source.
- Document recovery from managed-file loss as re-enrollment, not `StrictHostKeyChecking=no` or
  copying an unverified scan.
- Explain that direct Ansible use must use the current generated inventories; a handwritten
  inventory without the stable alias is outside the supported operational path.
- Update `devdocs/big/braindump/p3/memo.py` only after verification, replacing the open handoff with
  a pointer to the completed report. Preserve its original incident facts in the report/history.

## Verification

### Automated

- Run the focused suites while implementing each step, then the full nctl suite:

  ```text
  uv run --project nctl pytest -q nctl/tests/test_ssh_trust.py nctl/tests/test_config.py
  uv run --project nctl pytest -q nctl/tests/test_hosts_intent.py nctl/tests/test_hosts_intent_render.py
  uv run --project nctl pytest -q nctl/tests/test_production_contract.py nctl/tests/test_production_composer.py
  uv run --project nctl pytest -q nctl/tests/test_observation.py nctl/tests/test_dnsmasq_apply.py nctl/tests/test_reconcile_executor.py
  uv run --project nctl pytest -q nctl/tests
  ```

- Validate both rendered inventories with `ansible-inventory --list` through their existing atomic
  writers.
- Add an integration fixture with one node and four routes (`node.local`, `node.home.arpa`, local
  IP, Tailscale IP) asserting that every route is checked against one managed alias/key and a
  different key on any route fails.

### Live Phase 3 replay: `agdnsmasq`

1. Confirm the current `.local` trust source is the deliberately verified `agdnsmasq.local` entry;
   do not add a `192.168.0.2` entry to the ordinary user known_hosts file.
2. Run `nctl ssh enroll agdnsmasq --from-known-hosts --json` without `--yes`. Confirm it reports:
   - mDNS route `agdnsmasq.local`;
   - DesiredNode ID `27818c12-fe15-4c9f-83d0-7949523f6c33`;
   - alias `nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33`; and
   - an offered key exactly matching the pre-existing trusted `.local` key.
3. Repeat with `--yes`, then inspect using nctl/`ssh-keygen -F` that the dedicated managed file has
   the stable alias and no matching entry keyed by `.local`, `.home.arpa`, or `192.168.0.2`.
4. Render bootstrap and production inventories. Use `ansible-inventory --host agdnsmasq` to confirm
   both have the same `HostKeyAlias` and managed file while their `ansible_host` values may differ.
5. Run the mDNS bootstrap observation path. It must collect and ingest nodeutils successfully using
   the managed alias.
6. Run a production-inventory `ansible -m ping` while `ansible_host` resolves to `192.168.0.2`. It
   must succeed without adding an IP-keyed trust entry.
7. Run `nctl reconcile agdnsmasq` and inspect its SSH preflight, then run
   `nctl reconcile agdnsmasq --yes`. Observation, IPAM, production regeneration, dnsmasq setup, and
   records deployment must complete without host-key failure and reach the expected convergence
   state.
8. Verify the negative boundary without altering the real host:
   - point a disposable test inventory/fixture route at a server presenting another key and confirm
     mismatch/fail-closed behavior;
   - temporarily select an empty managed file in a disposable config and confirm reconcile refuses
     all writes with the enrollment instruction; and
   - confirm no test uses `StrictHostKeyChecking=no`, `accept-new`, or automatic key replacement.
9. Record commands, operation IDs, fingerprints (public SHA-256 values only), results, and any
   remaining friction in `devdocs/small/fix_sshkey/report_verification.md`. Then resume the broader
   Braindump Phase 3 conversational cases from their current desired/actual state.

## Exit criteria

- One verified managed key entry, indexed by immutable DesiredNode ID, authenticates the same node
  over mDNS, `.home.arpa`, reserved/static IP, and Tailscale routes.
- Changing only `ansible_host` never requires another enrollment and never adds an endpoint-keyed
  trust entry.
- Unknown, missing, changed, or wrong-host keys fail closed with actionable nctl output before host
  actuation; a predictable missing enrollment blocks a reconcile round before its writes.
- Enrollment and replacement require an exact previously trusted key or an explicitly supplied
  out-of-band SHA-256 fingerprint. An unverified scan plus `--yes` can never create trust.
- Bootstrap observation, operation-scoped inventory, production playbooks, `apply dnsmasq`, direct
  generated-inventory Ansible use, and reconcile all consume the same strict alias contract.
- No SSH trust data enters nintent, Nautobot actual state, nodeutils, drift classification, or the
  repository, and no compatibility shim remains for endpoint-keyed automation.
- The full nctl test suite passes and the live `agdnsmasq` Phase 3 replay converges with no one-off
  IP known_hosts workaround.
