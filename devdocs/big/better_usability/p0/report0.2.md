# Phase 0 — Step 0.2 report: Inventory every writer and default

Parent: [plan.md](plan.md) Step 0.2.

## What was done

Built the writer-side half of the reader/writer matrix (`field-classification.md` §5), one row per
creation/update **boundary** (not per field): regular Nautobot `ModelForm` CRUD, the Quick Add
form/view/operation, `operations/ipam.py` (confirmed as read-only planning, no ledger write),
intent-catalog REST (3 of 8 models only), `loaders.py` YAML normalization, `importers.py`
defaulting, the three nintent Jobs (`ImportIntentSources`, `AnalyzeIntentSources`,
`ReconcileDesiredIPAMIntent`), the seed/example YAML files under `nauto/`, nctl's REST write-back
(`dashboard/push.py`), and the admin/shell-only path for `DesiredNodeOperationalConfig`.

## Findings surfaced in this step

- **`ImportIntentSources`' `_import_intent_rows` is the only place in the entire codebase that
  programmatically instantiates a `DesiredNodeOperationalConfig` row.** Any Phase 3 lifecycle
  default change and any Phase 2 derivation change must both be applied here, not just in the UI
  forms — this is a first-class creation ingress, not a convenience path.
- **`AnalyzeIntentSources` unconditionally deletes and recreates every `DesiredDependency` row for
  a service on each run, with no diffing** — a manual edit to a dependency's `notes` or
  `resolution_status` is silently destroyed on the next analysis. Not currently flagged by the
  roadmap; logged as a Phase 4 residual, non-blocking finding.
- **The seed/example fixtures already model the Phase 3 target state** (`lifecycle: active`
  everywhere in `nauto/seed/*.yaml`) even though the live cluster — loaded through a different,
  earlier import — is entirely `lifecycle: planned`. This means Phase 3's default change will not
  break these fixtures; they're aspirational, not descriptive of current live state.
- **`nauto/seed/service_repositories.yaml` uses a top-level key (`service_repositories:`) that
  `loaders.load_intent_sources` explicitly rejects** (loaders.py:230-234) — this fixture would fail
  to load as written today. Flagged for Phase 4's recipe/fixture sweep.
- **`DesiredNodeOperationalConfig` has no REST route and no `operations.py` constructor** —
  confirmed precisely (not just "seems missing"): its only two creation paths in the whole
  repository are the Django `ModelForm`/`ObjectEditView` CRUD and the YAML import Job. This
  directly matches discussion.md Example 3 and is the strongest concrete argument for Phase 2's
  planned dissolution (no persistence-layer investment currently exists to preserve).
- Two-layer defaulting (a loader-dataclass default, then a separate importer-level default) exists
  for several fields (e.g. `ip_policy`, `dependency_type`) — flagged as a minor legibility issue,
  not a correctness bug, for Phase 4's non-blocking cleanup list.

No blocking surprises requiring human judgment.

## Next step

Step 0.3 — classify every field by authority (Intent/Derived/Override), building on the tier
assignments already drafted in §2's table and resolving the harder cases (`DesiredService.lifecycle`
semantics, node/service lifecycle, endpoint/connection selection, actual-state policy, SSH
port/power/laptop, IP range policy) called out explicitly by the plan.
