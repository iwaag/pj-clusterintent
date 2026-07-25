# Phase 4 Report — Step 3 (service placement observation in nctl drift)

Date: 2026-07-16. Implements [p4/plan.md](plan.md) Step 3. This is the third suggested commit
boundary. Service placement convergence is now evaluated by `nctl drift`; nauto retains inventory
ingest but no longer registers or carries its separate deterministic placement-review engine.

## What was built

### Typed actual service facts

`nctl_core.sources.actual.ActualFacts` now reads two additional allowlisted Device custom fields
from `_custom_field_data`:

- `observed_services`, normalized to a string-keyed mapping containing mapping-valued entries;
- `service_inventory_updated_at`, retained as the source timestamp string.

Unknown/non-mapping content remains excluded. The existing six production facts and their
consumers are unchanged. GraphQL already fetched `_custom_field_data`, so this requires no query
shape expansion and follows the live-schema-safe raw-map path used by `host_system` and
`network_interface`.

`[reconcile].service_observation_max_age_hours` is a strict positive integer with a default of 24,
matching the former nauto review default. `build_drift()` passes it explicitly through
`DriftContext`, making stale service evidence a controller-owned drift policy instead of an
implicit Job parameter.

### Placement-aware service evaluation

New `nctl_core/drift/service_placement.py` is a pure evaluator over plain inputs. The snapshot
adapter resolves:

- each active `DesiredServicePlacement` to its service and desired node;
- the node's realized Device and operational policy;
- expected host OS;
- the Device's typed observed-service map and service inventory timestamp.

The evaluator preserves desired membership when observation is absent and produces separate
findings:

- `service_missing` — a fresh inventory lacks the desired service key;
- `service_not_running` — the key exists but is not `running`/`active`;
- `service_observation_missing` — no realized Device/facts/timestamp/system is available;
- `service_observation_stale` — service evidence exceeds the configured age;
- `service_observed_on_wrong_node` — the service is running on a non-target Device;
- `service_placement_os_mismatch` — observed host OS conflicts with placement policy;
- `service_has_no_active_placement` — warning/manual-review evidence, never an invented placement.

Nodes with `actual_state_policy=declared` remain observation-exempt. Unexpected stopped entries
are not reported as a running wrong-node location. Docker/systemd source, endpoint, checked time,
service key, placement/profile/node/device IDs, expected OS, and observed state are preserved as
structured diff evidence where applicable.

`evaluate_all_services()` still merges the established lifecycle and dependency evaluation; it
does not discard unresolved dependencies or inactive lifecycle findings. The old blanket
`service_observed_facts_unknown` is no longer produced by the snapshot adapter. Missing/stale
observation codes resolve the service target to `unknown`; a known missing/stopped/misplaced/OS
conflict resolves to `drifting`; warning-only no-placement remains visible while the Phase 2
status contract stays `converged` because there is no error diff.

The drift engine now derives a service target's `observed_at` from the newest service inventory
timestamp among its active placements' realized Devices. Step 4 can therefore apply the same
observation-freshness rule to service targets when tightening `converging` semantics.

### Removal of the second drift engine

Removed from nauto:

- `jobs/service_placement_review.py`;
- `jobs/service_placement_eval.py`;
- `tests/test_service_placement_eval.py`;
- `ServicePlacementReview` import/registration/export.

The nauto README now states the boundary directly: nauto persists host observations, while
service-placement drift is computed only by `nctl drift`. Historical reports/plans remain as
historical records and were not rewritten.

## Parity and tests

The former nauto fixtures were ported into nctl-oriented coverage and normalized to the new stable
diff vocabulary. The parity matrix covers:

- running service + matching OS;
- missing and stopped observations;
- stale timestamp;
- no Device / missing timestamp / missing observed system;
- OS mismatch;
- running service on the wrong node;
- declared-node exemption;
- no active placement;
- deterministic output and no input mutation;
- Linux/Darwin OS normalization.

Additional integration tests prove snapshot ID resolution, active-placement filtering, structured
DiffRecord evidence, actual custom-field accessors, lifecycle/dependency merging, and the revised
rendered drift summaries.

Verification:

- `cd nctl && uv run pytest -q` — **325 passed**;
- `cd nctl && python3 -m compileall -q src tests` — passed;
- `cd nauto && uv run --with pyyaml python -m unittest discover -s tests -v` — **12 passed**;
- changed nauto modules compiled successfully;
- parent, nctl, and nauto `git diff --check` — passed.

The nauto count drops from 27 to 12 because all 15 tests belonging to the deleted duplicate drift
engine were deliberately removed; their behavioral cases now live under nctl tests.

## Read-only live check

`nctl drift --config ../nctl.toml --json` was attempted against the configured local Nautobot to
verify live Device facts without mutation. Nautobot returned HTTP 403, and nctl correctly emitted
`nautobot_fetch_failed` with no targets. No credential value was printed or copied and no write was
attempted. Consequently, the live `observed_services`/timestamp snapshot gate remains unverified
until the local token/config is refreshed. Local fixtures and the previously pinned live GraphQL
`_custom_field_data` shape cover the implementation boundary meanwhile.

## Deliberate non-work

- no Step 4 event-vocabulary or `converging` eligibility change yet;
- no Step 5 deployment-profile `observed_key` override; Step 3 uses authoritative
  `DesiredService.name`, matching Step 2 probe keys;
- no service actuation or automatic removal;
- no `nctl reconcile` planner/executor;
- no commit, push, Nautobot Git Repository sync/reload, or service restart;
- no rewriting of historical docs that accurately describe the former Job at their publication
  time.

## Files changed in this boundary

nctl:

- added `src/nctl_core/drift/service_placement.py` and `tests/test_service_placement.py`;
- updated actual facts, config/context wiring, service snapshot evaluation, comparators, target
  observation timestamps, drift rendering, and related tests.

nauto:

- deleted the placement review Job, duplicate evaluator, and evaluator tests;
- updated Job registration and README ownership documentation.

Parent repository:

- added this report. No commit was created.
