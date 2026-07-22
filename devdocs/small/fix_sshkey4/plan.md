# fix_sshkey4 Implementation Plan: strict SSH-store failures, one dnsmasq target contract, and complete verification

Date: 2026-07-22

## Goal

Close the remaining correctness and verification gaps found after `fix_sshkey3` without weakening
the SSH trust model or disturbing the now-working dnsmasq content-convergence path.

The completed result must provide all of the following:

1. Every malformed, unreadable, or invalid nctl-managed known_hosts store is handled as a
   structured `ssh_store_read_failed` result. No parser path may silently skip corruption, and no
   observation-time store failure may escape as a traceback or erase an already-started round.
2. The dnsmasq managed records destination is owned by one validated reconciliation metadata
   value. The deploy playbook, nodeutils probe hint, drift evidence, and action scope must all use
   that exact contract rather than independent path literals or host lists.
3. The nodeutils project metadata and `uv.lock` are synchronized, and the documented standard test
   command runs without modifying the worktree.
4. The automated multi-round convergence test, current non-default-port SSH closure, negative
   boundaries, and reproducible Ansible syntax checks omitted or substituted in `fix_sshkey3` are
   actually executed and recorded.

This is a completion initiative for `fix_sshkey3`, not a redesign of enrollment, dnsmasq rendering,
or nodeutils ingestion.

## Verified baseline

The following behavior is already working and must remain intact:

- the current desired and nodeutils-observed SHA-256 for
  `/etc/dnsmasq.d/nintent-records.conf` are both
  `118dd7e667439774fc6b0dd1acd49513be4ebb8b6f15967e6edacd4e708445b3`;
- the real `dnsmasq` service target is currently `converged`;
- the reversible `fix_sshkey3` DesiredEndpoint addition and removal both produced real
  `service_config_mismatch` and `dnsmasq_config` work;
- the add and removal operations re-observed the deployed file and restored the original digest;
- the production SSH preflight recorded one exact generation, route, port, alias, and matching
  public fingerprints;
- the current suites pass: nctl 914 tests, nodeutils 20 tests, and nauto 14 tests; and
- the root and all submodule worktrees are clean before this initiative begins.

The cluster is not globally clean for unrelated reasons: `aghub` and `agstudio` are currently
`unknown`, and `agdnsmasq` retains the pre-existing `missing_actual_ip_address`/repeated-IPAM
behavior. Those findings must remain visible and must not be misrepresented as failures or
successes of the dnsmasq content work.

## Outstanding problems

### 1. Managed known_hosts parse failures are silently ignored

`nctl_core.ssh_enroll.entries_for_lookup_name` catches `SshTrustError` from
`parse_known_hosts_line` and continues. A syntactically malformed managed-store line therefore
becomes an empty lookup result, often reported as `unenrolled`, instead of the promised
`ssh_store_read_failed` result.

This is fail-closed for actuation, but it is not operationally correct: corruption and a genuinely
missing enrollment have different remediation and must not share one error.

### 2. Observation can still leak a store-read exception after a round starts

`run_observation` performs its own defense-in-depth `check_ssh_enrollment`. That call can raise
`SshStoreReadError`, but `_run_observation_action` catches only `ValueError`. If the managed store
becomes unreadable or invalid after the round-start gate, the exception can escape the action
boundary. In a post-actuation observation this can occur after a successful dnsmasq deployment,
defeating `RoundOutcome`'s evidence-retention guarantee.

### 3. The dnsmasq destination path is duplicated

`deployment_profile_reconciliation.dnsmasq.action.managed_files.records.path` declares the
observation path, while `deploy_dnsmasq_records.yml` independently constructs the same destination
from `/etc/dnsmasq.d` and `nintent-records.conf`. `build_dnsmasq_apply` passes only the controller
source path, not the validated destination.

The current literals happen to match. If either side changes alone, nctl can repeatedly deploy one
file while nodeutils observes another.

### 4. A scoped dnsmasq action does not own one exact host set end to end

The planner and production SSH preflight use `action.parameters["host_slugs"]`, but
`build_dnsmasq_apply` targets every member of `dnsmasq_server`. Post-actuation observation returns
to the planned host list. With multiple dnsmasq placements, a host-scoped reconcile could therefore
actuate more hosts than it scanned at the production-generation gate and re-observe only one of
them.

The direct `nctl apply dnsmasq` command may continue to default to the complete inventory group,
but reconcile must pass and enforce its exact planned host set.

### 5. The nodeutils lockfile is stale

`nodeutils/pyproject.toml` declares project version `0.2.0`, while the editable nodeutils package in
`nodeutils/uv.lock` still says `0.1.0`. Running the reported nodeutils test command updates the
tracked lockfile, so the verification is not reproducible from a clean checkout.

The nodeutils dev dependency group also omits pytest even though the project plan documents
`uv run --project nodeutils pytest ...` as the standard test command.

### 6. Some required verification was substituted rather than completed

`fix_sshkey3` deliberately omitted a full mocked executor test for:

```text
content mismatch -> dnsmasq deploy -> v2 observation/ingest -> matching digest -> no repeated action
```

Its final report also referred to the old `fix_sshkey2` non-default-port proof and unit tests rather
than rerunning all `fix_sshkey3` Live verification A and negative-boundary steps. Finally, the
Ansible commands recorded as successful are not reproducible from the repository root because the
second playbook's local `roles/` path is not found from that working directory; both syntax checks
do pass when run from `ansible_agdev`.

## Corrected system contracts

### 1. The nctl-managed SSH store has one strict reader

Introduce one store-loading boundary, for example:

```text
ManagedSshStore
  raw_lines
  entries
  obsolete_entries

load_managed_ssh_store(path) -> ManagedSshStore
```

The exact name is implementation-defined, but the behavior is not:

- an absent store is a valid empty store and produces `unenrolled` for a requested host;
- blank lines and comments are allowed;
- every other line must be a valid ordinary supported host-key line;
- marker entries, malformed fields, unknown key types, invalid base64, hashed names, and other
  content that nctl itself never writes are store corruption;
- every current managed entry must use one bare nctl alias lookup name, never an endpoint name or
  IP;
- a syntactically valid historical `[nctl-node-UUID]:port` entry is recognized separately as an
  `obsolete_entry`, never used to authorize a connection, and may be removed only by the existing
  verified enrollment/replacement flow;
- parse, decoding, stat, permission, and read failures become `SshStoreReadError` with path and
  safe line-number context but without key blobs; and
- callers query the already-validated entry set. They do not catch and skip per-line parser
  failures independently.

Enrollment replacement still needs `raw_lines` to preserve comments and unrelated valid nctl
aliases. It must validate the whole store before computing or writing the replacement. Atomic
private writes and the dedicated SSH lock remain unchanged.

Do not make a malformed store self-healing. The operator must repair it. The only migration
exception is the already-supported, syntactically valid `[alias]:port` residue: a verified normal
enrollment may remove it while writing the current bare-alias entry.

### 2. Every store failure is structured at every public operation boundary

Audit all calls to the strict reader, including indirect calls through `run_observation`.

Expected behavior by boundary:

- `nctl ssh enroll`: `ssh_store_read_failed`, no store write;
- `nctl apply dnsmasq`: `ssh_store_read_failed`, no Ansible process;
- reconcile plan/pre-round gate: `ssh_store_read_failed`, no round starts;
- bootstrap observation inside a started round: retain the round and completed action results,
  append a failed observation result, terminate with `ssh_store_read_failed`;
- post-actuation observation: retain deployment/preflight evidence, set `progress_made: true`,
  refresh final drift once, and terminate with `ssh_store_read_failed`; and
- post-regeneration production scan: keep the existing `RoundOutcome` behavior.

Use a private action-execution outcome rather than encoding control flow in error-message strings.
For example:

```text
ExecutedAction
  result: ActionResult
  terminal_errors: list[EnvelopeError]
```

The public `ActionResult` and `nctl.reconcile.v2` schema do not need to change if the new type stays
internal. Append `result` before inspecting `terminal_errors`. If a store failure happens after any
successful mutation, use the existing final-drift refresh rule. If that refresh fails, add
`final_drift_unknown` and never reuse the pre-mutation snapshot as final state.

Populate the already-defined public preflight fields consistently while touching these paths:

- enrollment entries use `phase="enrollment"`;
- bootstrap entries keep `phase="bootstrap_route"`;
- production entries keep `phase="production_route"`; and
- inventory-driven dnsmasq apply entries use `phase="inventory_route"` and record route, port,
  managed fingerprints, and offered fingerprints without raw blobs.

No probe or preflight may authorize a new key.

### 3. Reconciliation metadata owns the dnsmasq destination

Add one validated resolver in nctl, built on `load_deployment_profiles` and
`load_profile_reconciliation`, that returns the dnsmasq `records` `ManagedFileSpec` used by:

- nodeutils probe-hint rendering;
- desired/actual drift evidence; and
- `build_dnsmasq_apply` Ansible extra variables.

Require the dnsmasq reconciliation entry to have:

- `action.kind == "dnsmasq_config"`;
- exactly the supported `managed_files.records` entry for this phase;
- an absolute destination path; and
- `digest == "sha256"`.

Remove the destination literal from `deploy_dnsmasq_records.yml`. The playbook must require and
validate `dnsmasq_records_config_file` as an absolute path supplied by nctl. Pass source and
destination together using a structured JSON/YAML extra-vars payload rather than shell-like
`key=value` concatenation:

```text
dnsmasq_records_src
dnsmasq_records_config_file
```

The source remains the operation-scoped rendered artifact. The destination comes only from the
validated reconciliation metadata.

### 4. Observed path is part of content evidence

Extend `ContentSpec` with the expected managed-file path and digest algorithm. A digest match is
not sufficient if the stored observation names a different path.

Add one explicit observation code:

```text
service_config_observation_mismatch
```

Use it when a `present`/`missing`/`unreadable` result exists under the expected managed-file key but
its reported path or digest algorithm does not match the active metadata contract. Classify it as
`OBSERVATION`, not immediate deployment: first collect fresh v2 facts using the current probe hint.
The next drift then becomes one of:

- matching path + matching digest: converged;
- matching path + missing/unreadable file: `dnsmasq_config` work; or
- matching path + different digest: `service_config_mismatch` and `dnsmasq_config` work.

Include expected path, observed path, digest algorithm, desired digest, observed digest, and status
in structured drift evidence. Continue to exclude file contents.

### 5. Reconcile scans, actuates, and observes one exact host set

Add an internal host-limit parameter to `build_dnsmasq_apply`:

- omitted for direct `nctl apply dnsmasq`, meaning all hosts in `dnsmasq_server`;
- explicitly supplied by reconcile from `action.parameters["host_slugs"]`;
- rejected if empty, duplicated after normalization, or not a subset of the effective inventory
  group; and
- applied with Ansible `--limit` to both setup and records-deploy playbooks.

The returned `DnsmasqApplyData.target_hosts`, inventory trust validation, inventory-route keyscan,
production-route preflight, Ansible limit, and post-actuation observation must describe the same
planned set for a reconcile action.

For a cluster-scoped action with two dnsmasq placements, both hosts are scanned, deployed, observed,
and evaluated independently against the same desired digest. For a host-scoped action, no sibling
host is mutated.

### 6. Lock and test commands are reproducible

In `nodeutils`:

- add pytest to the existing `dev` dependency group;
- regenerate `uv.lock` with the repository's installed uv version;
- confirm the editable package version in the lock is `0.2.0`;
- run `uv lock --check`; and
- run tests as `uv run --project nodeutils pytest -q nodeutils/tests` without `--with`.

The test and lint commands must leave `git -C nodeutils status --porcelain` empty.

Record Ansible commands with their real working directory:

```text
(cd ansible_agdev && ansible-playbook --syntax-check playbooks/dnsmasq/deploy_dnsmasq_records.yml)
(cd ansible_agdev && ansible-playbook --syntax-check playbooks/nautobot/run_nodeutils_collect.yml)
```

Do not report the repository-root variants as passing unless `ANSIBLE_ROLES_PATH` or an explicit
config makes them reproducible from a clean shell.

## Schema and compatibility decisions

- Keep `nodeutils.inventory.v2`: the report shape is unchanged.
- Keep dnsmasq export schema `5.0`, render/apply v2, and reconcile v2 unless implementation adds a
  new public field rather than only a new diff code/internal outcome.
- Keep the existing four content-state codes and add only
  `service_config_observation_mismatch` for stale/wrong observation identity.
- Do not restore v1 nodeutils compatibility.
- Do not add controller-side “last applied” state.
- Do not accept both the metadata destination and the playbook default. Absence of the metadata
  contract is a structured global/configuration error.

## Non-goals

- Solving `missing_actual_ip_address`, repeated IPAM, `aghub`, or `agstudio` drift.
- Rotating, automatically enrolling, or synchronizing SSH keys.
- Editing the real managed SSH store during disposable tests.
- General managed-file integrity monitoring beyond the nctl-owned dnsmasq records artifact.
- Changing nodeutils ingestion or redeploying the Nautobot Job when its runtime contract did not
  change.
- Declaring cluster-wide convergence when unrelated targets remain unknown.

## Step 1 — implement a strict managed SSH-store reader

Scope: `nctl`.

Primary files:

- `src/nctl_core/ssh_enroll.py`
- `src/nctl_core/ssh_trust.py` if a reusable validated-line helper is needed
- `src/nctl_core/reconcile/ssh_preflight.py`
- `src/nctl_core/inventory_trust.py`
- related tests

Implementation:

1. Introduce the one strict store loader and remove parser-error suppression from
   `entries_for_lookup_name` or replace that helper with queries over a validated store.
2. Validate the complete store before enrollment decisions and writes.
3. Keep absent-file behavior as an empty store.
4. Reject malformed and unsupported managed-store line forms with safe line-number detail.
5. Update enrollment, bootstrap, production, and inventory preflight callers to use the strict
   reader.
6. Populate `enrollment` and `inventory_route` evidence fields consistently.

Tests:

- absent file becomes `unenrolled`, not `ssh_store_read_failed`;
- invalid UTF-8, unreadable file, malformed field count, unknown key type, invalid base64, marker,
  hashed lookup, and endpoint-keyed name are structured store failures;
- a valid obsolete `[alias]:port` entry is reported as migration residue, never satisfies current
  enrollment, and is removed only after a separately verified enrollment write;
- one malformed unrelated line fails the whole nctl-managed store;
- valid comments plus multiple aliases/key types remain readable;
- a corrupt store prevents enrollment replacement and preserves the original bytes;
- inventory/production scans expose only SHA-256 fingerprints; and
- no Ansible or network probe starts after a store parse failure.

Step 1 exit criteria:

- No managed-store parser catches and skips corruption.
- Missing enrollment and invalid store are distinguishable everywhere.
- Valid existing bare-alias stores remain byte-compatible.

## Step 2 — make observation-time store failures round-safe

Scope: `nctl`.

Primary files:

- `src/nctl_core/observation.py`
- `src/nctl_core/reconcile/executor.py`
- `tests/test_observation.py`
- `tests/test_reconcile_executor.py`

Implementation:

1. Audit the indirect `run_observation -> check_ssh_enrollment` exception path.
2. Add the private action outcome/terminal-error boundary.
3. Append the failed observation result and the current `RoundSummary` before stopping.
4. Preserve every earlier successful bootstrap, inventory-render, service, and preflight record.
5. Refresh final drift after a prior mutation; emit `final_drift_unknown` if refresh fails.
6. Ensure a pre-round store failure still starts no round and reports no progress.

Tests:

- corrupt store before round start: zero rounds, zero mutation, `progress_made=false`;
- corrupt store during bootstrap observation: started round retained with failed observation;
- successful ledger action followed by observation store failure: ledger result retained,
  `progress_made=true`, fresh final drift;
- successful dnsmasq action followed by post-actuation observation store failure: production
  preflight and deployment retained, structured terminal error, fresh final drift;
- final-drift refresh failure adds `final_drift_unknown`; and
- no expected store/probe exception produces a traceback.

Step 2 exit criteria:

- Every started round is represented after every managed-store failure point.
- No successful mutation disappears because observation re-read the store.

## Step 3 — make dnsmasq destination and host scope one contract

Scope: `nctl` and `ansible_agdev`.

Primary files:

- `nctl/src/nctl_core/reconcile/profiles.py`
- `nctl/src/nctl_core/dnsmasq_apply.py`
- `nctl/src/nctl_core/reconcile/executor.py`
- `nctl/src/nctl_core/drift/service_placement.py`
- `nctl/src/nctl_core/drift/evaluation_snapshot.py`
- `nctl/src/nctl_core/reconcile/classify.py`
- `ansible_agdev/vars/deployment_profiles.yml`
- `ansible_agdev/playbooks/dnsmasq/deploy_dnsmasq_records.yml`
- related tests and docs

Implementation:

1. Add the validated dnsmasq managed-file resolver.
2. Remove the playbook destination default/literal and require the nctl-supplied destination.
3. Pass source and destination as structured extra vars.
4. Add reconcile-only exact host limiting while preserving direct-apply all-group behavior.
5. Extend `ContentSpec` and evidence with expected/observed path and algorithm.
6. Add and classify `service_config_observation_mismatch`.
7. Ensure the same exact host set flows through generation preflight, inventory preflight,
   setup/deploy, and post-actuation observation.

Tests:

- changing the metadata path changes both probe hint and Ansible destination with no source edit to
  the playbook;
- missing/invalid/extra dnsmasq managed-file metadata blocks before Ansible;
- observed digest equal but observed path different plans observation, not blind deployment;
- fresh observation at the new path becomes missing, then plans deployment;
- deploy to the new path followed by observation converges;
- direct apply targets the full dnsmasq inventory group;
- host-scoped reconcile targets, scans, deploys, and observes only the requested dnsmasq host;
- cluster scope with two placements handles both hosts and compares one desired digest
  independently;
- an out-of-group host limit is rejected before keyscan/Ansible; and
- command arguments contain no free-form shell interpolation or secrets.

Step 3 exit criteria:

- `rg nintent-records.conf` finds the operational destination only in the reconciliation metadata,
  fixtures, and explanatory docs, not as an independent deploy default.
- One planned host set is visible at every actuation and evidence boundary.

## Step 4 — repair nodeutils project reproducibility

Scope: `nodeutils`.

Primary files:

- `pyproject.toml`
- `uv.lock`
- developer documentation if it names the old command

Implementation:

1. Add pytest to the dev dependency group.
2. Regenerate and check the lockfile.
3. Run tests and ruff from a clean checkout.
4. Confirm neither command rewrites `uv.lock`.

Tests/checks:

```text
uv lock --project nodeutils --check
uv run --project nodeutils pytest -q nodeutils/tests
uv run --project nodeutils ruff check nodeutils
git -C nodeutils status --porcelain
```

Step 4 exit criteria:

- pyproject and lock both identify nodeutils `0.2.0`.
- Standard verification leaves the submodule clean.

## Step 5 — add the missing automated end-to-end coverage

Scope: tests across `nctl`, `nodeutils`, and `ansible_agdev` contracts.

Add one executor-level multi-round test using real drift/planner/classification code and mocked
external boundaries only:

```text
round 0 actual digest = old
  -> service_config_mismatch
  -> exact production SSH preflight
  -> dnsmasq_config succeeds
  -> post-actuation v2 observation/ingest reports desired digest

round 1 actual digest = desired
  -> no service_config_* diff
  -> no repeated dnsmasq_config action
  -> converged for the dnsmasq service scope
```

The test must use the real deterministic renderer and golden fixture, not hand-pick unrelated
digest strings. Assert action host sets, destination path, generation ID, route, port, alias,
fingerprints, post-observation host slugs, progress, and final drift.

Add variants for:

- initial `service_config_observation_missing` requiring observation before deployment;
- stale observed path requiring observation before deployment;
- two hosts where one starts converged and one mismatched;
- content already equal, proving no deploy repeats; and
- post-deploy store failure, proving partial evidence retention.

Run the complete repository checks:

```text
uv run --project nctl pytest -q nctl/tests
uv lock --project nodeutils --check
uv run --project nodeutils pytest -q nodeutils/tests
uv run --project nodeutils ruff check nodeutils
(cd nauto && python3 -m unittest discover -s tests -p 'test_*.py')
(cd nauto && python3 -m py_compile jobs/*.py)
(cd ansible_agdev && ansible-playbook --syntax-check playbooks/dnsmasq/deploy_dnsmasq_records.yml)
(cd ansible_agdev && ansible-playbook --syntax-check playbooks/nautobot/run_nodeutils_collect.yml)
```

Record warnings and unavailable tools accurately. Check every worktree after the commands.

## Step 6 — rerun SSH closure and negative boundaries

Use only disposable config, inventory, known_hosts files, and the established non-default-port
OpenSSH fixture. Do not edit the real managed store.

### Live verification A

1. Start or recreate the safe local non-default-port SSH fixture and record its exact port.
2. Enroll its verified public key under one bare disposable nctl node alias.
3. Prove OpenSSH succeeds with the bare alias at that non-default port.
4. Render/load a disposable inventory through installed `ansible-inventory`.
5. Prove exact common args plus hostile `ansible_ssh_args` is rejected before keyscan or Ansible.
6. Prove every forbidden SSH-policy variable is rejected.
7. Prove string/bool/out-of-range ports are rejected, while the integer fixture port is scanned at
   that exact port.
8. Prove empty store is `unenrolled`; malformed/invalid-UTF-8 store is
   `ssh_store_read_failed`.
9. Record effective `ssh -G` output sufficient to show strict checking, managed file, and alias,
   excluding user secrets.
10. Confirm hashes of the real store before and after are identical.

### Negative round boundaries

1. Run the same real SSH-requiring plan with a disposable empty store and prove zero mutation.
2. Use a disposable mismatched offered key and prove no service Ansible process starts.
3. Inject store corruption after a fake successful ledger action and verify retained round,
   progress, and refreshed final drift.
4. Inject store corruption after fake successful dnsmasq deployment and verify retained production
   preflight/deployment evidence.
5. Confirm JSON/event/artifact evidence has no raw SSH key blob, private-key material, or dnsmasq
   file contents.

These tests may use the real installed OpenSSH and Ansible tools, but must not contact or mutate the
real dnsmasq host except for the separate controlled verification below.

## Step 7 — controlled dnsmasq regression verification and documentation

After automated and disposable SSH gates pass, run one reversible live dnsmasq verification on
`agdnsmasq`.

1. Record the current desired digest, nodeutils-observed digest/path/status, daemon state, and
   unrelated drift findings.
2. Confirm the effective metadata destination passed to Ansible is
   `/etc/dnsmasq.d/nintent-records.conf` and no playbook default supplies it.
3. Create one temporary DesiredEndpoint through the normal nintent REST API in the authorized
   test range.
4. Require a plan containing `service_config_mismatch`, `dnsmasq_config`, the exact target
   `agdnsmasq`, and no sibling targets.
5. Apply and prove:
   - same-generation production SSH preflight;
   - matching managed/offered public fingerprints;
   - exact destination extra variable;
   - Ansible limited to `agdnsmasq`;
   - deployment success and post-actuation observation;
   - matching desired/observed digest and path; and
   - successful DNS answer.
6. Delete the endpoint through the normal API.
7. Require and apply reverse content drift, confirm DNS removal, and restore the original digest.
8. Confirm the test endpoint is absent, the daemon was never deliberately stopped, the real
   managed SSH store is unchanged, and no endpoint/IP known_hosts entry was added.

The overall reconcile envelope may still be `non_converged` because of the existing repeated-IPAM
issue. Report both facts separately: dnsmasq content convergence is the acceptance target; unrelated
node/IPAM findings remain open.

Update:

- `nctl/README.md`;
- `nodeutils/README.md` if the dev command changes;
- `ansible_agdev/README.md`, `README_ADMIN.md`, and `README_DEV.md`;
- `devdocs/small/fix_sshkey3/report_verification.md` with a superseding note, without rewriting its
  historical evidence; and
- new `fix_sshkey4` step reports and final verification report.

Record exact commands with working directories, commit IDs, operation IDs, generation ID, route,
port, aliases, public fingerprints, digests, path, target host set, Ansible recaps, DNS results,
cleanup, and final worktree status.

## Commit and rollout boundaries

Recommended commits:

1. `nctl: strictly validate the managed SSH store`
2. `nctl: retain rounds on observation trust-store failures`
3. `ansible_agdev: require the metadata-owned dnsmasq destination`
4. `nctl: bind dnsmasq destination and host scope to reconciliation metadata`
5. `nodeutils: synchronize project metadata and dev lock`
6. `nctl: add multi-round dnsmasq and trust-failure integration coverage`
7. `docs: record fix_sshkey4 automated and disposable SSH verification`
8. `docs: record reversible fix_sshkey4 live dnsmasq verification`

Commit submodules independently, then update root pointers and reports. Do not push automatically;
ask the user to push any submodule commit needed by a GitHub-cloning or GitHub-installed live path.

No Nautobot Job redeployment is expected because nauto and the nodeutils v2 runtime schema do not
change. If implementation unexpectedly changes either runtime component, stop and revise the
rollout section before live verification.

## Rollback

- Roll back nctl and ansible_agdev together if the destination contract change has been deployed;
  do not leave a caller that supplies no destination with a playbook that requires one.
- The existing deployed dnsmasq records path and bytes do not change during the code rollout.
- The strict SSH reader performs no migration and no automatic writes; rollback does not require
  touching the real managed store.
- The nodeutils lock/dev-dependency change has no collector runtime schema effect.
- Reverse any live test DesiredEndpoint through the normal REST API and reconcile removal before
  declaring rollback or cleanup complete.

## Final exit criteria

- Every invalid managed-store syntax and I/O condition becomes `ssh_store_read_failed`; no parser
  silently skips corruption.
- Missing store/enrollment remains a distinct `ssh_host_key_unenrolled` state.
- A store failure during bootstrap or post-actuation observation retains the started round, every
  completed action, production preflight evidence, progress, and a truthful final drift state.
- The dnsmasq destination path is sourced once from validated reconciliation metadata and passed
  explicitly to both observation and deployment.
- Drift rejects stale/wrong observed path identity even when the digest happens to match.
- Reconcile production scan, inventory scan, Ansible limit, actuation result, and post-observation
  all name the same planned dnsmasq hosts.
- Direct dnsmasq apply still supports the full inventory group safely.
- nodeutils pyproject/lock versions agree, pytest is a dev dependency, and standard verification
  leaves every worktree clean.
- The real multi-round executor integration test proves deploy/observe/converge with no repeated
  dnsmasq action.
- Current Live verification A and all negative boundaries pass using disposable trust state.
- The reversible live dnsmasq addition/removal passes, restores the original digest and DNS state,
  and leaves the real SSH store unchanged.
- Reports distinguish successful dnsmasq content convergence from the unrelated IPAM and unknown
  node findings.
