# Report — Step 4: observe managed-file digest through nodeutils and Nautobot

Date: 2026-07-22
Scope: `nodeutils`, `ansible_agdev`, `nctl`, `nauto` (submodules)
Status: **implemented and locally tested, not yet pushed or deployed**
(nodeutils: 19/19 unittest pass; nauto: 14/14 unittest pass; nctl focused:
79 pass / full suite: 901 pass)

## Goal (plan.md Step 4)

Extend nodeutils with a bounded, binary managed-file digest observation
(status/sha256/size/checked_at, never content), wire the deployed path
through one metadata-owned source (`ansible_agdev`'s
`deployment_profile_reconciliation`) into both the deploy playbook and
nctl-generated nodeutils probe config, and make nauto accept only the new
`nodeutils.inventory.v2` schema. No dual v1/v2 reader anywhere.

**This step deliberately stops short of pushing any commit or redeploying
the nauto Job to the local Nautobot** -- per the plan's own coordinated-
rollout ordering and this session's earlier check-in, that push/deploy
sequence is a separate, explicit action for you to run (or ask me to run)
once these four repos' changes are reviewed together.

## Changes

### 1. `nodeutils/nodeutils_collect.py`
- `SCHEMA_VERSION` bumped `nodeutils.inventory.v1` -> `v2` (coordinated
  breaking change, no dual reader); `COLLECTOR_VERSION` `0.1.0` -> `0.2.0`
  (`pyproject.toml` version matched).
- Added `MAX_MANAGED_FILE_BYTES` (4 MiB) and `observe_managed_file(path_str,
  collected_at)`: bounded binary read, returns `status` (`present`,
  `missing`, `unreadable`, `too_large`) plus `path`/`checked_at` and, only
  when `present`, `sha256`/`size`. Never returns file content.
- Added `managed_files_for_service(service_name, config, collected_at)`:
  reads `service_probe_hints.<name>.managed_files` from the (already
  existing) host-local probe config; a relative or otherwise malformed
  `path` is silently omitted (never probed against the collector's cwd).
- `normalize_observed_services` now attaches `managed_files` to a service's
  `observed_services` entry for every hint that configures them -- creating
  a minimal `source: "probe"` entry when docker/systemd detection alone
  never found the service, so managed-file observation doesn't silently
  depend on process-detection also succeeding.
- `example.self_inventory.yaml`, `README.md`: documented the new
  `service_probe_hints.<name>.managed_files` shape and the v2 report
  example.

### 2. `ansible_agdev/vars/deployment_profiles.yml`
- `deployment_profile_reconciliation.dnsmasq.action` gained `managed_files.
  records.path: /etc/dnsmasq.d/nintent-records.conf` (`digest: sha256`) --
  the one metadata-owned source of the path; `deploy_dnsmasq_records.yml`
  (unchanged) already writes to this exact path at mode `0644`, and no
  playbook change was needed.

### 3. `nctl_core/reconcile/profiles.py`
- Added `ManagedFileSpec` (`path`, `digest: Literal["sha256"] = "sha256"`),
  validated absolute-path-only.
- `ProfileAction` gained `managed_files: dict[str, ManagedFileSpec]`,
  restricted to `kind="dnsmasq_config"` (a `playbook` action declaring
  `managed_files` is rejected at load time -- out of scope for this phase).

### 4. `nctl_core/observation.py`
- `render_probe_hints(snapshot, node_id, profile_reconciliation=None)`:
  when given the validated `deployment_profile_reconciliation` map, an
  active placement's `ProfileAction.managed_files` is copied verbatim into
  its service's probe hint. `run_observation` now loads that metadata
  (`_load_profile_reconciliation_for_probe_hints`, best-effort: an
  unavailable/invalid contract degrades to no managed-file hints for that
  round rather than blocking observation/enrollment -- Step 5's drift
  comparator is where that same unavailability becomes a hard global
  error) and passes it through.

### 5. `nctl_core/dumps.py`
- `EXPECTED_SCHEMA_VERSION` bumped `nodeutils.inventory.v1` -> `v2`. A v1
  report is now rejected with a structured `DumpError`, not accepted.

### 6. `nctl_core/sources/actual.py`
- No code change: `read_actual_facts`'s existing `_observed_services()`
  already stores each service entry as a generic `dict(entry)`, so the new
  nested `managed_files` key passes through GraphQL parsing unchanged
  without any special-casing. Added a regression test proving this
  explicitly (see below) since the plan calls for it as an independent
  guarantee, not an inference from the pass-through code shape.

### 7. `nauto/seed/nodeutils_ingest.yaml`
- `schema_versions` replaced `nodeutils.inventory.v1` with `v2` (not
  appended alongside it).
- No code change in `jobs/ingest_nodeutils_inventory.py`: its
  `custom_fields["observed_services"] = services.get("observed_services")`
  is already a verbatim pass-through of whatever nodeutils reports, so the
  new `managed_files` metadata reaches the Nautobot custom field unchanged
  with zero additional code.

## Test changes

- `nodeutils/tests/test_inventory_report.py`: 10 new tests --
  `observe_managed_file` present/missing/too-large/directory-is-missing;
  `managed_files_for_service` rejects a relative path and a malformed
  (non-mapping) spec, accepts an absolute path; `normalize_observed_services`
  attaches `managed_files` even with no docker/systemd hit (`source:
  "probe"`) and merges it into a systemd-detected entry; no file content
  ever appears in a managed-file observation (checked via
  `json.dumps(entry)`).
- `nctl/tests/test_reconcile_profiles.py`: `test_real_repo_file_validates`
  (the live regression gate against the actual checked-in
  `deployment_profiles.yml`) extended to assert the new `managed_files`
  metadata; 3 new tests -- relative path rejected, digest defaults to
  `sha256`, `managed_files` forbidden on a `kind="playbook"` action.
- `nctl/tests/test_observation.py`: 2 new tests -- `render_probe_hints`
  attaches `managed_files` from `ProfileReconciliation` when the active
  placement's profile declares them; omits them (bare `{}` hint) when the
  profile has none.
- `nctl/tests/test_sources_actual.py`: 1 new test -- a nested
  `observed_services.dnsmasq.managed_files` structure survives
  `read_actual_facts` byte-for-byte (no field renaming/flattening).
- `nctl/tests/test_dumps.py`, `test_sources_snapshot.py`, `test_status.py`,
  `test_sources_observed.py`: schema-string fixtures bumped to
  `nodeutils.inventory.v2`.
- `nauto/tests/test_nodeutils_ingest_batch.py`: schema-string fixtures
  bumped to `v2` (these tests exercise the batch JSON parser only, not
  schema-version acceptance, so this is a consistency fix, not a behavior
  change).

## Verification

```
$ cd nodeutils && python3 -m unittest discover -s tests -v
Ran 19 tests ... OK

$ cd nauto && python3 -m unittest discover -s tests -v
Ran 14 tests ... OK

$ uv run --project nctl pytest -q nctl/tests/test_reconcile_profiles.py nctl/tests/test_observation.py \
    nctl/tests/test_sources_actual.py nctl/tests/test_dumps.py
79 passed

$ uv run --project nctl pytest -q nctl/tests
901 passed, 1 warning in 5.53s
```

`ansible-playbook --syntax-check` on both
`playbooks/dnsmasq/deploy_dnsmasq_records.yml` and
`playbooks/nautobot/run_nodeutils_collect.yml` passed (neither playbook's
tasks changed -- only the sibling `vars/deployment_profiles.yml` metadata
did).

Lint/type check: not run (no ruff/mypy dependency in nctl, consistent with
every prior step; nodeutils/nauto have no configured lint step either).

## Step 4 exit criteria

- [x] A fresh nodeutils observation provides verified actual bytes metadata
  for the deployed records file (`observe_managed_file` -- proven at the
  unit level; not yet exercised against the real `agdnsmasq` host, which is
  Step 6's live verification).
- [x] No new Nautobot model or custom field is required (`observed_services`
  JSON custom field already carries the nested `managed_files` structure
  unchanged).

## What remains before this step is actually live

Per the plan's "Coordinated rollout" section and this session's earlier
check-in, the following are **explicit next actions, not yet taken**:

1. Commit nodeutils locally (done) and **push** it -- your own step per
   `.local/localenv_memo.md`.
2. Update/test/**push** nauto, then **redeploy its Job** through the
   established GitHub-based local Nautobot flow.
3. Push ansible_agdev (already committed locally).
4. Push nctl (already committed locally); the root submodule pointer bump
   below is local-only until then.
5. Run one v2 observation/ingest on `agdnsmasq` (Step 6's Live verification
   B) only after 1-4 are live -- accepting both schemas simultaneously is
   explicitly out of scope, so this must happen in one coordinated
   maintenance window, not incrementally against the currently-running v1
   collector.

Until that rollout happens, the real `agdnsmasq` host is still running the
v1 nodeutils collector and the real Nautobot Job still validates against
`nodeutils.inventory.v1` -- nothing in this step has touched live
infrastructure.

## Handoff to Step 5

- Step 5's drift comparator can now rely on: `dnsmasq_render.
  compute_dnsmasq_render(snapshot).content_sha256` (Step 3) as the desired
  digest, and `ActualFacts.observed_services["dnsmasq"]["managed_files"]
  ["records"]` (this step, once rolled out) as the actual digest/status --
  both already round-trip correctly; Step 5 should not need to touch
  nodeutils/ansible_agdev/nauto again.
- Step 5 must treat an unavailable/invalid `deployment_profile_reconciliation`
  contract (the same one `observation.py` now loads best-effort) as a
  classified global drift error, per the plan's corrected contract item 4
  bullet 1 -- unlike the best-effort probe-hint path here, drift computation
  is not allowed to silently degrade.
