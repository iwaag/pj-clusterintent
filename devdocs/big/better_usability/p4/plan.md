# Better Usability Phase 4 Implementation Plan: Recipe and Feedback Consolidation

Parent roadmap: [`../roadmap.md`](../roadmap.md), Phase 4. Field authority and residual-work
inventory: [`../p0/field-classification.md`](../p0/field-classification.md), especially §2, §3,
§5, §7, and §8. Prerequisites: Phase 1 target-local isolation, Phase 2 operational derivation and
provenance, and Phase 3 live-on-creation behavior are deployed and verified by
[`../p1/report1.7.md`](../p1/report1.7.md), [`../p2/report2.8.md`](../p2/report2.8.md), and
[`../p3/report3.7.md`](../p3/report3.7.md).

## Goal

Finish the intent-first operator experience rather than leaving the earlier behavior changes as
separate implementation facts. For every desired node, the supported feedback surfaces must make
three layers distinguishable:

1. **recorded intent** — node lifecycle/type, endpoints, service placements, desired state, profile,
   and config;
2. **effective mechanism** — each derived/default/override operational value, its source, and
   whether an override won; and
3. **application effect** — included, deliberately inactive, outside production scope, or skipped,
   with the precise reason and placement-level effect.

At the same time, remove the residual field-tier contradictions assigned by Phase 0 to this phase
and replace the historical shell-oriented recipes with literal, current, UI + `nctl reconcile`
workflows. A common new-PC flow must require no operational-config row, manual lifecycle promotion,
hand-written inventory membership, or unexplained default.

This is the final consolidation phase of this initiative. It is allowed to remove unused schema
and output surface; it must not introduce compatibility fields, dual GraphQL readers, or a second
source of reconciliation truth.

## Current state (after Phase 3, 2026-07-21)

- nintent revision `e018ffe` is deployed with migration
  `0012_desired_node_lifecycle_default_active`. The local nintent baseline is 92 tests.
- nctl revision `e804620` is deployed with 607 tests. Production inventory/report schema is `2.0`,
  `nctl.drift.v1` emits one `derived_value_provenance` INFO record per node, and lifecycle command
  behavior is live.
- Existing live nodes were reviewed rather than silently migrated: `agpc` and `agstudio` are
  `active`; `agbach`, `agdnsmasq`, and `aghub` remain deliberately `planned`. Stale nodeutils data
  on the active nodes is a visible existing infrastructure finding, not a Phase 4 code defect.
- `nctl status` is controller/input health: Nautobot reachability, dump age, and submodule state.
  It is not a second per-target drift command. `nctl drift` owns target state, while the production
  companion report owns exact projection/application evidence.
- Drift JSON and the dashboard already retain `desired`/`actual` evidence, but drift text renders
  only each generic message. In particular, the human-readable line for
  `derived_value_provenance` does not say which values were derived, defaulted, or overridden.
- Production report `2.0` exposes operational provenance only for included hosts. Its separate
  `hosts`, `skipped`, `drift`, and `errors` collections do not give one uniform answer for every
  desired node, and lifecycle-out-of-scope nodes are represented only when an active placement
  happens to trigger `active_placement_not_applied`.
- Phase 0's remaining nintent contradictions are still present: editable IntentSource Job caches;
  Quick Add's `virtual_machine` node default versus the model/YAML `device` default; hidden
  `accepted_actual_types`; generic endpoint `ip_policy` disagreement; analysis metadata mixed into
  `DesiredService.requirements`; and inert `DesiredService.placement_policy`.
- `DesiredServiceSerializer(fields="__all__")` still auto-builds an `intent_source` hyperlink to an
  unregistered route. Service REST list/detail and response serialization after PATCH can fail when
  `intent_source` is non-null, which also makes dashboard status write-back incomplete.
- `AnalyzeIntentSources` deletes and recreates every dependency on every run, losing retained notes
  and resolution/link state even when the dependency's natural key did not change.
- `nauto/seed/service_repositories.yaml` is **not** an nintent strict-import fixture: current code
  confirms it remains the input of nauto's separately registered `Generate Desired Services` Job.
  Phase 0's “fix or remove stale fixture” item therefore needs a corrected ownership decision, not
  a blind top-level-key rename.
- The current `nctl/docs/add-a-basic-service.md` still teaches a `nautobot-server shell` example,
  contains a stale REST-gap note, and conflicts with the current bootstrap inventory description.
  There is no standalone current “register a new PC” recipe.

## Decisions taken head-on

### 1. Keep `nctl status` as controller health; make drift and the production report the node answer

Do not add desired-state fetching, `--host`, target status, or drift codes to `nctl status`. That
would make a cheap independently degrading health check call the full drift engine and create two
commands presenting the same target state with different freshness/failure semantics.

The three surfaces instead have an explicit division:

| Surface | Question answered | Source of truth |
|---|---|---|
| `nctl status` | Are Nautobot, local observations, and repository inputs available/fresh enough to work? | controller/input checks only |
| `nctl drift [--host NODE]` and dashboard | What is recorded, what was derived/overridden, and why is this target converged/drifting/unknown? | fresh `nctl.drift.v1` |
| `nctl render production` companion report | What exact node/placement intent entered or failed to enter the generated inventory? | one composition result |

Update status/drift/render documentation and status text help to state this split. Status text adds
one short “target state: use `nctl drift --host SLUG`” hint, but `nctl.status.v1` and its data model
do not change.

### 2. Replace the generic provenance diagnostic with one per-node intent/effect summary

Rename `derived_value_provenance` to `intent_effect_summary`; do not retain the old code as an
alias. It remains node-targeted and INFO severity, so it never changes target status and is
intentionally absent from `reconcile.classify.CODE_CLASSIFICATION`.

Each desired node gets exactly one summary, including nodes outside production scope. Its evidence
is closed and divided as follows:

```json
{
  "desired": {
    "node": {
      "id": "...",
      "slug": "agpc",
      "name": "agpc",
      "lifecycle": "active",
      "node_type": "device",
      "role": null,
      "accepted_actual_types": ["device"],
      "accepted_actual_types_source": "derived"
    },
    "endpoints": [],
    "placements": [],
    "operational_override": null
  },
  "actual": {
    "operational_values": {},
    "operational_finding": null,
    "production": {
      "state": "included",
      "reasons": [],
      "placement_effects": []
    }
  }
}
```

`production.state` is one of `included`, `skipped`, `out_of_scope`, or `unknown`. Every placement
effect is one of `applied`, `inactive_by_intent`, or `not_applied`, with stable reason codes. The
recorded placement includes service identity, instance, desired state, deployment profile, schema
version, config, assignment source, and endpoint reference. Derived operational records retain
Phase 2's exact `{value, source, source_reference, override_won}` contract.

The text renderer special-cases this INFO record into three compact lines (`intent`, `effective`,
`application`) rather than printing a generic message. It prints config keys, not arbitrary config
values; complete values remain in JSON/report evidence. The dashboard renders the same three
sections and source badges from the same record instead of inventing a dashboard-only summary.

Update the drift fingerprint ignore set from `derived_value_provenance` to
`intent_effect_summary`. Prove INFO-only changes do not cause reconcile `no_progress`, actions, or
status changes.

### 3. Introduce production report schema `3.0` without changing inventory schema `2.0`

The Ansible inventory variables and groups do not change. Keep
`PRODUCTION_INVENTORY_SCHEMA_VERSION = "2.0"`, and introduce the independent
`PRODUCTION_REPORT_SCHEMA_VERSION = "3.0"`. The `nctl.render.production.v1` envelope also remains;
only `data.report`/`report_json` and the written companion report advance.

Report `3.0` replaces the parallel `hosts`/`skipped`/`drift`/`errors` runtime collections with one
closed `nodes` collection. Do not emit both old and new shapes. Each desired node appears exactly
once with:

- node identity and recorded intent (including endpoint, override, and placement evidence);
- effective operational values or one structured derivation finding;
- production eligibility and `included`/`skipped`/`out_of_scope` result;
- placement-by-placement application effects; and
- structured local findings with code, severity, message, stage, and bounded evidence.

The summary adds `nodes`, `out_of_scope`, `applied_placements`, and
`not_applied_placements`; retain meaningful `eligible`, `included`, `skipped`, and placement totals.
The drift comparator translates report node records into `intent_effect_summary` plus existing
error/warning diffs. Thus text, JSON, dashboard, render report, and reconcile all consume the same
composition result rather than independently inferring effect.

Shared deployment-profile load/validation failure remains global. Today drift silently replaces a
`DeploymentProfilesError` with `{}`; Phase 4 instead emits global ERROR
`deployment_profiles_unavailable`, with the path and sanitized validation reason. It is classified
`MANUAL_REVIEW` and blocks cluster actuation because no node's placement effect can be established.
Render production continues to return a failed envelope and no report/inventory for that same
global contract failure.

### 4. Canonical node creation defaults to a physical `device`; Quick Add exposes derivation

`DesiredNode.node_type` is genuine Intent, but the personal-cluster “register a PC” default is
unambiguously `device`. Keep the existing model and YAML default and change the two conflicting
sites:

- Quick Add initial: `device`;
- `create_desired_node_with_primary_endpoint(node_type=...)`: `device`.

Explicit `virtual_machine`, `container`, or `service_host` always wins. Existing rows are not
changed and no Django migration is needed for this item.

Quick Add must stop submitting a hidden `accepted_actual_types`. Show a labeled derived preview
computed from the selected `node_type`, plus an optional explicit override control. Blank override
means “derive”; it must not persist a fake user choice merely because the preview was visible. The
preview updates when node type changes until an override is entered. Server-side cleaning remains
authoritative and uses the same mapping as the operation/YAML loader; JavaScript is presentation
only. The confirmation/success view states the effective value and `derived` or `override` source.

No new model provenance field is needed: the stored-list rule is deterministic — absence/empty
uses the per-node-type mapping; a non-empty differing list is an override. nctl exposes that source
in `intent_effect_summary`.

### 5. Generic endpoint defaults are `external`/not-published; Quick Host Add keeps an explicit contextual policy

Resolve the `ip_policy` contradiction by changing the generic Django model default from `static` to
`external`, matching strict YAML's no-address/no-policy result. The importer becomes a pure
projection and no longer adds its own `or "external"` fallback. When an explicit `ip_address` is
provided, strict YAML and the host operation continue to require a valid explicit policy rather
than silently choosing address ownership.

`generate_dnsmasq=False` remains the generic model/YAML/REST default because it is an opt-in
Override. Quick Host Add is a narrower composed use case (“one primary bootstrap endpoint”) and may
default visibly to `generate_dnsmasq=True` and `ip_policy=dhcp_reserved`. This difference is kept
only as a named Quick-Host policy shared by the form and operation, with help text stating that it
publishes the supplied IP and requires an address to produce records. It is no longer an accidental
duplicate default. An operator can turn publishing off or select `external`/`static` directly.

Migration `0013_*` alters only the future generic `ip_policy` default; existing endpoint values are
not rewritten. Tests cover generic model/REST omission, strict YAML omission, Quick Add omission,
and all explicit overrides so the contextual distinction cannot drift again.

### 6. Separate analysis provenance from operator requirements and remove inert placement policy

Add `DesiredService.analysis_provenance = JSONField(default=dict, blank=True, editable=False)` with
the closed subkeys `status`, `confidence`, `reasons`, and `warnings`. It is Job-owned, shown
read-only on service detail, returned read-only over REST/GraphQL when requested, and absent from
`DesiredServiceForm`.

`DesiredService.requirements` remains operator/catalog intent. `AnalyzeIntentSources` must not
overwrite it when refreshing an existing service. A newly analyzed service starts with `{}`;
matching later analysis updates only source/catalog fields, `analysis_provenance`, and
`last_analyzed_at`.

Migration `0013_*` moves only the four known legacy keys
`analysis_status`/`analysis_confidence`/`analysis_reasons`/`analysis_warnings` into the new closed
shape and removes those keys from `requirements`; all unknown/operator keys remain byte-for-byte.
The reverse migration merges the four legacy keys back for rollback.

Delete `DesiredService.placement_policy` outright. It has no current producer of non-empty data and
no consumer; retaining and displaying an inert Intent field contradicts the breaking-change
premise. Before migration, assert all live values are `{}`/null. The migration includes a guard
that aborts rather than dropping a non-empty value unexpectedly, then `RemoveField`. Remove it from
the form, detail template, REST/GraphQL shape, nctl query/typed snapshot, evaluation expected facts,
docs, and tests. Do not leave a deprecated property or ignored loader key.

This is a coordinated nintent/nctl GraphQL break. Old nctl asks for `placement_policy` and cannotrussia stock
run against the new schema; the matching nctl revision removes that query field. No dual query or
feature detection is added.

### 7. Derived caches are read-only, and service REST/status push must work

Remove `last_import_status` and `last_import_summary` from `IntentSourceForm.Meta.fields` while
retaining them on source detail/list pages as Job-derived values. `last_imported_at` stays unchanged.
No migration is needed.

Fix the service serializer by declaring `intent_source` as an ID-based related field rather than an
auto-generated hyperlink to the absent `intentsource-detail` route. Mark `analysis_provenance` and
`last_analyzed_at` read-only. Keep `reconciliation_status` and
`reconciliation_checked_at` writable because nctl dashboard is their intentional sole writer.

Test service GET/list/create/PATCH with non-null `intent_source`, including the exact dashboard
status-only PATCH. Remove the recipe's stale “REST is broken but nctl is unaffected” note only
after this path works against deployed Nautobot.

### 8. Analyze dependencies by natural-key diff instead of delete/recreate

For one analyzed service, key dependencies by
`(dependency_kind, namespace, name)`, matching `nic_unique_dependency_ref`:

- create new keys with `resolution_status=unresolved`;
- update source-owned `raw_ref` and `dependency_type` on retained keys;
- preserve retained `notes`, `resolution_status`, and `resolved_service`;
- delete keys no longer present in the source analysis; and
- reject duplicate normalized input keys before any write.

Wrap the service update and dependency sync in one transaction. Report created/updated/deleted/
unchanged counts instead of the obsolete `dependencies_replaced` count. This preserves intentional
operator notes and separately computed resolution while still allowing removed source intent to
disappear.

Consolidate default ownership at the same time: analysis/loader normalization produces complete
`dependency_type`, `namespace`, `resolution_status`, and endpoint `ip_policy`; importer helpers
validate/project those values without a second fallback layer.

### 9. Keep `nauto/seed/service_repositories.yaml` under its actual owner

Do not rename its root to `intent_sources` and do not feed it to nintent's strict loader. It is a
valid, separately owned input to nauto's registered `Generate Desired Services` candidate-generation
Job. Update Phase 0's living classification note and current nauto/nintent docs to state the two
formats and ownership boundaries explicitly:

- `service_repositories` → nauto candidate generation only, not authoritative desired state;
- `intent_sources` plus desired objects → nintent strict ledger import.

Add a small nauto loader/Job fixture test proving the current file parses through its actual reader,
and retain nintent's rejection test proving the same root is invalid there. This resolves the audit
item with evidence rather than deleting a live workflow.

### 10. Rewrite recipes around one ordinary convergence path

Create `nctl/docs/register-a-new-pc.md` and rewrite
`nctl/docs/add-a-basic-service.md`. The current path is GUI-first for ledger writes and nctl-first
for feedback/actuation; it must not require `nautobot-server shell`.

The new-PC recipe literally covers:

1. one-time manual `IntentSource` prerequisite, if none exists;
2. Quick Host Add with only genuine identity/address/publishing choices;
3. the visible derived node type, accepted actual types, lifecycle, DNS/mDNS names, and their
   override controls;
4. `nctl drift --host NODE` to inspect recorded/effective/application layers before mutation;
5. `nctl reconcile NODE` to review the bounded plan;
6. `nctl reconcile NODE --yes` for bootstrap collection, ingest/link/IPAM, production render, andrussia stock
   verification; and
7. a final host-scoped drift whose remaining INFO summary explains the chosen mechanism.

The basic-service recipe covers DesiredService + DesiredServicePlacement through Nautobot CRUD,
keeps service lifecycle `active` explicit (Phase 3 intentionally retained its `proposed` default),
then uses dry/apply reconcile and verifies the placement effect. It explains that deployment profile
and non-default `config` are genuine placement intent. The dnsmasq-self-bootstrap inventory override
is a clearly labeled exception, not the ordinary service path.

Document blank `IntentSource.ref` exactly as implemented: analysis tries a discovered repository
default branch first, then the deduplicated `HEAD`, `main`, and `master` fallbacks. An explicit ref
wins and is tried first.

Update `nctl/README.md`, `nintent/README.md`, `nintent/README_QUICK.md`, and the root README links.
Keep historical scenario transcripts unchanged but add narrow supersession links where a reader
might otherwise copy obsolete shell/manual-inventory steps.

## Finding and output integration

| Code | Target/severity | Message/evidence | Dashboard/status effect | Reconcile behavior |
|---|---|---|---|---|
| `intent_effect_summary` | node / INFO | recorded intent, operational value records/finding, production and placement effects | detail only; never changes status | intentionally absent from classification and semantic fingerprint |
| `deployment_profiles_unavailable` | global / ERROR | configured profile path plus bounded parse/contract reason | global red/failed feedback; no node status write-back | `MANUAL_REVIEW`; global blocker before any action |
| existing production local codes | node / ERROR | report-3.0 node finding with stage/evidence | node drifting/unknown under existing rules | retain existing classification and target pruning |
| `active_placement_not_applied` | node / WARNING | full placement intent and out-of-scope lifecycle reason | visible detail; warning-only target stays converged | retain `MANUAL_REVIEW`, target-local |

No nintent form/API validation error becomes a drift code. Quick Add, service REST, import, and Job
errors stay request/Job-scoped and perform no partial write. No new warning is silently omitted from
reconcile; the table above is exhaustive for new drift vocabulary.

## Reader/writer and transition matrix

| Boundary | Phase 4 contract | Required change | Tests |
|---|---|---|---|
| nintent model/migration | generic endpoint policy `external`; separate analysis provenance; no placement policy | `AlterField`, `AddField`, reversible data split, guarded `RemoveField` | migration operation/data/reverse tests and live preflight |
| IntentSource form/detail | Job caches visible but not editable | remove two form fields; retain read-only rendering | form field set and Job update visibility |
| DesiredService form/detail | requirements remain intent; analysis provenance labeled derived; no inert field | form/template updates | bound-form preservation and rendered separation |
| Quick Host Add | `device` default; derivation preview + optional accepted-type override; contextual endpoint policy visible | form, operation, template, small progressive JS | default/override, JS-independent POST, invalid values, atomicity |
| regular endpoint form/model | generic omission is external/not published | model default/help and migration | model/form/REST omission and explicit policies |
| strict YAML loader/import | complete normalized values; removed field rejected | remove duplicate importer fallback; keep strict unknown-key behavior | omission/explicit/update/idempotence |
| analysis importer/Job | provenance separate; requirements preserved; dependencies diffed | importer shape and transactional sync | create/update/delete/duplicate/rollback and notes/link preservation |
| REST serializers/ViewSets | service relation serializes without absent URL; derived analysis read-only | explicit related/read-only fields | GET/list/POST/PATCH and dashboard status-only PATCH |
| GraphQL/nctl desired source | no `placement_policy`; other intent needed for feedback is typed | coordinated query/model cutover | exact query fixture and old-field absence |
| production adapter/composer | one report node per desired node | enrich NodeInput/PlacementInput and report builder | included/skipped/out-of-scope/mixed placement matrix |
| production contract/render | inventory `2.0`, report `3.0`, no old report collections | split version constants and closed validator | reject report 2.0/extra keys; preserve inventory bytes |
| drift text/JSON | one `intent_effect_summary` per node plus existing actionable findings | comparator translation and compact renderer | exact evidence/source badges and host filtering |
| dashboard/status cache | same summary evidence; status push works for services | dashboard presentation + serializer fix | HTML evidence, push success/failure isolation |
| reconcile planner/executor | INFO ignored; global profile error blocks; local codes still prune only their node | classification/fingerprint updates | mixed good/bad, plan/apply, no unclassified code |
| nauto candidate seed | `service_repositories` retained under nauto | docs/classification + reader test only | actual-reader parse; nintent rejection retained |
| recipes | literal UI + drift + reconcile path | rewrite/add docs and links | command/help/path grep and scenario execution |
| live rows | no node/default bulk rewrite; service JSON moved safely | read-only counts/export before migration | post-migration value/count comparison |

## Mandatory Phase 0 gate coverage

1. **Failure scope:** the only new drift error is shared profile unavailability and is explicitly
   global. Every node/placement composition failure remains in its report node and blocks only that
   target. Form/import/analysis errors remain request/Job-scoped and transactional.
2. **End-to-end findings:** the finding table specifies target, severity, evidence, dashboard/status
   effect, and reconcile behavior. All reachable error codes are covered by classification; the new
   INFO record is intentionally omitted and tested as such.
3. **Readers and writers:** the matrix covers model, forms, Quick Add operation/template, REST,
   GraphQL, YAML/import Jobs, analysis Jobs, seed ownership, typed snapshots, composer, output
   contracts, drift/dashboard/status, reconcile, docs, tests, migration, and live rows.
4. **Overrides and provenance:** Quick Add distinguishes derived preview from an explicit override;
   report/drift expose every operational source and whether override won; generic versus contextual
   endpoint defaults are visible and documented; analysis metadata can no longer masquerade as
   operator requirements.
5. **Schema/data transition:** Decision 6 defines the reversible JSON split and guarded removal;
   Decision 3 splits report/inventory versions; the coordinated rollout and rollback below prohibit
   a mixed GraphQL window or compatibility shim.
6. **Isolation and orchestration:** Steps 4.4–4.7 cover pure contracts, text/dashboard rendering,
   mixed healthy/malformed nodes, global-profile failure, reconcile plan/apply behavior, and the
   literal current new-PC/basic-service scenarios.

## Step 4.1 — Freeze baselines, live data, and executable contracts

1. Run and record the nintent, nctl, and relevant nauto test baselines in `p4/report4.1.md`.
2. Read-only query live counts and values needed for migration safety: service `requirements`,
   `placement_policy`, dependencies/resolution links, endpoint policies/publishing flags, source
   cache fields, and node type/accepted-type pairs. Record bounded summaries, not credentials or
   unrestricted actual facts.
3. Assert every live `placement_policy` is empty. If not, stop this removal, export the values, and
   amend this plan/classification with a real consumer or intentional data mapping before coding.
4. Save representative pre-change GraphQL, `nctl drift --host`, dashboard drift JSON, production
   report `2.0`, and service REST/status-push fixtures with secrets removed.
5. Add failing contract tests for report `3.0`, `intent_effect_summary`, the two new drift-code
   classification expectations, service REST, migration JSON split, and dependency sync before
   implementing them.

## Step 4.2 — Land the complete nintent schema and creation-surface batch

In one nintent commit/rebuild batch:

1. add read-only `analysis_provenance` and remove `placement_policy` with migration `0013_*`;
2. implement the reversible legacy-analysis-key split and the non-empty-placement-policy guard;
3. alter the generic endpoint `ip_policy` default to `external` without changing existing rows;
4. remove source Job caches from the edit form and separate service intent/analysis detail sections;
5. make Quick Add default to `device`, expose the accepted-type derived preview/override, and share
   named contextual endpoint defaults with the host operation;
6. make the generic loader/importer boundary produce/project one complete endpoint policy;
7. fix DesiredService REST relation/read-only fields and prove dashboard PATCH response serialization;
8. remove every `placement_policy` reader/writer/test/doc reference inside nintent; and
9. generate/check migrations, run the full local suite, and inspect the migration file for any
   unintended row rewrite.

Do not rebuild Nautobot yet; the old nctl GraphQL query is incompatible with this schema.

## Step 4.3 — Make analysis updates provenance-safe and dependency-stable

1. Change analyzed-service defaults into create defaults plus update-owned fields, so an analysis
   refresh never replaces operator `requirements`.
2. Store normalized analysis metadata only in `analysis_provenance` and reject unexpected keys at
   the helper boundary.
3. Implement a pure dependency diff plan and a transactional ORM applier using the natural key.
4. Preserve notes/resolution/link for retained dependencies, delete source-removed keys, and reject
   duplicates before service/dependency writes.
5. Replace `dependencies_replaced` reporting with created/updated/deleted/unchanged counts.
6. Test first analysis, identical re-analysis, changed source fields, removal, addition, duplicate
   input, injected mid-transaction failure, and preservation of manually edited retained fields.

## Step 4.4 — Cut nctl to the reduced GraphQL shape and report schema `3.0`

1. Remove `placement_policy` from `DESIRED_QUERY`, typed service models, builders, evaluation facts,
   fixtures, and docs. Do not accept both GraphQL shapes.
2. Extend typed node/placement inputs only with the bounded recorded-intent fields required by the
   feedback contract, including service identity and assignment source.
3. Split inventory/report version constants. Keep generated inventory and Ansible host/group bytes
   unchanged for identical inputs.
4. Replace report `2.0`'s parallel node collections with deterministic report `3.0` `nodes` records.
5. Validate exact keys/enums/value-records/finding evidence; reject report `2.0`, partial node
   records, duplicate node/placement IDs, and placement effects that contradict node state.
6. Test all lifecycle/type scope states, successful derivation, derivation failure, later-stage
   local failure, active/disabled placements, mixed good+bad nodes, override wins, and no profiles.

## Step 4.5 — Consolidate drift text, dashboard, status guidance, and reconcile

1. Translate each report node into exactly one `intent_effect_summary` and its actionable
   findings; delete the old provenance builder/code.
2. Preserve the profile-load exception in drift context and emit
   `deployment_profiles_unavailable` globally instead of silently running with `{}`.
3. Add compact deterministic intent/effective/application text, with explicit derived/default/
   override labels and no arbitrary config-value dump.
4. Render the same sections and badges in the dashboard while retaining expandable raw evidence.
5. Update reconcile classification, global/local blocker handling, semantic fingerprint, and
   closed code-coverage tests in the same commit.
6. Keep `nctl.status.v1` health-only; update text/help/docs to direct per-target questions to drift.
7. Prove dashboard service status write-back succeeds on the new nintent serializer and that one
   failed target PATCH still does not block others.

## Step 4.6 — Correct residual ownership docs and rewrite the recipes

1. Update Phase 0's living artifact with the Phase 4 decisions and evidence: contextual Quick Add
   policy, removed placement policy, separated analysis provenance, and valid nauto seed ownership.
2. Add a nauto test that parses the checked-in `service_repositories.yaml` through
   `GenerateDesiredServices`' actual loader. Keep nintent's explicit rejection test.
3. Write `register-a-new-pc.md` and replace the shell example in `add-a-basic-service.md` with the
   current CRUD + drift + reconcile flow.
4. Reconcile the bootstrap descriptions: `hosts_intent.yml` is an SSH bootstrap inventory, while
   service actuation normally uses production inventory; document the dnsmasq override exception
   exactly once and link to it.
5. Document blank-ref resolution, generic versus Quick Host endpoint defaults, deliberate staging,
   override entry points, and how to read the three feedback layers.
6. Update current README/index links and add narrow supersession notes to historical scenario docs;
   do not rewrite dated reports as if they described current code.
7. Grep current docs for `DesiredNodeOperationalConfig`, default-planned claims, shell-only service
   creation, report schema `2.0` claims, `placement_policy`, stale REST warnings, and conflicting
   bootstrap group claims.

## Step 4.7 — Test the literal isolation and orchestration matrix

Run the full component suites plus an integration matrix containing:

- a new default device with one primary endpoint, fresh Linux/macOS observation, no operational
  override, and no accepted-type override;
- an explicit VM/service-host accepted-type override, proving the preview never becomes false
  persisted intent;
- generic endpoint omission versus Quick Host contextual DNS publishing, with and without an IP;
- one healthy active node beside ambiguous-endpoint, stale-observation, invalid-placement-config,
  planned-with-active-placement, and unsupported-node-type neighbors;
- derived, safe-default, and explicit override records in text, JSON, dashboard, and report `3.0`;
- placement `applied`, `inactive_by_intent`, and each `not_applied` route;
- missing/malformed shared profiles blocking globally with a classified code;
- cluster and host-scoped dry reconcile retaining independent healthy actions and ignoring only the
  INFO summary semantically;
- service analysis refresh preserving requirements and dependency notes/resolution/link;
- service REST list/detail/status PATCH with non-null source; and
- report/inventory artifact writes proving inventory `2.0` remains byte-stable while report `3.0`
  is closed and deterministic.

Then follow both recipes literally in an isolated fixture environment. A live disposable node or
service row may be used only with operator authorization; otherwise use an existing reviewed target
for read-only/dry paths and prove creation/deletion through the integration harness. Do not claim
the roadmap exit criterion from doc review alone.

## Step 4.8 — Coordinated rollout and live-safe verification

1. Confirm clean component worktrees and matching revisions; back up the Nautobot database.
2. Re-run the live preflight and export bounded service requirements/analysis/dependency data plus
   placement-policy emptiness for comparison.
3. Have the user push the complete nintent commit. Rebuild/recreate web, worker, and scheduler once;
   apply migration `0013_*`, run `showmigrations`, `check`, and
   `makemigrations --check --dry-run`.
4. Switch immediately to the matching nctl revision; do not operate old nctl against the removed
   GraphQL field.
5. Verify service REST list/detail and a status-only PATCH, source cache read-only UI, Quick Add
   defaults without creating a row, and the exact new GraphQL shape.
6. Compare pre/post service requirements, analysis provenance, dependencies, endpoint values, and
   node rows. Confirm migration changed no lifecycle, node type, endpoint policy value, or
   placement intent already stored.
7. Run `status`, host-scoped/full drift, production render without write, dashboard `--no-push`,
   and dry reconcile. Confirm every desired node has one summary and every existing actionable code
   remains classified.
8. With operator approval, run dashboard status push and only the reviewed recipe/reconcile apply
   paths. Known stale/unreachable infrastructure may remain visible; do not mutate intent merely to
   make the result green.
9. Record revisions, migrations, counts, test totals, report schema, recipe outcome, and any
   infrastructure limitation in `p4/report4.8.md`. Commit no token, unrestricted live fact,
   generated inventory/report, dashboard payload, or DB backup.

### Rollback boundary

Before migration, rollback is simply the preceding component revisions. After migration but before
new analysis runs, reverse `0013_*`, restore the old nctl revision, rebuild Nautobot, and verify the
reverse merge of analysis keys plus recreated empty `placement_policy`. If reverse migration or
post-migration writes make that unsafe, restore the pre-Phase-4 DB backup and both preceding
component revisions. Do not run old nctl during the new-schema interval, and do not add a temporary
GraphQL compatibility field to avoid this coordinated rollback procedure.

## Out of scope

- A second target-status implementation inside `nctl status` or a new `nctl explain` command.
- User/role permissions, approval separation, audit policy, or lifecycle transition enforcement.
- Changing node lifecycle defaults/states or service lifecycle's deliberate `proposed` default.
- New placement solvers or making service lifecycle/requirements automatically choose a node.
- Inferring placement `config`, IP ownership, or DNS publication when the operator has not selected
  the relevant contextual policy.
- Changing Ansible inventory schema/groups/variables or deployment-profile schema.
- Replacing nauto's candidate-generation workflow; this phase only clarifies its seed ownership.
- Repairing live SSH, nodeutils freshness, DNS, or service infrastructure merely exposed by the
  improved feedback.
- Rewriting dated design reports or historical transcripts beyond narrow current-path links.

## Exit criteria

- Every desired node has exactly one human- and machine-readable intent/effect summary showing
  recorded intent, effective derived/default/override values, and application/placement effect.
- Drift text, JSON, dashboard, and production report agree because they consume one report-node
  contract; recorded-but-not-applied intent always carries a reason.
- Production inventory remains schema `2.0` and byte-stable for equal inputs; the closed companion
  report is schema `3.0` and represents included, skipped, and out-of-scope nodes uniformly.
- Shared profile failure is a classified global blocker; all target-owned failures stay local and
  cannot suppress a healthy neighbor's plan/action.
- Quick Host Add defaults to `device`, exposes accepted-type derivation and overrides, and makes its
  contextual endpoint/DNS policy visible rather than accidental.
- IntentSource caches and service analysis provenance are read-only; operator requirements survive
  analysis; inert `placement_policy` and all runtime readers/writers are deleted.
- Re-analysis diffs dependencies without losing retained notes/resolution/link state.
- Service REST and dashboard status write-back work with non-null intent sources.
- The nauto `service_repositories` seed is proven valid under its real owner and explicitly invalid
  for nintent import; no misleading rename is made.
- A literal current “register a new PC” then “add a basic service” flow reaches a freshly checked
  converged result with only genuine intent supplied, or records an honest infrastructure finding
  without a hidden mechanism/manual-promotion step.
- Full suites, migration forward/reverse checks, mixed-node orchestration, docs grep, and coordinated
  live verification pass and are recorded in Phase 4 reports.

## Suggested commit order

1. **Contracts/tests:** frozen report `3.0`, drift-summary, migration, REST, and dependency-sync
   executable contracts.
2. **nintent batch:** migration `0013_*`, forms/Quick Add, analysis/dependency update, serializer,
   templates, and full nintent tests in one deployable rebuild unit.
3. **nctl GraphQL/report batch:** reduced query, typed inputs, split versions, report `3.0`, and
   closed composer/contract tests.
4. **nctl feedback/orchestration:** drift text/JSON/dashboard, profile failure, classification,
   fingerprint, status guidance, and full reconcile tests.
5. **nauto/docs:** seed ownership test, classification update, recipes, current README links, and
   literal scenario verification.
6. **Deployment report:** user push/rebuild/migration, matching nctl cutover, read-only comparison,
   approved live checks, and final Phase 4 report.

Commits may be developed and reviewed independently, but commits 2–4 form one coordinated runtime
cutover. Never deploy the nintent field removal without the matching nctl query removal, and never
split the nintent schema/form/analysis batch across multiple Nautobot rebuilds.
