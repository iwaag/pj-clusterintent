# Phase 1 Step 7 — Local and static verification

Parent: [plan.md](plan.md), Step 7.

## 1. Test suites

`nintent`: `python3 -m unittest discover -s nautobot_intent_catalog/tests` → 216 tests, `OK`.
`nauto`: `python3 -m unittest discover -s tests` → 110 tests, `OK`. `nauto`:
`python3 -m py_compile jobs/*.py` → clean.

## 2. Diff cleanliness

`git diff --check` (superproject), `git -C nintent diff --check`, `git -C nauto diff --check` —
all clean (working trees are committed/clean at this point in the phase; each step's commit was
already whitespace-checked implicitly by the identical command run before each commit).

## 3. Canonical YAML through the production loader

Loaded `nauto/seed/intent_sources.yaml` through the real `load_intent_sources()`: zero errors;
`intent_sources=[infrastructure, manual]`; `desired_nodes=[agbach, agdnsmasq, aghub, agpc,
agstudio]`; 5 `desired_endpoints`; `desired_ip_ranges=[dhcp-reserved, dhcp-unreserved,
network-infra]`; 0 compute platforms/instances; 6 `desired_services`; 1
`desired_service_placements`; 0 `desired_node_operational_overrides` — matches plan Section 4.2
exactly.

## 4. Required searches, re-run and classified

Re-ran all 21 required search terms across `nintent/` and `nauto/` (`.py`/`.yaml`/`.md`).
Compared to Step 0's baseline, active-code counts dropped to exactly the retained/expected set:

- `PreviewIntentSourceAnalysis`/`Preview Intent Source Analysis`: 0 active-code hits; 2 remaining
  hits are historical (`nintent/DEVLOG_PICKUP.md`, dated 2026-06-24) and current documentation
  (`nintent/README_QUICK.md`) not yet updated — Step 9's job.
- `GenerateDesiredServices`: 0 hits anywhere. `Generate Desired Services`/
  `generate_desired_services`/`service_repositories`/`service_repositories.yaml`/
  `desired_services.generated.yaml`: 0 active-code hits; all remaining hits are in
  `nauto/README.md` (current documentation, Step 9) and one docstring citation in
  `test_ingest_nodeutils_inventory_job.py` (a precedent-style comment, cosmetic, Step 9).
- `disable_missing`, `intent-import-preview.json`, `intent-import-apply.json`,
  `preview = BooleanVar`, `dependencies_deleted`: 0 hits anywhere — fully removed.
- `ensure_intent_sources`/`ensure_desired_services`: 1 hit each, both the new ownership test's
  negative assertions (`assertNotIn`) — expected, not a residual reference.
- `service_repositories`/`desired_node_operational_configs`: remaining hits are exactly the
  retained obsolete-alias rejection code in `loaders.py` and its tests — expected and required.
- `IntentSource`/`DesiredService`: 114/197 hits, scoped separately per plan Section 9.2 — a
  direct grep confirms `nauto/*.py` contains **zero** matches outside the new ownership test's
  negative assertions (`grep -rln "IntentSource\|DesiredService" nauto --include='*.py'` returns
  only `test_seed_home_cluster_ownership.py`); both models remain correctly used throughout
  `nintent`.
- `transaction.set_rollback`: 2 hits, both in the unrelated, untouched `ReconcileDesiredIPAMIntent`/
  test-fixture code path (Import/Analyze preview no longer depends on it — confirmed
  architecturally in Steps 4-5: `_apply_import`/`_apply_analysis` are reached only through the
  `if apply:` guard, never via `transaction.set_rollback`).
- `create_file`: 4 hits — `intent-import-result.json`, `intent-analysis-result.json`, and the
  unrelated, untouched `ipam-reconcile-summary.json` (×2, preview/apply text unchanged) — every
  one has a named retained artifact contract.
- `last_import_status`/`last_analyzed_at`: 9/7 hits — all in the retained Analyze-owned-field
  code/tests (Steps 1, 4, 5), no orphaned reference.

## 5. Job discovery and scope boundaries

`nauto/jobs/__init__.py` exposes exactly `SeedHomeCluster`, `IngestNodeutilsInventory`,
`AIResourceReview` (`register_jobs()` call and `__all__` both confirmed by direct read). No
`nintent/nautobot_intent_catalog/models.py` or migration file changed since Phase 1 began
(`git diff` against both the Phase-0-frozen superproject revision and the Phase-1-start nintent
revision for `models.py`/`migrations/` is empty). `nctl`, `nodeutils`, and `ansible_agdev`
submodule pointers are unchanged since Phase 1 began (`git diff` for those three paths is empty).

## Gate

Satisfied: all local tests pass; the diff is limited to Phase 1 scope (nintent's loader/importers/
import_plan/analysis_plan/jobs/tests, nauto's seed YAML/seed_home_cluster/jobs __init__/tests,
and this phase's own devdocs); no model file or migration changed; `nctl`/`nodeutils`/
`ansible_agdev` untouched. Proceeding to Step 8.
