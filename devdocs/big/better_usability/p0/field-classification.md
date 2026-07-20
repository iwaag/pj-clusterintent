# Better Usability Phase 0: Field Classification

Parent: [plan.md](plan.md) · [roadmap.md](../roadmap.md) · [discussion.md](../discussion.md).

Status: living artifact for this initiative. Built incrementally across Steps 0.1–0.7; do not
create a second, competing classification document — update this one and explain why in the same
change as the affected phase plan.

## 1. Scope and vocabulary

### Tiers (verbatim intent from roadmap.md, restated for this table)

- **Intent** — a human (or an explicitly delegated domain authority, e.g. an imported catalog)
  must decide the desired fact. Required and front-and-center is fine.
- **Derived** — the system can compute the ordinary value deterministically from inputs it already
  owns. Never demanded from the user; may still expose an optional override route.
- **Override** — an exceptional policy the system cannot safely universalize. Optional, has a safe
  default or an explicit "not set", consulted only when present.

Test applied to every row: *"If the operator never thought about this, is there a right answer the
system could safely pick?"* Yes → Derived or Override, never Intent.

### Exclusions

Framework-owned `PrimaryModel` fields — `id`, `created`, `last_updated`, `tags`, custom-field
infrastructure (`_custom_field_data`), computed-field/relationship infrastructure, and the
`get_absolute_url`/`__str__` plumbing — are out of scope per roadmap.md. Listed once here, not
repeated per model. Every other field declared by `nautobot_intent_catalog` (the 8 models below) is
in scope, including JSON container fields (audited as a container row plus a subfield appendix,
§3) and relationship fields the app itself declares (`intent_source`, `realized_device`,
`realized_vm`, `resolved_service`, `local_endpoint`, `tailscale_endpoint`, `desired_endpoint`,
`realized_ip_address`).

"Writable today" (e.g. `reconciliation_status` is technically `NautobotModelSerializer`-writable
because the ViewSet uses `fields = "__all__"`) does not by itself make a field Intent — see
`DesiredNode.reconciliation_status` / `DesiredService.reconciliation_status` below, both Derived
despite nominal REST writability.

### Models audited

`IntentSource`, `DesiredService`, `DesiredDependency`, `DesiredNode`, `DesiredEndpoint`,
`DesiredServicePlacement`, `DesiredNodeOperationalConfig`, `DesiredIPRange` — all in
`nintent/nautobot_intent_catalog/models.py`. 100 app-declared fields total (12 + 21 + 9 + 14 + 14 +
11 + 10 + 9), each appears in the table below exactly once.

### Legend used in the table

- **Phase —** means no roadmap phase currently owns a change to this field; it is correctly
  classified and behaves consistently with its tier today.
- Contradiction cells say **None** when required/default/editable behavior already matches the
  tier.

## 2. Field classification table

### IntentSource

| Model.field | Current schema/default | Current writers | Tier | Authority/rationale | Contradiction | Target behavior | Owning phase |
|---|---|---|---|---|---|---|---|
| `name` | `CharField`, required | `IntentSourceForm` (forms.py:122); `importers.intent_source_defaults` computes from URL host when unset (importers.py `_name_from_url`) | Intent | Operator names the source; auto-suggestion from URL is a convenience, not a takeover | None | Keep required Intent with auto-suggest-when-blank | — |
| `slug` | `SlugField`, unique, required | Form; `importers._slug_from_text(name/url)` when unset | Intent | Identity the operator may override; slugified default is a convenience | None | Keep | — |
| `source_type` | choices, default `git_repository` | Form; `IntentSourceEntry.source_type` default `"git_repository"` (loaders.py) | Intent | Declares where the source comes from | None | Keep | — |
| `url` | `URLField`, unique, blank/null | Form; loader | Intent | — | None | Keep | — |
| `ref` | `CharField`, blank/null | Form; loader passthrough (jobs.py:465 `ref=intent_source.ref`) | Intent | Optional pin of a git ref | None (resolution of a null `ref` at fetch time was not traced beyond this passthrough — cosmetic gap, does not change tier/schema) | Keep; Phase 4 may document the null-ref default explicitly in the recipe sweep | Phase 4 (doc-only) |
| `enabled` | `BooleanField`, default `True` | Form; bulk `IntentSource.objects.filter(...).update(enabled=False)` for sources missing from a re-import (jobs.py:514-520, `disable_missing` option) | Intent (with a system-triggered off switch as an explicit, visible side effect of re-import, not silent) | Operator turns a source on/off; `disable_missing` is an explicit opt-in import option, not invisible | None | Keep | — |
| `owner` | `CharField`, blank/null | Form; loader | Intent | — | None | Keep | — |
| `description` | `TextField`, blank/null | Form; loader (`IntentSourceEntry` has no `description` field — `importers.intent_source_defaults` hard-codes `"description": None` unconditionally, importers.py:53, overwriting nothing since the loader never carries one) | Intent | — | None (the import path simply never sets it; manual edit via form is the only writer that matters) | Keep | — |
| `source_config` | `JSONField`, default `{}` | Form; loader builds from `service_hint`, `catalog_paths`, `basic_file_paths`, `raw_url_template` | Intent container, mixed subfields — see §3 | Holds both Intent (`service_hint`) and Derived-with-override (`catalog_paths`/`basic_file_paths` default from `DEFAULT_CATALOG_PATHS`/`DEFAULT_BASIC_FILE_PATHS`, loaders.py:22-30) | None | Keep; §3 documents subfields | — |
| `last_import_status` | `CharField`, blank/null, help text says system-derived | **Contradiction:** `IntentSourceForm.Meta.fields` (forms.py:131) exposes it as manually editable; sole real writer is `AnalyzeIntentSources.run` (jobs.py:206-211, `save(update_fields=[...])`) | Derived | Job-computed cache of the last analysis/import run | **Yes** — a human can hand-edit a value the next Job run silently overwrites, with no UI cue it's a cache | Remove from `IntentSourceForm.Meta.fields`; render read-only | Phase 4 |
| `last_imported_at` | `DateTimeField`, blank/null | Sole writer `AnalyzeIntentSources.run` (jobs.py:206-211) | Derived | Same as above | None — correctly absent from `IntentSourceForm.Meta.fields` | Keep as-is (already the model done right) | — |
| `last_import_summary` | `JSONField`, default `{}` | **Contradiction:** exposed in `IntentSourceForm.Meta.fields` (forms.py:132); sole real writer is the same Job | Derived | Same as above | **Yes**, same footgun as `last_import_status` | Remove from form; read-only | Phase 4 |

### DesiredService

| Model.field | Current schema/default | Current writers | Tier | Authority/rationale | Contradiction | Target behavior | Owning phase |
|---|---|---|---|---|---|---|---|
| `name` | `SlugField`, required | Form; loader (`_slug_from_text(name)` fallback when `slug` key absent, loaders.py:561-562 — note this actually derives *slug* from name, not the reverse) | Intent | — | None | Keep | — |
| `slug` | `SlugField`, required | Form; loader | Intent | — | None | Keep | — |
| `display_name` | `CharField`, required | Form; loader | Intent | — | None | Keep | — |
| `service_type` | choices, default `service` | Form; loader | Intent | — | None | Keep | — |
| `lifecycle` | choices, default `proposed` | Form (editable, no override); analysis path hard-codes `"proposed"` unconditionally (importers.py:85, `desired_service_defaults`, used only for catalog-analysis-created rows); seed YAML (`nauto/seed/home_cluster.yaml`) always sets `active` explicitly | Intent (declares the service's own maturity — distinct axis from `DesiredNode.lifecycle`, which gates production inclusion) | Roadmap Phase 3 explicitly asks Phase 0 to record what consumes this field; see rulebook §4 — it feeds only a drift *warning*, never a production-eligibility gate (no `DesiredService`-side equivalent of `PRODUCTION_ELIGIBLE_LIFECYCLES` exists; eligibility is 100% node- and placement-driven) | None as a required-field contradiction (it already defaults safely); the open question is only whether the *default* value for analysis-created rows should stay `proposed` | Keep `proposed` default for analysis-derived rows (they *should* need a look); confirm no default change needed for manually-declared rows, which already set `active` explicitly | Phase 3 (decision-of-record only, per roadmap; no forced change) |
| `intent_source` | FK CASCADE, required | Form; loader/jobs resolve by slug | Intent | — | None | Keep | — |
| `source_ref` | `CharField`, blank/null | Form; loader | Intent | — | None | Keep | — |
| `source_catalog_path` | `CharField`, blank/null | Form; loader | Intent | — | None | Keep | — |
| `catalog_kind` | `CharField`, blank/null | Form; loader | Intent | — | None | Keep | — |
| `catalog_namespace` | `CharField`, default `"default"` | Form; loader (loaders.py:120,556-557) | Intent (with a sensible default value, not Override — every service has *a* namespace, "default" is just the common case, not a rare exception) | — | None | Keep | — |
| `catalog_metadata_name` | `CharField`, required | Form; loader | Intent | — | None | Keep | — |
| `catalog_owner` | `CharField`, blank/null | Form; loader | Intent | — | None | Keep | — |
| `catalog_lifecycle` | `CharField`, blank/null | Form; loader; analysis path copies the Backstage entity's own `spec.lifecycle` string verbatim (importers.py:92) | Derived (a verbatim import of external catalog metadata, not a decision made in this system) | Purely descriptive provenance from the source catalog; distinct from `DesiredService.lifecycle` | None | Keep | — |
| `prefers_gpu` | `BooleanField`, default `False` | Form; loader (loaders.py:127,579-582); analysis path (analysis.py:486-490 hard-codes `False` for analysis-derived rows, later consumed importers.py:93) | Intent | Genuine placement preference only a human/catalog author states | None | Keep | — |
| `min_memory_gb` | `DecimalField`, blank/null | Form; loader | Intent | — | None | Keep | — |
| `requirements` | `JSONField`, default `{}` | Form; loader hard-codes `{}` for manually-declared rows (importers.py:132-133, `desired_service_entry_defaults`); analysis path instead *fills* it with `analysis_status`/`analysis_confidence`/`reasons`/`warnings` (importers.py:95-100) | Intent container, mixed — see §3 | The manually-declared path treats this as a pure Intent bag (currently always empty); the analysis path silently blends in Derived provenance (`analysis_status`, `analysis_confidence`) under the same key with no separate label | **Yes, mild** — analysis provenance and operator-declared requirements share one undifferentiated JSON key | Separate analysis provenance into a clearly labeled sub-key (or its own field) so a human requirement is never confused with system-derived analysis metadata | Phase 4 (residual, non-blocking for Phases 1–3) |
| `placement_policy` | `JSONField`, default `{}` | Form; loader/importers hard-code `{}` on **every** creation path (importers.py:101,133) | Intent (reserved for future placement constraints) | **Finding:** fetched into the nctl typed snapshot (sources/desired.py:220) and folded into `_expected_service_facts["placement_policy"]` (drift/evaluation.py:597) but never read again anywhere in `drift/` or `reconcile/` (confirmed by grep — single occurrence) — it is round-tripped but functionally inert; every row in the live cluster and every seed file has it as `{}` | Not a tier contradiction (an unset Intent field with no unsafe default is fine), but flag as a dead/unconsumed surface | Phase 4 should decide: keep as a documented future hook, or remove as an unused surface consistent with the breaking-change premise | Phase 4 |
| `notes` | `TextField`, blank/null | Form; loader | Intent | — | None | Keep | — |
| `last_analyzed_at` | `DateTimeField`, blank/null | **Sole writer:** `AnalyzeIntentSources.run` (jobs.py:221-229, added to `update_or_create` defaults) | Derived | Job-run cache | None — correctly absent from `DesiredServiceForm.Meta.fields` | Keep as-is | — |
| `reconciliation_status` | choices, blank, help text: "derived cache… written by nctl over REST; not editable here" | **Sole writer:** `nctl dashboard` REST `PATCH /api/plugins/intent-catalog/services/{id}/` (nctl/src/nctl_core/dashboard/push.py:67-70) | Derived | — | None — correctly absent from `DesiredServiceForm.Meta.fields`; REST writability via `fields="__all__"` is intended (that is nctl's only write path) | Keep as-is | — |
| `reconciliation_checked_at` | `DateTimeField`, blank/null | Same nctl REST PATCH as above | Derived | — | None | Keep as-is | — |

### DesiredDependency

| Model.field | Current schema/default | Current writers | Tier | Authority/rationale | Contradiction | Target behavior | Owning phase |
|---|---|---|---|---|---|---|---|
| `source_service` | FK CASCADE, required | Form; jobs.py bulk-recreates all dependencies per service on every analysis run (jobs.py:235-243, unconditional delete+recreate, no diffing) | Intent | — | None | Keep | — |
| `dependency_kind` | `CharField`, required | Form; loader/analysis | Intent | — | None | Keep | — |
| `namespace` | `CharField`, default `"default"` | Form; `importers.dependency_defaults` defaults to `"default"` if empty (importers.py:144) | Intent (sensible default) | — | None | Keep | — |
| `name` | `CharField`, required | Form; loader | Intent | — | None | Keep | — |
| `raw_ref` | `CharField`, required | Form; loader | Intent | — | None | Keep | — |
| `dependency_type` | `CharField`, required | Form; `importers.dependency_defaults` falls back to `dependency_kind` if unset (importers.py:147) | Intent (with a Derived fallback when the more specific type isn't stated) | — | None | Keep | — |
| `resolution_status` | choices, default `unresolved` | Form; `importers.dependency_defaults` defaults to `"unresolved"` if empty (importers.py:148) | Derived — resolution is something the system determines by matching against known services, not something a human declares | Model default already matches tier | None | Keep | — |
| `resolved_service` | FK SET_NULL, blank/null | Form; set by resolution logic (outside the 6 files inventoried here in depth, but consistent with `resolution_status`) | Derived | System match result | None | Keep | — |
| `notes` | `TextField`, blank/null | Form | Intent | — | None | Keep | — |

### DesiredNode

| Model.field | Current schema/default | Current writers | Tier | Authority/rationale | Contradiction | Target behavior | Owning phase |
|---|---|---|---|---|---|---|---|
| `name` | `CharField`, required | Form; Quick Add form (`node_data()`, forms.py:83); `create_desired_node_with_primary_endpoint` (hosts.py:92-101); loader | Intent | — | None | Keep | — |
| `slug` | `SlugField`, unique, required | Same paths; Quick Add auto-slugifies `name` when blank (forms.py:67-77, `clean_slug`) | Intent (with a convenience auto-slug) | — | None | Keep | — |
| `node_type` | choices, default `device` | Form (Quick Add UI-level `initial=virtual_machine`, forms.py:29-32 — differs from the model's own default); `create_desired_node_with_primary_endpoint(node_type: str = "virtual_machine")` (hosts.py:35); loader default `"device"` (loaders.py, applied loaders.py:414-419) | Intent | The model default (`device`) and the Quick Add/operation default (`virtual_machine`) disagree | **Yes** — three independent defaults exist (`device` in models.py:294, `virtual_machine` in forms.py:31/hosts.py:35, `device` again in loaders.py) for the same field with no single source of truth | Phase 4/consistency review: pick one canonical default (or document why Quick Add intentionally differs from bulk YAML import) | Phase 4 |
| `lifecycle` | choices, default `planned` | **Five independent hard-coded sites**, all currently agreeing on `"planned"`: model field default (models.py:299); Quick Add form `initial=` (forms.py:36); `create_desired_node_with_primary_endpoint(lifecycle: str = "planned")` (hosts.py:37); YAML loader fallback (loaders.py:439, `_choice(...,"planned")`); no ViewSet-level default (REST always requires an explicit value or model default applies) | **Intent today — target Derived-away (Override-adjacent) per Phase 3** | Discussion.md Example 2/Principle 5: for the single operator, "the moment intent is expressed, the system should act on it." Today this is required-in-effect for anything to leave `planned` | **Yes, the central one:** all 5 live `DesiredNode` rows are `lifecycle=planned` (confirmed live via GraphQL, 2026-07-20) and nothing in the entire system ever promotes one — no `nctl` command, no nintent UI affordance, no automatic bump on reconcile | Default to `active` on creation, across every one of the 5 sites listed, in the same batched nintent rebuild (roadmap Phase 3); keep `planned` as a formal, explicitly reachable state via a new promotion/demotion CLI, not deleted | **Phase 3** |
| `role` | `CharField`, blank/null | Form; Quick Add (`node_data()`); `create_desired_node_with_primary_endpoint` (hosts.py:92-101) | Intent | — | None | Keep | — |
| `description` | `TextField`, blank/null | Form; Quick Add; operation | Intent | — | None | Keep | — |
| `accepted_actual_types` | `JSONField`, default `[]`, validated in `clean()` (models.py:369-396) | Form (hidden field in Quick Add, `widget=forms.HiddenInput`, forms.py:33); `_accepted_actual_types` computes a per-`node_type` default when omitted (hosts.py:177-208, e.g. `device`→`["device"]`); loader default per `_ACTUAL_TYPE_DEFAULTS` (loaders.py:1160-1165, applied 420-424) | Derived (from `node_type`), with an explicit override path (any user/YAML value that overrides the per-type default) | The ordinary case ("a device realizes as a device") needs no user input; a `service_host` accepting multiple realized-object kinds is the exception | None — already behaves as Derived-with-override; only the UI hides the field entirely in Quick Add rather than showing it as a labeled derived value | Show as a pre-filled, clearly-labeled derived value rather than a hidden input, so an unusual node can override it visibly | Phase 4 (surfacing, per discussion.md Principle 3) |
| `expected_spec` | `JSONField`, default `{}` | Form; loader (validated as a mapping, loaders.py:410-412); Quick Add does **not** expose this at all (absent from `DesiredHostQuickAddForm`) | Intent container — see §3 (subkeys `hostname`/`serial`/`uuid`/`platform` genuinely consumed for identity-mismatch detection: `serial_mismatch`, `uuid_mismatch`, `platform_mismatch`, `hostname_mismatch` in `reconcile/classify.py`) | A human states expected hardware identity to catch a wrong-device swap; system cannot derive this before first observation | None | Keep; Quick Add omission is fine since these are exception-only declarations, not everyday input | — |
| `intent_source` | FK SET_NULL, blank/null | Form; Quick Add (optional); operation | Intent | — | None | Keep | — |
| `realized_device` | FK SET_NULL, blank/null | Form (manually settable!); **primary writer is the `link_actual_node` reconciler**, `Classification.AUTOMATIC` in `reconcile/classify.py:57` for code `actual_node_not_linked` | Derived (system links the desired node to its realized Nautobot Device once observed) | Manual form editability exists for the rare case an automatic match is wrong, functioning as a de facto override | None (manual form field + automatic reconciler already matches the Derived-with-override pattern) | Keep; consider explicitly labeling manual edits here as an override in provenance output (§4) | Phase 2 (provenance labeling only) |
| `realized_vm` | FK SET_NULL, blank/null | Form; same reconciler family, but composer.py explicitly treats a realized VM as `unsupported_actual_type` today ("Schema 1.0 supports nodeutils-backed Devices only", adapter.py:101-102) | Derived (same as `realized_device`), currently unsupported downstream of realization | Same pattern; VM realization exists in the schema ahead of VM support in production composition | Contradiction is structural, not field-level: the field is fully modeled but every VM-realized node is currently skip-classified `unsupported_actual_type` | No field-level change; VM production support (if ever built) is out of this roadmap's scope | — (out of scope; not owned by Phases 1–4) |
| `notes` | `TextField`, blank/null | Form | Intent | — | None | Keep | — |
| `reconciliation_status` | choices, blank | **Sole writer:** `nctl dashboard` REST PATCH (`dashboard/push.py:67-70`, route `nodes/{id}/`) | Derived | — | None — correctly absent from `DesiredNodeForm.Meta.fields` | Keep as-is | — |
| `reconciliation_checked_at` | `DateTimeField`, blank/null | Same nctl REST PATCH | Derived | — | None | Keep as-is | — |

### DesiredEndpoint

| Model.field | Current schema/default | Current writers | Tier | Authority/rationale | Contradiction | Target behavior | Owning phase |
|---|---|---|---|---|---|---|---|
| `name` | `CharField`, required | Form; Quick Add hard-codes `initial=DesiredEndpoint.ENDPOINT_TYPE_PRIMARY` into a **hidden** field (forms.py:56-60, i.e. the endpoint is always literally named `"primary"` from Quick Add); operation | Intent (constrained to `"primary"` in the one supported creation UI today) | — | None | Keep | — |
| `desired_node` | FK CASCADE, required | Form; operation | Intent | — | None | Keep | — |
| `endpoint_type` | choices, default `primary` | Form (Quick Add hidden field, same default); loader default `"primary"` (loaders.py:491) | Intent | — | None | Keep | — |
| `ip_address` | `CharField`, blank/null | Form; Quick Add; realized by `ReconcileDesiredIPAMIntent` indirectly through `realized_ip_address` (not this field itself) | Intent (a static/declared address) or empty when DHCP-assigned | — | None | Keep | — |
| `ip_policy` | choices, default `static` | Form; **model default is `static`**, but `importers.desired_endpoint_defaults` independently defaults absent-YAML entries to `"external"` (importers.py:231, and again in loaders.py:482-483 "neither address nor policy set → external") | Intent (declares how the address is managed: `static`/`dhcp_reserved`/`external`) | — | **Yes** — the Django model field default (`static`) and the YAML-import default (`external`) disagree; a form-created endpoint with no explicit policy silently becomes `static` while a YAML-imported one with no explicit policy silently becomes `external` — a genuinely different desired-state outcome depending only on which creation path was used | Pick one canonical no-input default (roadmap does not currently flag this one — Phase 0 surfaces it as new work) and apply it identically on both paths, or require explicit `ip_policy` whenever `ip_address` is set (already enforced one direction: importers.py:211-212 raises if address is set without policy) | **Phase 1 or 4** (cross-path default conflict; recommend Phase 4 recipe/consistency sweep since it's not a global-failure risk, just an inconsistent no-input outcome) |
| `dns_name` | `CharField`, blank/null | Form; **auto-filled** by `default_dns_name(node.name)` (names.py:22-29) via `importers.desired_endpoint_defaults` (importers.py:216-221) when the endpoint is the node's `primary`/`primary` one and `dns_name` is unset | Derived (with override — explicit YAML/form value always wins) | Ordinary case: every primary endpoint gets a predictable `<node-name>.home.arpa`-style name for free | None — already Derived-with-override; not labeled as derived in any output | Add provenance labeling (§4) so an auto-filled DNS name is visibly distinguished from an explicitly chosen one | Phase 2 (provenance) |
| `mdns_name` | `CharField`, blank/null | Same auto-fill via `default_mdns_name(node.name)` (names.py:32-36, fixed `.local` suffix) | Derived (with override) | Same as `dns_name` | Same as `dns_name` | Same as `dns_name` | Phase 2 (provenance) |
| `vpn_dns_name` | `CharField`, blank/null | Form; Quick Add | Override (only set when Tailscale/VPN access is the exception) | — | None | Keep | — |
| `protocol` | `CharField`, blank/null | Form; Quick Add | Intent/Override (rarely set; no current consumer found in the composer/drift inventories — likely descriptive only) | — | None (no contradiction found; simply lightly used) | Keep | — |
| `port` | `PositiveIntegerField`, blank/null | Form; Quick Add | Intent/Override | — | None | Keep | — |
| `generate_dnsmasq` | `BooleanField`, **model default `False`** | Form; Quick Add form sets `initial=True` (forms.py:47) and `create_desired_node_with_primary_endpoint(generate_dnsmasq: bool = True)` (hosts.py:48) — both **disagree with the model default** | Override (opt-in dnsmasq registration) | — | **Yes** — model default `False`, but both current creation UI/operation paths default new endpoints to `True`; a directly-created `DesiredEndpoint` (e.g. via REST, since `DesiredEndpointSerializer` exposes it) silently gets `False` while the documented Quick Add recipe path gets `True` | Reconcile the model default with the two independently-agreeing UI/operation defaults (make the model default `True` to match actual practice, or explicitly document why REST/model differs) | Phase 4 |
| `dnsmasq_record_type` | choices, default `host_record` | Form; Quick Add (`initial=DesiredEndpoint.DNSMASQ_HOST_RECORD`, agrees); loader default `"host_record"` (loaders.py:500) | Intent/Derived-adjacent (the common case never needs to be chosen) | All three sites agree today | None | Keep | — |
| `realized_ip_address` | FK SET_NULL, blank/null | Form (manually settable); **primary writer is `ReconcileDesiredIPAMIntent`** (`reconcile_ipam` `AUTOMATIC` reconciler, jobs.py `_apply_ipam_reconcile_plan`, `save(update_fields=["realized_ip_address"])`) | Derived (system-linked realized IPAM object), with manual override via form for the rare wrong-match correction | — | None | Keep; provenance labeling recommended (§4) | Phase 2 (provenance) |
| `description` | `TextField`, blank/null | Form | Intent | — | None | Keep | — |

### DesiredServicePlacement

| Model.field | Current schema/default | Current writers | Tier | Authority/rationale | Contradiction | Target behavior | Owning phase |
|---|---|---|---|---|---|---|---|
| `desired_service` | FK PROTECT, required | Form; loader/jobs resolve by reference | Intent | — | None | Keep | — |
| `desired_node` | FK PROTECT, required | Form; loader/jobs | Intent | — | None | Keep | — |
| `desired_endpoint` | FK PROTECT, blank/null, `clean()` enforces it belongs to `desired_node` (models.py:594-599) | Form; loader/jobs | Intent (Override-flavored: only needed when the placement must bind to a specific non-default endpoint) | — | None | Keep | — |
| `instance_name` | `SlugField`, required | Form; loader | Intent | — | None | Keep | — |
| `desired_state` | choices, default `active` | Form (editable); loader **always supplies an explicit value** in every current seed row (`nauto/seed/intent_sources.yaml`, all 6 placements set `desired_state: active`), so the model default is never actually exercised by the import path | Intent | This is the actual production/consumption on/off switch for a placement (drift/evaluation_snapshot.py filters `placement.desired_state == "active"`) | None | Keep | — |
| `instance_role` | `CharField`, blank/null | Form; loader (optional — present on 4/6 seed rows, absent on 2) | Intent | — | None | Keep | — |
| `deployment_profile` | `SlugField`, required, `CheckConstraint` non-empty | Form; loader | Intent | Must match a key in `ansible_agdev/vars/deployment_profiles.yml` (`dnsmasq`, `grafana`, `home_assistant`, `nomad_client`, `nomad_server`, `prometheus`, `prometheus_node_exporter`) | None | Keep | — |
| `config_schema_version` | `CharField`, model default `"1"`, `CheckConstraint` non-empty | **`DesiredServicePlacementForm` intentionally excludes it** (forms.py:228-232 docstring: "the contract only supports a single config schema version… manual CRUD always means the model default"); loader/YAML **always supplies it explicitly** (`config_schema_version: "1"` in every seed row) — the model default is reachable only via a hypothetical direct REST/shell insert, since no ViewSet exists for this model either | Override, correctly implemented (single supported value today; the field exists so a future schema bump has somewhere to go) | This is the one field in the whole audit that is already exactly "the model done right" per discussion.md | None | Keep as-is | — |
| `config` | `JSONField`, default `{}`, `CheckConstraint` object-typed | Form; loader | Intent container, schema keyed by `deployment_profile` — see §3 (audited against `ansible_agdev/vars/deployment_profiles.yml`) | **This is discussion.md Example 1's field.** Recorded intent here has no effect unless the owning node is `PRODUCTION_ELIGIBLE_LIFECYCLES` (`{"approved","active"}`, composer.py:52) — i.e. under today's all-`planned` live cluster, every placement `config` value is silently inert | **Yes — the central Phase 1 finding.** A non-empty `config` on a placement whose node is `planned` is recorded, valid, and completely without effect, with no visible signal anywhere | Emit a "recorded but not applied: node not in production scope" drift/status finding whenever a placement's config would matter but its node isn't eligible (roadmap Phase 1, discussion.md Example 1) | **Phase 1** |
| `assignment_source` | choices, model default `manual` | **`DesiredServicePlacementForm` intentionally excludes it** (same docstring as above: "manual CRUD always means `assignment_source` manual"); loader **always supplies it explicitly** (`assignment_source: yaml` in every seed row) | Override/provenance tag, correctly implemented — matches `config_schema_version`'s pattern | — | None | Keep as-is | — |
| `reason` | `TextField`, blank/null | Form | Intent | — | None | Keep | — |

### DesiredNodeOperationalConfig

| Model.field | Current schema/default | Current writers | Tier | Authority/rationale | Contradiction | Target behavior | Owning phase |
|---|---|---|---|---|---|---|---|
| `desired_node` | OneToOne PROTECT, required | Form (only manual creation path — **no REST ViewSet, no programmatic constructor call anywhere in nintent** except the generic `model(**identity)` upsert inside the YAML import Job, jobs.py:611/593-601) | Structural (identifies which node this config is for) | — | **Yes, structural** — the model as a whole has **zero rows in the live cluster** (confirmed live 2026-07-20) and no creation path except hand-filling the Django-admin-equivalent form or authoring YAML; this is discussion.md Example 3 in full | Dissolve per roadmap Phase 2 favored shape — see §4 decision | **Phase 2** |
| `actual_state_policy` | choices, **required, no model default** | Form; loader treats it as **strictly required** (`_strict_mapping_errors`, loaders.py:730-736 — no fallback value) | Derived (whether a node is `required` (needs live observation) vs. `declared` (e.g. HAOS) is fully determined by whether the node is nodeutils-observable — a fact the system already knows once realized) | Test: "if the operator never thought about this, is there a right answer?" — yes, for any node that already has a realized Device with nodeutils facts, or conversely is declared as a non-observable appliance like HAOS | **Yes, central** — required with no default is the exact opposite of the tier's target behavior; it is also the field whose absence triggers the global `ContractError` at composer.py:185 (see §6) | Derive from realization/observability state; declared-only hosts (HAOS) get an explicit override marker instead | **Phase 2** |
| `expected_host_os` | choices, blank/null, conditionally required via `clean()` (models.py:721-723) | Form; loader strictly validated (loaders.py:786-806 cross-field rules) | Derived — from the last nodeutils observation (`observed_system` custom field, `nctl_core/sources/actual.py:77,91`) | A fresh/unobserved, stale, or unsupported-OS node must not guess (roadmap scenario matrix) | None as a schema contradiction (already optional at the DB level); the contradiction is that nothing today *computes* it — a human must type `linux`/`macos` even though nodeutils already observed the OS | Auto-derive from the latest fresh nodeutils observation; missing/stale/unsupported observation is a structured local finding (composer.py `_host_actual_skip_reasons`/`actual_state_problem`), never a guess | **Phase 2** |
| `declared_host_os` | choices (`haos` only), blank/null, conditionally required | Form; loader | Override | Only meaningful for the exception (currently only HAOS) | None | Keep as the named override route for non-observable hosts | Phase 2 (retained as the override half of the dissolved model) |
| `connection_path` | choices, **required, no model default** | Form; loader strictly required (loaders.py:748-751) | Derived — a node with exactly one usable endpoint has one obvious connection path; a node with a designated-primary endpoint among several has a deterministic pick; only genuine ambiguity (multiple equally plausible endpoints, or a forced Tailscale/non-standard path) needs a human | Same "no default" problem as `actual_state_policy` | **Yes, central** — required with no default; every live node today has exactly one primary endpoint (confirmed live), which is precisely the easy case the roadmap says should never require input | Derive from endpoint topology per the rulebook (§4); ambiguity produces an explicit finding, never a silent pick | **Phase 2** |
| `local_endpoint` | FK PROTECT, blank/null, conditionally required (`clean()` models.py:746-748) | Form; loader | Derived (the node's sole/primary local endpoint) with Override for a forced non-default choice | — | None as schema; currently must be hand-picked even in the single-endpoint case | Auto-select when exactly one usable local endpoint exists; explicit only to override | Phase 2 |
| `tailscale_endpoint` | FK PROTECT, blank/null, conditionally required (`clean()` models.py:743-745) | Form; loader | Override (Tailscale is the exception, not the default connection path) | — | None | Keep as Override; no auto-derivation needed since it only matters when `connection_path=tailscale` | Phase 2 (persisted as-is in the override shape) |
| `ansible_port` | `PositiveIntegerField`, blank/null | Form; loader (optional-but-explicit — no hidden fallback string; a missing value stays `None`, downstream presumably defaults to Ansible's standard port 22 outside this model) | Override, already correct | Roadmap explicitly names this as "the model done right" | None | Keep as-is | — |
| `power_control` | choices, model default `none` | Form; **loader treats it as required with no fallback** (loaders.py:735, in the `required` set) — i.e. every YAML-imported row must state it explicitly even though the model has a safe default | Override, already mostly correct | Roadmap names this as one of the good defaults | **Mild** — the loader path never actually reaches the model default because it's YAML-required; the REST/model path (if a config were ever created directly) would use the safe default. Inconsistent strictness across ingress paths, not a missing-default problem | Loader could relax `power_control` to optional, falling through to the model default `none`, for parity with the model-level design | Phase 2 (minor, bundle with the broader dissolution work) |
| `is_laptop` | `BooleanField`, model default `False` | Form; **loader also treats it as required** (loaders.py:735) — same pattern as `power_control` | Override, already correct at the model level | Same as `power_control` | Same mild inconsistency | Same as `power_control` | Phase 2 (minor) |

### DesiredIPRange

| Model.field | Current schema/default | Current writers | Tier | Authority/rationale | Contradiction | Target behavior | Owning phase |
|---|---|---|---|---|---|---|---|
| `name` | `CharField`, required | Form; loader | Intent | — | None | Keep | — |
| `slug` | `SlugField`, unique, required | Form; loader | Intent | — | None | Keep | — |
| `start_address` | `CharField`, required | Form; loader | Intent | — | None | Keep | — |
| `end_address` | `CharField`, required | Form; loader | Intent | — | None | Keep | — |
| `range_policy` | choices, default `static_pool` | Form; loader (falls back to `"static_pool"` only if somehow still `None` post-validation, loaders.py:881) | Intent | — | None | Keep | — |
| `lifecycle` | choices, default `planned` | Form; **loader hard-codes `lifecycle or "planned"`** (loaders.py:882) — a second, independent site agreeing with the model default | Intent (this is a distinct lifecycle axis from `DesiredNode`/`DesiredService` — governs whether the range is in effect for dnsmasq/IPAM projection, not production-inventory eligibility) | No `PRODUCTION_ELIGIBLE_LIFECYCLES`-style gate was found referencing `DesiredIPRange.lifecycle` in the nctl inventory performed here — its consumption path was not traced beyond dnsmasq rendering (out of the files inventoried for this phase) | None found within the audited surface, but flagged as **unverified** rather than confirmed — the dnsmasq render path (`nctl_core/dnsmasq*.py`) was not in this phase's file list | Phase 4 residual sweep should confirm `DesiredIPRange.lifecycle`'s consumption before assuming it needs the same Phase-3 treatment as node/service lifecycle | Phase 4 (verification, not a confirmed change) |
| `generate_dnsmasq` | `BooleanField`, default `False` | Form; loader default `False` (loaders.py:883) | Override (opt-in) | — | None | Keep | — |
| `dnsmasq_options` | `JSONField`, default `{}` | Form; loader default `{}` (loaders.py:868-871,884) | Intent/Override container — see §3 | — | None | Keep | — |
| `description` | `TextField`, blank/null | Form | Intent | — | None | Keep | — |

## 3. Structured JSON subfield appendix

| Container field | Known/consumed subkeys | Tier of subkey | Notes |
|---|---|---|---|
| `IntentSource.source_config` | `service_hint` | Intent | Free-text hint used by analysis (analysis.py) |
| | `catalog_paths` | Derived-with-override | Defaults to `DEFAULT_CATALOG_PATHS` (loaders.py:22-30) when absent/null |
| | `basic_file_paths` | Derived-with-override | Defaults to `DEFAULT_BASIC_FILE_PATHS` similarly |
| | `raw_url_template` | Intent/Override | Passed through to `IntentSourceEntry.raw_url_template`, no default found |
| `DesiredService.requirements` (manually-declared path) | *(none — always `{}`)* | — | `desired_service_entry_defaults` hard-codes `{}` (importers.py:132) |
| `DesiredService.requirements` (analysis-derived path) | `analysis_status` | Derived | Hard-coded `"catalog_derived"` (analysis.py:475) |
| | `analysis_confidence` | Derived | Hard-coded `"medium"` (analysis.py:476) |
| | `reasons`, `warnings` | Derived | From analysis engine output (importers.py:95-100) |
| `DesiredService.placement_policy` | *(none observed — always `{}`, unconsumed downstream)* | Intent (vestigial) | See table row finding above |
| `DesiredNode.expected_spec` | `hostname` / `host_name` | Intent | Compared for `hostname_mismatch` (evaluation.py:559) |
| | `serial` / `serial_number` | Intent | Compared for `serial_mismatch` |
| | `uuid` / `node_uuid` | Intent | Compared for `uuid_mismatch` |
| | `platform` / `os` | Intent | Compared for `platform_mismatch` |
| `DesiredEndpoint` — no JSON fields | n/a | n/a | — |
| `DesiredServicePlacement.config` | keys declared per-profile in `ansible_agdev/vars/deployment_profiles.yml` (`dnsmasq`: `bind_interfaces`, `cache_size`, `dhcp_authoritative`, `enable_dhcp`, `interfaces`, `listen_addresses`, `local_domain`, `upstream_servers`; `grafana`: `datasource_is_default`, `datasource_name`, `datasource_provisioning_enabled`, `prometheus_port`, `prometheus_scheme`; `home_assistant`: none; `nomad_client`: `datacenter`, `node_class`, `raw_exec_enabled`, `region`; `nomad_server`: `bootstrap_expect`, `datacenter`, `region`, `retry_join`; `prometheus`: `listen_address`, `retention_time`; `prometheus_node_exporter`: none) | Intent (each key is a genuine per-placement mechanism choice the deployment profile schema explicitly allows) | Every key optional (`required: false` throughout today); type-checked by `map_placement_config` (contract.py) against the declared `type`/`items` |
| `DesiredIPRange.dnsmasq_options` | Not enumerated by any consumer inventoried in this phase (dnsmasq render path out of file scope) | Unverified | Phase 4 residual sweep item, same caveat as `DesiredIPRange.lifecycle` |

---

*(Sections 4–9 — derivation/override rulebook, reader/writer matrix, failure-scope matrix,
lifecycle ingress matrix, phase assignment, open issues — are appended in later steps of this
document's construction; see `report0.1.md` onward for the running log.)*
