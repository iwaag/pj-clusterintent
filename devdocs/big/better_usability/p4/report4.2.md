# Phase 4 Step 4.2 — Land the complete nintent schema and creation-surface batch

Parent: [plan.md](plan.md), Step 4.2.

All nine sub-items landed in nintent. Nautobot is **not** rebuilt (per the plan: "Do not rebuild
Nautobot yet; the old nctl GraphQL query is incompatible with this schema"). No submodule push was
performed — pushing `nintent` is the user's own step per `.local/localenv_memo.md`
([[feedback-phase-execution-style]]).

## 1–2. `analysis_provenance` added, `placement_policy` removed, migration `0013_*`

`models.py`: `DesiredService.analysis_provenance = JSONField(default=dict, blank=True,
editable=False)` added; `placement_policy` field removed.

`migrations/0013_analysis_provenance_and_generic_endpoint_policy.py` (new), four operations in
order:

1. `AddField analysis_provenance`.
2. `RunPython split_legacy_analysis_keys` / reverse `merge_legacy_analysis_keys_back` — moves the
   four legacy keys (`analysis_status`, `analysis_confidence`, `analysis_reasons`,
   `analysis_warnings`) out of `requirements` into `analysis_provenance`'s closed
   `status`/`confidence`/`reasons`/`warnings` shape, byte-for-byte, leaving every other
   `requirements` key untouched. Reversible for rollback.
3. `RunPython guard_placement_policy_is_empty` / reverse no-op — re-checks at migration time (not
   just at Step 4.1 planning time) that every `placement_policy` is `{}`/null; raises `RuntimeError`
   naming the offending PKs instead of silently dropping data if that has changed.
4. `RemoveField placement_policy`.
5. `AlterField DesiredEndpoint.ip_policy` default `static` → `external` (future rows only; no
   `RunPython` rewrites existing rows).

**Not verifiable locally**: per `nintent/README_DEV.md`, this repo's Django-free local suite
cannot import `django` at all (confirmed: `ModuleNotFoundError: No module named 'django'` even for
a bare migration-file import) — migrations, `makemigrations --check --dry-run`, and `showmigrations`
require the live Nautobot container and are Step 4.8's job. Verified locally instead: `python3 -m
py_compile` on every changed file including the migration (all pass), and manual inspection
confirming the migration's only two `RunPython` operations touch exactly the four named legacy keys
and the guard's read-only check — no other row data is rewritten by this migration.

## 3–4. IntentSource caches read-only; service intent/analysis sections separated

`forms.py`: `IntentSourceForm.Meta.fields` no longer includes `last_import_status` /
`last_import_summary` (still rendered read-only on `intentsource.html`, confirmed unaffected —
that template reads `object.last_import_status` etc. directly, not through the form).
`DesiredServiceForm.Meta.fields` drops `placement_policy`.
`desiredservice.html`: "Placement Policy" detail row replaced with a read-only "Analysis
Provenance" row (`object.analysis_provenance`).

## 5. Quick Add defaults to `device`; accepted-type derivation preview + override

- `operations/hosts.py`: `create_desired_node_with_primary_endpoint(node_type=...)` default
  `"virtual_machine"` → `"device"`.
- `forms.py`: `DesiredHostQuickAddForm.node_type` initial `NODE_TYPE_VIRTUAL_MACHINE` →
  `NODE_TYPE_DEVICE`. `accepted_actual_types` changed from a `JSONField`/`HiddenInput` (silently
  always submitting `None` today, since nothing ever populated it) to a visible, optional
  `CharField` with a `clean_accepted_actual_types` that returns `None` for blank input (derive) or
  a parsed list (override) — the same "absence/empty derives, non-empty differing list is an
  override" rule the operation already implements (Decision 4: "No new model provenance field is
  needed").
- `desiredhost_quick_add.html`: added a read-only preview span
  (`#id_accepted_actual_types_preview`) updated by a small presentation-only `<script>` that
  mirrors `operations.hosts._accepted_actual_types`'s mapping on `node_type` change, plus the now-
  visible override field. Comment ties the JS mapping back to the Python source of truth so the two
  cannot silently diverge.
- `views.py`: `DesiredHostQuickAddView`'s success message now states the effective
  `accepted_actual_types` and whether it was `derived` or `override`, per the plan's "confirmation/
  success view states the effective value and source."

## 6. Generic endpoint `ip_policy` external default; importer becomes pure projection

`models.py` (see §1–2): model default `external`. `importers.py`:
`desired_endpoint_defaults()`'s `"ip_policy": endpoint.ip_policy or "external"` simplified to
`"ip_policy": endpoint.ip_policy` — `loaders._parse_desired_endpoint` (unchanged, already
implements the no-address/no-policy → `"external"` rule at `loaders.py:488-489`) always resolves a
real value before an entry reaches the importer, so the `or "external"` was a second, now-redundant
fallback. `desired_service_defaults`/`desired_service_entry_defaults` also drop their
`"placement_policy": {}` keys (the field no longer exists; `update_or_create(defaults=...)` would
otherwise raise `TypeError` on the next analysis run).

## 7. Service REST relation and read-only fields fixed

`api/serializers.py`: `DesiredServiceSerializer.intent_source` now declared
`serializers.PrimaryKeyRelatedField(queryset=IntentSource.objects.all())` instead of the
`fields = "__all__"`-generated hyperlink to the unregistered `intentsource-detail` route —
`p4/fixtures/service_rest_list_pre.json` (Step 4.1) captured the exact `ImproperlyConfigured` this
fixes. `Meta.read_only_fields = ("analysis_provenance", "last_analyzed_at")`;
`reconciliation_status`/`reconciliation_checked_at` deliberately left writable (nctl dashboard's
sole writer). **Not verifiable locally** for the same reason as the migration — DRF/Nautobot
imports require the live container; re-running `service_rest_list_pre.json`'s `curl` against
deployed Nautobot is Step 4.8's job.

## 8. `placement_policy` readers/writers swept

`grep -rl placement_policy nintent/` now returns only migration history (`0001_initial.py`, and the
new `0013_*` that removes it) — no other `.py`/`.html` reference remains inside nintent.
(nctl's GraphQL query/typed snapshot removal is explicitly Step 4.4's job, not this step's — the
plan splits the coordinated schema break across nintent/nctl commits precisely so each side's
change is reviewable independently.)

## 9. Migration inspection and full suite

`uv run python -m unittest discover -s nautobot_intent_catalog/tests -p 'test_*.py'` — **92
passed** (unchanged from the Step 4.1 baseline; two existing tests updated in place to match the
new contract rather than adding new ones: `test_operations_hosts.py`'s default-node-type
assertion now expects `device`/`["device"]`, and `test_importers.py`'s
`test_primary_desired_endpoint_defaults_missing_names_from_resolved_node` now constructs its
`DesiredEndpointEntry` with the already-resolved `ip_policy="external"` a real loader run would
have produced, since `desired_endpoint_defaults` no longer supplies that fallback itself). Two
`"placement_policy": {}` removals in `test_importers.py`'s and `importers.py`'s expected-defaults
dicts kept in lockstep.

**Bonus normalization beyond the plan's literal item list**: Quick Host Add's `ip_policy=
dhcp_reserved` / `generate_dnsmasq=True` defaults were two independent hardcoded literals in
`forms.py` and `operations/hosts.py`. Named them `QUICK_HOST_IP_POLICY` /
`QUICK_HOST_GENERATE_DNSMASQ` in `operations/hosts.py` and had `forms.py` import them, per
Decision 5's "named Quick-Host policy shared by the form and operation" — the plan describes this
as a named/shared concept but item 5 didn't spell out the mechanical fix; this closes that gap.

## Result

No blocking surprise. All nine sub-items landed; local suite green at the same 92-test baseline.
Everything DB/Nautobot-dependent (migration apply/reverse, REST live behavior, Quick Add template
rendering) is explicitly deferred to Step 4.8's live verification, consistent with this repo's
documented Django-free local test policy rather than a gap introduced by this step. Step 4.3
(analysis provenance-safe updates, dependency natural-key diff) is next and is the step that
actually rewrites `jobs.py`'s `AnalyzeIntentSources` — deliberately not touched here beyond the
minimal `placement_policy` key removal required to keep `importers.py` callable against the new
schema.
