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
| `lifecycle` | choices, default `planned` | Form; **loader hard-codes `lifecycle or "planned"`** (loaders.py:882) — a second, independent site agreeing with the model default | Intent (distinct lifecycle axis from `DesiredNode`/`DesiredService`) | **Confirmed consumer:** gates dnsmasq range export via `ELIGIBLE_NODE_LIFECYCLES` (`nctl_core/dnsmasq.py:367-372`, code `range_lifecycle_not_exportable`) — the same lenient bootstrap-eligible set used for node export (`{"planned","approved","active"}`, hosts_intent.py:35), **not** the stricter `PRODUCTION_ELIGIBLE_LIFECYCLES` (`{"approved","active"}`) used for production composition | None — a range already at `planned` is already dnsmasq-exportable today, so a Phase 3 default-to-`active` change (if ever extended to this model) would not newly unlock anything already blocked | Confirmed no hidden gate risk; no change required unless Phase 3 is explicitly extended to this model (roadmap does not currently ask for that) | — |
| `generate_dnsmasq` | `BooleanField`, default `False` | Form; loader default `False` (loaders.py:883) | Override (opt-in) | — | None | Keep | — |
| `dnsmasq_options` | `JSONField`, default `{}` | Form; loader default `{}` (loaders.py:868-871,884) | Intent/Override container — see §3 | **Confirmed consumer:** subkey `lease_time` read at `nctl_core/dnsmasq.py:341` | None | Keep | — |
| `description` | `TextField`, blank/null | Form | Intent | — | None | Keep | — |

### Decision notes for difficult classification cases (Step 0.3)

Per-field tier/rationale is recorded in the table above; this records the cross-field judgment
calls the plan requires explicitly, rather than hiding the reasoning inside individual cells.

1. **Node and service lifecycle are different axes despite sharing a vocabulary.**
   `DesiredNode.lifecycle` gates two things: bootstrap/dnsmasq export eligibility
   (`ELIGIBLE_NODE_LIFECYCLES = {"planned","approved","active"}`, hosts_intent.py:35,
   dnsmasq.py:290) and production-inventory eligibility (`PRODUCTION_ELIGIBLE_LIFECYCLES =
   {"approved","active"}`, composer.py:52) — real, escalating enforcement. `DesiredService.lifecycle`
   gates nothing structurally; it only feeds a drift **warning** (`service_lifecycle_inactive` for
   `deprecated`/`retired`, `missing_service_lifecycle` for empty/`unknown`, evaluation.py:493-505).
   Decision: `DesiredNode.lifecycle` is the field Phase 3 must default to `active`; nothing found in
   this audit requires changing `DesiredService.lifecycle`'s default away from `proposed` — the
   value that matters is that analysis-derived services start `proposed` (they should get a human
   look) while manually/YAML-declared services already set `active` explicitly today. Phase 3 owns
   recording this as the decision, per roadmap's own instruction, with no forced default change.

2. **`node_type` vs. `accepted_actual_types`.** `node_type` is Intent — the operator states what
   kind of thing this is. `accepted_actual_types` is Derived from `node_type` via
   `_ACTUAL_TYPE_DEFAULTS` (hosts.py:177-208, loaders.py:1160-1165), with an explicit override for
   the genuine exception (a `service_host` that may realize as more than one actual type). Decision:
   keep the tier split as-is; the only correction needed is surfacing (Quick Add currently hides the
   derived value in a `HiddenInput` rather than showing it as a labeled, overridable derived value —
   Phase 4, discussion.md Principle 3).

3. **Identity/name/slug/source/catalog metadata, across all 8 models.** Every `name`/`slug`/
   `display_name`/`catalog_*` field is Intent, full stop — auto-suggestion (slugify-from-name,
   name-from-URL) is a convenience default for the *value*, not a change of *authority*. The test
   ("if the operator never thought about this, is there a right answer?") fails here: the system can
   *guess* a slug, but it cannot decide the operator meant that guess rather than something else, so
   these remain Intent even where a default value exists. This distinguishes them from truly Derived
   fields like `accepted_actual_types`, where the computed value is *the* right answer, not a guess to
   confirm.

4. **Endpoint fields and connection selection.** `endpoint_type`/`ip_address`/`protocol`/`port` are
   Intent (declares what the endpoint is). `ip_policy` is Intent but has the cross-path default
   contradiction logged in §2 (model `static` vs. import `external`). `dns_name`/`mdns_name` are
   Derived-with-override (auto-filled from the node name, `names.py`). **Connection selection
   itself — which endpoint `DesiredNodeOperationalConfig.local_endpoint`/`tailscale_endpoint` should
   point to, and `connection_path`'s value — is Derived, spanning both models**: a node with exactly
   one usable endpoint has one obvious path (today's live-cluster case, 5/5 nodes); a node with
   several endpoints but exactly one designated primary has a deterministic pick; multiple equally
   plausible endpoints must produce an explicit ambiguity finding, never a silent lexical/arbitrary
   winner. This is the central Phase 2 derivation rule, detailed in §4.

5. **Service requirements/dependencies/placement/desired_state/deployment_profile/config.**
   `requirements`, `min_memory_gb`, `prefers_gpu` are Intent (placement preferences only a human or
   delegated catalog states). `DesiredDependency`'s own reference fields are Intent with a Derived
   `resolution_status`/`resolved_service` (the system matches, doesn't decide, what the dependency
   *is*). `DesiredServicePlacement.desired_state` is Intent (the on/off switch). `deployment_profile`
   is Intent (which mechanism template applies — Ansible cannot guess this). `config` is an Intent
   container keyed by the chosen profile's declared schema (`ansible_agdev/vars/
   deployment_profiles.yml`) — never Derived, since Ansible cannot guess e.g. dnsmasq
   `listen_addresses`. None of this cluster is tier-misclassified; the defect here (discussion.md
   Example 1) is entirely about **visibility of effect**, not authority — Phase 1's job, not a
   reclassification.

6. **Actual-state policy and observed vs. declared hosts.** `actual_state_policy` is Derived: a node
   whose realized object is/should-be nodeutils-observable is `required`; a node whose declared
   platform is known non-observable (today only HAOS, `home_assistant` deployment profile marked
   `observe_only: true` in `deployment_profile_reconciliation`) is `declared`. This is not a coin
   flip the operator should ever be asked — it follows directly from what kind of host this is.
   Decision (detailed in §4): derive from node/placement context; declared-only hosts get an
   explicit override marker rather than being inferred by absence of data.

7. **Expected/declared OS.** `expected_host_os` is Derived from the latest **fresh** nodeutils
   observation (`observed_system` custom field mapped `Linux→linux`/`Darwin→macos`,
   `sources/actual.py:77,91`; freshness enforced by `actual_state_problem`, contract.py:284-302,
   default `ACTUAL_MAX_AGE_HOURS`). `declared_host_os` is Override, used only for `haos` today.
   Missing/stale/unsupported observation must never be guessed — it already has a structured local
   skip path (`_host_actual_skip_reasons`, composer.py:267-296) that Phase 2 reuses rather than
   invents new.

8. **SSH port, power control, laptop behavior.** All three are Override, and are — per the roadmap's
   own words — "the model done right" already: safe defaults (`ansible_port=None` implying the
   downstream Ansible default port, `power_control=none`, `is_laptop=False`), consulted only when
   present. The one correction found is process, not tier: the YAML loader marks `power_control`/
   `is_laptop` as *required* keys (loaders.py:735) even though the model has safe defaults for both,
   so every YAML author must restate the default explicitly. Phase 2 should relax the loader to let
   these two fall through to the model default when absent, matching how the model already behaves.

9. **Reconciliation status/timestamps and import-analysis status/timestamps.** Both families are
   Derived caches written by an external process (nctl's dashboard REST push for
   `reconciliation_status`/`reconciliation_checked_at`; nintent's own Jobs for
   `last_import_status`/`last_imported_at`/`last_import_summary`/`last_analyzed_at`). Decision: the
   `DesiredNode`/`DesiredService` reconciliation-cache fields are already correctly read-only in
   their forms — no change. `IntentSource`'s two form-exposed cache fields are the one genuine
   contradiction (§2), corrected in Phase 4.

10. **IP range policy/lifecycle and dnsmasq projection controls.** `range_policy` is Intent — a human
    states the pool's policy; Ansible/dnsmasq cannot infer whether a range is static, DHCP-reserved,
    DHCP-dynamic, or excluded. `DesiredIPRange.lifecycle` **is** consumed (confirmed this step, not
    left open): it gates dnsmasq range export via the same lenient `ELIGIBLE_NODE_LIFECYCLES` set
    used for node bootstrap export (`dnsmasq.py:367-372`, code `range_lifecycle_not_exportable`),
    which already includes `planned` — so unlike `DesiredNode.lifecycle`, a range at the model
    default is already exportable today, and Phase 3's node-lifecycle default change carries no
    hidden-gate risk here. `generate_dnsmasq`/`dnsmasq_options` are Override, consistent with the
    equivalent `DesiredEndpoint` fields.

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
| `DesiredIPRange.dnsmasq_options` | `lease_time` | Intent/Override | Read at `nctl_core/dnsmasq.py:341`; other keys round-trip via `dnsmasq_query.py:88` without a confirmed consumer traced in this phase — non-blocking, cosmetic |

## 4. Derivation and override rulebook (Step 0.4)

### Common provenance contract

Every derived/default/override output value must carry, at minimum:

- **effective value** — what the system used;
- **source kind** — one of `intent`, `derived`, `default`, `override`;
- **source reference/input summary** — e.g. the endpoint id used, the observation timestamp, the
  override row/field that won;
- **override-won flag** — whether an explicit override replaced a derived/default candidate;
- **finding** — present whenever derivation was impossible or ambiguous (never silently blank).

This is the semantic contract; Phase 2 owns the concrete JSON field names and the production
output-schema version bump that carries it (roadmap.md Phase 2 exit criteria).

### Rulebook

| Value | Inputs | Precedence/algorithm | Missing/stale/ambiguous behavior | Safe default | Override persistence | Output provenance |
|---|---|---|---|---|---|---|
| `DesiredNodeOperationalConfig.actual_state_policy` (target: **derived from the presence of a declared-platform override, not stored as its own field**) | Whether an explicit declared-platform override is set for this node | `declared` if a declared-platform override (see `declared_host_os` row) is present for the node; else `required`. This collapses `actual_state_policy` into a computed fact of `declared_host_os`'s presence rather than an independently-required field — the central simplification this audit recommends for Phase 2 | N/A — always resolvable from override presence; no ambiguity possible | `required` (assume observable until told otherwise) | N/A (derived, not itself overridable — the override lives on `declared_host_os`) | source=`derived`, reference="no declared-platform override present" or "declared_host_os=<value>" |
| `DesiredNodeOperationalConfig.expected_host_os` | Latest nodeutils observation (`observed_system` custom field, `_OBSERVED_SYSTEM_MAP {"Linux":"linux","Darwin":"macos"}`, `sources/actual.py:77,91`); its freshness (`collected_at` vs. generation time, `contract.py:284-302`); whether a realized object exists at all (`actual_type_problem`) | If `actual_state_policy` resolves to `required`: take the latest fresh observation's `observed_system`, normalize via the map | No realized object → `missing_actual_node`-class finding, node stays bootstrap-observable only; stale (`> ACTUAL_MAX_AGE_HOURS`) → `stale_actual_data`; unparseable timestamp → `invalid_actual_timestamp`; present but not `Linux`/`Darwin` → `unsupported_observed_host_os`. **Never guessed** — production composition skips the node locally (`_host_actual_skip_reasons`) in every one of these cases rather than picking a default OS | None (no safe default OS exists) | `declared_host_os` (below) bypasses this entirely | source=`derived`, reference=`observed_system@<collected_at>`; on skip, a finding with the specific code above, no value |
| `DesiredNodeOperationalConfig.declared_host_os` | Operator's explicit declaration (currently only `haos` is a valid value) | Set only when the node's actual platform is known non-observable by nodeutils; drives `actual_state_policy=declared` per the row above | N/A (optional; absence means "not a declared platform", not an error) | Not set (falls through to the observation-based derivation) | This field **is** the override persistence location | source=`override`, reference=the explicit value; override_won=true whenever set |
| `DesiredNodeOperationalConfig.connection_path` + `local_endpoint` + `tailscale_endpoint` | The node's `DesiredEndpoint` rows: which are "usable local" (`_endpoint_is_usable_local` — has a usable IP, or a `dns_name`, or an `mdns_name`) vs. "usable Tailscale" (`endpoint_type=vpn` with a usable IP, `_endpoint_has_usable_ip`); whether any endpoint is designated `endpoint_type=primary` | 1) Exactly one usable-local endpoint and no forced-Tailscale override → `connection_path=local`, `local_endpoint=`that endpoint (today's live case, 5/5 nodes). 2) Multiple usable-local endpoints with exactly one `endpoint_type=primary` → deterministically pick the primary one. 3) A Tailscale/forced path is **never** auto-selected — it is Override-only (below) | 0 usable-local endpoints → node stays bootstrap/mDNS-exportable only (`hosts_intent.py`'s existing mDNS-only path), production connection cannot be derived, structured local finding, no silent fallback. Multiple usable-local endpoints with **no** designated primary → explicit ambiguity finding; never a lexical/arbitrary pick | None when 0 or >1-without-primary; otherwise the single/primary candidate is safe | Explicit `connection_path=tailscale` + an explicitly chosen `tailscale_endpoint`, or an explicit non-default `local_endpoint` pick, is the retained override route | source=`derived`, reference=endpoint id/name/type used for the pick; on override, source=`override`, reference=the operator-chosen endpoint |
| `DesiredNodeOperationalConfig.ansible_port` | none (Override) | Use as given; when absent, downstream Ansible/production composition uses its own implicit default (outside this model's scope) | N/A — optional by design | `None` (implicit downstream default) | This field itself | source=`override` when set, else absent (no derived value asserted) |
| `DesiredNodeOperationalConfig.power_control` | Platform (`expected_host_os`/`declared_host_os`) constrains the *valid* set (`allowed_power` in `clean()`, models.py:750-756) but does not choose a value | Model default `none` is always safe; loader should stop requiring it explicitly (§2 finding — a process fix, not a derivation change) | An invalid combination for the resolved platform is a target-local validation finding (`clean()` already enforces this) | `none` | This field itself | source=`default` when using `none` with no explicit input, `override` when explicitly set |
| `DesiredNodeOperationalConfig.is_laptop` | none (Override) | Use as given | N/A | `False` | This field itself | source=`default`/`override` |
| `DesiredNode.accepted_actual_types` | `node_type` | `_ACTUAL_TYPE_DEFAULTS[node_type]` (e.g. `device`→`["device"]`) unless explicitly overridden | N/A — every `node_type` has a default mapping | per-`node_type` default | Explicit list in form/YAML/REST | source=`derived`, reference=`node_type`; source=`override` when the list differs from the type default |
| `DesiredEndpoint.dns_name` / `mdns_name` (for the node's `primary`/`primary` endpoint only) | `DesiredNode.name` | `default_dns_name(name)` / `default_mdns_name(name)` (`names.py`) when the endpoint is primary/primary and the field is unset | Non-primary endpoints or an explicitly-set value are never auto-filled | Computed from node name | Explicit `dns_name`/`mdns_name` value | source=`derived`, reference=node name; source=`intent` when explicitly set |
| `DesiredNode.realized_device` / `realized_vm` | Actual-ledger Device/VM candidates matching this desired node (nodeutils ingest → Nautobot) | `link_actual_node` `AUTOMATIC` reconciler (`reconcile/classify.py:57`); ambiguity is already a `MANUAL_REVIEW` code (`ambiguous_actual_node_candidates`), absence is `missing_actual_node`/`no_realized_object` | Multiple candidates → `ambiguous_actual_node_candidates` (manual review, no arbitrary pick); none → `missing_actual_node` | None (no link) | Manual form edit is the de facto correction path for a wrong automatic link | source=`derived` (reconciler-linked) or `override` (manually corrected via form) — **currently unlabeled**, a Phase 2 provenance gap |
| `DesiredEndpoint.realized_ip_address` | `DesiredEndpoint.ip_address`/`dns_name`/`ip_policy`, actual IPAM ledger state | `reconcile_ipam` `AUTOMATIC` reconciler (`operations/ipam.py` plan → `create_ip_address`/`link_ip_address` actions) | Conflicting/ambiguous IPAM state → existing `MANUAL_REVIEW` codes (`missing_ip_policy_range`, `ambiguous_ip_policy_range`, `ip_policy_range_mismatch`, etc.) | None (no link) | Manual form edit | Same unlabeled-provenance gap as `realized_device` |
| `DesiredDependency.resolution_status` / `resolved_service` | `raw_ref`/`dependency_kind`/`namespace`/`name` matched against known `DesiredService` rows | System match: 0 candidates → `unresolved`; exactly 1 → `resolved` + `resolved_service` set; declared out-of-repo → `external`; explicitly suppressed → `ignored` | No unique match → stays `unresolved`, visible as such | `unresolved` | `resolution_status=external`/`ignored` are themselves the override/exception route | source=`derived` for `resolved`, `intent`/`override` for `external`/`ignored` |
| `DesiredService.catalog_lifecycle` | Source catalog entity's own `spec.lifecycle` string | Verbatim copy at analysis time (importers.py:92) | Absent in source → stays blank, not an error | blank | N/A (purely descriptive) | source=`derived` (imported), reference=catalog entity |
| `IntentSource.{last_import_status,last_imported_at,last_import_summary}`, `DesiredService.last_analyzed_at`, `{DesiredNode,DesiredService}.{reconciliation_status,reconciliation_checked_at}` | The owning Job/nctl run's own outcome | Last-write-wins by the sole writer (`AnalyzeIntentSources`/`ImportIntentSources` Jobs; nctl `dashboard/push.py`) | Blank/null = "never run yet", itself informative, not an error state | blank/null | N/A (pure cache, no override concept applies) | source=`derived`, reference=the run id/timestamp that wrote it |
| `DesiredServicePlacement.config_schema_version` / `assignment_source` | none (Override, already correct) | Model default (`"1"`/`"manual"`) unless the creation path states otherwise | N/A | `"1"` / `"manual"` | Explicit value (YAML/import already stamps `"yaml"`/`"generated"`/`"policy"` when applicable — **`"generated"` and `"policy"` are reserved choice values with no current writer**, presumably intended for a future auto-placement/policy-engine feature) | source=`default`/`override` |

### Minimum scenario matrix (roadmap-required)

| Scenario | Required policy decision | Where enforced today / to be enforced |
|---|---|---|
| Fresh observed Linux/macOS with one usable primary endpoint | Ordinary derived production input: `actual_state_policy=required`, `expected_host_os` from observation, `connection_path=local` from the sole endpoint | Matches all 5 live nodes today; Phase 2 derivation rules above |
| Fresh node known only by mDNS, no actual object yet | Bootstrap observation remains possible (`hosts_intent.py` mDNS-only export); production waits locally (`missing_actual_node`/`no_realized_object`, already `MANUAL_REVIEW`/skip-classified) | Already correct; Phase 2 must not regress it |
| Missing/stale/unsupported observed OS | Never guess; structured local finding (`missing_actual_data`/`stale_actual_data`/`unsupported_observed_host_os`) and observation/review path | Already implemented in `contract.py`/`composer.py`; Phase 2 reuses, doesn't reinvent |
| Declared/non-observable host such as HAOS | Explicit override (`declared_host_os=haos`) and validation (`clean()` already enforces the cross-field rules) | Retained override shape (§ decision below) |
| Exactly one usable endpoint | Deterministic local endpoint/path derivation | New in Phase 2 (currently a required manual field) |
| Multiple endpoints with exactly one designated primary | Deterministic designated-primary rule | New in Phase 2 |
| Multiple equally plausible endpoints | Explicit ambiguity finding; no lexical/arbitrary winner | New in Phase 2 |
| Forced Tailscale or non-standard SSH port | Optional override and visible provenance | Retained override shape; provenance labeling new in Phase 2 |
| Unsafe OS/power combination | Target-local validation/finding, never silent coercion | Already enforced by `DesiredNodeOperationalConfig.clean()`'s `allowed_power` check; Phase 2 must preserve this validation in whatever shape replaces the model |

### Phase 2 persistence-shape decision

**Dissolve wins**, confirmed by this audit (roadmap's own favored default, now backed by concrete
evidence rather than assumption):

- Every ordinary-case value in the rulebook above (`actual_state_policy`, `expected_host_os`,
  `connection_path`, `local_endpoint`) is fully computable from data the system already owns
  (`DesiredEndpoint` topology + the actual-ledger observation), with `actual_state_policy` reducible
  to a fact *about* `declared_host_os` rather than needing its own storage at all.
  `DesiredNodeOperationalConfig` currently has **zero rows in the live cluster** and exactly one
  programmatic creation path (the YAML import Job) — there is no persisted-row value being relied
  upon anywhere today to justify keeping the required model.
- What survives as **named override fields** (not a whole required model): `declared_host_os`
  (drives the `declared` policy), `tailscale_endpoint` + forced `connection_path=tailscale`, a
  forced non-default `local_endpoint`, `ansible_port`, `power_control`, `is_laptop`. These are
  exactly the fields the roadmap and this audit agree are "the model done right" already — Phase 2
  should persist them as an optional one-to-one override record (same shape, `OneToOne` to
  `DesiredNode`, but every field genuinely optional with the whole row itself optional, i.e. no row
  = "use pure derivation"), not delete the concept, only its required-ness.
- `nintent_operational_config_id` (contract.py `_BASE_HOST_VARIABLES`) must be replaced or removed
  from the production output contract per roadmap instruction once the row is no longer guaranteed
  to exist; a stable derived host identifier (`nintent_desired_node_id`, already present) already
  covers the same provenance need.
- This decision must be re-confirmed, not silently assumed, if a later phase's implementation work
  finds a concrete case the derivation can't handle safely — but no such case was found in this
  audit's live-cluster/scenario-matrix review.

## 5. Reader/writer matrix — writer boundaries (Step 0.2)

One row per creation/update ingress boundary, not one vague "nintent" row. Reader boundaries
(runtime consumers) are appended in §5b (Step 0.5).

| Boundary | Read/write | Fields/models | Current behavior/default | Required change | Owning phase/tests |
|---|---|---|---|---|---|
| Nautobot regular `ModelForm` CRUD (`forms.py` + `views.py` `ObjectEditView` quads + `urls.py`) | Write | All 8 models except the Quick-Add-only fields; every model has a form | Each `Meta.fields` list is the single source of truth for what's editable per model; two Job-managed `IntentSource` cache fields (`last_import_status`, `last_import_summary`) are wrongly included (see §2) | Remove the two cache fields from `IntentSourceForm.Meta.fields` | Phase 4; test: form rejects/ignores those fields |
| Quick Add form + view (`DesiredHostQuickAddForm`, `DesiredHostQuickAddView`, `operations.hosts.create_desired_node_with_primary_endpoint`) | Write | `DesiredNode` (`name`, `slug`, `node_type`, `accepted_actual_types` hidden, `lifecycle`, `role`, `description`, `intent_source`) + `DesiredEndpoint` (`ip_address`, `dns_name`, `mdns_name`, `vpn_dns_name`, `protocol`, `port`, `generate_dnsmasq`, `ip_policy`, `dnsmasq_record_type`, hidden `endpoint_name`/`endpoint_type`) in one atomic transaction | This is the sole node+endpoint creation path in the app; independently hard-codes `node_type=virtual_machine`, `lifecycle=planned`, `generate_dnsmasq=True`, `ip_policy=dhcp_reserved` as its own defaults, disagreeing with model defaults in 3 of those 4 cases (§2) | Change `lifecycle` default to `active` (Phase 3); reconcile `node_type`/`generate_dnsmasq` default disagreement (Phase 4); no `DesiredNodeOperationalConfig` is created here today — Phase 2 must decide whether Quick Add should trigger derivation immediately or leave it to first render | Phase 2 (operational-config trigger) + Phase 3 (lifecycle) + Phase 4 (default reconciliation) |
| `operations/ipam.py` | Read-only planning | Reads `DesiredEndpoint.ip_address/dns_name/ip_policy/realized_ip_address`; writes nothing on the 8 audited models (it returns a plain-dict constructor payload for an **actual** `IPAddress`, consumed elsewhere) | Confirms no direct write path for `DesiredIPRange`/`DesiredEndpoint` exists here — the write happens later, in the `ReconcileDesiredIPAMIntent` Job below | None needed; documented so a future change doesn't assume this file writes ledger fields | — |
| intent-catalog REST (`api/serializers.py` + `api/views.py` + `api/urls.py`) | Read/write | Only `DesiredNode`, `DesiredService`, `DesiredEndpoint` have a `NautobotModelViewSet`/`NautobotModelSerializer` (`fields = "__all__"`); **`IntentSource`, `DesiredDependency`, `DesiredServicePlacement`, `DesiredNodeOperationalConfig`, `DesiredIPRange` have zero REST routes** | This is intentional today for the REST-exposed 3 (nctl's dashboard push depends on it, §5b); the absence of routes for the other 5 is a route-not-yet-needed gap, not a bug | Phase 2's chosen persistence shape for operational-config overrides must decide whether it needs a REST route (a future `nctl` promotion/override command would need one if it writes over HTTP rather than only via Django admin/YAML) | Phase 2 (only if the override shape needs REST) |
| YAML dataclasses + normalization (`loaders.py`, 1185 lines) | Parse/validate, produces plain dataclasses, not a DB write itself | All 8 models' YAML shape; independently hard-codes some defaults (`lifecycle="planned"` at 2 sites, `node_type`/`accepted_actual_types` defaults, `ip_policy` fallback to `"external"`) that duplicate-and-sometimes-disagree-with model defaults (§2) | See per-field contradictions already logged in §2; this file is the actual source of truth for "what happens when a YAML author omits a key" | Batch with Phase 2/3 nintent changes | Phase 2 + Phase 3 |
| `importers.py` (defaulting layer between loader dataclasses and Django model kwargs) | Produces model-kwargs dicts, not a DB write itself | Adds its own defaults on top of the loader's (`requirements`/`placement_policy` hard-coded `{}`, `namespace`/`resolution_status`/`dependency_type` fallbacks, DNS/mDNS auto-fill via `names.py`, `ip_policy or "external"` repeated fallback) | Two-layer defaulting (loader dataclass default, then importer default) for several fields is itself a minor legibility problem — it's not always obvious which layer "owns" a given no-input default | Phase 4 could consolidate to one defaulting layer per field as a non-blocking cleanup | Phase 4 |
| `ImportIntentSources` Job (`jobs.py:114-162`, `_import_intent_rows` `jobs.py:474-603`) | Write (upsert, `transaction.atomic()`) | Creates/updates, in order: `IntentSource`, `DesiredNode`, `DesiredIPRange`, `DesiredEndpoint`, `DesiredService`, `DesiredServicePlacement`, `DesiredNodeOperationalConfig` via `_validated_upsert` (`model(**identity)` + `setattr` + `full_clean()` + `save()`, jobs.py:606-619); also bulk-disables missing `IntentSource` rows (`disable_missing` option, jobs.py:514-520) | **This is the only place in nintent that ever instantiates a `DesiredNodeOperationalConfig` row programmatically** | Every creation-ingress change for Phase 3 (`lifecycle` default) must be applied here too, since this is a first-class creation path, not just UI | Phase 2 + Phase 3; tests: `test_jobs_import.py` |
| `AnalyzeIntentSources` Job (`jobs.py:165-248`) | Write | `IntentSource.last_import_status/last_imported_at/last_import_summary` (targeted `save(update_fields=...)`); `DesiredService.last_analyzed_at` + `update_or_create` of analysis-derived services (`lifecycle` hard-coded `"proposed"`, `placement_policy={}`); unconditional delete+recreate of all `DesiredDependency` rows per service | The dependency delete+recreate has no diffing — any manually-added `DesiredDependency.notes`/`resolution_status` edit is destroyed on the next analysis run | Not currently flagged by the roadmap; note as a residual finding — manual edits to Job-owned rows should either be protected or the Job should diff instead of blind-recreate | Phase 4 (residual, non-blocking) |
| `ReconcileDesiredIPAMIntent` Job (`jobs.py:251-346`, `_apply_ipam_reconcile_plan` jobs.py:388-437) | Write | `DesiredEndpoint.realized_ip_address` only (`save(update_fields=["realized_ip_address"])`) | This is the `reconcile_ipam` `AUTOMATIC` reconciler's actual ledger write | None | — |
| Seed/example YAML (`nauto/seed/intent_sources.yaml`, `nauto/seed/home_cluster.yaml`) | Data, consumed by `ImportIntentSources` | `intent_sources.yaml`: 9 nodes (`lifecycle: active`, explicit), 9 endpoints, 6 placements (`desired_state: active`, `assignment_source: yaml`, `config_schema_version: "1"` all explicit), 9 operational configs (full example coverage of `required`+linux/macos and `declared`+haos); `home_cluster.yaml`: 5 services (`lifecycle: active` explicit) | **The example/seed data already assumes the Phase 3 target state** (`lifecycle: active` everywhere) even though the live cluster (loaded via a different, presumably earlier, import) is all `planned` — the seed files are aspirational fixtures, not what actually got imported live | None — documents that Phase 3's default change won't break these fixtures; they already model the target behavior | — |
| `nauto/seed/service_repositories.yaml` | Dead/rejected input | Uses the legacy top-level key `service_repositories:`, which `loaders.load_intent_sources` explicitly rejects (loaders.py:230-234) | This file would fail to load as written today | Phase 4 recipe sweep should either update or remove this stale fixture | Phase 4 |
| nctl REST write-back (`nctl_core/dashboard/push.py`) | Write | `DesiredNode.reconciliation_status/reconciliation_checked_at`, `DesiredService.reconciliation_status/reconciliation_checked_at` via `PATCH /api/plugins/intent-catalog/{nodes,services}/{id}/` | Degrades-never-fails by design (`StatusPushData`); a target kind with no ledger row (anything but `node`/`service`) is silently counted `skipped_no_row`, which is itself visible in the dashboard push summary, not hidden | None | — |
| Admin/shell-only paths | Write (manual, no UI/API) | `DesiredNodeOperationalConfig` has no REST ViewSet and no `operations.py` constructor — its only creation paths are the `NautobotModelForm`/`ObjectEditView` CRUD or the YAML import Job above | Confirms discussion.md Example 3's "no creation path" claim precisely; there is no Django `admin.py` in this app either (none found) | Phase 2's dissolution decision removes the need for this path entirely for the ordinary case; only the override remainder needs *a* path, chosen in Phase 2 | Phase 2 |

## 5b. Reader/writer matrix — runtime consumer boundaries (Step 0.5)

| Boundary | Read/write | Fields/models | Current behavior/default | Required change | Owning phase/tests |
|---|---|---|---|---|---|
| `nctl_core/sources/desired.py` (GraphQL query + typed snapshot) | Read | All 8 models, every field enumerated in §2 (this is the single ingestion point all of nctl reads from) | One GraphQL query, one typed `DesiredSnapshot`; choice fields lowercased centrally (`_lower`) | Adding provenance (§4) or bumping the operational-config shape (Phase 2) means extending this query/snapshot — it is the one place that must change for any new field | Phase 2; tests: existing `sources/desired.py` fixtures |
| `production/adapter.py` | Read | Joins `operational_configs`/`placements`/`actual.devices` by `node_id`; builds `EndpointInput`/`OperationalConfigInput`/`PlacementInput`, **dropping** `instance_role`, `endpoint_id`, `service_id`, `assignment_source` from placements and `desired.py`'s `node_id` from operational configs (folded into `NodeInput.id`) | Confirms which fields survive into production composition at all — a field absent here can never affect a host regardless of what's declared in nintent | Phase 2's dissolved-model adapter must still populate whatever the new optional override shape provides | Phase 2 |
| `production/composer.py` | Read | `is_production_eligible` (node lifecycle+type gate), `_host_actual_skip_reasons` (actual-state skip), `evaluate_platform_policy`/`resolve_connection_variables`/`map_placement_config`/`merge_host_variables` (contract.py helpers) | See §6 for the full failure-scope classification of every `ContractError`/skip path here | Phase 1 (local-fail `missing_operational_config`) + Phase 2 (derivation replaces the operational-config lookup) | Phase 1 + Phase 2 |
| `drift/comparators.py` + `drift/evaluation.py` + `drift/evaluation_snapshot.py` + `drift/service_placement.py` | Read | `node_existence` reads `operational_configs`/`realized_device_id`/`realized_vm_id`; `production_policy` re-runs the composer and surfaces its skips/drift as diffs; `evaluate_node_intent`/`evaluate_endpoint_intent`/`evaluate_service_intent` read `expected_spec`, `lifecycle` (service only), `ip_policy`/`dns_name`/`generate_dnsmasq`, dependency resolution; `evaluate_active_placement` reads `actual_state_policy`/`expected_host_os`/`deployment_profile`/`instance_name` (never `config`) | `DesiredNode.lifecycle` is **not** read anywhere in `evaluation.py` for gating (only captured as a descriptive fact) — the drift engine's own node-level checks are lifecycle-agnostic; only `production_policy` (via the composer) is lifecycle-sensitive | None required by drift itself for Phase 3's default change; Phase 2 changes what `operational_configs` looks like, which this layer must follow | Phase 2 (follow adapter/composer changes) |
| `reconcile/executor.py` (`_group_hosts_by_playbook`) | Read | `expected_host_os` (precedence) then `declared_host_os` (fallback) from `snapshot.desired.operational_configs`, keyed by node id, to select `playbook_by_os` | `connection_path`/`local_endpoint`/`tailscale_endpoint`/`ansible_port`/`power_control`/`is_laptop` are **not read anywhere in `reconcile/`** — OS-playbook selection is the only reconcile-time consumer of the operational-config cluster; everything else's consumption is entirely inside `production/composer.py` at render time | Phase 2's derived `expected_host_os`/`declared_host_os` must still resolve here identically; no interface change needed if the typed snapshot shape is preserved | Phase 2 |
| `production/contract.py` (schema + host variables) | Read (validates) / defines schema | `PRODUCTION_INVENTORY_SCHEMA_VERSION="1.0"`; `_BASE_HOST_VARIABLES` (14 keys, §2/§4); `_REPORT_KEYS`; no field ties a host record back to `IntentSource`/catalog origin today | Phase 2 must bump `PRODUCTION_INVENTORY_SCHEMA_VERSION` when it changes `nintent_operational_config_id` and adds provenance fields (§4's common contract) | Phase 2 |
| **Downstream Ansible consumption of `_BASE_HOST_VARIABLES`** (traced this step, `ansible_agdev/{playbooks,roles,templates}`, excluding `inventories/generated/`) | Read | Confirmed genuinely branched-on in playbook/role logic: `host_os` (`playbooks/power/{generate,deploy}_home_assistant_power_switches.yml:63-68`, `roles/nomad_client_macos/defaults/main.yml:47`), `power_control` (same power-switch playbooks), `is_laptop` (`playbooks/bootstrap/linux_initial_setup.yml:11`, `when: is_laptop \| default(false) \| bool`), `local_ip`/`mac_address`/`network_interface` (6/3/6 files respectively — WoL and interface-targeting roles). **Metadata-only / not branched on by any playbook task**: `connection_path` (only appears as a literal hardcoded string in a template, `templates/home-assistant-power-switches.yaml.j2:28,35` — the exported inventory value itself is never read), `tailscale_ip` (only in docs/generated group_vars, no playbook logic), `nintent_desired_node_id`/`nintent_operational_config_id`/`nautobot_device_id`/`nintent_active_placement_ids` (0 hits anywhere in `ansible_agdev` source — pure provenance for humans/nctl, confirming `contract.py`'s own docstring claim). `ansible_port` is consumed by the Ansible **engine** itself (the reserved per-host connection variable), not by any playbook task — its 0 in-playbook hit count is expected, not a gap | None required for Phases 1–3; Phase 2 should note that removing/renaming `nintent_operational_config_id` is safe precisely because no playbook reads it | Phase 2 (informs the deletion list below) |
| nintent internal readers: `views.py`/`tables.py`/`filters.py` (display only), templates, tests, README, migrations | Read | UI display and filtering only; already inventoried per-field in §2 | No behavior beyond rendering | Phase 3/4 changes to `lifecycle`/operational-config must update fixtures in `tests/` accordingly | Phase 2 + Phase 3; tests: `nautobot_intent_catalog/tests/*` (88 passing today) |

### Transition impact map

For each target schema change identified above:

| Change | Django migration | Existing-row policy | Output/envelope schema bump | Coordinated deploy order & rollback point | Deletion list |
|---|---|---|---|---|---|
| **`DesiredNode.lifecycle` default → `active`** (Phase 3) | `AlterField` changing the field default only (no data migration — Django field defaults apply only to future INSERTs) | Explicit: the roadmap's own instruction stands — do **not** silently promote the 5 currently-`planned` live nodes; use the new promotion/demotion CLI (Phase 3 deliverable) as a reviewed one-time action, or an intentional data migration if the operator prefers that instead | None (no nctl output schema depends on the field's default, only its value, which is already read) | nintent-only change (model default + the 4 other hard-coded sites in forms.py/hosts.py/loaders.py) → commit → push → `docker compose build` → restart Nautobot; nctl needs no matching change since it already reads whatever `lifecycle` value is present. Rollback point: revert the nintent commit and rebuild; no nctl rollback needed since nctl made no matching change | None (no field/model removed) |
| **`DesiredNodeOperationalConfig` dissolution → optional override record** (Phase 2) | `DeleteModel` for the required model (or `AlterField` making every field nullable + the row itself optional, depending on final Phase 2 implementation plan) retained in migration history per roadmap's "normal migrations still required" premise | Zero live rows today (confirmed) — no data-loss risk; no transition logic needed for existing data, only for the 9-row seed fixture (`nauto/seed/intent_sources.yaml`), which must be re-authored to the new override-only shape in the same change | `PRODUCTION_INVENTORY_SCHEMA_VERSION` bump (`contract.py:31`, currently `"1.0"`) to add provenance fields and to replace/remove `nintent_operational_config_id` from `_BASE_HOST_VARIABLES` | **Coordinated breaking rollout** (roadmap's own rule): land the nintent schema change and the nctl composer/adapter/GraphQL change together, test both sides against each other before either ships, have the user push nintent → rebuild/restart Nautobot → then run the matching nctl revision. Rollback point: keep the pre-dissolution nctl revision runnable against the pre-dissolution nintent schema until the coordinated cutover is verified; do not run mixed versions as a steady state | Old model's admin-equivalent form/view/URL entries if the model is fully replaced rather than field-relaxed; `nintent_operational_config_id` from `_BASE_HOST_VARIABLES`; the `loaders.py`/`importers.py`/`jobs.py` strict-required validation for the dissolved fields (`actual_state_policy`, `connection_path` as user-supplied YAML keys) |
| **`ip_policy`/`node_type`/`generate_dnsmasq` cross-path default reconciliation** (Phase 4) | None (behavior-only; no schema change, only which literal default each code path uses) | N/A | None | nctl-independent; nintent-only code change (forms.py/hosts.py/loaders.py/importers.py), no rebuild-coordination needed beyond the normal nintent push/rebuild cycle | None |
| **`missing_operational_config` global → node-local skip** (Phase 1) | None (`nctl`-only, no nintent schema involved) | N/A | New skip reason code integrated into `_host_actual_skip_reasons` and a new/updated `reconcile/classify.py` entry (§6) — this is itself effectively superseded once Phase 2 removes the field's required-ness, but Phase 1 ships first per the roadmap's sequencing rationale and must still handle the interim required-field state correctly | `nctl`-only, no coordinated nintent rollout | None |
| **Placement `config` "recorded but not applied" finding** (Phase 1) | None | N/A | New drift/status code, classified in `reconcile/classify.py` (§6) | `nctl`-only | None |
| **`IntentSourceForm` removes two Job-managed cache fields** (Phase 4) | None (form `Meta.fields` change only) | N/A | None | nintent-only | None (fields stay on the model, just not form-editable) |

## 6. Failure-scope matrix for Phase 1 (Step 0.6)

Every `raise ContractError(...)` reachable from `compose_production_inventory` (`production/composer.py` +
`production/contract.py`), inventoried exhaustively by grep (57 call sites total: 1 in composer.py,
56 in contract.py). Grouped by where in the composition pipeline each is raised, per
`composer.py`'s own docstring split ("global contract violations... abort the whole
run... host-specific actual state problems skip only the affected host").

**Critical integration finding, central to this section:** today, *every* `ContractError` —
regardless of which group below it falls in — is caught only at the outermost boundary
(`production_render.py:73-82`, `drift/comparators.py:185-201`) and converted into a single
`Target(kind="global")` diff. Because `reconcile/classify.py`'s `classify()` sends any
`Target.kind == "global"` diff straight to `_GLOBAL_CLASSIFICATION` (always `MANUAL_REVIEW`) without
ever consulting the per-code `CODE_CLASSIFICATION` table, **none of the 15 target-scoped codes in
Group C below currently reach that table at all.** The moment Phase 1 changes any of them to a
`Target(kind="node")` (or a new placement-scoped kind), `classify()` will look the code up in
`CODE_CLASSIFICATION` for the first time — and because none of them are registered there today,
every one would raise `UnclassifiedDiffCodeError` (classify.py:138-146) unless Phase 1 adds them.
This is the concrete mechanism behind the roadmap's own warning ("moving `missing_operational_config`
… changes it from the global blanket classification to a code that must be explicitly classified…
do not let it become an `UnclassifiedDiffCodeError`") — and it applies to all 15 codes, not only the
one the roadmap names by example.

### Group A — shared deployment-profile schema (correctly global; raised by `validate_deployment_profiles`, before the per-node loop, composer.py:161)

| Code | Origin (contract.py) | Scope | Required scope | Reconcile handling owner |
|---|---|---|---|---|
| `invalid_profile_json`, `invalid_profile_map`, `invalid_profile`, `duplicate_profile_group`, `unsupported_profile_schema`, `invalid_profile_variables`, `invalid_profile_variable`, `invalid_ansible_variable`, `duplicate_variable_assignment`, `unsupported_profile_type`, `invalid_profile_required`, `invalid_profile_item_type`, `unexpected_profile_items` | `validate_deployment_profiles` and its helpers (contract.py:110-190) | Global — malformed `ansible_agdev/vars/deployment_profiles.yml` affects every node/placement, no single target owns it | Stays global (`Target(kind="global")`, `MANUAL_REVIEW` via `_GLOBAL_CLASSIFICATION`) — no change needed | Unchanged |

### Group B — final closed-output-contract validation (correctly global; raised after the per-node loop, composer.py:262-263)

| Code | Origin (contract.py) | Scope | Required scope | Reconcile handling owner |
|---|---|---|---|---|
| `invalid_inventory_schema`, `dangling_group_member`, `invalid_report_schema`, `invalid_contract_keys`, `invalid_slug`, `unsupported_inventory_schema`, `invalid_generation_id`, `invalid_generated_at`, `invalid_report_path`, `invalid_profile_digest`, `invalid_connection_address` (when raised during document-level IP normalization), `unknown_host_variable`, `invalid_group_member` | `validate_production_inventory_document` / `validate_production_report` (contract.py:370-540) | Global — corruption of the fully-assembled document/report, not attributable to one node | Stays global | Unchanged |

### Group C — per-node/per-placement composition (currently global by accident; Phase 1's actual work)

| Code | Origin | Target kind/evidence | Required scope | Reconcile handling owner |
|---|---|---|---|---|
| `missing_operational_config` | composer.py:185-188, node loop | `node`, evidence = `node.slug` | **Local** — one node's missing config skips only that node (roadmap's flagship example) | **NEW**: register in `CODE_CLASSIFICATION` as `MANUAL_REVIEW` (operator must add/complete the config — or, once Phase 2 ships, this code disappears entirely since the field is no longer required) |
| `invalid_actual_state_policy` | `evaluate_platform_policy`, contract.py:258,272,275, called from `_compose_host` (composer.py:313-319) | `node` | Local | **NEW**: `MANUAL_REVIEW` |
| `unsupported_observed_host_os` | `evaluate_platform_policy`, contract.py:260 | `node` | Local | **NEW**: `MANUAL_REVIEW` (a human must fix the observation source or add a `declared_host_os` override — not an `OBSERVATION`-reconciler-fixable code, since a re-observation of a genuinely unsupported OS won't change the outcome) |
| `invalid_platform_power` | `evaluate_platform_policy`, contract.py:277 | `node` | Local | **NEW**: `MANUAL_REVIEW` |
| `endpoint_node_mismatch` | `validate_endpoint_ownership`, contract.py:239, called from `_validated_endpoint` (composer.py:375) | `node` (or `endpoint`, since the mismatch is between two records) | Local | **NEW**: `MANUAL_REVIEW` |
| `unresolved_connection_path` | `resolve_connection_variables`, contract.py:338, called composer.py:323-330 | `node` | Local | **NEW**: `MANUAL_REVIEW` |
| `invalid_connection_path` | `resolve_connection_variables`, contract.py:341 | `node` | Local | **NEW**: `MANUAL_REVIEW` |
| `invalid_connection_address` | `resolve_connection_variables` → `_normalize_ip`, contract.py:547, when raised for a specific node's endpoint address (as opposed to the document-level use in Group B) | `node` | Local | **NEW**: `MANUAL_REVIEW` (this code's dual raise sites mean Phase 1 must distinguish *which* call site fired it — the per-node one is local, the document-level one in Group B stays global; do not blanket-classify by code name alone) |
| `unknown_profile` | `map_placement_config`, contract.py:204, called from `_compose_host`'s per-placement loop (composer.py:356-361) | **Placement-scoped, not node-scoped** — a specific `DesiredServicePlacement` names a profile that doesn't exist; Phase 1 must decide whether `Target.kind` is `"node"` (attributed to the host it would have landed on, matching `production_policy`'s existing skip-reason pattern) or a new `"placement"` kind — Phase 0 flags this choice explicitly rather than presuming one | Local (to the one placement/node) | **NEW**: `MANUAL_REVIEW`; Phase 1 implementation plan must settle the `Target.kind` question before adding this to `CODE_CLASSIFICATION` |
| `unsupported_config_schema` | `map_placement_config`, contract.py ~207-210 | Placement-scoped (same open question as `unknown_profile`) | Local | **NEW**: `MANUAL_REVIEW` |
| `invalid_placement_config` | `map_placement_config`, contract.py:212 | Placement-scoped | Local | **NEW**: `MANUAL_REVIEW` |
| `unknown_config_key` | `map_placement_config`, contract.py:216 | Placement-scoped | Local | **NEW**: `MANUAL_REVIEW` |
| `missing_required_config` | `map_placement_config`, contract.py:221 | Placement-scoped | Local | **NEW**: `MANUAL_REVIEW` |
| `invalid_profile_value_type` | `map_placement_config`, contract.py ~226-230 | Placement-scoped | Local | **NEW**: `MANUAL_REVIEW` |
| `conflicting_host_variable` | `merge_host_variables`, contract.py:353, called composer.py:365 | `node` — roadmap's own rule: "a conflict between two assignments on one host is local to that host, even if the current merge helper raises a generic `ContractError`" | Local | **NEW**: `MANUAL_REVIEW` |

### New "recorded but not applied" finding (Phase 1, discussion.md Example 1)

Not a `ContractError` today — does not exist yet. Required per roadmap Phase 1 ("Surface
ignored/derived intent"): whenever a `DesiredServicePlacement` is `desired_state=active` on a node
that is *not* `PRODUCTION_ELIGIBLE_LIFECYCLES`-eligible, emit a visible finding rather than silence,
including the placement/config evidence even when `config == {}}` (discussion.md's exact dnsmasq-
loopback scenario).

| Code (proposed) | Target kind/evidence | Severity | Reconcile handling owner |
|---|---|---|---|
| `placement_config_not_applied` (name TBD by Phase 1's implementation plan; must not collide with existing codes) | `node` (or `service`), evidence = placement id/instance_name + the node's current lifecycle + the `config` value that isn't taking effect | `WARNING` (matches drift's existing severity for a "the system chose not to enforce this yet" class of finding, e.g. `ingest_lag`) | **NEW**: `MANUAL_REVIEW` — the only fix is a human decision (promote the node, or accept the placement is intentionally inert); reconcile cannot automatically act on it |

### Existing correctly-local skip-reason codes (for contrast — already right, not part of Phase 1's fix list)

`_host_actual_skip_reasons` (composer.py:267-296) already returns a `list[str]`, not an exception,
and is already surfaced as a per-node entry in the report's `"skipped"` array (composer.py:190-204,
256) rather than aborting anything: `no_realized_device` / `unsupported_actual_type`
(`actual_type_problem`), `missing_actual_data` / `stale_actual_data` / `invalid_actual_timestamp`
(`actual_state_problem`), `missing_observed_system` / `missing_mac_address` /
`missing_network_interface` (`missing_required_facts`, keyed by consumer — `host_os` needs
`observed_system`, `wol` needs `mac_address`, `network_interface` needs `network_interface`). All
of these already appear in `reconcile/classify.py`'s `_OBSERVATION_CODES` group
(`reconciler_id="observe_node"`) — this is the pattern Group C's 15 codes should be integrated
alongside, per roadmap's explicit instruction ("matching the existing
`_host_actual_skip_reasons` pattern"), even though most of Group C is a data-correction problem
(`MANUAL_REVIEW`) rather than an observation-freshness problem (`OBSERVATION`).
