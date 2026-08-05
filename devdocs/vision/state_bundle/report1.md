# state_bundle Step 1 report — `nctl desired export`

Status: **complete** (all stated exit criteria exercised and passed).

## What was built

`nctl desired export` emits the complete current desired state as one
canonical Phase 0 batch document — the exact YAML shape `nctl desired
apply -f` accepts. Default output is the raw YAML document on stdout
(`nctl desired export > snapshot.yaml` just works); `--json` wraps it in the
new `nctl.desired.export.v1` envelope (`document`, per-kind `counts`,
`operation_count`).

Changed files (all in `nctl/` plus docs):

- `nctl/src/nctl_core/desired_export.py` (new) — pure
  snapshot-to-document projection (`export_document`), fidelity policy,
  envelope builder, YAML renderer. The writable contract (10 kinds, identity
  key shapes and member order, per-kind writable field sets, writer kind
  dependency order) is pinned from `nintent/nautobot_intent_catalog/batch.py`.
- `nctl/src/nctl_core/cli/main.py` — thin `desired export` Typer command
  under the existing `desired_app` group.
- `nctl/src/nctl_core/compute/collection.py` — new `READINESS_ISSUE_CODES` +
  `decode_unready_instances()` (see contract-gap note below).
- `nctl/src/nctl_core/sources/desired.py` — `DesiredSnapshot` gains
  `unready_compute_instances`, populated by `fetch_desired_snapshot` from the
  same single GraphQL round trip (no second desired-state query).
- `nctl/README.md` — `### desired export` section, usage lines, and a
  responsibility-map row for `desired_export.py`.
- `README.md` (superproject) — export documented next to the desired-state
  operator workflow, explicitly as a complement to (not replacement of) the
  PostgreSQL dumps in `.local/backups/`.

## Design decisions (per plan)

- Built on `fetch_desired_snapshot`'s existing pinned query/decoding; choice
  fields are therefore already lowercased back to the batch vocabulary.
- One format owner: the export *is* a batch document (`dry_run: true` +
  `operations`), each operation an `upsert` with the writer's exact identity
  key shape (`{slug}`, `{desired_node, name, endpoint_type}`,
  `{consumer_placement: {desired_service, instance_name}, binding_name}`,
  etc.). Key member order matches the writer's identity tuples, which the
  batch decoder checks order-sensitively.
- Every writable field is emitted explicitly (apply is a partial upsert; an
  omitted field would be silently "preserved" and mask an incomplete export).
- Determinism (README_DEV lesson 5): operations stable-sorted by writer kind
  order then identity, fixed YAML key order, free-form JSON values
  (`config`, `expected_spec`, `dnsmasq_options`) recursively key-sorted. Kind
  order equals the writer's dependency order, so the document also applies
  cleanly onto an empty database.
- Fail closed on infidelity, by name: unresolved snapshot references
  (`unresolved_reference`), snapshot model fields the exporter cannot write
  back (`unexportable_field` — a guard that trips when the snapshot models
  grow ahead of this module), and decode-time source issues that dropped or
  normalized row data (`desired_source_issue`) all fail the export; no
  partial document is emitted.

## Contract gap found and fixed (not papered over)

The first live export failed exactly as the plan's fidelity rule demands:
the scratch cluster's only `DesiredComputeInstance` (node `agdnsmasq`) is
excluded from `DesiredSnapshot.compute_instances` by the compute
NIC-readiness policy (`compute_primary_endpoint_missing` — that node has no
conforming primary endpoint), so a snapshot-based export would have silently
lost a fully writable row.

That is a readiness/actuation policy, not a data-integrity problem: the
row's writable fields are complete and valid. Fix: `collection.py` now
exposes `decode_unready_instances()` (re-decoding only rows whose sole issue
is in `READINESS_ISSUE_CODES`), `DesiredSnapshot` carries them as
`unready_compute_instances` (documented as never planning/actuation input),
and the exporter includes them. Readiness exclusions and `duplicate_mac_address`
(which flags rows without altering them) are the only non-fatal source-issue
codes; everything else still fails the export. Planning input
(`compute_instances`) and drift behavior are unchanged.

## Acceptance evidence

Unit/CLI tests (`nctl/tests/test_desired_export.py`,
`test_cli_desired_export.py`, plus a fetch-level case in
`test_sources_desired.py`):

- known fixture snapshot covering all 10 writable kinds → exact expected
  operations (identity shapes, key member order, explicit values, reference
  resolution to slugs/identity dicts, realized-* pks, `None` handling);
- byte-identical YAML across repeated exports and across shuffled input row
  order; YAML round-trips (`safe_load`) to the same document;
- `unresolved_reference`, `desired_source_issue` (fatal case), and
  `unexportable_field` each fail by name; readiness-excluded instances are
  exported and non-fatal; `duplicate_mac_address` is non-fatal;
- CLI: raw YAML by default, envelope with `--json`, exit 1 with no partial
  document on failure;
- readiness exclusion at the fetch layer lands the row in
  `unready_compute_instances` with the issue retained.

Gates run (commands and working directories per README_DEV matrix):

| gate | command | result |
|---|---|---|
| nctl ordinary | `nctl$ uv run pytest -q --durations=20` | **1248 passed** (was 1245 before this step) |
| compute conformance | `root$ uv run --project nctl pytest -q devtests/test_strategy/test_compute_conformance.py` | **1 passed** |

Live round-trip on the scratch Nautobot (the definitive check), evidence
retained under `.local/state_bundle_step1/` (git-ignored):

```
$ uv run --project nctl nctl desired export > .local/state_bundle_step1/export-snapshot.yaml   # exit 0
$ uv run --project nctl nctl desired apply -f .local/state_bundle_step1/export-snapshot.yaml --json
  totals: {'conflict': 0, 'create': 0, 'delete': 0, 'unchanged': 38, 'update': 0}
  errors: []   transaction: {'committed': False, 'status': 'dry_run'}
```

All 38 operations previewed `unchanged` — zero creates/updates/deletes/
conflicts — and per-kind counts were: 5 nodes, 3 ip_ranges, 6 endpoints,
1 compute_platform, 1 compute_instance (the readiness-excluded `agdnsmasq`
row, present as required), 10 services, 7 placements, 3 bindings,
2 workspaces (no operational overrides exist live). A second export was
byte-identical to the first (`cmp` clean). No `--yes` was used anywhere:
this step performed zero desired-state writes.

## Notes for later steps

- The export document is Step 2's `desired.yaml` bundle payload; its
  envelope schema name for the manifest is `nctl.desired.export.v1`.
- `nctl desired export` exits non-zero with named errors if the cluster ever
  develops a fatal source issue; a bundle recipe should treat that as a stop,
  not bundle a partial backup.
