# Report — Step 3: bind dnsmasq destination and host scope to reconciliation metadata

Date: 2026-07-22
Scope: `nctl` and `ansible_agdev`
Status: **complete** (nctl full suite: 947 pass; both Ansible syntax checks pass)

## Goal (plan.md Step 3 / outstanding problems #3 and #4)

Close two duplications:

- the dnsmasq deployed destination was declared once in
  `deployment_profile_reconciliation.dnsmasq.action.managed_files.records.path`
  (already the single source for nodeutils probe hints and drift evidence,
  since fix_sshkey3 Step 4) but `deploy_dnsmasq_records.yml` independently
  defaulted the same path, and `build_dnsmasq_apply` never read the
  metadata at all — a shell-like `-e dnsmasq_records_src=...` was the only
  extra var it passed;
- a scoped dnsmasq reconcile action planned/scanned/preflighted a specific
  host set (`action.parameters["host_slugs"]`) but `build_dnsmasq_apply`
  always actuated and re-observed the complete `dnsmasq_server` inventory
  group, so a host-scoped reconcile could mutate a sibling host it never
  scanned.

Also closed outstanding problem #4 (observed path is part of content
evidence): a digest match alone no longer proves convergence if the stored
observation names a different managed-file path.

## Changes

### 1. `nctl_core/reconcile/profiles.py` — the one destination resolver

- Added `resolve_dnsmasq_records_spec(entries) -> ManagedFileSpec`: requires
  exactly one `deployment_profile_reconciliation` entry with
  `action.kind == "dnsmasq_config"`, and that entry's `managed_files` to be
  exactly `{"records": ManagedFileSpec(...)}`. Absolute path and
  `digest == "sha256"` are already enforced by `ManagedFileSpec` itself at
  load time. Missing/duplicate/misshaped is `ProfileReconciliationError`,
  never a fallback default.

### 2. `nctl_core/dnsmasq_apply.py`

- `build_dnsmasq_apply` gained `host_limit: list[str] | None = None`. When
  given: rejected if empty (`dnsmasq_host_limit_empty`), internally
  duplicated (`dnsmasq_host_limit_duplicated`), or not a subset of the
  resolved `dnsmasq_server` inventory group
  (`dnsmasq_host_limit_not_in_group`) — every rejection happens before any
  keyscan or Ansible process. When accepted, it replaces `target_hosts`
  entirely, so `DnsmasqApplyData.target_hosts`, the SSH trust-contract
  validation, `check_inventory_ssh_preflight`, and both playbook's
  `--limit` all describe the identical set. Direct `nctl apply dnsmasq`
  never passes it, so it keeps defaulting to the whole group with no
  `--limit`.
- After the (possibly narrowed) `target_hosts` is resolved, loads
  `load_deployment_profiles` + `load_profile_reconciliation` and calls
  `resolve_dnsmasq_records_spec`; any failure returns
  `dnsmasq_records_metadata_invalid` before the SSH trust contract/keyscan
  or either Ansible process.
- The deploy-playbook invocation now passes one JSON `-e` payload —
  `{"dnsmasq_records_src": ..., "dnsmasq_records_config_file": ...}` — via
  `json.dumps` as a single argv element, replacing the old
  `-e dnsmasq_records_src=<path>` shell-like concatenation. The destination
  value comes only from `resolve_dnsmasq_records_spec`, never a literal.

### 3. `ansible_agdev/playbooks/dnsmasq/deploy_dnsmasq_records.yml`

- Removed the `dnsmasq_config_dir`/`dnsmasq_records_config_file` default
  vars.
- Added a `pre_tasks` assertion (mirroring the existing
  `dnsmasq_records_src` one) requiring `dnsmasq_records_config_file` to be
  defined, non-empty, and absolute — a caller that supplies no destination
  now fails closed instead of silently reusing the old default.
- The "ensure configuration directory exists" task now derives the
  directory from `dnsmasq_records_config_file | dirname` instead of the
  removed `dnsmasq_config_dir` var.
- `ansible-playbook --syntax-check` passes (from `ansible_agdev`, per
  fix_sshkey3's known repository-root `roles/` caveat).

### 4. `nctl_core/reconcile/executor.py`

- `_run_playbook_action`'s `dnsmasq_config` branch now passes
  `host_limit=sorted(action.parameters.get("host_slugs") or [])` to
  `build_dnsmasq_apply` — the same `action.parameters["host_slugs"]`
  source `action_host_slugs()` (production SSH preflight, post-actuation
  observation host list) already uses, so all four now name the same
  planned set for a reconcile action.

### 5. Observed path is part of content evidence

- `nctl_core.drift.service_placement.ContentSpec` gained `expected_path:
  str` and `digest_algo: str = "sha256"`.
- `_evaluate_content_drift`: a `present`/`missing`/`unreadable`/`too_large`
  result under the expected managed-file key whose reported `path` differs
  from `content_spec.expected_path` now short-circuits to the new
  `service_config_observation_mismatch` gap — classified `OBSERVATION` in
  `classify.py` (a fresh probe under the current hint runs before any
  `service_config_*` conclusion, never a blind deploy) — before any
  status/digest-specific code is considered. `report` now always includes
  `expected_content_path` and (when a file result exists)
  `observed_content_path`.
- `nctl_core.drift.evaluation_snapshot._content_spec_by_service_id` now
  populates the new fields from the same `ManagedFileSpec` it already reads
  (`entry.action.managed_files[managed_file_key]`).
- No `nodeutils` change was needed: `nodeutils_collect.py`'s
  `observe_managed_file` already stores `"path"` in every managed-file
  result regardless of status (present/missing/unreadable/too_large), so
  the "stored observation names a different path" comparison was already
  observable, just not yet checked.
- Digest **algorithm** comparison is not gated in code: nodeutils only ever
  computes SHA-256 and reports no separate algorithm field, so there is
  currently no observed value to disagree with `content_spec.digest_algo`.
  The field is carried through evidence for forward compatibility (per the
  plan's "digest algorithm" evidence requirement) but the only real check
  today is path equality — noted here rather than adding a check against
  data that does not exist.

## Test changes

- `tests/test_dnsmasq_apply.py`: `_config()` now writes a valid
  `vars/deployment_profiles.yml` with a `dnsmasq_config` profile/
  reconciliation entry by default (`_write_deployment_profiles` helper,
  parameterized on `records_path`), since this metadata is now a required
  precondition for every apply. 8 new tests: missing metadata blocks
  before any `ansible-playbook` call; changing the metadata path changes
  the deploy playbook's JSON extra-vars destination with no source-file
  edit; empty/duplicated/out-of-group `host_limit` are each rejected
  before `ansible-playbook`; a host-scoped call targets, scans (via
  `--limit`), and deploys only the requested host; a direct call
  (`host_limit=None`) still targets the full group with no `--limit`.
- `tests/test_service_placement.py`: `CONTENT_SPEC` now carries
  `expected_path`; 4 new tests — a stale observed path with a matching
  digest is `service_config_observation_mismatch`, not converged; the same
  holds when the stale-path result's status is `missing`; a matching path
  with a matching digest is still `satisfied`; a matching path with a
  different digest is still ordinary `service_config_mismatch` (proves the
  path check is additive, not a replacement for the digest check).
- `tests/test_reconcile_profiles.py`: 3 new tests for
  `resolve_dnsmasq_records_spec` — returns the one spec; missing profile is
  an error; more than one `dnsmasq_config` profile is an error.
- `tests/test_reconcile_classify.py`'s existing exhaustiveness scan picked
  up `service_config_observation_mismatch` automatically (it scans literal
  `"code": "..."` strings in `service_placement.py`); no test file edit was
  needed there, only the `classify.py` table entry.
- `tests/test_reconcile_executor.py`: the one existing
  `build_dnsmasq_apply` stub gained a `host_limit=None` parameter to match
  the new call signature.

## Verification

```
$ uv run pytest -q tests/test_dnsmasq_apply.py
35 passed in 0.42s

$ uv run pytest -q tests/test_service_placement.py
19 passed in 0.02s

$ uv run pytest -q tests/test_reconcile_profiles.py tests/test_reconcile_classify.py
... passed

$ uv run pytest -q tests
947 passed, 1 warning in 5.59s   # full suite (Step 2 baseline 933 + 14 new)

$ (cd ansible_agdev && ansible-playbook --syntax-check playbooks/dnsmasq/deploy_dnsmasq_records.yml)
playbook: playbooks/dnsmasq/deploy_dnsmasq_records.yml

$ (cd ansible_agdev && ansible-playbook --syntax-check playbooks/nautobot/run_nodeutils_collect.yml)
playbook: playbooks/nautobot/run_nodeutils_collect.yml

$ grep -rn nintent-records.conf ansible_agdev/playbooks    # empty
$ grep -rn nintent-records.conf ansible_agdev/vars
ansible_agdev/vars/deployment_profiles.yml:154:          path: /etc/dnsmasq.d/nintent-records.conf
```

Lint/type check: still none configured (unchanged from every prior step).

## Step 3 exit criteria

- [x] `rg nintent-records.conf` finds the operational destination only in
  the reconciliation metadata (and fixtures/docs) — confirmed above; the
  playbook now has no literal or default of its own.
- [x] One planned host set is visible at every actuation and evidence
  boundary — `action.parameters["host_slugs"]` now flows through
  production SSH preflight, `build_dnsmasq_apply`'s inventory
  preflight/Ansible `--limit`, and post-actuation observation identically
  for a reconcile-driven dnsmasq action; direct `nctl apply dnsmasq` is
  unaffected and still targets the whole group.
- [x] Drift rejects a stale/wrong observed-path identity even when the
  digest happens to match (`service_config_observation_mismatch`).

## Handoff to Step 4 / Step 7

- `ansible_agdev/README.md` (the `-e dnsmasq_records_src=...` example and
  the playbook description) and `README_DEV.md` still describe the
  pre-Step-3 single-var invocation; updating them is explicitly Step 7's
  scope (`Update: ... ansible_agdev/README.md, README_ADMIN.md,
  README_DEV.md`), left untouched here to keep this step's diff to the
  behavioral contract.
- Step 4 (nodeutils lockfile/dev-dependency reproducibility) is unaffected
  by this step and can proceed independently.
