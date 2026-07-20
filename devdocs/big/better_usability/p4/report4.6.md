# Phase 4 Step 4.6 — Correct residual ownership docs and rewrite the recipes

Parent: [plan.md](plan.md), Step 4.6.

## 1. Phase 0 living artifact updated

`p0/field-classification.md` §8 Phase 4 gained a "Phase 4 resolution status (2026-07-21)"
subsection: each of the ten numbered Phase-4 items now states done/evidence, citing the exact
`p4/report4.N.md` where it landed. Item 2's contextual-defaults note is explicit that
`generate_dnsmasq`/`ip_policy` were deliberately **not** unified to one literal value — Decision 5
kept Quick Host Add's narrower named policy distinct from the generic default — so a future reader
doesn't mistake the documented contextual split for an unresolved contradiction.

## 2. nauto seed ownership: proven with evidence, not renamed

New `nauto/tests/test_generate_desired_services.py` — loads
`jobs/generate_desired_services.py` directly (stubbing `nautobot.apps.jobs` in `sys.modules`,
since unlike the two existing nauto test targets this module imports it unconditionally at the
top level) and calls its actual `_load_repository_specs` reader against the checked-in
`seed/service_repositories.yaml`, asserting it parses to one `RepositorySpec` with the expected
URL and default catalog/basic-file paths. nauto suite: **14 passed** (12 + 2 new, including a
malformed-input rejection test). nintent's existing
`test_loader_does_not_accept_old_service_repositories_root` (confirmed present, unmodified) is the
other half of the boundary: the same file is proven valid under its real owner and explicitly
invalid for nintent's strict loader — no root-key rename, matching Decision 9 exactly.

## 3. Recipes rewritten around the current UI + drift + reconcile flow

New `nctl/docs/register-a-new-pc.md`: the literal one-time-`IntentSource` → Quick Host Add →
derived-preview/override → `nctl drift --host` → `nctl reconcile` (dry, then `--yes`) → final
drift sequence, plus the `nctl lifecycle` demotion path for deliberate staging and the blank-`ref`
resolution order (item 5 below).

Rewrote `nctl/docs/add-a-basic-service.md`: the `nautobot-server shell` Python snippet is gone,
replaced with the actual Nautobot UI CRUD paths (`/plugins/intent-catalog/services/add/`,
`/plugins/intent-catalog/placements/add/` — confirmed against `nintent/urls.py`, both exist as
full `ObjectEditView`s already, this was never actually shell-only). The stale "Known gap" section
documenting the `DesiredServiceSerializer` 500 is deleted outright — Step 4.2 fixed the bug it
described (`p4/report4.2.md` item 7); re-stating a fixed bug as a live gap would itself become
stale documentation. Added explicit `nctl drift --host` / `nctl reconcile` (dry, then `--yes`)
verification steps the old recipe never had, and called out `deployment_profile`/non-default
`config` as genuine placement intent per Decision 10.

## 4. Bootstrap descriptions reconciled

`nctl/README.md` already correctly described `hosts_intent.yml` as the bootstrap-only inventory
and the dnsmasq `--inventory` override as a one-time escape hatch (lines 89–111, unchanged) — no
conflicting claim was found elsewhere to reconcile. `add-a-basic-service.md` now links to that
one description instead of re-explaining the exception inline, per Decision 10's "document ...
exactly once and link to it."

## 5. Blank-ref resolution, contextual defaults, staging, override entry points, feedback layers

Documented in `register-a-new-pc.md`: blank `IntentSource.ref` tries the discovered default
branch, then deduplicated `HEAD`/`main`/`master`, explicit ref always first (matches
`analysis.py::_intent_source_refs`, unchanged code, now stated where an operator reads it rather
than only in source comments). Quick Host Add's contextual endpoint defaults, the
`nctl lifecycle` staging/promotion entry point, the accepted-actual-types override control, and
how to read `intent_effect_summary`'s three layers are each covered where the operator actually
encounters them in the flow, not as a separate reference section.

## 6. README/index links; supersession note

`nctl/README.md` gained a "Recipes" section linking both docs near the top (previously only one
inline link existed, buried in the dnsmasq bootstrap-sequence paragraph). Root `README.md` and
`nintent/README.md`/`README_QUICK.md` were checked and found to contain no stale recipe links to
update — they reference `nctl/README.md` generically, not the recipe docs directly. Added one
narrow supersession note to `devdocs/small/basic_service/report3.md` (a dated scenario transcript
that used `nautobot-server shell`), pointing at the current recipe without rewriting the
historical record itself, per Decision 10's explicit instruction.

## 7. Doc grep sweep

Checked `nctl/docs/`, `nctl/README.md`, `nintent/README.md`, `nintent/README_QUICK.md`,
`nintent/README_DEV.md`, and root `README.md` for: `DesiredNodeOperationalConfig` (zero hits),
`placement_policy` (zero hits), report-schema-`2.0` claims (zero hits), stale REST-gap warnings
(the one instance was the "Known gap" section deleted in item 3 above), and conflicting bootstrap-
group claims (none found beyond the already-correct description in item 4). "Default-planned"
claims: the few remaining `planned` mentions in `nintent/README.md`/`nctl/README.md` all correctly
describe it as a deliberate-staging state or a lifecycle enum value, not a stale default.

## Result

No blocking surprise. All seven sub-items landed. Full suites remain green: nctl 616, nintent 98,
nauto 14. Step 4.7 (the full isolation/orchestration test matrix, including literally following
both rewritten recipes in an isolated fixture environment) is next; Step 4.8's coordinated live
rollout is last and needs the user's explicit push/rebuild involvement per
`.local/localenv_memo.md`.
