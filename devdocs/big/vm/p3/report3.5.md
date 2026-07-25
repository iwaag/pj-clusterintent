# Step 5 — Add the final nctl desired schema and scoped source issues

Status: `complete` (local implementation and test-suite proof; the running nctl deployment is
coordinated with the live cutover in Step 8, matching commits happen in Step 7).

## 1. `nctl/src/nctl_core/sources/desired.py`

- `DESIRED_QUERY` gained `desired_compute_platforms { id name slug provider_type lifecycle
  control_node { id slug } config_schema_version config realized_cluster { id }
  realized_cluster_source }` and `desired_compute_instances { id desired_node { id slug }
  platform { id slug } instance_kind desired_power_state vcpus memory_mb root_disk_gb
  config_schema_version config realized_vm { id } realized_vm_source }`, matching
  `nintent/nautobot_intent_catalog/models.py`'s `DesiredComputePlatform`/`DesiredComputeInstance`
  field-for-field. `desired_endpoints` gained `mac_address`. `desired_nodes.realized_vm { id }` /
  `realized_vm_source` were removed outright (destructive, matching nintent Step 2's migration;
  no dual-read).
- New pydantic models `DesiredComputePlatform`, `DesiredComputeInstance`, `DesiredSourceIssue`
  (`code, target_kind, target_id, target_slug_or_name, severity, scope, message, evidence,
  blocked_consumers` per plan Section 5.9). `DesiredNode.realized_vm_id`/`realized_vm_source` are
  gone; `DesiredEndpoint.mac_address` is added (canonicalized, `None` on anything malformed).
  `DesiredSnapshot` gained `compute_platforms`, `compute_instances`, `source_issues`.
- A Django-free port of nintent's `compute_contract.py` (provider/lifecycle/kind/power/source
  vocabularies, platform/instance config-key validators, `vcpus`/`memory_mb`/`root_disk_gb`/`vmid`
  bounds, `normalize_mac_address`, `effective_lifecycle`, `effective_value`/
  `effective_single_source_value`, `select_compute_primary_endpoint`,
  `effective_compute_defaults`) lives in this same module — nctl has no runtime dependency on the
  nintent Python package (separate deployable), so the shared contract is reimplemented here
  deliberately kept behaviorally identical, not imported.
- `_build_compute_collections()` is the row-scoped validator required by plan Section 5.9: each
  platform/instance row is parsed independently (`_build_compute_platform`/
  `_build_compute_instance`, wrapped in `try/except (KeyError, TypeError, ValueError)`); a bad row
  becomes a `DesiredSourceIssue` and is excluded from the typed collections, never raised out of
  `fetch_desired_snapshot()`. Checks implemented: unique platform slug (collision voids every
  colliding row, `scope=global`), one instance per node (keeps the first row, flags the rest),
  existing node/platform references, dependency-blocking (an instance referencing an
  already-invalid platform is excluded and the platform's own issue gets that instance's id
  appended to `blocked_consumers`), and — only for an effective `active`/`approved` instance — the
  single-primary-endpoint topology check (`compute_primary_endpoint_missing`/
  `compute_primary_endpoint_ambiguous`). `_validate_endpoint_macs()` re-checks the raw MAC per
  endpoint row to distinguish "malformed" (`invalid_mac_address` issue) from "legitimately absent",
  plus a global `duplicate_mac_address` check across the whole desired-endpoint set. Only a row
  missing its own `id` remains an unhandled `KeyError`, i.e. a normal global fetch failure — matches
  plan's "corruption that makes row identity/scope unknowable remains a global fetch failure."

## 2. Legacy `DesiredNode.realized_vm` removal from every nctl consumer

Grepped every non-comment reference to the deleted field and removed it, rather than repointing it
at the new (differently-scoped) `DesiredComputeInstance.realized_vm`:

- `drift/evaluation.py` / `drift/evaluation_snapshot.py`: `evaluate_node_intent`,
  `_realized_node_objects`, `evaluate_endpoint_intent`, `_interface_candidates_for_endpoint`,
  `_endpoint_ipam_self_observation` all dropped their `realized_vm`/`node_realized_vm` parameter;
  guest-OS realization is Device-only now. This makes `multiple_realized_links` structurally
  unreachable through this path (no VM slot left to feed it) — the constant itself is left in place
  (dead but harmless; not disturbing `reconcile/classify.py`'s manual-review set beyond removing
  the field that actually went away).
- `drift/comparators.py`: `node_existence()` dropped the `realized_vm_missing` branch and
  `vms_by_id` lookup; the `no_realized_object` guard is Device-only.
- `drift/status.py` / `reconcile/classify.py`: `"realized_vm_missing"` removed from
  `UNKNOWN_CODES`/`_MANUAL_REVIEW_CODES` (the code can no longer be produced).
- `reconcile/ledger.py`: `_CANDIDATE_FIELD_BY_OBJECT_TYPE` no longer maps
  `"virtualization.virtualmachine"` to `"realized_vm"` — `execute_link_actual_node` can now only
  PATCH `realized_device`. Linking a VM onto a `DesiredComputeInstance` is a different
  object/endpoint and stays out of scope (Phase 4, per plan Section 5.1's dispatch table).
- `production/adapter.py`: `_realized_state()` dropped the `node.realized_vm_id` branch that used
  to truthfully report VM-only realization as `unsupported_actual_type` — there is nothing left to
  detect since the field doesn't exist.

## 3. Compute rows stay inert in drift/planner/dashboard/reconcile

No new comparator, reconciler, or plan-dispatch code reads `compute_platforms`/`compute_instances`
— dispatch in this codebase is entirely opt-in by registration (`drift/registry.py`'s
`@register(...)`, `reconcile/registry.py`'s `register_reconciler`), so a collection nothing reads
is architecturally inert by construction. `tests/test_vm_p3_compute_stays_inert.py` proves it
concretely: a `SourceSnapshot` with one fully valid platform+instance is run through the real
`compute_drift()` and `build_plan()` (not mocks), and every diff/manual-review/unsupported/action
record is asserted to have neither a `compute_platform`/`compute_instance` target kind nor the
test's platform/instance id.

## 4. Test suite

`uv run pytest -q` (own re-run, not just the implementer's): **1011 passed**, 1 pre-existing
unrelated warning (`starlette`/`httpx` deprecation). Coverage added/changed:

- `test_sources_desired.py`: new compute-platform/instance rows parse into `DesiredSnapshot`;
  `desired_endpoints.mac_address` parses/canonicalizes; a malformed instance (bad config key), a
  malformed platform (bad `provider_type`), and a malformed MAC each land in `source_issues` with
  the row excluded from the typed collections while an unrelated healthy node/endpoint in the same
  fetch call still parses normally (the core isolation proof); duplicate platform slug and
  duplicate instance-per-node scenarios; a dangling platform/node reference producing a
  target-scope issue; an invalid platform whose issue's `blocked_consumers` lists the dependent
  instance id; `desired_nodes.realized_vm` confirmed absent from the query text.
- `test_drift_comparators.py`, `test_production_adapter.py`: the two scenario tests for the deleted
  `realized_vm_missing`/VM-only-realization branches were removed (the scenarios no longer exist).
- `test_drift_evaluation_snapshot.py`: new test proves a node with `realized_device_id` set plus a
  sibling `DesiredComputeInstance` (same snapshot, `realized_vm_id` set) produces no
  `multiple_realized_links` gap via `evaluate_all_nodes()` — compute-VM realization is invisible to
  the guest-OS ambiguity path by construction (`evaluate_node_intent`'s signature no longer has a
  `realized_vm` parameter to feed).
- New `test_vm_p3_compute_stays_inert.py` (Section 3 above).
- `effective_lifecycle()` unit tests cover all five branches of the table in plan Section 5.4.
- `select_compute_primary_endpoint()` unit tests cover zero/one/ambiguous candidates for an
  active/approved instance, and confirm a planned-lifecycle instance is exempt from the check.

`grep -rn realized_vm nctl/src nctl/tests` confirms every remaining hit is either the new,
differently-scoped `DesiredComputeInstance.realized_vm(+_source)` field, an explanatory
comment/docstring about the removal, or inert leftover `"realized_vm": None` keys in a few
pre-existing mocked GraphQL/REST JSON fixtures (`test_drift_render.py`, `test_reconcile_ledger.py`,
`test_p4_intent_effect_summary_contract.py`, `test_dnsmasq_render.py`) that were not touched because
`fetch_desired_snapshot()` no longer reads that key at all — harmless dead data in those fixtures,
not a behavioral gap; `fetch_desired_snapshot()` correctly resolves the new `desired_compute_*` keys
via `data.get(...)` with an empty-list default, so these older fixtures continue to parse.

## Gate

The final nctl schema reads both new compute roots and the endpoint MAC; every legacy
`DesiredNode.realized_vm` reference is gone from source and tests, not repointed; a malformed
compute/MAC row is reported as a scoped `DesiredSourceIssue` and never crashes the fetch or affects
an unrelated node/endpoint in the same snapshot; an invalid platform's `blocked_consumers` names the
instances it blocks; valid compute rows are provably inert to drift/planner/dashboard/reconcile
dispatch; and `multiple_realized_links` is provably unreachable via compute-VM realization now that
guest-OS realization is Device-only. No live Nautobot/database access was needed or performed in
this step (nctl has no environment-backed test path — Steps 6/8/9-11 are where this schema meets
the live cutover and real GraphQL responses).

Proceeding to Step 6.
