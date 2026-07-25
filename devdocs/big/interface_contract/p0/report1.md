# Phase 0 Step 1 — Build the static interface and consumer inventory

Parent: [plan.md](plan.md), Step 1.

Private evidence: `.local/interface-contract/p0/20260725T122031Z/07_required_search_terms.txt`
(full required-search-term grep, 381 lines), `08_nctl_nauto_wrappers.txt`,
`09_makefiles_ci_rest_paths.txt`, `10_nauto_seed_and_graphql.txt`.

## Method

Ran the plan's mandatory 19-term search (`DesiredServiceViewSet` … `@extras_features("graphql")`)
across `nintent`, `nctl`, `nauto`, `nodeutils`, `ansible_agdev`, and `devdocs`, then targeted
follow-up greps for `rest_get`/`rest_post`/`rest_patch`/`rest_delete` callers, Makefiles/CI, nauto
seed writers, and nctl's use of GraphQL `intent_source`. All commands were read-only (`grep`,
`find`, `wc`, `cat`).

## nintent static inventory (current source, matches roadmap size baseline exactly)

- 12 models carry `@extras_features("graphql")`: `IntentSource`, `DesiredService`,
  `DesiredDependency`, `DesiredNode`, `DesiredEndpoint`, `DesiredComputePlatform`,
  `DesiredComputeInstance`, `DesiredServicePlacement`, `DesiredNodeOperationalOverride`,
  `DesiredIPRange`, `BrainDumpDocument`, `AlignmentReview` (`models.py` lines 82, 128, 221, 278,
  426, 566, 741, 905, 1018, 1140, 1198, 1235) — matches roadmap's "12 nintent models" baseline.
- `api/urls.py` registers 7 REST collections: `nodes`, `services`, `endpoints`,
  `compute-platforms`, `compute-instances`, `braindumps`, `alignment-reviews` — matches roadmap's
  "7 broad REST ModelViewSets" baseline.
- `api/serializers.py`: 8 of the classes use `fields = "__all__"` — `BrainDumpDocumentSerializer`,
  `AlignmentReviewSerializer`, `DesiredNodeSerializer`(+identity field list variant),
  `DesiredServiceSerializer`, `DesiredEndpointSerializer`, `DesiredComputePlatformSerializer`,
  `DesiredComputeInstanceSerializer` (lines 34, 52, 64, 102, 121, 157, 173).
- `urls.py` registers exactly 60 `path()` entries (`grep -c "path("` = 60) — matches roadmap's "60
  nintent UI routes" baseline. All 12 `ObjectEditView`/12 `ObjectDeleteView` subclasses confirmed
  present (`views.py`), including `AlignmentReviewAddView`/`AlignmentReviewEditView`/
  `AlignmentReviewDeleteView` (named routes `alignmentreview_add`/`_edit`/`_delete`,
  `views.py:441,468,475` and `urls.py:183,188,193`), `DesiredHostQuickAddForm`/View
  (`forms.py:29`, `views.py:186`, route `desiredhost_quick_add` at `urls.py:45`), and the Source
  YAML diagnostic page (`views.py:506,522`, route `source_yaml_list` at `urls.py:8`). All match the
  roadmap's named deletion list exactly, with named callers only inside `nintent` itself (test
  files and templates), no caller in `nctl`/`nauto`/Makefiles/CI.
- `create_desired_node_with_primary_endpoint` (`operations/hosts.py:40`) is called only from
  `DesiredHostQuickAddView` (`views.py:194`) and its own unit tests — no caller outside the
  route being deleted.

Classification: `DesiredServiceViewSet`, `DesiredEndpointViewSet`, `DesiredComputePlatformViewSet`,
`DesiredComputeInstanceViewSet`, all `ObjectEditView`/`ObjectDeleteView` subclasses, Quick Host Add,
and the Source YAML diagnostic page are `dead_reference` with respect to any caller outside
`nintent`'s own UI/test tree — `runtime_caller` only within the surface being deleted itself, i.e.
no positive-proof retention case per §5.2.

## nintent Jobs (live registration, cross-checked with Step 0 evidence)

11 `nautobot_intent_catalog.jobs` classes are registered; 4 are `installed=True`:
`Import Intent Sources`, `Analyze Intent Sources`, `Preview Intent Source Analysis`,
`Reconcile Desired IPAM Intent` — matches roadmap's "four nintent Jobs, including the duplicate
Preview Job." `PreviewIntentSourceAnalysis` (`jobs.py:63`) has no caller besides its own
registration and the `Analyze` Job's shared analyzer code — classification `dead_reference` /
scheduled for deletion per roadmap §7, superseded by `Analyze Intent Sources` preview mode. The 7
`installed=False` Job records (`Evaluate Endpoint/Node/Service Intent`, `Export Ansible Hosts
Intent`, `Export Production Inventory`, `Export dnsmasq Records`, `Sync Deployment Profiles`) have
no matching current source class — `generated_or_cache` (stale Nautobot `Job` DB rows from a
previous nintent revision, out of this initiative's scope; not deleted or touched, only noted).

## nauto static inventory

- `nauto/jobs/__init__.py` registers 4 Jobs: `SeedHomeCluster`, `IngestNodeutilsInventory`,
  `AIResourceReview`, `GenerateDesiredServices`.
- `GenerateDesiredServices` (`jobs/generate_desired_services.py:439`) reads
  `seed/service_repositories.yaml` and can write `seed/desired_services.generated.yaml`. No caller
  outside its own registration and its own test (`tests/test_generate_desired_services.py`) — no
  nctl or Makefile caller found. Classification: `dead_reference` (roadmap-scheduled deletion,
  "no unique consumer").
- `seed_home_cluster.py` still imports and writes `nautobot_intent_catalog.models.IntentSource` and
  `DesiredService` (lines 22–24, 314–396) — `runtime_caller`, but roadmap-scheduled for removal in
  Phase 1 (nauto must stop writing nintent desired rows).
- `nauto/seed/home_cluster.yaml` still carries `intent_sources:` (line 497) and
  `desired_services:` (line 503) roots to be moved to `nauto/seed/intent_sources.yaml` per roadmap
  §4/Phase 1.
- `nauto/seed/intent_sources.yaml` currently declares 5 of the 9 canonical roots:
  `intent_sources: []` (empty), `desired_nodes`, `desired_endpoints`,
  `desired_service_placements`, `desired_node_operational_overrides`. `desired_ip_ranges`,
  `desired_compute_platforms`, `desired_compute_instances`, `desired_services` are absent —
  omission, not a contract violation (the plan's 9-root contract permits omitted roots).

## nctl static inventory — REST callers

Every `rest_post`/`rest_patch`/`rest_delete` call site in `nctl/src` (excluding tests):

| Caller | Method | Path | Target collection |
|---|---|---|---|
| `lifecycle.py:109` | PATCH | `{INTENT_API_BASE}/nodes/{id}/` (`lifecycle`) | `nodes` |
| `reconcile/ledger.py:116` | PATCH | `{INTENT_API_BASE}/nodes/{id}/` | `nodes` |
| `reconcile/ledger.py:261` | GET | `{INTENT_API_BASE}/nodes/{id}/` | `nodes` — the known non-approved-exception GET the roadmap assigns to Phase 2 GraphQL replacement |
| `braindump.py:347` | POST | `{BRAINDUMP_API_BASE}/` | `braindumps` |
| `braindump.py:393` | PATCH | `{BRAINDUMP_API_BASE}/{id}/` | `braindumps` |
| `braindump.py:483` | DELETE | `{BRAINDUMP_API_BASE}/{id}/` | `braindumps` |
| `braindump.py:438,445,454` | PATCH/POST | `{ALIGNMENT_REVIEW_API_BASE}/...` | `alignment-reviews` |
| `braindump.py:508` | DELETE | `{ALIGNMENT_REVIEW_API_BASE}/{id}/` | `alignment-reviews` |
| `jobs.py:77` | POST | Job run protocol | Job protocol, not domain |

A repository-wide grep for `/services/`, `/endpoints/`, `/compute-platforms/`, `/compute-instances/`
inside `nctl/src` returns **zero matches** — nctl has no caller for any of the four REST
collections the roadmap schedules for deletion. This positively confirms roadmap §6.2's deletion
list has no real caller within the audit boundary.

`rest_get` has exactly 5 call sites in `nctl/src` (excluding tests, excluding the client method
definition itself): `jobs.py:128` (Job lookup by name), `jobs.py:144` (JobResult polling),
`jobs.py:200` (artifact/status), `reconcile/ledger.py:261` (the node-confirmation GET flagged
above). No other `rest_get` caller exists. Classification per plan §6.2: 3 are `status`/`Job
lookup`/`Job result polling`, 1 (`ledger.py:261`) is the named non-approved exception assigned to
Phase 2.

nctl's GraphQL query modules (`sources/desired.py`, `sources/actual.py`, `sources/braindump.py`,
`sources/snapshot.py`, `sources/__init__.py`, plus `dnsmasq_render.py`, `hosts_intent_render.py`,
`dnsmasq.py`, `dnsmasq_query.py`, `lifecycle.py`, `nautobot.py`, `status.py`, `cli/main.py`,
`drift/evaluation.py`, `production/adapter.py`) were grepped for `intent_source` (case-insensitive,
non-test): **zero matches**. Confirms roadmap's basis for removing GraphQL registration from
`IntentSource` — its only current readers are in-process nintent Jobs, not nctl.

## nctl CLI command inventory

`cli/main.py` registers exactly the 11 top-level commands the roadmap requires: `status`, `actual`
(via `@app.command()`), `drift`, `reconcile`, `lifecycle`, plus sub-apps `render`, `apply`, `ops`,
`braindump`, `ssh`, `session` — matches roadmap §6.6/"11 top-level commands" baseline. No generic
CRUD, REST passthrough, or GraphQL passthrough command exists.

## Makefiles / CI / operator workflows

Only one tracked `Makefile` exists in the whole superproject: `ansible_agdev/Makefile`. It invokes
`nctl` as a subprocess (`NCTL ?= uv run --project ../nctl nctl`) and contains no direct REST/UI
route reference — it is a wrapper over the CLI boundary already covered above, not an independent
consumer. No `.github/workflows/` CI files exist anywhere in the superproject or submodules
(`find . -path '*/.github/workflows/*'` returned nothing) — there is no CI automation to search for
route callers.

## Classification summary (§5.1 vocabulary)

| Match category | Classification | Basis |
|---|---|---|
| `nodes`/`braindumps`/`alignment-reviews` REST collections | `runtime_caller` | nctl `lifecycle.py`, `reconcile/ledger.py`, `braindump.py` call sites listed above |
| `services`/`endpoints`/`compute-platforms`/`compute-instances` REST collections | no caller found → deletion candidate confirmed | zero nctl call sites, zero Makefile/doc-only-current reference |
| All 12 `ObjectEditView`/`ObjectDeleteView` UI mutation classes, Quick Host Add, Source YAML page, `alignmentreview_add/edit/delete` UI routes | no caller outside nintent's own UI/tests → deletion candidate confirmed | plan's required-term search, `08`/`09` evidence |
| `PreviewIntentSourceAnalysis` Job | no caller besides own registration/tests → deletion candidate confirmed | `05_jobs_hooks_scheduled_gitrepo.txt`, `07` evidence |
| nauto `GenerateDesiredServices` Job + `service_repositories.yaml`/`desired_services.generated.yaml` | no caller besides own registration/tests → deletion candidate confirmed | `10` evidence |
| `IntentSource` GraphQL registration | no nctl reader → removal candidate confirmed | `intent_source` grep in `nctl/src/nctl_core/sources` = 0 matches |
| `reconcile/ledger.py:261` node REST GET | `runtime_caller`, but explicitly the non-approved exception the roadmap assigns to Phase 2 replacement | plan §6.2 |
| 7 `installed=False` stale nintent Job DB rows | `generated_or_cache` (out of scope) | Step 0 live query |
| `nauto/seed/home_cluster.yaml` `intent_sources`/`desired_services` roots and `seed_home_cluster.py` writes | `runtime_caller` today, scheduled for Phase 1 removal | `10` evidence |

## Gate

Every match from the plan's required 19-term search plus the follow-up REST/CLI/Makefile/GraphQL
searches has been classified. No unclassified active match remains. The roadmap's deletion list
(4 REST ViewSets, all UI mutation surfaces, `PreviewIntentSourceAnalysis`, nauto
`GenerateDesiredServices`) has zero real callers within the declared audit boundary (nintent/nctl/
nauto/nodeutils/ansible_agdev source, current docs, the one Makefile, and the absent CI). The
retained set (`nodes`/`braindumps`/`alignment-reviews` REST, 4 installed Jobs minus Preview, 11 CLI
commands, GraphQL for all objects except `IntentSource`) each has a named current caller. Proceeding
to Step 2.
