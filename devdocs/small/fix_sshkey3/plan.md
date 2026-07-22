# fix_sshkey3 Implementation Plan: dnsmasq content convergence and complete SSH preflight evidence

Date: 2026-07-22

## Goal

Finish the work exposed by the incomplete `fix_sshkey2` Live verification B.

This initiative has two inseparable outcomes:

1. A change to the desired DNS/DHCP records must become real drift and cause
   `nctl reconcile --yes` to deploy the changed dnsmasq artifact even when the daemon is already
   running.
2. The SSH trust gate around that deployment must use one exact production-generation identity,
   route, and port; reject every inventory-level policy override; preserve partial-round evidence;
   and record enough public evidence to prove what it checked.

The result must be demonstrated with the same safe, reversible DesiredEndpoint change that
`fix_sshkey2` attempted. Do not stop the live dnsmasq daemon and do not fabricate a false
nodeutils observation merely to force an action.

## Current state

The `fix_sshkey2` implementation correctly established several important properties:

- managed known_hosts entries use the bare DesiredNode UUID alias on all ports;
- legacy endpoint lookup is separate and port-aware;
- SSH paths resolve relative to `nctl.toml`;
- a production route missing from an explicit map never falls back to mDNS;
- configured and override inventories both receive a managed-entry and offered-key preflight; and
- Live verification A proved the bare alias with real OpenSSH over a non-default port.

The full nctl suite currently passes (`871 passed, 1 warning`), and the repository worktrees are
clean. The live test endpoint created by `fix_sshkey2` was deleted and the original desired state
was restored.

The implementation and verification are nevertheless incomplete for the following reasons.

### 1. dnsmasq content is absent from drift

Service placement drift currently compares only observation freshness, service presence, running
state, and unexpected location. A new or changed DesiredEndpoint changes the deterministic
dnsmasq render, but it does not change the observed `dnsmasq` service's `running` state.
Consequently, no `dnsmasq_config` action is planned.

This is not only a test-fixture limitation. In normal operation, desired DNS, DHCP reservation, or
DHCP range changes can remain undeployed while `nctl drift` reports the dnsmasq service as
converged.

### 2. arbitrary inventory can override the closed SSH policy

`validate_inventory_trust_contract()` checks the exact generated
`ansible_ssh_common_args`, but currently accepts other effective host vars such as:

```yaml
ansible_ssh_args: >-
  -o StrictHostKeyChecking=no
  -o HostKeyAlias=attacker
```

Ansible places `ssh_args` before `ssh_common_args`; OpenSSH keeps the first obtained value.
The current validator therefore accepts an inventory that makes the real connection use
`StrictHostKeyChecking=no` and a different alias.

The validator also treats a string `ansible_port: "2222"` as port 22 during preflight while
Ansible may use it as port 2222.

### 3. the post-regeneration route is fresh but the port/identity snapshot is stale

The executor resolves the route from `render_context.source_snapshot`, then calls
`verify_offered_keys()` with the round-start `snapshot.desired`. The scan can therefore combine
a new route with an old `ansible_port` or old desired identity.

### 4. failed post-regeneration checks discard successful action evidence

Bootstrap/IPAM actions and production inventory installation may already have succeeded when a
post-regeneration scan fails. The exception path exits before appending `RoundSummary`, producing
`rounds: []`, `progress_made: false`, and a pre-mutation drift document labeled as final.

### 5. successful post-regeneration scans are not persisted

`ReconcileData.ssh_preflight` contains only the round-start enrollment-presence result. It does
not record the production generation ID, route, port, managed/offered fingerprints, or
post-regeneration result. The operation artifact therefore cannot prove the key assertion in Live
verification B.

### 6. some non-ready and I/O states bypass structured handling

- `_ssh_scan_errors()` ignores `unenrolled`, so a managed-store change between the initial and
  post-regeneration checks can proceed to Ansible.
- Managed-store read failures are structured in enrollment, but can still escape from reconcile
  and dnsmasq preflight.
- Production route resolution does not prove that a target was actually included in the installed
  production inventory; it can resolve a route from a source node that composition skipped.

## Corrected system contract

### 1. dnsmasq convergence is based on deployed content, not daemon state alone

The dnsmasq service has two independent actual-state dimensions:

| Dimension | Desired | Actual |
|---|---|---|
| Process state | active DesiredServicePlacement | nodeutils observed service state |
| nctl-managed records file | deterministic nctl-rendered bytes | SHA-256 of the file read on the target |

A running daemon with a different records-file digest is drifting. A matching file digest with a
stopped daemon is also drifting. Both must be represented independently in `nctl drift`.

The first implementation covers the nctl-owned records/ranges file
`/etc/dnsmasq.d/nintent-records.conf`. It does not claim to cover every dnsmasq package default
or `ansible.conf` setting; that broader service-configuration problem remains separate and must
be documented explicitly.

### 2. the desired dnsmasq artifact must be byte-deterministic

The currently deployed conf contains `generated_at` and `operation_id` comments. A full-file
digest therefore changes on every render even when desired state is unchanged.

Change the managed conf byte contract so identical source state produces identical bytes:

```text
# Generated by nctl
# schema_version: <version>
<sorted DNS/DHCP directives>
```

Keep timestamps and operation IDs in the nctl envelope, event log, and artifact metadata, not in
the deployed file. Compute:

```text
content_sha256 = lowercase hex SHA-256 of the exact UTF-8 conf bytes
```

Nodeutils computes the same standard full-file SHA-256. There is no comment-stripping algorithm,
sidecar acknowledgment, controller-local “last applied” state, or second semantic canonicalizer.

This is a deliberate breaking byte-contract change:

- bump `DNSMASQ_EXPORT_SCHEMA_VERSION` from `4.0` to `5.0`;
- bump `nctl.render.dnsmasq.v1` to `nctl.render.dnsmasq.v2`; and
- bump `nctl.apply.dnsmasq.v1` to `nctl.apply.dnsmasq.v2`.

Do not retain a dual renderer or digest old timestamped bytes. The first reconciliation after
rollout legitimately replaces the old file once.

### 3. nodeutils is the verified source for deployed-file digest

Extend nctl-generated service probe hints with a closed managed-file observation:

```yaml
service_probe_hints:
  dnsmasq:
    systemd_unit: dnsmasq.service
    managed_files:
      records:
        path: /etc/dnsmasq.d/nintent-records.conf
        digest: sha256
```

The path must come from validated deployment-profile reconciliation metadata and be used by both
the deploy action and observation configuration. Do not duplicate the path independently in nctl
and the Ansible playbook.

Nodeutils reports only metadata, never file content:

```json
{
  "observed_services": {
    "dnsmasq": {
      "state": "active",
      "source": "systemd",
      "managed_files": {
        "records": {
          "path": "/etc/dnsmasq.d/nintent-records.conf",
          "status": "present",
          "sha256": "<64 lowercase hex>",
          "size": 1234,
          "checked_at": "<timestamp>"
        }
      }
    }
  }
}
```

Statuses are `present`, `missing`, `unreadable`, and `too_large`. Hash reads are binary,
bounded, and allowed only for absolute paths supplied by the trusted nctl-generated probe config.
The records file is mode `0644`, so the existing non-root nodeutils execution can read it.

The existing Nautobot `observed_services` JSON custom field remains the storage surface; do not
add an applied-digest model or a new database. The nauto ingestor must preserve and test the nested
managed-file metadata unchanged.

Because the nodeutils report contract gains new actual-state semantics, make this a coordinated
breaking change:

- bump `nodeutils.inventory.v1` to `nodeutils.inventory.v2`;
- make the nauto ingest policy accept v2 only; and
- make nctl dump parsing expect v2 only.

Do not add a v1/v2 dual reader. Regenerate current observations with the v2 collector during
rollout.

### 4. dnsmasq digest drift has explicit codes and an observation loop

For each active placement whose validated reconciliation action is `dnsmasq_config`, compare the
one desired content digest with the managed-file observation on each target host.

Use distinct drift codes:

- `service_config_observation_missing` — fresh service observation has no managed-file result;
  classified as `OBSERVATION`.
- `service_config_missing` — nodeutils explicitly observed the file as missing; automatic
  `service_profile` classification, resolved to `dnsmasq_config` by profile metadata.
- `service_config_unreadable` — file exists but could not be read/hashed; automatic deployment
  may repair owner/mode/content, but a repeated result becomes actionable failure evidence.
- `service_config_mismatch` — observed SHA-256 differs from desired SHA-256; automatic
  `dnsmasq_config`.

Every diff includes the service/placement/node identity, managed-file observation key/path,
desired digest, actual digest/status, and observation time. It never includes file contents.

`DNSMASQ_CONFIG.requires_observation` becomes true. After a successful deployment, reconcile runs
nodeutils collection/ingest for the action's `parameters["host_slugs"]`, then the next round
recomputes drift. Fix the current post-actuation observation target extraction, which reads
service target slugs instead of the node host list.

Expected bounded flow:

```text
round 0 (only when v2 config observation is absent):
  observe node -> ingest v2 managed-file digest

round 1:
  service_config_mismatch/missing -> SSH preflight -> deploy dnsmasq -> observe/ingest

round 2:
  desired digest == observed digest -> converged
```

The default three-round limit is sufficient.

### 5. production SSH preflight consumes a resolved target from the installed composition

Replace the split `DesiredSnapshot + RouteOverrides` production API with one immutable resolved
target built during successful production composition:

```text
ResolvedSshTarget
  slug
  desired_node_id
  alias
  route
  port
  generation_id
```

Only nodes actually included in `composition.inventory["ssh_hosts"]` receive a target. Route and
port come from the same `NodeInput` and effective operational values used to compose that host.

`ProductionRenderContext` carries the exact target map alongside its envelope. After staged
validation and atomic installation, the executor scans those targets directly. A planned service
host missing from the map is `no_resolvable_production_target`; it never falls back to mDNS and
never uses the round-start snapshot.

Bootstrap preflight remains a separate constructor that selects mDNS and port from one
`DesiredSnapshot`. Do not make a single optional-argument function switch between bootstrap and
production behavior.

### 6. inventory SSH trust validation is an allowlist, not one exact-field check

For each target loaded through `ansible-inventory`:

- require a canonical DesiredNode UUID;
- require the exact UUID-derived alias;
- require the exact controller-generated `ansible_ssh_common_args`;
- require `ansible_port` to be an integer in `1..65535` when present;
- require `ansible_connection` to be absent or exactly `ssh`; and
- reject any inventory variable capable of replacing or preceding the closed policy, including:
  - `ansible_ssh_args`;
  - `ansible_ssh_extra_args`;
  - `ansible_scp_extra_args`;
  - `ansible_sftp_extra_args`;
  - `ansible_ssh_executable`;
  - `ansible_host_key_checking`; and
  - `ansible_ssh_host_key_checking`.

Prefer a closed allowed-prefix/field set over an ever-growing denylist where practical. Tests must
use the installed Ansible connection-plugin ordering and `ssh -G` to prove that the previously
accepted override is now rejected.

This contract governs nctl-controlled inventory data. An operator explicitly invoking Ansible
outside nctl with hostile CLI options or environment variables remains outside this initiative,
but documentation must state that such overrides leave the supported path.

### 7. every started round and every SSH decision remains visible

Replace exception-only post-regeneration termination with an internal round outcome:

```text
RoundOutcome
  summary
  terminal_errors
  had_side_effects
```

Once `round_started` is emitted, append its `RoundSummary` on success, interruption, regeneration
failure, and SSH preflight failure. Record each completed action before evaluating the terminal
error.

Compute `progress_made` from successful mutating actions, not from whether the summary happened
to be appended. If a failure occurs after a successful mutation, perform one final read-only drift
refresh. If that refresh itself fails, say that final state is unknown instead of labeling the
pre-mutation drift as final.

Define a richer public preflight record:

```text
phase: enrollment | bootstrap_route | production_route | inventory_route
round
slug
alias
route
port
generation_id
status
detail
managed_fingerprints
offered_fingerprints
```

Fingerprints are public SHA-256 values. Raw key blobs remain excluded. Put per-round records in
`RoundSummary.ssh_preflight` and retain a flattened top-level summary only if needed for operator
convenience.

Map every non-ready status, including `unenrolled`, to a structured error. Convert managed-store
read/parse errors and probe `OSError`/timeout failures into envelopes rather than uncaught
exceptions.

This output change bumps `nctl.reconcile.v1` to `nctl.reconcile.v2`. Do not retain a parallel v1
serializer.

## Non-goals

- Stopping the real dnsmasq daemon to manufacture service drift.
- Writing a fabricated service observation into Nautobot.
- Treating a controller-local “last applied digest” as actual host state.
- Persisting the rendered dnsmasq file or its contents in Nautobot.
- General-purpose file integrity monitoring.
- Full content convergence for every deployment profile or every dnsmasq package/base-setting
  file. This initiative covers the nctl-owned records/ranges artifact.
- SSH CA, SSHFP, automatic key rotation, or trust synchronization between controllers.
- Weakening strict SSH behavior for a test.
- Backward-compatibility readers or dual output schemas during this breaking-change phase.

## Step 1 — close the SSH inventory and probe error contracts

Scope: `nctl`.

Files:

- `src/nctl_core/inventory_trust.py`
- `src/nctl_core/dnsmasq_apply.py`
- `src/nctl_core/ssh_enroll.py`
- `src/nctl_core/reconcile/ssh_preflight.py`
- related tests and compatibility snapshots

Implementation:

1. Add a structured effective-inventory SSH target validator with the allowlist above.
2. Validate port type/range instead of coercing invalid values to 22.
3. Reject policy-changing connection variables before managed-file or network access.
4. Turn managed-store read/encoding/parse failures into
   `ssh_store_read_failed` for reconcile and dnsmasq apply.
5. Make all real probe functions wrap `TimeoutExpired`, `OSError`, nonzero exit, and malformed
   output as `SshTrustError`.
6. Include `unenrolled` in post-scan error mapping.

Tests:

- exact common args plus `ansible_ssh_args=-o StrictHostKeyChecking=no` is rejected;
- alias override, custom SSH executable, local connection, scp/sftp/ssh extra args are rejected;
- an integer port 2222 is scanned as 2222;
- string, boolean, zero, negative, and >65535 ports are rejected;
- unreadable/corrupt managed store returns a structured error and invokes no Ansible command;
- keyscan executable missing and timeout return structured unreachable errors; and
- a store removed between enrollment and post-regeneration scan stops as unenrolled.

Step 1 exit criteria:

- No supported inventory variable can precede or replace the generated host-key policy.
- Invalid ports never silently become 22.
- Trust-store/probe failures do not escape as tracebacks.

## Step 2 — make production SSH targets generation-exact and preserve round evidence

Scope: `nctl`.

Files:

- `src/nctl_core/production/composer.py`
- `src/nctl_core/production_render.py`
- `src/nctl_core/reconcile/ssh_preflight.py`
- `src/nctl_core/reconcile/executor.py`
- reconcile/production tests and compatibility snapshots

Implementation:

1. Add `ResolvedSshTarget` and populate it only after a node is successfully included in
   `ssh_hosts`.
2. Carry the target map in `ProductionRenderContext`; assert its generation ID matches the
   inventory/report generation.
3. Replace production `resolve_production_routes(...)+verify_offered_keys(old_snapshot,...)` with
   direct verification of these targets.
4. Keep bootstrap target construction separate.
5. Add phase/round/route/port/generation/fingerprint fields to preflight results.
6. Introduce `RoundOutcome`; always retain partial action and preflight evidence.
7. Refresh final drift after any failed round that completed a mutation.
8. Derive post-actuation observation hosts from `parameters["host_slugs"]`.

Tests:

- old snapshot port 22/new generation port 2222 scans only route:new-port;
- a node with a resolvable source route but skipped from production composition is rejected before
  service Ansible;
- generation, route, and port in the scan record equal the installed composition;
- IPAM success followed by mismatch retains both the IPAM and production-render action results;
- the same result reports `progress_made: true` and a fresh final drift;
- production write failure retains its failed action in the round;
- successful production scan is visible in JSON/text/artifacts with fingerprints but no blobs;
- interruption retains actions completed before interruption; and
- post-action observation receives node slugs, never service slugs.

Step 2 exit criteria:

- No production scan reads route, port, or identity from the round-start snapshot.
- Every started round is represented in output.
- Live verification can prove the exact generation/route/port/key decision from artifacts alone.

## Step 3 — create deterministic dnsmasq bytes and a desired digest

Scope: `nctl`.

Files:

- `src/nctl_core/dnsmasq.py`
- `src/nctl_core/dnsmasq_render.py`
- `src/nctl_core/dnsmasq_apply.py`
- CLI/serve/compatibility tests and documentation

Implementation:

1. Remove volatile timestamp/operation comments from the managed conf bytes.
2. Add a pure `dnsmasq_content_sha256(conf: str)` helper over exact UTF-8 bytes.
3. Add `content_sha256` to render/apply data and operation events.
4. Add a pure render-from-snapshot context so drift and CLI rendering use one implementation.
5. Bump dnsmasq export/render/apply contracts as specified above.
6. Preserve `generated_at` and `operation_id` in JSON/event metadata only.

Tests:

- equal snapshots at different times/operation IDs produce byte-identical conf and digest;
- one DNS record, DHCP reservation, range, or meaningful directive change changes the digest;
- comments containing runtime metadata are absent from deployed bytes;
- digest equals a standard independent SHA-256 test vector;
- dry-run/apply deploy exactly the bytes whose digest is reported; and
- old compatibility snapshots are replaced, not conditionally accepted.

Step 3 exit criteria:

- Desired dnsmasq content has one stable 64-hex digest.
- Re-rendering unchanged state cannot create drift.

## Step 4 — observe managed-file digest through nodeutils and Nautobot

Scope: `nodeutils`, `ansible_agdev`, `nctl`, and `nauto`.

Files:

- `nodeutils/nodeutils_collect.py`, example config, tests, README
- `ansible_agdev/vars/deployment_profiles.yml`
- `ansible_agdev/playbooks/dnsmasq/deploy_dnsmasq_records.yml`
- `nctl/src/nctl_core/reconcile/profiles.py`
- `nctl/src/nctl_core/observation.py`
- `nctl/src/nctl_core/dumps.py`
- `nauto/jobs/ingest_nodeutils_inventory.py`
- `nauto/seed/nodeutils_ingest.yaml`
- related tests/docs

Implementation:

1. Extend validated reconciliation metadata with a closed managed-file observation for
   `dnsmasq_config`.
2. Pass that same path to the deploy playbook and nctl-generated nodeutils probe hints.
3. Add bounded binary SHA-256 observation and explicit statuses to nodeutils.
4. Attach managed-file results to the normalized observed-service entry.
5. Bump the nodeutils report schema to v2 across collector, nctl parser, ingest policy, fixtures,
   and docs.
6. Prove nauto preserves the nested metadata exactly in `observed_services`.
7. Update nctl `ActualFacts` tests to prove the nested data survives GraphQL parsing unchanged.

Tests:

- present file digest/size/path/status;
- missing, unreadable, and oversized files;
- relative or malformed probe paths rejected;
- no file contents in serialized report, logs, or Nautobot fields;
- probe hints appear only on hosts with the active profile placement;
- deployment and observation use one metadata-owned path;
- v1 reports are rejected after coordinated rollout; and
- v2 collect -> ingest -> GraphQL -> nctl ActualFacts round trip preserves the digest.

Step 4 exit criteria:

- A fresh nodeutils observation provides verified actual bytes metadata for the deployed records
  file.
- No new Nautobot model or custom field is required.

## Step 5 — add dnsmasq content drift and automatic reconciliation

Scope: `nctl`.

Files:

- `src/nctl_core/drift/context.py`
- `src/nctl_core/drift/comparators.py` or a dedicated dnsmasq comparator
- `src/nctl_core/drift/service_placement.py`
- `src/nctl_core/reconcile/classify.py`
- `src/nctl_core/reconcile/reconcilers.py`
- `src/nctl_core/reconcile/planner.py`
- `src/nctl_core/reconcile/executor.py`
- drift/planner/executor tests

Implementation:

1. Load validated reconciliation metadata into `DriftContext); an unavailable contract is a
   classified global error, never silent convergence.
2. Compute one desired dnsmasq context from the same `SourceSnapshot` used for drift.
3. Compare it with every active dnsmasq placement's managed-file observation.
4. Emit the four explicit service-config codes and structured evidence.
5. Classify observation-missing as observation and missing/unreadable/mismatch as automatic
   service-profile work.
6. Let the profile action continue to resolve that work to `dnsmasq_config`; do not create a
   second dnsmasq-only planner.
7. Mark dnsmasq actions as requiring post-actuation observation.
8. Ensure multiple dnsmasq targets receive and verify the same desired digest independently.

Tests:

- running service + matching digest is converged;
- running service + changed DesiredEndpoint is `service_config_mismatch`;
- running service + manually changed file digest is also mismatch;
- missing observation first plans observation, not blind deployment;
- explicit missing/unreadable file plans dnsmasq deployment;
- stopped service and matching digest still plans service recovery;
- deployment followed by v2 observation converges within three rounds;
- unchanged desired/actual content never repeats the action;
- host scope includes the service-content drift for its placement;
- two targets allow one converged and one mismatched result; and
- profile metadata unavailable cannot report the service converged.

Step 5 exit criteria:

- Changing a generated DNS/DHCP directive necessarily changes `nctl drift`.
- `nctl reconcile --yes` deploys it and proves the observed digest before declaring convergence.

## Step 6 — documentation, coordinated rollout, and verification

### Documentation

Update:

- root `README.md`;
- `nctl/README.md`;
- `nodeutils/README.md` and example probe config;
- `nauto/README.md`;
- `ansible_agdev/README.md`, `README_ADMIN.md`, and `README_DEV.md`;
- `devdocs/small/fix_sshkey2/report_verification.md`; and
- new step reports plus `devdocs/small/fix_sshkey3/report_verification.md`.

Preserve the `fix_sshkey2` facts and operation IDs. Add a superseding notice stating that its
“safe fixture” blocker revealed a real dnsmasq content-convergence gap, now addressed here. Do not
rewrite the historical attempt as a successful verification.

Document explicitly:

- process health and managed-content convergence are different;
- only the nctl-owned records/ranges file is content-observed in this phase;
- direct `nctl apply dnsmasq --yes` remains available, but routine desired-state changes flow
  through reconcile;
- actual digest comes from nodeutils, not from a controller acknowledgment; and
- SSH preflight fingerprints are public metadata while raw keys remain excluded.

### Coordinated rollout

Because the live observation playbook clones nodeutils from GitHub, the order matters:

1. Implement and test nodeutils v2 locally; commit it and ask the user to push.
2. Update and test nauto's v2 ingest contract; commit/push and deploy the updated Job through the
   established GitHub-based local Nautobot flow.
3. Update ansible_agdev reconciliation metadata/playbook contract and commit it.
4. Update nctl readers, drift, executor, and schemas against those exact versions.
5. Update root submodule pointers and devdocs.
6. Run one v2 observation/ingest on `agdnsmasq` before evaluating content drift.

Do not temporarily accept both nodeutils schemas. Coordinate the commits and deployment in one
maintenance session.

### Automated verification

Run focused tests per step, then:

```text
uv run --project nctl pytest -q nctl/tests
uv run --project nodeutils pytest -q nodeutils/tests
```

Run the nauto and ansible_agdev repository-standard test/syntax commands documented in those
repositories, including:

```text
ansible-playbook --syntax-check ansible_agdev/playbooks/dnsmasq/deploy_dnsmasq_records.yml
ansible-playbook --syntax-check ansible_agdev/playbooks/nautobot/run_nodeutils_collect.yml
```

Run available project lint/type checks. If a tool is absent from project dependencies, record it
as not run; do not report it as passing.

Add a cross-repository golden fixture containing exact deterministic conf bytes and SHA-256.
Both nctl and nodeutils tests must independently reproduce the same digest.

### Live verification A — SSH policy closure

Use disposable inventories/configs and the existing safe non-default-port tunnel fixture:

1. Reconfirm that a bare alias succeeds on the non-default port.
2. Confirm an inventory containing exact common args plus hostile `ansible_ssh_args` is rejected
   before keyscan/Ansible.
3. Confirm string port `"12222"` is rejected and integer `12222` scans the tunnel.
4. Confirm empty/corrupt managed stores return structured errors.
5. Confirm no disposable test writes the real managed store.

### Live verification B — safe dnsmasq content convergence

Target: real `agdnsmasq`, using no service interruption and no fabricated observation.

1. Confirm nodeutils v2 is deployed and a fresh observation records the current
   `nintent-records.conf` digest.
2. Confirm `nctl drift` shows the existing dnsmasq placement converged on both process and
   content.
3. Through the normal nintent REST interface, create one reversible test DesiredEndpoint in the
   existing authorized static range, with `generate_dnsmasq=true`.
4. Run `nctl reconcile agdnsmasq` and require a `service_config_mismatch` diff plus a planned
   `dnsmasq_config` action. If either is absent, stop without apply.
5. Run `nctl reconcile agdnsmasq --yes`.
6. From its artifacts, prove:
   - production inventory generation and ID;
   - non-empty `production_route` SSH preflight;
   - exact route, port, alias, and matching public fingerprints;
   - dnsmasq deployment action and Ansible recap;
   - post-action nodeutils v2 collect/ingest;
   - desired and observed content digests equal; and
   - scoped convergence with no one-off IP known_hosts entry.
7. Resolve the test DNS name through the deployed dnsmasq server and verify the expected address.
8. Delete the test DesiredEndpoint through the normal interface.
9. Require reverse `service_config_mismatch`, reconcile again, verify DNS removal, and confirm
   the original digest/state is restored.

### Negative live boundaries

With the real service left untouched:

- run the same real SSH-requiring plan against a disposable empty managed store and confirm zero
  mutating actions before `ssh_host_key_unenrolled`;
- use a disposable mismatched key/route fixture and confirm production service actuation does not
  start;
- cause a disposable post-regeneration failure after a fake successful ledger action and confirm
  the partial round/progress/final-drift evidence is retained; and
- confirm raw SSH blobs and dnsmasq contents are absent from JSON/event evidence.

Record commands, commits, deployed submodule versions, operation IDs, generation IDs, routes,
ports, public fingerprints, desired/actual content digests, Ansible recap, DNS query results, and
cleanup results.

## Commit boundaries

Recommended sequence:

1. `nctl: close inventory SSH contract and structured errors`
2. `nctl: generation-exact SSH targets and durable round evidence`
3. `nctl: deterministic dnsmasq artifact and digest`
4. `nodeutils: v2 managed-file digest observation`
5. `nauto: ingest nodeutils v2 managed-file observations`
6. `ansible_agdev: one managed dnsmasq path for deploy and observation`
7. `nctl: nodeutils v2 reader and dnsmasq content drift`
8. `docs: coordinated rollout and automated verification`
9. `docs: live fix_sshkey3 verification evidence`

Commit each submodule independently before updating root pointers. Per the local environment
policy, do not push automatically; ask the user to push the required submodule commits.

## Rollback

- Roll back code by submodule commit; do not rewrite the managed SSH store.
- The first v5 dnsmasq deployment removes volatile comments but preserves the generated
  directives. Rolling code back does not require restoring those comments.
- If rollout stops after nodeutils v2 deployment but before nctl drift support, the nested digest
  remains harmless actual metadata in the existing JSON custom field.
- Do not restore nodeutils v1 compatibility in runtime code. Complete the coordinated version
  rollout or roll every component back to its prior commit.
- Reverse any live test DesiredEndpoint through the normal REST interface and reconcile its
  removal before declaring cleanup complete.

## Final exit criteria

- Equal desired dnsmasq inputs produce byte-identical managed conf and one stable SHA-256 digest.
- Nodeutils v2 observes the real deployed records file and Nautobot/nctl preserve that digest
  unchanged without storing file contents.
- A desired DNS/DHCP content change or a manual target-file change produces explicit service
  content drift even while dnsmasq remains running.
- `nctl reconcile --yes` deploys content drift, observes again, and reaches digest equality within
  the bounded round limit.
- Production SSH preflight gets alias, route, and port only from a target included in the installed
  generation.
- Hostile inventory SSH overrides and invalid port types are rejected before network or Ansible
  execution.
- Unenrolled, mismatch, unreachable, invalid inventory, store I/O, and probe failures are distinct
  structured errors.
- Every started round and every successful mutation remains visible after a later failure.
- Successful production scans record phase, round, generation, route, port, and public
  fingerprints without raw blobs.
- The full test suites and repository-standard syntax checks pass.
- The reversible live DesiredEndpoint addition and removal both trigger real
  `dnsmasq_config` actions, preserve strict SSH trust, pass DNS queries, and return the cluster to
  its original converged state.
