# Phase 4 Step 4.5 — Consolidate drift text, dashboard, status guidance, and reconcile

Parent: [plan.md](plan.md), Step 4.5.

This step finally resolves the two contract tests that have been correctly failing since
[report4.1.md](report4.1.md).

## 1. `derived_value_provenance` → `intent_effect_summary`; deleted the old builder

`drift/comparators.py`: `_derived_value_provenance_diff`/`_persisted_value_record` deleted.
Replaced by `_intent_effect_summary_diff_from_record` (pure re-labeling of a report-3.0 node
record into a `DiffRecord`) and `_intent_effect_summary_diff_unknown` (for when composition
never ran). No old-code alias kept. `production/composer.py`'s `NodeOutcome`,
`build_node_report_record`, and `try_resolve_operational_values` were promoted from
underscore-private to shared internal API specifically so the drift comparator and the
production composer build the *same* per-node record rather than two independently-maintained
shapes — this is the literal mechanism behind "the drift comparator translates report node
records into `intent_effect_summary`."

Every desired node now gets exactly one `intent_effect_summary`, including nodes composition
never reached:

- Profiles available and composition succeeds: `composition.report["nodes"]` records translate
  directly (`production.state` ∈ `included`/`skipped`/`out_of_scope`).
- Profiles unavailable, or a global `ContractError` aborts composition: each node gets a record
  with `production.state = "unknown"` (composition was never attempted, not a guess) built from
  `try_resolve_operational_values` + a synthetic `NodeOutcome`. This is where `report3.0`'s
  reserved `unknown` state (never emitted by the composer itself, confirmed in `report4.4.md`)
  turns out to be used after all — by the drift comparator, not the composer.
- `_placement_effect_entry` (composer.py) gained a `production_unknown` reason for this case,
  parallel to `node_out_of_scope`/`node_skipped`.

Fingerprint (`reconcile/fingerprint.py`) needed no code change — it already filters to
`Severity.ERROR` only, so the renamed INFO code is automatically excluded; only its stale
docstring example was updated.

## 2. `deployment_profiles_unavailable` global blocker

`drift/context.py`: `DriftContext` gained `profiles_error: str | None`. `drift_render.py`'s
`fetch_and_compute_drift` now threads `DeploymentProfilesError`'s message through instead of
discarding it. `drift/comparators.py`'s `production_policy` checks `context.profiles_error`
first: if set, yields one global `ERROR` `deployment_profiles_unavailable` diff (message = the
sanitized path+reason `DeploymentProfilesError` already carries) and every node still gets its
`intent_effect_summary` (state `unknown`) — mechanism visibility doesn't depend on profiles.
`envelope.ok` stays `True` (drift itself didn't fail); `classify()`'s existing
`target_kind == "global" → MANUAL_REVIEW` branch handles the new code automatically, and the
executor's existing `plan.has_global_blocking_findings()` guard (Decision 5, unchanged) blocks
every action while it's present — confirmed by new test
`test_deployment_profiles_unavailable_is_a_global_blocking_finding`.

**Both of Step 4.1's originally-failing contract tests now pass**:
`test_missing_deployment_profiles_becomes_global_error` and
`test_invalid_deployment_profiles_becomes_global_error`.

## 3. Compact deterministic intent/effective/application text

`drift_render.py`: `render_drift_text` special-cases `code == "intent_effect_summary"` into
`_intent_effect_summary_lines`, three fixed lines instead of the generic
`[severity] message`:

```
    [info] intent: lifecycle=active node_type=device accepted_actual_types=device (derived) placements: primary(web/active/profile=web/config_keys=['enabled'])
    [info] effective: host_os=linux (derived) connection_path=local (default) ...
    [info] application: state=included primary=applied
```

Placement config is represented only by `config_keys=[...]` (sorted key list) — never the
values; test `test_intent_effect_summary_lines_show_config_keys_not_values` asserts a secret
value doesn't appear in the rendered text while its key does. Every operational value shows its
`source` label (`derived`/`default`/`override`) inline. A `not_applied`/`inactive_by_intent`
placement effect shows its `reason` code.

## 4. Dashboard: same sections/badges, expandable raw evidence

`dashboard/template.html`: `renderDiff`'s inline JS special-cases `intent_effect_summary` the
same way the text renderer does — `renderIntentEffectSummary` builds the three sections
(intent/effective/application) with a `sourceBadge()` element per derived/default/override
value and per placement effect, then appends a collapsed `<details class="ies-raw"><summary>raw
evidence</summary>...</details>` holding the full `desired`/`actual` JSON (previously always
inline) so complete evidence stays one click away without cluttering the default view. Every
other diff code's rendering is untouched. Verified by generating a real HTML page from a
fabricated `intent_effect_summary` envelope and confirming the sections/raw-evidence markup are
present and well-formed (balanced `<script>` tags) — **not** verified in an actual browser;
that's Step 4.8's `nctl dashboard` live check, consistent with this being client-side JS no
Python test can execute.

## 6. `nctl status` stays health-only; text points to drift

`status.py`: module docstring states the Decision 1 split explicitly.
`render_status_text` gained exactly one trailing line: `` target state: use `nctl drift --host
SLUG` `` — `nctl.status.v1`'s schema/data model is unchanged (new test
`test_render_status_text_points_to_drift_for_target_state` asserts the text, not a schema
change).

## 5/7. Reconcile classification, fingerprint, and isolation

No `classify.py` table change needed: global-kind diffs were already unconditionally
`MANUAL_REVIEW` regardless of code (Decision 2 of the original core_reconcile roadmap), so
`deployment_profiles_unavailable` is covered by construction, not by adding an entry. Dashboard
push isolation (item 7's "one failed target PATCH still does not block others") was already
implemented and tested in `dashboard/push.py` (`_push_one` catches per-target, `push_statuses`
loops all targets regardless) — `test_push_counts_server_errors_as_failed_and_continues` already
proves this locally. **Deferred to Step 4.8**: proving the status PATCH actually succeeds
against a live rebuilt Nautobot with the new `DesiredServiceSerializer` (Step 4.2's fix) — that
half needs the real container, consistent with every other DB/Nautobot-dependent item in this
phase's reports so far.

## Tests

Full nctl suite: **616 passed** (up from Step 4.4's 610), zero failures — the two Step
4.1-deferred contract tests now pass for real. Updated for the rename/shape change:
`test_drift_comparators.py` (5 tests), `test_drift_engine.py` (1), `test_drift_render.py`
(profiles-file-by-default fixture change plus 2 new tests), `test_reconcile_planner.py` (rename
+ 1 new global-blocker test), `test_drift_status.py`, `test_dashboard_html.py` (rebuilt fixture
to the new record shape), `test_status.py` (1 new test).

## Result

No blocking surprise. All seven sub-items landed to the extent locally verifiable; the two
explicitly browser/live-only pieces (dashboard visual rendering, live status-PATCH proof) are
named and deferred to Step 4.8 rather than silently skipped. Step 4.6 (docs/recipes) is next —
it's the step that finally updates `nctl/README.md`, `add-a-basic-service.md`, and writes
`register-a-new-pc.md`, none of which have needed touching yet since no doc referenced the old
shapes this phase changed.
