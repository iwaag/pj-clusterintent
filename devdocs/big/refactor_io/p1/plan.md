# Phase 1 Plan — Reusable Batch Planning and Apply Service

Status: **planned** (implementation not started).

Input contract: [`../p0/report.md`](../p0/report.md). This document does not restate the field
classification, the batch envelope, or the identity table — read Phase 0 for those and treat them
as fixed.

## Goal

nintent gains one importable service that takes a decoded batch document in memory, plans it
without writing, and applies an accepted plan in a single transaction. No HTTP, no server-side
file path, no Job is required to call it.

The reduced field set from Phase 0 lands in the same phase, so the service is built against the
final schema instead of a schema that is about to shrink.

## Scope

In scope:

- Django-free request decoding, per-kind validation, and planning.
- ORM apply in one `transaction.atomic()` block, plus a post-commit confirmation refetch.
- Explicit `delete` with reference checks and deterministic ordering.
- The Phase 0 schema reduction in nintent (migration + code + UI + serializers + fixtures).
- The matching nctl **read-side** changes, because nctl selects several removed fields today.
- Re-pointing the existing `Import Intent Sources` Job at the new service so only one planner and
  one apply path exist.

Out of scope (later phases): the REST endpoint (Phase 2), nctl write-path cutover to the endpoint
(Phase 3), removal of `nauto/seed/intent_sources.yaml` and the Import Job itself (Phase 3/4), any
deployment of the rebuilt Nautobot image (Phase 2).

## Design decisions to implement

These are the decisions Phase 0 left to Phase 1. Everything not listed here — module layout, class
vs. function style, naming, error wording — is the implementer's choice.

### 1. Per-kind specification instead of per-root loaders

Today `loaders.py` normalizes nine whole YAML roots into nine strict entry dataclasses. Replace
that with one spec per `kind` covering: target model, key fields, per-field coercion/validation,
the set required when creating, reference fields and the kind they point at, and the relations
that block a delete.

Consequence: validation becomes per-field, not per-entry. Field rules run over exactly the keys
present in `values`. The required-field set is enforced **only** when the operation creates a new
row. The existing strict rules (unknown key rejected, slug/choice/address/port validation,
in-document duplicate detection) carry over; reuse the current helper functions rather than
rewriting them.

`desired_dependency` has no YAML root today (it was written only by the Analyze Job). It is a
first-class batch kind from this phase on.

### 2. Partial upsert semantics

- `values` keys present → planned against the stored row; keys absent → untouched and reported as
  preserved. Explicit `null` clears a nullable field.
- `IntentSource` identity is always `slug`. The current `url`-based identity for
  `source_type: git_repository` disappears with the field.
- Keep `plan_upsert()` in `import_plan.py` as the single create/update/unchanged/conflict decision
  function. Its `locked_fields` argument exists for the Analyze/YAML ownership split that this
  phase deletes; drop it if nothing needs it after the reduction.

### 3. Deletion

- A delete is planned as `delete` when the row exists, `unchanged` when it does not (a delete is
  idempotent, not an error).
- Reference check is evaluated against the **post-batch** state: a delete conflicts if any desired
  row would still point at the target after every operation in this batch is applied. Do not rely
  on FK `CASCADE` or `PROTECT` to produce that answer — check it in the planner so the caller sees
  a `conflict` with the blocking rows named.
- Apply order: upserts in reference order (source → node → ip range → endpoint → platform →
  instance → service → dependency → placement → override), then deletes in reverse order.

### 4. Result shape

One versioned artifact (`nintent.desired-state-batch.v1` or similar), deterministic for identical
input, containing per-operation `create | update | delete | unchanged | conflict` with identity,
changed fields, conflict reasons, totals, and the transaction outcome. Reuse the ideas in
`build_artifact()`; do not keep both the Import and Analyze artifact shapes.

Nothing about the request or the result is persisted.

### 5. Service surface

Roughly:

```python
plan_batch(document: dict) -> BatchResult          # never writes
apply_batch(document: dict) -> BatchResult         # plans, then commits once if clean
```

Both must be callable from a plain Django test without HTTP. YAML/JSON decoding to `dict` belongs
to the caller (Phase 2's endpoint, or the Import Job adapter).

## Steps

One commit and one short report entry per step, as usual.

### Step 1 — Schema reduction (nintent)

Delete every field in the Phase 0 removal column with one ordinary Django migration, and remove
their readers in the same commit: model fields, serializers, filters, tables, templates, loader
normalization, importer helpers, and tests.

This also removes the `Analyze Intent Sources` Job, `analysis.py`, `analysis_plan.py`, the analysis
artifact shape, and the analysis-owned importer helpers — the Job's entire output is either a
removed field or `DesiredDependency`, which becomes a batch kind.

`nauto/seed/intent_sources.yaml` must lose the removed keys too, or the strict loader will reject
it as unknown-key input. Keep the file for now; Phase 4 deletes it.

Watch for: `provider_type` and `config_schema_version` on the compute platform/instance are fixed
discriminators — their validation moves into `compute_contract.py` code in this same commit, it is
not dropped.

### Step 2 — nctl read-side alignment

nctl currently selects and uses removed fields. Required changes:

- `nctl_core/sources/desired.py` — drop the removed selections and dataclass fields
  (`realized_device_source`, `dns_name_source`, `mdns_name_source`,
  `realized_ip_address_source`, `instance_role`, `assignment_source`, `display_name`,
  platform/instance `provider_type` and `config_schema_version`). `DesiredServicePlacement`
  **keeps** `config_schema_version`.
- `nctl_core/reconcile/ledger.py` — the `link_actual_node` guard and its post-PATCH confirmation
  currently read and write `realized_device_source`. Base both on `realized_device_id` alone and
  stop sending the `_source` field in the PATCH body.
- `nctl_core/compute/` — stop reading the removed discriminators; Proxmox/v1 is a code constant.
- `nctl_core/production/` — drop `instance_role`/`assignment_source` from the placement model,
  adapter, report, and allowed-key list.

Regenerate the compute conformance fixture; owner and consumer fixtures must match again.

These changes are forward-compatible: a query that stops selecting a field works against both the
currently deployed nintent and the reduced one, so nctl stays usable throughout the phase.

### Step 3 — Kind registry and request decoding

Envelope validation (`dry_run`, `operations[]`, `op`, `kind`, `key`, `values`), per-kind specs, and
per-field validation. Pure Python, no Django import, unit-testable directly.

### Step 4 — Planner

Read existing rows through `.values()` into plain dicts, resolve references against the union of
stored rows and rows created earlier in the same batch, and produce the full result artifact.
Unresolved or ambiguous references and blocked deletes are `conflict`s, never exceptions — one bad
operation must not stop the rest of the batch from being planned and reported.

### Step 5 — Apply

`apply_batch()` plans first, refuses to write if the plan has any conflict or error, then applies
inside one `transaction.atomic()` with `full_clean()` on every touched row. Any failure aborts and
rolls back the whole batch. Confirm the committed identities with a post-commit refetch and report
mismatches truthfully rather than assuming success.

### Step 6 — Import Job becomes a thin adapter

`Import Intent Sources` keeps its file input and its `apply` toggle, but its body becomes: read the
file → map the nine YAML roots to `upsert` operations → call the service → render the result. The
duplicate `_plan_import`/`_apply_import`/`_confirm_import` implementations in `jobs.py` are deleted
in this commit. The Job never deletes rows; omission stays non-destructive.

### Step 7 — Verification and report

Run the gates below, write `devdocs/big/refactor_io/p1/report.md` results into a Result section,
and stop. No push, no image rebuild, no deployment.

## Tests

New coverage (place each at the lowest layer that can prove it):

- Django-free: envelope and per-field validation errors, unknown kind/field, missing key, required
  field missing on create, partial `values` preserving untouched fields, in-batch reference
  resolution, delete-blocked-by-reference, deterministic result ordering.
- Django runtime: `dry_run` performs zero writes; mixed create/update/delete commits atomically;
  one invalid operation anywhere leaves every row unchanged; delete ordering works for a
  node with endpoints and placements; a `full_clean()` failure during apply rolls back.
- The existing `test_jobs_import` scenarios must still pass through the adapter.

Gates for this phase:

| gate | command |
|---|---|
| nintent Django-free fast | `python3 -m unittest discover -s nautobot_intent_catalog/tests` (from `nintent`) |
| Nautobot runtime clean | `./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean` |
| nctl ordinary | `uv run pytest -q --durations=20` (from `nctl`) |
| compute conformance | `uv run --project nctl pytest -q devtests/test_strategy/test_compute_conformance.py` |
| nauto ordinary | `python3 -m unittest discover -s tests` (from `nauto`) |

The runtime gate copies the local checkouts into the Nautobot container, so the migration and the
service are fully verifiable before anything is pushed or rebuilt. If the Django-free suite's
expected skip count changes, update the number in `README_DEV.md`.

## Prohibitions

Only these:

1. `dry_run` writes nothing, and an accepted batch is applied completely or not at all.
2. No second desired-state planner or apply implementation survives Step 6.
3. No new persistent model, field, or table — no request archive, import history, or revision row.
4. No compatibility shims for removed fields: no aliases, no default-value stand-ins, no readers
   kept "just in case".
5. No deployment in this phase — commit locally, leave the push and image rebuild to Phase 2.

Everything else is at the implementer's discretion.

## Exit criteria

- `plan_batch()`/`apply_batch()` are importable and tested without HTTP.
- Tests prove: dry-run writes nothing, apply is atomic, references resolve within one batch,
  explicit delete works and is blocked when something still points at the target, and invalid
  input leaves current state unchanged.
- The Phase 0 removal set is gone from nintent, with migrations applied cleanly on the scratch
  database, and nctl reads and reconciles against the reduced schema.
- All gates above pass and every worktree is clean.

## Known risks

- **nctl coupling is real, not cosmetic.** `realized_device_source` is a guard condition and a
  confirmation assertion in the ledger reconciler; removing it changes behavior, not just a
  selection list. Keep the guard (refuse to relink an already-linked node) using
  `realized_device_id`.
- **Strict loading of the seed file.** Reducing model fields without reducing
  `nauto/seed/intent_sources.yaml` turns the Import Job red on unknown keys.
- **Partial `values` vs. today's whole-entry validators.** This is the largest refactor in the
  phase; budget for it rather than trying to reuse the entry dataclasses unchanged.
