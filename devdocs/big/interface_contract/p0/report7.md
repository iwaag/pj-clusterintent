# Phase 0 Step 7 — Freeze the final interface matrix and field-level contracts

Parent: [plan.md](plan.md), Step 7.

This step adopts the roadmap's already-specified target contract (roadmap.md §"Required interface
matrix", §6.2–§6.6) as **frozen** for Phases 1–4, cross-referenced against the evidence gathered in
Steps 0–6 and amended by the Step 6 disposition ledger. No new design decision is introduced here
beyond what Steps 1–6 evidenced; where the roadmap's target and this audit's evidence agree, the
roadmap text is the frozen contract.

## 1. Final interface matrix (with evidence references)

Reuses roadmap.md's "Required interface matrix" table (nintent objects, actual-ledger objects,
operations) unchanged, with the following evidence anchors added:

- Every `keep`/`delete` decision for nintent REST ViewSets, UI mutation views, and Jobs is proved by
  Step 1 (`report1.md`, zero-caller confirmation) plus the Step 6 external-caller attestation
  (`report6.md` Decision 5).
- Every `keep` GraphQL root is proved by Step 2's live introspection (`report2.md`) and the pinned
  query digests below.
- IntentSource's GraphQL-removal decision is proved by the zero-match `intent_source` grep in
  `nctl/src/nctl_core/sources` (Step 1).

## 2. Frozen GraphQL selection manifest

| Query | File | Normalized SHA-256 |
|---|---|---|
| Desired snapshot (9 roots: nodes, endpoints, ip_ranges, operational_overrides, service_placements, services, dependencies, compute_platforms, compute_instances) | `nctl/src/nctl_core/sources/desired.py:60-177` (`DESIRED_QUERY`) | `e6e34a9f6dd1a561f6a446e7ac464dc62b9566c989d96df0d3561cbfded17357` |
| Actual snapshot (devices, clusters, virtual_machines, vm_interfaces, interfaces, ip_addresses) | `nctl/src/nctl_core/sources/actual.py:37-86` (`ACTUAL_QUERY`) | `f2b8808491d5cc80f5cbe65cfc05841bb18d82ad13cdbeee3f50a97c234e879a` |
| Braindump list | `nctl/src/nctl_core/sources/braindump.py:23-40` (`LIST_QUERY`) | `e276ec2a13eebe7fc0e416e9ff08d785bb6a122d14a006e020afa0f048f2c19d` |
| Braindump show | `nctl/src/nctl_core/sources/braindump.py:42-59` (`SHOW_QUERY`) | `003a5ffec0e00c7abb0a8a6e85af355abb2a34599bc845ff35e9cbd7b4aebe70` |

Digest method: extract the triple-quoted query text, collapse all whitespace runs to a single
space (`" ".join(text.split())`), SHA-256 the result. Reproducible via the same normalization in a
later phase to detect selection drift.

`IntentSource` GraphQL registration (`@extras_features("graphql")` at `models.py:82`) is **removed**
in Phase 2 — no query above selects `intent_source`/`intent_sources`, confirmed by Step 1's
zero-match search. All other 11 `@extras_features("graphql")` models remain registered; their exact
selected fields are the field lists shown in the four query texts above (the desired/actual/braindump
snapshots are the complete set of nctl-consumed GraphQL fields — no other nctl module issues a
GraphQL query per Step 1's module-wide `graphql|gql` grep).

## 3. Frozen REST method/field manifest

Target state (Phase 2 implements; current live state per Step 2 is still full CRUD on all 7
collections — not yet narrowed):

| Collection | Final methods | Writable fields | Current writer (Step 1 evidence) |
|---|---|---|---|
| `nodes` | GET (incidental) + PATCH | `lifecycle`, `realized_device`, `realized_device_source` | `nctl lifecycle` (`lifecycle.py:109`), `link_actual_node` reconciler (`reconcile/ledger.py:116`) |
| `braindumps` | GET + POST/PATCH/DELETE | `title`, `body`, `authorship` | `nctl braindump` (`braindump.py:347,393,483`) |
| `alignment-reviews` | GET + POST/PATCH/DELETE | `braindump` (create only), `summary` (create/replace) | `nctl braindump review` (`braindump.py:438,445,454,508`) |
| `services`, `endpoints`, `compute-platforms`, `compute-instances` | deleted entirely | n/a | none (Step 1: zero nctl call sites; Step 6 Decision 5: no external caller) |

Minimum frozen response payload (per plan §6.2, cross-checked against current model fields,
`models.py`):

- **node**: `id`, `name`, `slug`, `node_type`, `lifecycle`, `role`, `realized_device`,
  `realized_device_source`, `created`, `last_updated`. (`accepted_actual_types`, `expected_spec`,
  `intent_source`, `notes` remain readable if a current consumer needs them — no nctl REST consumer
  reads node fields today beyond the lifecycle PATCH itself, so these are display-only fields the
  Phase 2 serializer author may keep or trim without violating this contract, provided the three
  writable fields above stay exactly as specified.)
- **Braindump**: `id`, `title`, `body`, `authorship`, `created`, `last_updated`.
- **Alignment Review**: `id`, `braindump`, `summary`, `created`, `last_updated`.

`fields = "__all__"` (8 current occurrences, Step 1) must be replaced by these explicit lists in
Phase 2; framework metadata beyond `created`/`last_updated` is not frozen as required.

`link_actual_node`'s current REST GET precondition/confirmation calls (`reconcile/ledger.py:261`,
the one non-approved `rest_get` exception, Step 1) are replaced by a GraphQL read in Phase 2 — this
is the only REST→GraphQL confirmation change required; `nctl lifecycle`, Braindump, and review
writes already confirm through GraphQL per roadmap Decision 3.

## 4. Frozen read-only UI route manifest

Retained (read-only list/detail, from the live route walk in Step 2, `15_ui_routes.txt`):
`intentsource_list`/`intentsource` (detail), `desirednode_list`/`desirednode`,
`desiredendpoint_list`/`desiredendpoint`, `desirediprange_list`/`desirediprange`,
`desirednodeoperationaloverride_list`/`desirednodeoperationaloverride`,
`desiredservice_list`/`desiredservice`, `desireddependency_list`/`desireddependency`,
`desiredserviceplacement_list`/`desiredserviceplacement`,
`desiredcomputeplatform_list`/`desiredcomputeplatform`,
`desiredcomputeinstance_list`/`desiredcomputeinstance`,
`braindumpdocument_list`/`braindumpdocument` (with its nested, distinct Alignment Review panel,
`templates/nautobot_intent_catalog/braindumpdocument.html:54-60`, Step 1).

Removed (no caller beyond nintent's own UI/tests, Step 1; no external caller, Step 6 Decision 5):
all 12 `*_add`/`*_edit`/`*_delete` named routes (`intentsource_add/_edit/_delete`,
`desirednode_add/_edit/_delete`, `desiredendpoint_add/_edit/_delete`,
`desirediprange_add/_edit/_delete`, `desirednodeoperationaloverride_add/_edit/_delete`,
`desiredservice_add/_edit/_delete`, `desireddependency_add/_edit/_delete` [note: no independent
list-page mutation existed beyond edit/delete since Dependency has no `_add` route per the live
route walk], `desiredserviceplacement_add/_edit/_delete`,
`desiredcomputeplatform_add/_edit/_delete`, `desiredcomputeinstance_add/_edit/_delete`,
`braindumpdocument_add/_edit/_delete`), `desiredhost_quick_add`, `source_yaml_list`,
`alignmentreview_add`/`alignmentreview_edit`/`alignmentreview_delete`. No domain-mutation POST may
remain reachable from any retained route.

## 5. Frozen YAML root/field/ownership manifest

The 9 canonical roots (unchanged from plan §6.4, current loader already enforces exactly these plus
rejecting `service_repositories`/`desired_node_operational_configs`, Step 2):

```text
intent_sources
desired_nodes
desired_endpoints
desired_ip_ranges
desired_compute_platforms
desired_compute_instances
desired_services
desired_service_placements
desired_node_operational_overrides
```

Ownership rules frozen per plan §6.4 and roadmap "Operational fields have one writer":

- `lifecycle`: YAML sets on create only; an existing node's lifecycle is nctl-`lifecycle`-owned and
  must survive re-import unchanged (this rule already resolved the `agbach`/`agpc`/`agstudio`
  lifecycle non-conflict in Step 4, no live/YAML mismatch needed for that field).
- `realized_device`/`realized_device_source`, `realized_ip_address`/`realized_ip_address_source`,
  `realized_cluster`/`realized_cluster_source`, `realized_vm`/`realized_vm_source`: never YAML-owned.
- Source-analysis fields (`display_name`, `catalog_namespace`, `catalog_metadata_name`,
  `requirements`, `desired_dependencies`) are Analyze-Job-owned, not YAML-owned, except the initial
  values YAML/`Seed Home Cluster` may create.
- Operator-owned `DesiredService` lifecycle/requirements/notes are preserved from analysis on
  re-import.
- Omission of any root or row never authorizes deletion, retirement, unlinking, or disabling.

**Phase 1 content instructions frozen by Step 6's decisions** (not applied here — Phase 0 is
documentation-only):

1. Move `Infrastructure` IntentSource + its 5 `desired_services` from `home_cluster.yaml` into
   `intent_sources.yaml`'s `intent_sources`/new `desired_services` roots (Step 5, uncontested).
2. Remove the 6 checked-in-only nodes (`agmbp2019`, `agmbp2018`, `agprometheus`, `aggrafana`,
   `agnomad`, `aghaos`) and their placements/overrides from `intent_sources.yaml`
   (Step 6 Decision 1).
3. Add `agdnsmasq`, `aghub`, the `Manual` IntentSource, the `dnsmasq` DesiredService, and its
   placement to `intent_sources.yaml` (Step 6 Decision 2).
4. Update `agbach`/`agpc`/`agstudio` endpoint rows in `intent_sources.yaml` to the live
   `dns_name`/static-IP/`OVERRIDE` shape, replacing `mdns_name`/`ip_policy: external`
   (Step 6 Decision 3).
5. Add a new `desired_ip_ranges` root with `dhcp-reserved`, `network-infra`, `dhcp-unreserved`
   (Step 6 Decision 4).

## 6. Frozen Job variable and artifact schemas

Adopted unchanged from roadmap §6.5/plan §6.5 (no evidence in Steps 0–6 contradicts this target):

| Job | Frozen variables |
|---|---|
| Import Intent Sources | `source_file`; `apply` defaulting to `false` |
| Analyze Intent Sources | `fetch_timeout`; `include_disabled`; `apply` defaulting to `false` |
| Reconcile Desired IPAM Intent | existing `commit_changes`, `include_inactive`, `desired_node` (unchanged) |

`disable_missing` and the standalone `preview` boolean are removed from Import; `apply=false` is the
safer replacement polarity. `Preview Intent Source Analysis` is deleted (Step 1: confirmed
`dead_reference`, no caller beyond its own registration).

Artifact schema fields for Import/Analyze preview+apply are exactly the field lists enumerated in
plan §6.5 (schema version, mode, source identity/digest, scope/counts, per-object model/identity/
action/changed-fields, conflicts/errors, create/update/unchanged totals, write/commit flag,
transaction result for Import; equivalent fields for Analyze). `ipam-reconcile-summary.json` /
`nctl.ipam.reconcile.summary.v1` are retained unchanged (plan §6.5, no incompatibility found in this
audit).

## 7. Frozen CLI command set

Unchanged: `status`, `actual`, `drift`, `reconcile`, `lifecycle`, `render`, `apply`, `ops`,
`braindump`, `ssh`, `session` — confirmed live via `nctl --help` (Step 2, `11_nctl_help.txt`). REST
helpers in `nctl_core/nautobot.py` (`rest_get`/`rest_post`/`rest_patch`/`rest_delete`) are retained
only for the call sites enumerated in Step 1's REST caller table — no unclassified helper remains.

## 8. AI Resource Auto Review JobHook

Confirmed live, `enabled=True`, bound to Job `AI Resource Review` (Step 0, `05_jobs_hooks...txt`).
Explicitly deferred per roadmap — no code change in this initiative; noted as untouched.

## 9. Migration/schema confirmation

No model field removal or addition is required by this frozen contract — every field referenced
above already exists on the current models (`models.py`, confirmed field-by-field while assembling
§3/§5 above). `makemigrations --check --dry-run` was not re-run in Step 7 (no model change is
proposed to check); Step 0 already confirmed migrations are applied through `0016` with no pending
migration state. No new migration is created by this initiative.

## Gate

Every retained checkmark in the roadmap's interface matrix now has an evidence reference from Steps
0–6. Every planned deletion is backed by Step 1's no-caller search plus Step 6's external-caller
attestation. GraphQL selections are pinned with reproducible digests; REST methods/fields, UI
routes, YAML roots/fields/ownership (including the 5 Phase-1 content changes from Step 6), Job
variables/artifacts, and the CLI set are frozen. No new interface/ownership decision remains for
Phases 1–4 to make independently. Proceeding to Step 8.
