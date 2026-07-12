# Step 9 Report: Update Service Evaluation and Placement Review

## Summary

Completed Step 9. Reworked `nauto`'s Service Placement Review so it reads the desired convergence
target from the persisted nintent models (`DesiredService` + active `DesiredServicePlacement`)
instead of a YAML file catalog, deterministically compares that target against observed Device facts,
and reports each drift category separately. The review is now strictly advisory: it never mutates
active placements, and a missing or stopped observation is reported as drift rather than removing a
placement from the desired membership. The deterministic comparison was extracted into a pure,
database-free helper module and covered with unit tests, including the explicit proof that absent
observations do not drop desired inventory membership.

## Status of plan items

| # | Item | Outcome |
|---|------|---------|
| 1 | Deterministic evaluation compares DesiredService + active placements against `observed_services` and actual host facts | New pure `evaluate_placement_drift` joins active placements to realized Devices, observed services, observed OS, and freshness |
| 2 | Placement review output is a proposal only; no mutation of active placements | Job is read-only; logs an explicit "advisory only / never mutates" warning; LLM contract reframed to `proposed_actions` (advisory) |
| 3 | Remove file-based desired-service loading where persisted nintent models are authoritative | Deleted `load_desired_services`, the `desired_services_file` Job var, and `seed/desired_services.yaml`; the Job now queries nintent models |
| 4 | Report missing service, wrong node, stale observation, insufficient actual facts, and desired/actual OS mismatch separately | Distinct codes `missing_service`, `wrong_node`, `stale_observation`, `insufficient_actual_facts`, `os_mismatch`, never folded together |
| 5 | Tests proving absent observations do not remove desired inventory membership | `test_absent_observation_keeps_placement_as_desired_member` plus 14 more pure-function tests |

## Changes

### nauto/jobs/service_placement_eval.py (new, pure helper)

A database-free module (no Django/Nautobot imports), mirroring the existing
`nodeutils_ingest_batch.py` pure-helper pattern, so the drift logic is unit-testable over plain data:

- `evaluate_placement_drift(services, placements, devices, device_node_map)` returns a per-service
  drift report. Deterministic (sorted by service key, then instance name), pure (never mutates
  inputs).
- `evaluate_active_placement(...)` evaluates one active placement and emits each drift category
  independently. Crucially, an absent or stopped observation **always** returns the placement as a
  desired member annotated with `missing_service` — it is never dropped.
- `normalize_observed_os(...)` maps the observed nodeutils `facts.system` (`Linux`→`linux`,
  `Darwin`→`macos`) only for OS-drift detection. The normalized observed value is never exported as
  `host_os` here (that remains the production exporter's job), and the desired `expected_host_os` is
  used only to record drift, never as a fallback for export.
- Declared nodes (HAOS, `actual_state_policy=declared`) carry no nodeutils observation, so
  observation-based drift does not apply and absence is not "missing".
- Wrong-node detection: a service observed running on a Device that is not an active placement target
  is reported under `unexpected_locations` with the `wrong_node` code, separate from desired
  membership.

### nauto/jobs/service_placement_review.py (rewritten)

- Removed the file catalog reader (`load_desired_services`) and the `desired_services_file` Job var.
- `load_services_and_placements()` reads `DesiredService` and active (`desired_state=active`)
  `DesiredServicePlacement` rows from nintent, resolving each placement's realized Device and
  operational config (`actual_state_policy`, `expected_host_os`, `declared_host_os`). Returns `None`
  when nintent is not installed.
- `load_device_facts()` builds a name-keyed map of observed Device facts trimmed to what drift needs:
  identity, freshness (`is_stale`/age), `observed_system` (from the `host_system` custom field), and
  `observed_services`. Capacity/candidate-scoring fields (cpu/memory/gpu/docker) were dropped because
  candidate scoring was removed — observed facts must not drive desired membership.
- `load_device_node_map()` maps each realized Device name to its DesiredNode slug for wrong-node
  reporting.
- `run()` evaluates drift, logs the deterministic report, and emits an explicit advisory-only
  warning. With `dry_run=false` it still calls the LLM, but the prompt now frames active placements
  as the authoritative convergence target, requires the five drift categories to be reported
  distinctly, and labels remediation as advisory `proposed_actions`.
- Removed now-dead helpers (`_list_value` was already gone; `_int_value`/`_float_value` removed) and
  the candidate-scoring logic.

### nauto/seed/desired_services.yaml (removed)

The only consumer was the old file-based review; nintent models are now authoritative. Removed
outright per the breaking-redesign mandate (no transitional artifacts). The Git-analysis proposal
generator (`generate_desired_services.py`) is unaffected — it writes
`desired_services.generated.yaml` as a candidate proposal, not an authoritative catalog.

### nauto/README.md

- Updated the Job description and the "desired services" section to state that desired services and
  placements live in nintent (`DesiredService`/`DesiredServicePlacement`) with no file catalog as a
  second source of truth.
- Documented the five distinct drift categories and that a missing/stopped observation is reported as
  drift rather than removing the placement.
- Clarified that `Generate Desired Services` produces a candidate proposal, not authoritative state.

### nauto/tests/test_service_placement_eval.py (new)

15 unit tests over the pure module (no DB), all passing:

- `test_absent_observation_keeps_placement_as_desired_member` — the Step 9.5 invariant.
- Separate-category coverage: `missing_service` (absent and stopped), `wrong_node`,
  `stale_observation`, `insufficient_actual_facts` (no realized device, and missing `observed_system`),
  `os_mismatch`, and combined stale+OS-mismatch proving codes are not folded together.
- Declared HAOS node has no observation drift; `no_active_placement` status; satisfied case;
  determinism + input-immutability; and `normalize_observed_os` mapping.

## Verification

- `python3 -m py_compile` passes on both `service_placement_review.py` and `service_placement_eval.py`.
- `python3 -m unittest tests.test_service_placement_eval` — 15 tests pass.
- `python3 -m unittest tests.test_nodeutils_ingest_batch` — 9 tests still pass (no regression).
- Repo-wide grep confirms no remaining references to `desired_services.yaml`, `desired_services_file`,
  `load_desired_services`, `preferred_services`, `service_roles`, or the removed numeric helpers in
  `nauto`/`nintent`/`ansible_agdev` (excluding `.generated.yaml`, `build/lib`, `.venv`).
- No execution environment is available, so the Job was not run against a live Nautobot database. The
  database-touching paths (`load_services_and_placements`, `load_device_facts`, `load_device_node_map`)
  are thin model queries; the substantive comparison logic is the pure module, which is fully tested.

## Exit Criterion Status

Met in contract terms. The evaluation now explains drift across the five required categories while
inventory membership remains the desired convergence target: active placements are always reported as
desired members regardless of whether the service is currently observed, and the review is incapable
of mutating placements. Live confirmation against a real Nautobot instance requires an execution
environment.

## Notes

- Observed-service matching uses the `DesiredService.name` as the `observed_key`, because
  `observed_services` is keyed by the service name self-reported by nodeutils. This is the single
  documented match key; if desired and observed names ever need to diverge, that should become an
  explicit typed field rather than heuristic matching.
- The OS normalization map is intentionally duplicated as a tiny 2-entry constant in the nauto review
  rather than imported from nintent's production contract: the review is a separate package and a
  cross-package runtime import would couple it to nintent internals. The authoritative `host_os`
  export still lives solely in the nintent production exporter; this copy is used only for drift
  reporting and never for export.
- Step 10 (final cross-repo cleanup and whole-pipeline verification) remains.
