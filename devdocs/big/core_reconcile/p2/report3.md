# Phase 2 Report — Step 3 (Comparator framework and drift core)

Date: 2026-07-15. Implements [p2/plan.md](plan.md) Step 3.

## What was built

New package `nctl/src/nctl_core/drift/`:

- `model.py` — the stable diff-record shape: `Target` (`kind` — deliberately a plain string,
  not a closed enum, so a comparator can report `"global"`/`"device"`-scoped diagnostics without
  a schema break; `slug`/`name`/`id`), `DiffRecord` (`target`, `code`, `severity`
  `error`/`warning`/`info`, `message`, `desired`/`actual` evidence dicts, `sources` — which of
  the three sides produced the evidence), and `Status`
  (`converged`/`drifting`/`converging`/`unknown`).
- `context.py` — `DriftContext` (`generated_at`, `profiles`, `events_dir`): the non-source
  inputs every comparator may need, kept separate from `SourceSnapshot` since none of the three
  are "a source" in the Step 1 sense.
- `registry.py` — `register(resource_type)` decorator plus `run_comparators`, which always
  returns diff records sorted by `(target.kind, target identity, code)` regardless of
  registration order — the roadmap's pluggability requirement made concrete and tested (see
  below).
- `operations.py` — `latest_operation_timestamp_for_target`: scans the Phase 0 event-log
  directory (`<log_dir>/<operation_id>.jsonl`) for the newest event whose `data` payload
  mentions a given target slug anywhere (recursively through dicts/lists — matches e.g. `apply
  dnsmasq`'s `target_hosts` list). Backs the `converging` status rule; expected to rarely fire
  until Phase 4 registers reconcilers, so the lookup and status are defined now rather than
  bolted on later as a schema change.
- `status.py` — `derive_status`: `unknown` when any error-severity diff's code is in a
  documented `UNKNOWN_CODES` set (no realized object, unsupported actual type, missing/stale/
  invalid actual data, fetch/parse failure — "we don't have reliable actual data", not "the data
  disagrees"); `converging` when an operation targeting the node postdates its newest actual
  observation; `drifting` for any other error; `converged` otherwise (warning/info diffs don't
  change status but still appear in the payload).
- `comparators.py` — three initial comparators, all registered under `"node"`:
  - `node_existence` — a lightweight, non-fuzzy check: does `realized_device_id`/
    `realized_vm_id` actually resolve in the actual snapshot, and does a node whose operational
    config requires actual state (`actual_state_policy == "required"`) have *any* realized
    object linked at all. Deliberately **not** the full candidate-matching/ranking nintent's
    `evaluate_node_intent` does (scoring unlinked nodes against Device/VM candidates by name/
    serial) — that fuzzy matching is explicitly Step 4's evaluation port; Step 3 only checks
    links that already exist.
  - `ingest_lag` — compares each observed dump's `collected_at` against the matching device's
    ingested `last_seen` (via `sources.actual.ActualFacts.collected_at`, matched by exact
    `Device.name == dump.identity.hostname`, the same resolution rule nauto's ingest Job uses).
    `info` severity — a dump newer than the last ingest is expected between collection and
    ingest, not necessarily wrong. Attributed to the owning desired node when
    `realized_device_id` links to the matched device, otherwise to a `kind="device"` target so
    the diagnostic isn't silently dropped just because no desired node claims the device yet.
  - `production_policy` — calls the **Step 2 composer directly**
    (`compose_production_inventory`, via `production.adapter.build_production_node_inputs`)
    instead of reimplementing platform-policy/freshness logic a second time, exactly as the plan
    requires ("reusing `evaluate_platform_policy` + skip-reason helpers from Step 2, so the
    composer's `skipped`/`drift` report entries and `nctl drift` diffs can never disagree"). Each
    `report["skipped"]` reason becomes one `error`-severity diff per node; each
    `report["drift"]` entry (currently only `desired_actual_os_mismatch`) becomes one
    `warning`-severity diff; a composition-wide `ContractError` (e.g. an unknown deployment
    profile) becomes a single `kind="global"` diff instead of failing the whole drift run. Uses
    a placeholder all-zero generation id/digest since only `skipped`/`drift` are read, never the
    generation-specific inventory/report fields.
- `engine.py` — `compute_drift(snapshot, context) -> DriftResult`: runs every registered
  comparator, then groups diff records into one `TargetStatus` per target. Every desired node is
  seeded up front with zero diffs (so it reports `converged` even if no comparator says
  anything — "AI can read just [drift] to explain the current state" only holds if silence means
  "nothing wrong"); comparator-produced targets outside the desired-node set (`kind="device"`,
  `kind="global"`) are added as their own targets rather than dropped. `_observed_at_for` derives
  each node's "newest actual observation" timestamp (its realized device's `last_seen`) for the
  `converging` rule.

CLI/Config/Envelope wiring (`nctl drift`) is intentionally **not** included — that's Step 5's
job. `engine.compute_drift` only needs a `SourceSnapshot` and a `DriftContext`, so it stays fully
testable with synthetic snapshots (as `production/composer.py` does for Step 2), matching the
plan's boundary between "drift core" (Step 3) and "`nctl drift` CLI" (Step 5).

## Tests

- `tests/test_drift_registry.py` — the ordering-independence guarantee itself: two comparators
  registered in reverse-alphabetical order still produce alphabetically-sorted output; sorting by
  `(target, code)` across mixed targets; `registered_resource_types()`. Uses a `monkeypatch`-based
  fixture to swap out the module-global `_REGISTRY` per test, so registering throwaway test
  comparators can't leak into other tests (the registry is process-global, populated at import
  time by `comparators.py`).
- `tests/test_drift_operations.py` — no-events-dir case, finding a timestamp via a
  `target_hosts` list, no-match case, latest-across-multiple-files, tolerance for malformed JSON
  lines and missing timestamps, and matching a target nested inside a dict value (not just a
  list) — exercises `_mentions_target`'s full recursion.
- `tests/test_drift_status.py` — all four status outcomes plus the two `converging` sub-cases
  (operation newer/older than observation) and the no-events-dir-configured fallback to
  `drifting`.
- `tests/test_drift_comparators.py` — each comparator directly (bypassing the registry) against
  synthetic `SourceSnapshot`s: `node_existence`'s three flagged cases plus two clean cases
  (declared-policy nodes are correctly never flagged); `ingest_lag`'s device-vs-node attribution,
  the not-newer no-op case, the no-matching-device no-op case, and the never-ingested case;
  `production_policy`'s no-profiles skip, a real skip-reason pass-through
  (`no_realized_device`), an OS-mismatch drift pass-through as a `warning`, and a global
  `ContractError` (`invalid_platform_power`) becoming exactly one `kind="global"` diff.
- `tests/test_drift_engine.py` — a clean node seeds as `converged` with an empty diff list; a
  node with a dangling `realized_device_id` resolves to `unknown`; multiple nodes sort correctly
  and summarize independently; a global production-policy contract error surfaces as its own
  `kind="global"` target alongside the per-node targets.

## Live end-to-end check

No prior drift engine exists to run a parity gate against (this is new functionality, unlike
Steps 1–2's ports), so verification here is a live smoke test instead: ran the full assembly —
`Config.load()` → `NautobotClient` → `build_source_snapshot` → `load_deployment_profiles` →
`DriftContext` → `compute_drift` — against the real dev Nautobot instance and the configured
dumps directory.

Result: all 5 desired nodes (`agdnsmasq`, `agbach`, `aghub`, `agpc`, `agstudio`) report
`converged` with zero diffs. This is the correct output for the current dataset, not a silent
failure: as recorded in report1/report2, none of the desired nodes has an operational config
yet, so `node_existence`'s "required policy but no realized object" check never applies, and
`production_policy` finds zero production-eligible nodes (all `lifecycle: planned`). `ingest_lag`
also produced no diff for the one real dump found (`agstudio.local`) — its `collected_at` is not
newer than the matching device's ingested `last_seen`, which is the correct no-op outcome given
that data, not a bug (spot-checked the underlying values directly). The whole pipeline ran with
no exceptions end to end, including the `load_deployment_profiles` filesystem read against the
real `ansible_agdev` checkout.

## Verification

- `uv run pytest -q` — **183 passed** (34 new; 149 pre-existing from Phases 0–1 and Steps 1–2,
  no regression).
- Live end-to-end smoke test — see above; ran cleanly against real Nautobot data and the real
  ansible_agdev deployment-profiles file, with output consistent with the dataset's known shape.

## Deviations from plan

- None functionally. The one structural choice worth calling out: the plan's Step 3 heading is
  "Comparator framework and drift core," and its Step 5 CLI bullet describes the
  `nctl.drift.v1` envelope — read together, this implies the pure computation (comparators +
  status derivation + per-target grouping) belongs to Step 3, while `Config`/`NautobotClient`/
  `Envelope` wiring belongs to Step 5. Implemented exactly that split (`engine.compute_drift`
  takes only a `SourceSnapshot`/`DriftContext`, no `Config`), mirroring how Step 2 split
  `production/` (pure-ish) from `production_render.py` (Config/Envelope glue). This keeps Step 3
  fully unit-testable without a live Nautobot connection, as done above.

## Commit boundary

Clean, self-contained, nctl-only commit: the comparator framework, drift core, and their full
test suite, fully green, with a live end-to-end smoke test recorded. This is commit 3 of the
plan's suggested order ("nctl: comparator framework + drift core").

**Not done yet, deliberately left for the next commit(s):**

- Step 4 — port `evaluations.py`'s logic as comparators (node candidate-ranking, endpoint IP/
  interface matching, DesiredIPRange classification, DHCP-MAC extraction, service gaps), which
  will supersede/refine `node_existence`'s placeholder existence check with real fuzzy matching;
  switch `render dnsmasq`'s MAC source off `intent_evaluations` GraphQL onto the ported
  comparators; both parity gates the plan calls for.
- Step 5 — `nctl drift` CLI (`Config`/`Envelope` wiring around `engine.compute_drift`, text
  rendering, `--host`/`--service` filters).
- Step 6 — the single nintent push cycle deleting both proto-drift-engines.
- Step 7 — ansible_agdev cleanup and the deferred Phase 1 live-apply proof.
- Step 8 — docs and report closeout.

Next: Step 4 — port `evaluations.py` as comparators and switch `render dnsmasq`'s MAC source.
