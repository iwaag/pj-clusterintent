# P5 Step 5 — Full matrix, manifest, and measurements

Status: complete.

Private evidence: `.local/nctl-modularization/p5/20260728T073933Z/`.

Tuple at execution: superproject `044b928`, nctl `2592ee1`, nintent `4f46bc8`, nauto `6dab422`,
nodeutils `775ed7f`, ansible_agdev `66b31c8`. All six worktrees were clean at the start.

## The inherited runtime blocker

The previous attempt stopped on a duplicate-column failure while creating `test_nautobot` and
recorded it as an unresolved environment blocker. It was not a Nautobot migration defect and needed
neither a runtime re-pin nor a data reset. `p5/problem.md` carries the diagnosis and the two wrapper
defects that produced it: a failed or interrupted run preserved its half-built test database, and a
label that collected nothing exited `0`. Both were fixed in `044b928` before this step re-ran, and
both runtime modes then built `test_nautobot` from empty without incident.

## 1. Root command matrix

Every gate ran from its stated working directory and reported its own case count.

| gate | cases | result |
|---|---|---|
| nctl ordinary | 976 | pass |
| compute conformance | 1 | pass |
| nintent Django-free | 236 run, 14 skipped | pass |
| nauto ordinary | 110 | pass |
| nodeutils ordinary | 54 | pass |
| Ansible helper ordinary | 4 | pass |
| Nautobot runtime reuse (`--keepdb`) | 299 | pass |
| Nautobot runtime clean (`--clean`) | 299 | pass |
| OpenSSH conformance | 2 | pass |
| Ansible conformance | 1 | pass |
| privileged-helper integration | 1 | pass |
| measurement (`--runtime`) | reports runtime 299 | pass |

Against Step 0: nctl ordinary moved from 974 to **976**, which is Step 1's two added pure-module
boundary cases and no other change. Every other component count is unchanged. Step 0 recorded no
runtime count because the blocker prevented one; **299** is therefore the first honest runtime figure
for this phase, and the `--clean` run produced it from a database rebuilt through all 476 migrations.

## 2. Named boundary proofs

All thirteen were invoked individually by ID, not as part of a suite, inside the mechanical manifest
resolution below: `dnsmasq-convergence`, `non-dhcp-ipam-convergence`, `reconcile-host-scope`,
`reconcile-dry-plan`, `partial-ipam-progress`, `forced-observation-refresh`, `desired-mac-safe-stop`,
`compute-inert`, `deterministic-rendering`, `unmanaged-no-delete`, `operation-evidence-reader`,
`post-mutation-evidence`, and `prose-authority`. Each ran and passed with its own stated case count.
`post-mutation-evidence` and `prose-authority` — the two the previous attempt could not reach — each
ran one case through the Nautobot runtime gate.

## 3. Manifest resolution

All 27 rows were resolved by script (`resolve_manifest.py`), which parses the table, converts each
owning test ID into the selector its named gate accepts, runs it alone, and requires a non-zero case
count. 28 IDs executed; the final run has **zero failures**.

The first run found one defect the table had been carrying: `observation-freshness` named
`ProxmoxClusterVmUpsertTests`, a class that does not exist in
`nauto/tests/test_proxmox_cluster_vm_upsert.py`. The owning test is
`FreshnessTests.test_older_observed_at_is_stale_and_not_applied`, which passes. `MANIFEST.md` is
corrected. This is exactly the failure that reading the table instead of executing it would have
missed, since the nauto suite as a whole passes either way.

## 4. Measurements

The Phase 0 method (`collect_step3.py`, copied unmodified except for its output root) ran into
`*-after.tsv` beside the Step 0 `*-before.tsv`.

| measure | before (Step 0, nctl `b5b4a44`) | after (nctl `2592ee1`) |
|---|---|---|
| `nctl_core` modules | 93 | 95 |
| `nctl_core` source lines | 17,346 | 17,228 |
| internal import edges | 308 | 317 |
| test files / lines | 77 / 19,876 | 77 / 19,876 |
| collected nctl cases | 974 | 976 |
| `drift/evaluation.py` lines | 1,036 | 133 |
| modules over 300 lines | 21 | 22 |
| layer-violation rows | 15 | 15 |

`drift/evaluation.py` fan-out fell from 6 to 2 while its fan-in rose from 4 to 6, which is the shape
of a module that stopped deciding and became a shared vocabulary. `drift/node_evaluation.py` (307
lines, fan-in 2) and `drift/endpoint_evaluation.py` (476 lines, fan-in 1) took the decisions.

**Layer violations: none removed, none added — the 15 rows are byte-identical to the Phase 0
baseline.** This is a limitation of the Phase 0 method as much as a result: its `domain` set is a
hard-coded list of six module names, so modules created after Phase 0 are classified
`orchestration` and can never be flagged. The initiative's actual boundary enforcement is
`tests/test_module_boundaries.py`, which does cover the new pure modules and proves that importing
either evaluator loads no transport or CLI module. Reporting the unchanged count without that
qualification would overstate what the number means; reporting improvement would be false.

Runtime: nctl ordinary 5.8–6.2s, Nautobot runtime 46.3s for 299 cases. Slowest nctl cases are the
`test_status.py` connectivity cases at 0.27–0.31s each; the slowest case anywhere in the matrix is
the privileged-helper traversal at 2.19s. Skips: 14 in nintent Django-free, the documented
Nautobot/file-location set. No other gate skipped anything.

## 5. Artifacts and envelopes

Re-captured with read-only and plan-mode commands only; no `--yes`, no Job apply, no SSH, Ansible,
nodeutils, ingest, or Proxmox operation ran.

- `dnsmasq-records.conf` is **byte-identical** to the Step 0 capture with no normalization at all
  (`ac1f19a5…`).
- `hosts_intent.yml`, `hosts-intent-export.json`, `production.yml`, and the production report JSON
  diff to **empty** against both the Step 0 capture and the Phase 0 baseline once the declared
  generation-id and timestamp exclusions are applied. The normalizer was validated by reproducing
  Step 0's own normalized files exactly before it was trusted.
- All five envelopes (`drift`, `reconcile` plan-mode, and the three renders) have **identical field
  sets and identical drift-code/target-status vocabularies** to Step 0, compared by extracted key
  paths rather than by eye.
- The only surviving value differences anywhere are clock- and identity-derived: observation
  `age_hours` (113.0 → 114.1), the ULID `operation_id` and the four paths derived from it, and
  `nctl status` showing the new submodule SHA and one more hour of observation age. These are not
  masked by the normalizer — they are shown rather than hidden, because masking a ULID would also
  mask a real path-contract change.

No envelope field, error code, event name, artifact field, drift code, target status, exit code, CLI
flag, or command name changed.

## 6. Documentation verification

`verify_readme_map.py` checks `nctl/README.md` mechanically: all 50 repository path tokens resolve
(templates with placeholders, globs, or absolute deployment paths are excluded by shape, not by
name); all 22 modules over 300 lines have a responsibility row; `Layout`, `Adding a comparator`,
`Adding a reconciler`, and `Module admission` are all present; and the three registration anchors
(`drift/registry.py`, `reconcile/registry.py`, `reconcile/actions/`) are both documented and real.

One stale path was found and fixed: the README opened by pointing at
`devdocs/vision/core_reconcile/`, which was moved to `devdocs/big/core_reconcile/` before this
initiative. The root `README.md` already used the correct path.

## 7. Compute inertness

Read-only inspection of the persistent Nautobot database: `desired_compute_platforms=0`,
`desired_compute_instances=0`. Compute remains inert, and the `compute-inert` proof passed
individually.

## Deviations

- Two tracked files were edited outside the Step 5 plan text: `devtests/test_strategy/MANIFEST.md`
  (the wrong owning class, §3) and `nctl/README.md` (the stale doc path, §6). Both are in the
  phase's declared scope and both are corrections this step's own verification produced.
- The runtime-gate wrapper and `README_DEV.md` were changed in the separate preceding commit
  `044b928`, not in this step.
