# Phase 4 Report — Step 2 (collect → controller report cache → Nautobot ingest)

Date: 2026-07-16. Implements [p4/plan.md](plan.md) Step 2. This is the second suggested commit
boundary. It establishes the reusable observation path across nctl, Ansible, nodeutils, and nauto;
it does not yet expose `nctl reconcile` or delete the previous combined orchestration playbook.

## What was built

### nctl observation pipeline

New `nctl/src/nctl_core/observation.py` owns the library-level observation sequence:

1. render a fresh deterministic bootstrap inventory from the desired snapshot and require every
   requested slug to be bootstrap-eligible;
2. render a private per-host `probe-config/<host>.yaml` from active desired service placements;
3. run `run_nodeutils_collect.yml` with an explicit host `--limit` and no shell interpolation;
4. retrieve reports with `ansible.builtin.slurp --tree` into the private operation directory;
5. strictly decode base64, enforce the configured byte ceiling, require UTF-8 and
   `nodeutils.inventory.v1`, reject stale reports, cross-check hostname/FQDN against the selected
   inventory host, and reject duplicate canonical identities;
6. retain validated operation copies and atomically replace
   `<inventory.dumps_dir>/<host>.json` with mode `0600`;
7. serialize only validated/cached reports into `report_batch`, execute and poll the exact
   `Ingest Nodeutils Inventory` Job, require its exact structured artifact, cross-check one result
   per submitted source, and refetch actual state through GraphQL in the production path.

The result is typed per host. A failed/unreachable/malformed host does not prevent independent
valid hosts from reaching the ingest Job, but it keeps the overall observation result false.
Likewise, a terminally successful Job whose artifact says `skipped` is an explicit host failure.
Raw report/base64 content is confined to private artifacts and the Job request; events contain
host/status summaries only.

`OperationArtifacts` gained confined private-directory creation. Its atomic writer is also reused
for the controller cache, including same-directory temporary creation, flush/fsync, replacement,
permission hardening, cleanup on failure, and preservation of the previous cache file when replace
fails. `dumps.py` gained an in-memory `parse_dump_text()` entry point so unvalidated content never
has to be installed as a dump first.

Strict `[reconcile]` settings now also include:

- `max_report_bytes = 2097152`;
- `max_report_age_hours = 72`;
- `ingest_policy_file = "seed/nodeutils_ingest.yaml"`.

### Structured nauto ingest outcome

`nauto/jobs/ingest_nodeutils_inventory.py` now accumulates one result for every submitted source.
`ingest_report()` returns `created`, `updated`, or `unchanged` together with device name, changed
fields, and report hash; validation/policy errors become `skipped` rows with sanitized messages.

The Job writes `nodeutils-ingest-summary.json` after its database transaction using the new pure
schema builder in `jobs/nodeutils_ingest_summary.py`:

- schema: `nodeutils.ingest.summary.v1`;
- explicit batch `dry_run` state;
- counts for `created`, `updated`, `unchanged`, and `skipped`;
- one source row per input.

Writing the FileProxy after the transaction is intentional: a dry-run database rollback no longer
rolls back the evidence artifact. Existing ingest policy and transactional write behavior remain
unchanged.

### Host-side probe configuration and recognition

`run_nodeutils_collect.yml` accepts an optional controller probe-config directory, copies the
selected host file to `/var/lib/nodeutils/nctl-probe-config.yaml` with mode `0600`, and adds
`--config` to collection. It still owns only host clone/update/dependency sync/collection and has
no Nautobot token, URL, Job, or REST task.

nodeutils Docker and systemd recognition now includes all `service_probe_hints` keys. Matching is
longest-name-first, and an explicit systemd unit mapping takes precedence, avoiding the ambiguous
`prometheus` versus `prometheus-node-exporter` prefix. The report schema remains
`nodeutils.inventory.v1`.

Step 2's plan text mentions deployment-profile metadata as the eventual source of probe details.
That metadata contract is assigned to Step 5 and does not exist yet. At this boundary nctl derives
the non-secret keys from authoritative active `DesiredServicePlacement` + `DesiredService.name`;
Step 5 can add profile-specific unit/endpoint overrides without changing this transport.

## Tests and verification

New nctl observation tests cover:

- deterministic active-placement probe hints;
- two-host collection, private operation copy, atomic cache update, and batch serialization;
- partial retrieval with the available host still ingested;
- wrong identity and stale report rejection before cache installation;
- duplicate canonical identities;
- completed Job plus `skipped` outcome remaining a failure;
- external cache replacement and preservation after a simulated atomic-replace failure.

nodeutils fixtures cover a configured Docker dnsmasq service and explicit Nomad/node-exporter
systemd units. nauto's pure summary tests pin all outcome counts, dry-run state, row preservation,
and rejection of an unknown outcome.

Verification results:

- `cd nctl && uv run pytest -q` — **316 passed** after the final Step 2 tests;
- `cd nodeutils && uv run --with pytest pytest -q` — **9 passed**;
- `cd nauto && uv run --with pyyaml python -m unittest discover -s tests -v` — **27 passed**;
- `ansible-playbook --syntax-check` for `run_nodeutils_collect.yml` — passed;
- Python compilation for all changed Python modules — passed;
- `git diff --check` in nctl, ansible_agdev, nodeutils, and nauto — passed.

The first nodeutils run exposed a real prefix-order defect (`prometheus` won before the configured
`prometheus-node-exporter`); matching precedence was corrected and the suite then passed. The first
nauto invocation lacked PyYAML in the bare host interpreter, so verification was repeated with an
ephemeral `pyyaml` dependency rather than modifying the project environment.

## Live boundary and deliberate non-work

No live host collection or write-mode ingest was executed at this boundary. The nauto Job source
must first be committed and then synchronized/reloaded in Nautobot before the new summary artifact
exists server-side; the local environment memo also requires that sequence. Running the old live
Job before that sync could only prove the obsolete log-only behavior. Step 1 already proved the
generic Job launch/poll/FileProxy transport against local Nautobot.

Still deferred:

- no `nctl reconcile` CLI, planner, or bounded execution loop;
- no Step 3 service-drift evaluator port or actual-facts schema extension;
- no Step 4 `converging` event-semantics change;
- no Step 5 deployment-profile action/probe metadata;
- no deletion of `collect_nodeutils_and_ingest_nautobot.yml` before cutover;
- no mutation of the ignored local `nctl.toml`; its controller dump directory must be reviewed
  before live collection;
- no commit, push, Nautobot repository sync/reload, or service restart was performed.

## Files changed in this boundary

nctl:

- added `src/nctl_core/observation.py` and `tests/test_observation.py`;
- updated `artifacts.py`, `config.py`, `dumps.py`, `example.nctl.toml`, and related tests.

ansible_agdev:

- updated `playbooks/nautobot/run_nodeutils_collect.yml`.

nodeutils:

- updated `nodeutils_collect.py` and `tests/test_inventory_report.py`.

nauto:

- added `jobs/nodeutils_ingest_summary.py` and `tests/test_nodeutils_ingest_summary.py`;
- updated `jobs/ingest_nodeutils_inventory.py`.

Parent repository:

- added this report. Step 1 changes/report remain uncommitted in the shared worktree, so a real
  repository commit sequence should preserve the submodule boundaries and include both completed
  reports as appropriate.
