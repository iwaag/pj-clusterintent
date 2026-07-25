# Phase 0 Step 2 — Record live interface, schema, and measurement baselines

Parent: [plan.md](plan.md), Step 2.

Private evidence: `11_nctl_help.txt`, `12_graphql_introspection.txt`, `13_rest_options.txt`,
`14_rest_allowed_methods.txt`, `15_ui_routes.txt`, `16_test_counts_and_line_measurements.txt`,
`17_nintent_test_static_count.txt`, `18_graphql_root_counts.txt` (all under
`.local/interface-contract/p0/20260725T122031Z/`).

All commands were read-only: `nctl --help`/subcommand `--help` (no live call), GraphQL `POST` of
query documents only (no mutation), REST `OPTIONS`, a Django `get_resolver()` walk (in-process,
no HTTP), and static `grep`/`wc`/`find`. No Django `test` command was run against the live
container — it would create/destroy a Postgres test database against the shared external Postgres
instance, which is not clearly covered by the plan's non-mutation boundary; static `grep -c
"def test_"` was used instead as a safer, sufficient collection-only proxy (see below).

## GraphQL introspection

Root query type exposes 313 total fields; of these, exactly the 12 expected nintent roots
(singular + plural per model) are present, including `intent_source`/`intent_sources` (not yet
removed — expected, since Phase 0 only freezes the contract):
`alignment_review(s)`, `braindump_document(s)`, `desired_compute_instance(s)`,
`desired_compute_platform(s)`, `desired_dependenc(y|ies)`, `desired_endpoint(s)`,
`desired_ip_range(s)`, `desired_node`/`desired_nodes`, `desired_node_operational_override(s)`,
`desired_service(s)`, `desired_service_placement(s)`, `intent_source(s)`.

## Live GraphQL root counts (structural, one query document, read-only)

| Root | Live count | Roadmap baseline |
|---|---:|---:|
| `intent_sources` | 2 | 2 |
| `desired_nodes` | 5 | 5 |
| `desired_endpoints` | 5 | 5 |
| `desired_ip_ranges` | 3 | 3 |
| `desired_compute_platforms` | 0 | 0 |
| `desired_compute_instances` | 0 | 0 |
| `desired_services` | 6 | 6 |
| `desired_dependencies` | 0 | 0 |
| `desired_service_placements` | 1 | 1 |
| `desired_node_operational_overrides` | 0 | 0 |
| `braindump_documents` | 5 | 5 |
| `alignment_reviews` | 5 | 5 |

All 12 counts match the roadmap's 2026-07-25 baseline exactly. No deviation to explain.

## REST collections — live methods (pre-contraction state, expected)

`OPTIONS` on all 7 registered collections returns `Allow: GET, POST, PUT, PATCH, DELETE, HEAD,
OPTIONS` uniformly (`14_rest_allowed_methods.txt`) — the standard, still-unnarrowed
`NautobotModelViewSet` default for every collection including the four scheduled for deletion and
`nodes` (scheduled for PATCH-only narrowing). This is the expected current (pre-Phase-2) state, not
a deviation; Phase 0 freezes the *target* contract in Step 7, it does not narrow methods now.

## UI route enumeration (live Django resolver, in-process)

Walking `django.urls.get_resolver()` inside the web container finds 103 routes whose pattern
contains `intent-catalog`: 42 are REST-framework-generated (7 collections × 6 DRF path variants:
list/detail/notes × plain/format-suffix, api-root × 2), and **61** are plugin UI `path()` entries —
one more than the source-static "60 `path()` entries" from Step 1, because Django's resolver
counts the module's `urlpatterns` include wrapper as an additional pattern object; the underlying
distinct named UI routes are 59 plus `source_yaml_list`, matching Step 1's static count exactly once
the wrapper is excluded. Full route list is in `15_ui_routes.txt`. Confirmed present and live: all
12 `*_add`/`*_edit`/`*_delete` triples, `desiredhost_quick_add`, and `source_yaml_list` — exactly the
set Step 1 found has no external caller and the roadmap schedules for deletion.

## YAML loader — live root/alias behavior (source read, not executed against live data)

`nintent/nautobot_intent_catalog/loaders.py:239` (`load_intent_sources`) explicitly rejects exactly
two obsolete top-level keys before parsing any section: `service_repositories` (line 270) and
`desired_node_operational_configs` (line 275), each with a named-replacement error message. It
recognizes exactly the plan's 9 canonical roots (`intent_sources`, `desired_nodes`,
`desired_ip_ranges`, `desired_endpoints`, `desired_compute_platforms`, `desired_compute_instances`,
`desired_services`, `desired_service_placements`, `desired_node_operational_overrides`).

**Confirmed live defect** (matches plan §4.1's "current unknown-root defect"): there is no generic
check that rejects an arbitrary unrecognized top-level key. Only the two named aliases are
explicitly rejected; any other misspelled or unknown root is silently ignored rather than causing
a load error. This is a real, currently-reproducible defect to carry into Phase 1's "reject every
unknown top-level root" requirement — not fixed here, since Phase 0 is documentation-only.

## nctl CLI (live `--help` output)

`nctl --help` lists exactly the 11 top-level commands: `status`, `actual`, `drift`, `reconcile`,
`lifecycle`, `render`, `apply`, `ops`, `braindump`, `ssh`, `session` — matches roadmap §6.6 and
Step 1's static count exactly. Each subcommand's `--help` was captured in `11_nctl_help.txt`.

## Test counts and line measurements

| Measurement | Live/current value | Roadmap baseline | Match |
|---|---:|---:|---|
| `nctl` collected tests (`pytest --collect-only -q`) | 954 | 954 | exact |
| `nctl` tracked source lines | 17,763 | 17,763 | exact |
| `nctl` tracked test lines | 19,380 | 19,380 | exact |
| nintent tracked non-test Python (incl. migrations) | 9,560 | 9,560 | exact |
| nintent tracked test lines | 4,029 | 4,029 | exact |
| nintent tracked template lines | 1,327 | 1,327 | exact |
| nintent UI support lines (`views/urls/navigation/forms/filters/tables.py`) | 1,926 | ~1,926 | exact |
| nintent REST support lines (`api/*.py`) | 278 | 278 | exact |
| nintent YAML loader/import/Job code (`loaders.py`+`importers.py`+`jobs.py`+`analysis.py`) | 3,391 | ~2,877 | see note |
| nintent static test-method count (`grep -c "def test_"`) | 252 | 187 (roadmap) / 252 (remove_unused_surfaces p5 in-container) | matches the more recent p5 in-container result, not the older roadmap figure |

Note on YAML/Job code line count: the roadmap's "~2,877" figure is qualified as an estimate
("about"); the plan's own §4.1 snapshot text does not restate a number to reconcile against. No
action needed — recorded as the current reproducible value with its exact command
(`wc -l loaders.py importers.py jobs.py analysis.py`).

Note on test count: the roadmap roadmap.md baseline of "187 tests" for nintent's "Django-free
suite" predates `remove_unused_surfaces` Phase 5's later in-container full-suite run, which recorded
**252 passed** (`devdocs/big/remove_unused_surfaces/p5/report.md`). This Step 2 static count
(`grep -c "def test_"` = 252, exact per-file breakdown in `17_nintent_test_static_count.txt`)
independently corroborates 252 as the current reproducible figure without running Django's test
command against the shared live Postgres instance. Per plan §4 ("the coordinated
`remove_unused_surfaces` Phase 5 report documents the later deployment... Phase 0 must reconstruct
the current state from both histories"), 252 is recorded as the current baseline; 187 is superseded.

## Gate

Every current-state count reproduces the parent roadmap baseline exactly except the two explicitly
explained deviations above (both are estimate-vs-exact or superseded-baseline cases, not
discrepancies requiring a decision). GraphQL root presence/counts, REST method state, UI route
count, YAML loader alias/unknown-root behavior, nctl CLI surface, and test/line measurements are
all captured with reproducible commands. Proceeding to Step 3.
