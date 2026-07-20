# Better Usability Phase 2 Implementation Plan: Derived Node Operations, Explicit Overrides

Parent: [roadmap.md](../roadmap.md) — Phase 2. Rationale:
[discussion.md](../discussion.md). Authoritative classification and derivation rules:
[p0/field-classification.md](../p0/field-classification.md), especially §4 (derivation and
provenance), §5/§5b (readers, writers, and transition impact), §6 (failure scope), and §8
(Phase 2 assignment). Phase 1 prerequisite and current local-failure behavior:
[p1/plan.md](../p1/plan.md) and [p1/report1.7.md](../p1/report1.7.md).

## Goal

Remove `DesiredNodeOperationalConfig` as required user input. For the common case, a node with a
placement, a usable endpoint, and a fresh nodeutils observation must render and actuate without an
operational-config row:

1. derive observed/declared policy and host OS from an optional declared-platform override plus
   fresh actual evidence;
2. derive the local connection path and endpoint deterministically from the node's endpoints;
3. retain only genuine exceptions in an optional `DesiredNodeOperationalOverride` row;
4. expose every effective value with its source, source reference, and whether an override won;
5. keep missing, stale, unsupported, ambiguous, and invalid target-owned inputs local to their
   node through render, drift, dashboard, and reconcile; and
6. remove the old model, GraphQL/YAML/UI surface, output field, and dead diff vocabulary outright.

This is one coordinated breaking rollout across `nintent` and `nctl`. It also updates the `nauto`
seed and current user-facing nintent/nauto documentation. It does not change node lifecycle
defaults; that remains Phase 3.

## Current state (after Phase 1, 2026-07-20)

- Phase 1 is complete. Its final baseline is **569 passing nctl tests**; Phase 0's unchanged
  nintent baseline is **88 passing tests**.
- The live development ledger has five `DesiredNode` rows, zero
  `DesiredNodeOperationalConfig` rows, and all five nodes remain `planned`. The absence of live
  operational rows means the schema replacement needs no live data copy, but the deployment must
  still assert that count immediately before migration.
- Phase 1 already turns every audited node/placement-owned composition failure into a structured
  node-local finding and allows unrelated healthy-target work to continue. Phase 2 must reuse that
  path for derivation failures rather than introduce a new report/error channel.
- `nctl_core.sources.desired` currently fetches the required model through the GraphQL root
  `desired_node_operational_configs`; `production.adapter` joins it to a node;
  `production.composer` rejects its absence; `drift.evaluation_snapshot` reuses its policy/OS;
  and `reconcile.executor` reads its stored OS to select a playbook.
- Production inventory/report schema is `1.0`. Included hosts carry
  `nintent_operational_config_id`; the report states effective values but not their provenance.
- `nauto/seed/intent_sources.yaml` contains nine full operational-config rows. Some contain real
  exceptions (HAOS declaration, non-standard SSH port, WOL/macOS sleep, laptop behavior); the
  remaining derived OS/path/endpoint values are repeated mechanism data.

## Decisions taken head-on

### 1. Replace the model with `DesiredNodeOperationalOverride`; do not make the old model nullable

Create an optional one-to-one model named `DesiredNodeOperationalOverride` and delete
`DesiredNodeOperationalConfig` from the runtime. The new model contains only:

- `desired_node` — one-to-one identity;
- `declared_host_os` — optional, initially only `haos`;
- `connection_path` — optional forced path (`local` or `tailscale`);
- `local_endpoint` — optional forced local endpoint;
- `tailscale_endpoint` — optional forced Tailscale endpoint;
- `ansible_port` — optional, `1..65535`;
- `power_control` — optional input with effective default `none`; and
- `is_laptop` — optional input with effective default `false`.

`actual_state_policy` and `expected_host_os` do not exist on the new model. They are derived facts,
not renamed fields. The old class, constraint, form, filter, table, views, URLs, template, reverse
name, GraphQL root, YAML root, loader/importer helpers, Job counters, docs, and tests are deleted or
replaced in the same change. There is no alias, deprecated root, dual query, or data-copy adapter.

The override row itself is optional. Its form and YAML schema require only `desired_node`; every
override field is individually optional, but row validation requires at least one non-default
override so an empty/no-op row cannot be saved. Model/form/loader validation also enforces:

- selected endpoints belong to the row's node;
- a forced Tailscale path requires one VPN endpoint with a usable IP and forbids a local endpoint;
- a forced local endpoint implies/permits only the local path and must have IP, DNS, or mDNS;
- a `tailscale_endpoint` without `connection_path=tailscale` is invalid;
- `declared_host_os=haos` may use a derived/forced local path or a complete forced Tailscale path;
- HAOS permits only `power_control=none`; observed Linux/macOS power compatibility is checked after
  OS derivation in nctl; and
- an entirely no-op row (no non-default override value) is rejected so the existence of a row
  remains meaningful.

Regular Nautobot CRUD and strict YAML import are sufficient override writers in Phase 2. No REST
ViewSet is added for this model: no Phase 2 nctl command writes overrides, and inventing an API
solely for hypothetical future use would expand the mutation surface without serving this phase.

### 2. One pure resolver owns operational derivation

Add a pure nctl resolver (a focused `production/derivation.py`, or an equivalently isolated module)
used by production composition, service-placement evaluation, provenance rendering, and reconcile
playbook selection. No consumer independently reimplements endpoint or OS precedence.

For one node the resolver receives: all of its `DesiredEndpoint` rows, its optional
`DesiredNodeOperationalOverride`, its realized object and allowlisted actual facts, and the
operation's fixed `generated_at`. It returns an immutable effective operational value object plus
per-field provenance, or one structured target-local derivation failure.

The exact precedence is:

1. **Policy and OS**
   - `declared_host_os` present → `actual_state_policy=declared`, `host_os=declared_host_os`; no
     realized object or nodeutils observation is required.
   - no declaration → `actual_state_policy=required`; require a supported realized object, a
     parseable fresh `collected_at`, and `observed_system` of `Linux` or `Darwin`; normalize to
     `linux`/`macos`.
   - missing/stale/invalid actual evidence reuses the existing observation skip codes. An
     unsupported observed OS remains `unsupported_observed_host_os`. No OS is guessed.
2. **Connection path and endpoint**
   - a valid forced Tailscale path + endpoint wins;
   - a valid forced local endpoint wins and makes the effective path local;
   - otherwise consider usable-local endpoints (IP, DNS, or mDNS): exactly one wins; when there
     are several, exactly one `endpoint_type=primary` wins; zero or multiple-without-a-unique-
     primary is an explicit finding;
   - Tailscale is never auto-selected; and
   - no lexical/name/ID ordering is used to resolve semantic ambiguity.
3. **Connection address**
   - for required/observed local hosts, a fresh observed local IP remains the first effective
     address source; then the selected endpoint's IP/DNS/mDNS; the node slug is not accepted as a
     substitute for a missing usable endpoint;
   - for declared local hosts, use the selected endpoint's IP/DNS/mDNS; and
   - for Tailscale, use the selected VPN endpoint IP.
4. **Defaults and overrides**
   - `ansible_port`: absent means the Ansible default and is not emitted as a host var;
   - `power_control`: absent/default → `none`; explicit non-default value wins after platform
     validation;
   - `is_laptop`: absent/default → `false`; explicit `true` wins.

Freshness is evaluated once against the fixed generation time. A reconcile operation must pass its
operation timestamp to the same resolver when grouping hosts by `playbook_by_os`; it must not read a
removed stored OS or use wall-clock time independently in each consumer.

### 3. Use one closed provenance shape in report schema `2.0`

Set `PRODUCTION_INVENTORY_SCHEMA_VERSION = "2.0"`. Remove
`nintent_operational_config_id` from allowed/emitted host variables. Do not replace it with an
always-present fake ID; `nintent_desired_node_id` already provides stable node provenance.

Each successful `report.hosts[]` entry gains `operational_values`, with these keys:

- `actual_state_policy`;
- `host_os`;
- `connection_path`;
- `connection_endpoint`;
- `connection_address`;
- `ansible_port`;
- `power_control`; and
- `is_laptop`.

Every entry uses the same closed value record:

```json
{
  "value": "linux",
  "source": "derived",
  "source_reference": {
    "kind": "nodeutils_observation",
    "observed_system": "Linux",
    "collected_at": "2026-07-20T00:00:00Z"
  },
  "override_won": false
}
```

`source` is exactly `derived`, `default`, or `override` for this operational cluster. Optional
values such as an absent `ansible_port` still have a record (`value=null`, `source=default`) so
absence is legible. An override source references the override row ID and field; an endpoint source
references endpoint ID/name/type; observation provenance exposes only the allowlisted system and
timestamp, never the unrestricted actual-fact payload.

When a value cannot be resolved, the existing `skipped`/`errors` pair contains the same field name,
candidate/override evidence, and a `finding` code. A partially populated successful provenance
record is never emitted.

Add one node-targeted INFO diagnostic, `derived_value_provenance`, to `nctl drift` for each desired
node. It summarizes the resolved operational records plus the persisted derived-link/name
provenance in Decision 4. INFO never changes target status and, because it is intentionally absent
from `CODE_CLASSIFICATION`, reconcile ignores it under the existing non-error rule. This makes
derived choices visible in drift JSON/text and dashboard details even when the node is converged;
`nctl render production --json` exposes the stricter schema-2.0 report copy for included hosts.

`validate_production_report()` validates all nested keys, source values, `override_won` booleans,
and source-reference shapes. The version bump is not cosmetic: compatibility snapshots must reject
a `1.0` report carrying the new shape and a `2.0` report carrying the removed host variable.

### 4. Persist provenance for the other Phase 0 derived/override gaps in the same nintent batch

Phase 0 §4/§8 also assigns provenance for `dns_name`/`mdns_name`, node realization links, and the
realized IP link to Phase 2. Add system-managed source metadata while nintent is already taking one
coordinated schema/rebuild change:

- `DesiredEndpoint.dns_name_source`, `mdns_name_source`: `derived` when Quick Add/YAML defaulting
  generated the value, `intent` when explicitly supplied;
- `DesiredNode.realized_device_source`, `realized_vm_source`: `derived` when
  `link_actual_node` writes the link, `override` when a human sets/replaces it through the form or
  a general REST write; and
- `DesiredEndpoint.realized_ip_address_source`: `derived` when the IPAM reconciliation Job links
  it, `override` when set manually.

Source fields are hidden/read-only in normal forms. REST serializers expose them as validated
metadata because `execute_link_actual_node` must PATCH the link and `source=derived` atomically;
when a general REST/form write changes a link without an explicit automation source, the serializer
or form stamps `override`. Update Quick Add, importer defaults, regular form save hooks, the
DesiredNode/DesiredEndpoint serializers, `execute_link_actual_node`, and
`ReconcileDesiredIPAMIntent` together. Clearing a value clears its source. A non-null value with a
null/invalid source fails validation.

Historical source cannot be proved from current values. The migration therefore uses a
conservative transition: existing explicit DNS/mDNS values become `intent`; existing realized
links become `override`; null values keep a null source. It never labels historical data
`derived` based only on equality with a generated default or on guesswork. All post-migration
automatic writes are exact.

Extend the nctl typed snapshot with these source fields and include them in
`derived_value_provenance` using the same closed value record as Decision 3 (with `intent` also
allowed for explicitly supplied DNS/mDNS). Generated/automatic links use `override_won=false`;
explicit DNS/name or manual-link values use `override_won=true` and reference the owning field/row.
This closes the Phase 0 provenance assignment without adding mutable source controls to the UI.

### 5. New endpoint-derivation failures are node-local and fail closed in reconcile

Add exactly two new error codes:

| Code | Trigger | Target/severity | Evidence | Reconcile |
|---|---|---|---|---|
| `missing_connection_endpoint` | no usable local endpoint and no complete forced-Tailscale override | node / error | node plus all endpoint IDs/types and which usable-address fields were absent | `MANUAL_REVIEW`; blocks production actuation only for that node |
| `ambiguous_connection_endpoints` | more than one usable local endpoint and no unique primary or forced local endpoint | node / error | sorted candidate ID/name/type/address summary | `MANUAL_REVIEW`; blocks production actuation only for that node |

They use Phase 1's structured local error/report/drift pipeline and join the composer's canonical
production-blocking code set in the same commit that makes them reachable. Mixed good+bad render,
planner, and executor tests are mandatory.

Remove dead mechanism codes from runtime declarations/classification/tests when their producer is
deleted: `missing_operational_config`, `invalid_actual_state_policy`,
`invalid_connection_path`, `desired_actual_os_mismatch`, and
`service_placement_os_mismatch`. Retain reachable validation codes such as
`unsupported_observed_host_os`, `invalid_platform_power`, `endpoint_node_mismatch`,
`unresolved_connection_path`, and `invalid_connection_address`.

Rename Phase 1's historical runtime constant `PHASE1_LOCAL_CODES` to a semantic current name such
as `PRODUCTION_BLOCKING_NODE_CODES`; both classifier and planner import the same set. This is a
runtime vocabulary cleanup, not a compatibility alias. Source history remains in the Phase 1 docs.

### 6. `DesiredService.placement_policy` is deferred explicitly to Phase 4

Phase 0 allowed its unused future-hook decision in Phase 2 or Phase 4. It is unrelated to node
operation derivation and has no reader in this change, so Phase 4 owns the keep/remove product
decision. Phase 2 does not change the field or imply that it affects endpoint/OS selection.

### 7. This is a coordinated breaking migration, with no mixed-version support

The nintent migration creates `DesiredNodeOperationalOverride`, deletes
`DesiredNodeOperationalConfig`, adds the provenance-source fields, and performs only the
conservative source backfill in Decision 4. It does not copy operational-config rows. Deployment
must abort before migration if the live old-row count is non-zero; the current expected count is
zero.

The strict YAML root becomes `desired_node_operational_overrides`. The old
`desired_node_operational_configs` root and its derived keys are invalid input, not silently
ignored and not converted. `nauto/seed/intent_sources.yaml` is rewritten so:

- ordinary OS/path/endpoint rows disappear;
- WOL, macOS sleep, laptop, and other true exceptions remain as compact override rows; and
- HAOS keeps `declared_host_os`, its necessary endpoint/path exception, and non-standard port.

The GraphQL root changes to `desired_node_operational_overrides`. nctl queries only the new root.
There is no query fallback or dual Pydantic model. The running nctl and nintent revisions must be
cut over together.

Rollback point: database backup plus the pre-Phase-2 nintent/nctl revisions, before any new
override or provenance writes occur. With the asserted zero old rows, reversing the migration and
rebuilding the old nintent image is lossless. If new override/source data has already been written,
export it first; there is intentionally no automatic converter back to the deleted schema.

## Reader/writer and transition matrix

| Boundary | New contract | Required change | Tests |
|---|---|---|---|
| nintent model/migration | Optional override only; derived policy/OS removed; source metadata added | Create/delete models, constraints, conservative source backfill | migration/model validation |
| regular forms + DesiredNode detail | Override CRUD only; source fields managed, not editable | replace old CRUD/template; add/edit link from node; source-aware save behavior | form/template tests |
| Quick Add + host operation | still creates node + primary endpoint, no override row | stamp generated DNS/mDNS source as `derived`; never auto-materialize override | operations tests |
| REST serializers | node/endpoint values plus read-only source metadata | manual relationship writes stamp `override`; nctl link PATCH explicitly stamps `derived` atomically | serializer + ledger tests |
| strict YAML loader/importer/Job | optional `desired_node_operational_overrides`; old root rejected | replace dataclass, normalizer, duplicate check, defaults, upsert, counts; relax power/laptop omission | loader/import/Job tests |
| `ReconcileDesiredIPAMIntent` | link and source change atomically | stamp `realized_ip_address_source=derived` in both create/link paths | Job/IPAM tests |
| seed and live docs | only exceptions are written | rewrite seed and nintent/nauto README/CONCEPT current-state sections | loader parses seed; doc grep |
| nctl GraphQL + typed snapshot | fetch all endpoints, optional overrides, source metadata | replace query root/model/list; remove old names completely | desired-source/snapshot fixtures |
| production adapter/resolver | node receives all endpoints + optional override + actual facts | replace operational-config join with shared derivation inputs | adapter/resolver unit tests |
| composer/contract/render | effective config always derived or locally failed; schema `2.0` | remove missing-row gate/ID; add strict provenance; new local codes | contract/composer/render/CLI/compatibility tests |
| drift comparators/evaluation | resolved policy/OS/provenance from shared resolver | remove stored expected-OS mismatch paths; add INFO provenance; preserve local errors | comparator/engine/status/dashboard tests |
| reconcile classifier/planner | current semantic blocker set | add two new codes, delete dead codes, keep fail-closed coverage and host filtering | classify/planner mixed-node tests |
| reconcile executor | playbook OS from shared resolver at fixed operation time | remove `operational_configs` lookup; never guess when resolution fails | executor/action-group tests |
| generated inventory/report | schema `2.0`; old artifact unsupported | regenerate at cutover; never hand-edit or translate `1.0` | output snapshot tests + read-only live render |

## Mandatory Phase 0 gate coverage

The six roadmap planning gates are closed as follows:

1. **Failure scope:** shared profile schema and final closed-document corruption remain global.
   Observation gaps retain their existing node-local codes. The two new ambiguity/absence codes
   and all override/platform/address validation failures are node-local.
2. **End-to-end findings:** Decisions 3 and 5 define target, severity, message/evidence, report,
   drift/status/dashboard effect, classification, and blocked-node execution semantics. The INFO
   provenance code is intentionally non-blocking and tested as omitted from reconcile.
3. **Readers and writers:** the matrix covers model/forms/Quick Add/REST/YAML/Jobs/seed, GraphQL,
   typed snapshots, adapter/resolver/composer, service evaluation, executor, docs, and artifacts.
4. **Overrides and provenance:** Decision 1 names every persistence field; Decision 2 fixes
   precedence and ambiguity behavior; Decisions 3/4 define value/source/reference/override-won
   output without guessing historical provenance.
5. **Schema/data transition:** Decision 7 states Django operations, the zero-row assertion,
   conservative provenance backfill, schema `2.0`, strict cutover order, and rollback boundary.
6. **Isolation and orchestration:** Steps 2.4–2.7 cover pure resolution, mixed good/bad render,
   drift/dashboard, cluster/host planning, partial healthy execution, and coordinated live checks.

## Step 2.1 — Freeze baselines and executable contracts

1. Run the full nintent and nctl suites and record exact counts in `p2/report2.1.md`.
2. Reconfirm live `DesiredNodeOperationalConfig` count is zero through a read-only GraphQL/ORM
   query; record only the count, never credentials or unrestricted facts.
3. Add table-driven resolver tests before changing GraphQL/model shapes. Freeze the Phase 0
   scenario matrix and the exact provenance JSON record.
4. Inventory every old symbol/root/field with `rg`; save the expected deletion list in the report
   so the final no-artifact sweep is objective.
5. Add the two new codes to classification/blocker coverage in the same implementation commit in
   which the resolver can emit them.

## Step 2.2 — Land the complete nintent schema/writer batch

In one nintent change:

1. add the override model and its validation;
2. delete the old runtime model and CRUD/YAML/import surface;
3. add and backfill source metadata from Decision 4;
4. make every automatic/manual writer stamp or clear source atomically;
5. add migration `0010_*` with normal forward/reverse operations retained in history;
6. rewrite nintent README/CONCEPT examples around optional overrides; and
7. run the nintent suite and migration checks.

Do not rebuild the running Nautobot yet. The matching nctl revision must be complete and tested
against the new schema before the coordinated cutover.

## Step 2.3 — Replace the nctl source shape and implement the resolver

1. Replace the GraphQL root and Pydantic model/list with
   `DesiredNodeOperationalOverride` / `operational_overrides`; add provenance source fields to node
   and endpoint models.
2. Pass all node endpoints, optional override, realized state, and fixed generation time to the
   shared resolver.
3. Implement Phase 0's exact zero/one/many/unique-primary endpoint rules and forced-override
   precedence.
4. Implement declared-vs-required OS resolution and normalized, allowlisted provenance.
5. Return typed effective values; never pass partially derived dictionaries between consumers.
6. Test ordinary Linux/macOS, declared HAOS, all override combinations, stale/missing/unsupported
   evidence, invalid ownership/address/power, and deterministic candidate ordering.

## Step 2.4 — Move production composition and output to schema `2.0`

1. Remove the missing-operational-config branch and old input dataclass.
2. Resolve each eligible node before composition; turn resolver failures into Phase 1-style
   `LocalCompositionError` entries with exact evidence and skip only that node.
3. Keep inventory host variables behaviorally identical for effective connection/OS/power/laptop
   values, except for removing `nintent_operational_config_id` and updating schema metadata.
4. Add and strictly validate `report.hosts[].operational_values`.
5. Remove dead OS-mismatch generation and dead code constants/tests.
6. Prove a healthy node with no override row renders byte-deterministically and a bad neighbor does
   not change its host/group/placement output.

## Step 2.5 — Wire drift, dashboard, service evaluation, and reconcile

1. Emit `derived_value_provenance` per node with operational, name, and link provenance; pin INFO
   severity, converged status, dashboard visibility, HTML escaping, and reconcile omission.
2. Make `node_existence` derive `required` from absence of `declared_host_os`; remove its old
   operational-config lookup.
3. Make service placement evaluation consume the shared effective policy/OS. Declared hosts remain
   observation-exempt. Remove `service_placement_os_mismatch`, because expected OS is no longer an
   independent declared value.
4. Update the canonical production blocker set, classification table, planner host filtering, and
   exhaustive code-coverage tests.
5. Replace executor playbook selection with the shared resolver and fixed operation timestamp.
   A resolution failure must already be a scoped plan finding; executor fallback to `None`/an
   arbitrary playbook is forbidden.
6. Cover host-scoped and cluster reconcile with one ambiguous/missing-endpoint node plus one
   healthy node: healthy work proceeds; blocked-node production actions do not.

## Step 2.6 — Rewrite seed data and current documentation

1. Convert `nauto/seed/intent_sources.yaml` to the strict override root, retaining only actual
   exceptions and deleting repeated expected OS/local endpoint/path values.
2. Parse the complete seed through the real loader and assert idempotent import.
3. Update `nauto/README.md`, `nintent/README.md`, and `nintent/CONCEPT.md` current contracts.
4. Do not rewrite historical `devdocs/functions/*` or completed core-reconcile reports; they are
   implementation history, not live instructions. Add a short supersession note only where a
   current index points users at an obsolete recipe.
5. Leave the end-user "add/register" recipe rewrite to Phase 4, as sequenced by the roadmap.

## Step 2.7 — Test the full scenario and orchestration matrix

At minimum cover:

| Scenario | Expected result |
|---|---|
| fresh observed Linux/macOS + one usable endpoint + no override | included; required policy, OS, local path, and endpoint derived with provenance |
| several endpoints + one primary | primary selected deterministically |
| several usable endpoints + no unique primary | `ambiguous_connection_endpoints`; node skipped/local manual review |
| zero usable endpoints | `missing_connection_endpoint`; bootstrap remains possible, production locally skipped |
| stale/missing actual evidence | existing observation finding; no guessed OS |
| unsupported observed OS | local `unsupported_observed_host_os` |
| declared HAOS override | no nodeutils requirement; explicit override provenance |
| forced local endpoint | override wins; alternate derived candidate remains visible in source summary |
| forced Tailscale + VPN endpoint | included with Tailscale address; incomplete pair rejected/locally reported |
| non-standard port / WOL / macOS sleep / laptop | override/default provenance and platform validation correct |
| mixed healthy + every bad case | healthy inventory and safe reconcile actions survive unchanged |
| schema `1.0` artifact under new code | rejected; no compatibility translation |
| old GraphQL/YAML/model names | absent/rejected; no shim |

Focused nintent tests:

```bash
uv run --project nintent pytest -q \
  nintent/nautobot_intent_catalog/tests/test_loaders.py \
  nintent/nautobot_intent_catalog/tests/test_importers.py \
  nintent/nautobot_intent_catalog/tests/test_jobs_import.py \
  nintent/nautobot_intent_catalog/tests/test_operations_hosts.py \
  nintent/nautobot_intent_catalog/tests/test_operations_ipam.py \
  nintent/nautobot_intent_catalog/tests/test_templates.py
```

Focused nctl tests:

```bash
uv run --project nctl pytest -q \
  nctl/tests/test_sources_desired.py \
  nctl/tests/test_sources_snapshot.py \
  nctl/tests/test_production_adapter.py \
  nctl/tests/test_production_contract.py \
  nctl/tests/test_production_composer.py \
  nctl/tests/test_production_render.py \
  nctl/tests/test_cli_render_production.py \
  nctl/tests/test_drift_comparators.py \
  nctl/tests/test_drift_engine.py \
  nctl/tests/test_drift_evaluation_snapshot.py \
  nctl/tests/test_drift_status.py \
  nctl/tests/test_dashboard_html.py \
  nctl/tests/test_reconcile_classify.py \
  nctl/tests/test_reconcile_ledger.py \
  nctl/tests/test_reconcile_planner.py \
  nctl/tests/test_reconcile_executor.py \
  nctl/tests/test_compatibility_snapshots.py
```

Then run both full suites. Executor tests use fakes; no test performs a real ledger write,
Nautobot rebuild, Job trigger, or Ansible actuation.

## Step 2.8 — Coordinated deployment and read-only live verification

1. Commit/test the matching nintent, nctl, and nauto changes; keep submodule/root commits reviewable.
2. Recheck old live-row count is zero and take a database backup. Stop if either condition fails.
3. Ask the user to push the nintent commit (the local environment installs nintent from GitHub).
4. Rebuild/restart Nautobot and run migrations using the documented compose environment.
5. Without running an old nctl revision against the new server, switch immediately to the matching
   nctl revision and verify the new GraphQL root/fields.
6. Run read-only checks:

```bash
uv run --project nctl nctl render production --json
uv run --project nctl nctl drift --json
uv run --project nctl nctl reconcile --json
```

Expected live behavior while all nodes remain `planned`: render/drift/reconcile envelopes succeed;
the old GraphQL root is absent; active-placement Phase 1 warnings remain; node provenance is
visible; no `missing_operational_config` exists; and the dry plan contains no unclassified code.
Do not use `--out`, dashboard status push, `reconcile --yes`, or temporary live promotion in this
phase's verification.

7. Record migration, GraphQL, test counts, and read-only live results in `p2/report2.8.md`. Confirm
   no token, live UUID dump, unrestricted actual facts, or generated inventory artifact was added
   to Git.

## Out of scope

- Defaulting `DesiredNode.lifecycle` to `active`, promoting existing planned nodes, or adding the
  lifecycle CLI — Phase 3.
- Rewriting end-user registration/service recipes or making all status surfaces narrate every
  remaining tier — Phase 4, except the Phase 2 provenance required for this schema change.
- Automatically choosing Tailscale, arbitrarily ranking equally plausible endpoints, guessing an
  OS, or coercing an unsafe power setting.
- Adding an override REST API or nctl override mutation command without a concrete Phase 2 writer.
- Keeping the old model/YAML/GraphQL/output shape alive during deployment.
- Deciding `DesiredService.placement_policy`, or fixing unrelated `node_type`, `ip_policy`, and
  `generate_dnsmasq` default inconsistencies — Phase 4.
- Mutating live lifecycle/override/link data or running real reconcile/Ansible actions as part of
  verification.

## Exit criteria

- [ ] An observed Linux/macOS node with a placement, one usable endpoint, and no override row
  produces the correct production host, OS group, connection variables, and actuation playbook.
- [ ] HAOS, forced endpoint/path, non-standard port, power, and laptop exceptions remain possible
  through the optional override row and are the only mechanism data a human enters.
- [ ] Every effective operational value exposes value, source, source reference, and
  `override_won`; unresolved/ambiguous values produce explicit local findings.
- [ ] DNS/mDNS and realized node/IP link source metadata is written by every ingress and visible in
  nctl provenance without historical-source guessing.
- [ ] Zero/multiple endpoint cases skip only their node; mixed healthy targets still render and
  reconcile independently; shared/output-contract corruption remains global.
- [ ] Every reachable error code is classified; dead operational-config/expected-OS codes and the
  `PHASE1_LOCAL_CODES` runtime name are removed without leaving compatibility aliases.
- [ ] Production inventory/report schema is `2.0`; `nintent_operational_config_id`, old model,
  old GraphQL root, old YAML root, old UI/import surface, and old typed models are absent.
- [ ] Migration/backfill, existing-row policy, coordinated rollout, and rollback point are tested
  and recorded; the live pre-migration zero-row assertion is satisfied.
- [ ] Seed YAML contains only genuine overrides and passes strict, idempotent import tests.
- [ ] Focused/full nintent and nctl tests, compatibility snapshots, no-artifact grep, and read-only
  live checks pass; unrelated submodules/worktrees remain clean.
- [ ] Phase 3 can change node lifecycle to `active` without creating an operational-config step or
  exposing a cluster-wide failure path.

## Suggested commit order

Because the runtime cutover is coordinated, commits may be reviewed separately but are deployed
as one version set:

1. **nintent schema and writers:** new override model, old model deletion, provenance fields,
   migration, CRUD/YAML/import/REST/Job writers, tests, and current docs.
2. **nctl source and resolver:** new GraphQL/typed shape, shared resolver, unit tests, and the two
   new codes plus classification in the same commit.
3. **production schema `2.0`:** composer/contract/report provenance, dead-code removal, render and
   compatibility tests.
4. **drift/reconcile integration:** INFO provenance, service evaluation, semantic blocker set,
   planner/executor shared derivation, mixed orchestration tests.
5. **seed/docs and verification report:** compact override seed, full regressions, coordinated
   deployment evidence, and root submodule pointer updates.

No intermediate commit may produce an unclassified error code. No deployed state may pair the new
nintent schema with an old nctl query or the old nintent schema with the new nctl query.
