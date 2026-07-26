# Phase 4 Step 1 — Open Problem: `link_actual_node` mutation evidence lost on post-PATCH confirmation failure

Found while adding [report1.md](report1.md) Section 8's missing nctl node-link boundary tests.
Not fixed in Step 1 (test/documentation scope only); recorded here for an explicit decision
before Step 2 or later relies on `reconcile`'s progress/convergence accounting.

## Where

`nctl/src/nctl_core/reconcile/executor.py`, `_execute_action()`'s
`except (LedgerActionError, NautobotJobError, NautobotError)` branch (around line 805), together
with `_execute_round()`'s `had_side_effects` accumulation (lines 552 and 618) and
`_run_apply()`'s `data.progress_made` computation (line 500).

## What happens

`execute_link_actual_node()` (`nctl_core/reconcile/ledger.py`) does, in order:

1. GraphQL precondition read (refuse to replace an existing link).
2. `PATCH /api/plugins/intent-catalog/nodes/<id>/` — this is the actual write.
3. A post-PATCH GraphQL refetch that must confirm the exact link landed.

If step 3 disagrees with what step 2 just wrote, it raises `LedgerActionError` with code
`node_link_not_confirmed` or `node_link_source_not_confirmed`. At that point **the PATCH in step
2 has already succeeded and the database row is already mutated** — the error is about
confirmation, not about whether a write happened.

`_execute_action()` catches this and builds:

```python
result = ActionResult(
    action_id=action.id,
    reconciler_id=action.reconciler_id,
    action_kind=action.action_kind,
    target_slugs=target_slugs,
    success=False,
    error=f"{code}: {exc}",
)
```

`ActionResult.mutated` is not set here, so it defaults to `False` — even though a real write just
happened. Two consumers then read `mutated`/`success` in a way that under-counts this case:

- `_execute_round()`: `had_side_effects = had_side_effects or executed.result.success` (both the
  bootstrap-phase and service-phase loops) — reads `.success`, not `.mutated`.
- `_run_apply()`: `data.progress_made = any(action.success or action.mutated for ... )` — this one
  *does* check `.mutated`, but since `.mutated` was never set `True` for this action, it doesn't
  help.

Net effect: a round whose only action is a `link_actual_node` that PATCHed successfully but
failed confirmation is reported with `had_side_effects=False`. Per the comment at
`_run_apply()` lines 453-463, `had_side_effects` is what decides whether a fresh post-mutation
drift snapshot is fetched before the run reports failure — so this specific failure mode can
report a stale, pre-mutation drift as if it were current, even though the live row was actually
changed.

## Why this wasn't just fixed here

The `mutated` field exists specifically to distinguish "a write happened" from "the action fully
succeeded" — precedent: `reconcile_ipam`'s `ipam_policy p6 Step 4` decision, which sets
`mutated=bool(ipam_result.applied_endpoint_ids)` independent of `success` for exactly this reason
(a partially-applied IPAM Job run still mutated some rows even though the action as a whole
isn't `success`). The same reasoning applies to `link_actual_node`'s post-PATCH confirmation
failure — but fixing it means either:

- setting `mutated=True` in `_execute_action`'s except branch specifically for
  `node_link_not_confirmed`/`node_link_source_not_confirmed`, and/or
- changing `_execute_round`'s `had_side_effects` checks from `.success` to `.mutated`.

The second change is not local to `link_actual_node` — it would also change behavior for every
other reconciler's failed-but-partially-mutated case (e.g. `reconcile_ipam`, where
`had_side_effects` today is likewise driven by `.success` only, so a partial IPAM apply that
overall fails also doesn't currently trigger a post-failure drift refresh by itself). That is a
behavioral change to `reconcile`'s convergence/progress semantics across multiple reconcilers, not
a test-coverage gap, and outside Interface Contract Phase 4 Step 1's authorized scope (source/
test/documentation repair only, per `plan.md` Section 3.4). It also was not part of Interface
Contract Phase 3's original scope at all — `link_actual_node`/`reconcile_ipam` execution belongs
to the separate `ipam_policy`/reconcile-executor line of work, not to the nintent UI/API/GraphQL
contraction this Phase 4 plan governs.

## Current state

- Not fixed. No production code changed.
- Test coverage added instead:
  `nctl/tests/test_reconcile_executor.py::test_link_actual_node_confirmation_failure_after_successful_patch_is_recorded_not_dropped`
  proves the failed `ActionResult` (with its error code) survives in `RoundSummary.actions` and
  does not terminate the round — i.e. the record itself is not silently dropped, only its
  `mutated`/`had_side_effects` accounting undercounts it.
- `mutated=False` on `ActionResult` for this exact failure path is asserted implicitly (the test
  does not assert on `mutated`, but the fixture's monkeypatched `execute_link_actual_node` raises
  before returning a result, so the code path exercised is exactly the one described above).

## Decision needed

1. Fix `link_actual_node`'s post-PATCH-confirmation-failure `ActionResult.mutated`, leaving
   `had_side_effects`'s `.success`-only check as-is elsewhere (narrowest fix, but
   `had_side_effects` still won't pick it up since it also reads `.success`).
2. Fix both: set `mutated=True` for this failure code *and* change `had_side_effects` to read
   `.mutated` — but audit every other reconciler's failure path (at minimum `reconcile_ipam`) for
   the same gap before changing shared round logic.
3. Leave as-is and treat a post-PATCH confirmation failure as an operational anomaly serious
   enough that a stale drift snapshot on report is an acceptable, rare cost (current behavior).
4. Something else — e.g. surface a distinct terminal/manual-review state for "write succeeded,
   confirmation failed" instead of folding it into ordinary action failure.

This is a separate decision from Interface Contract Phase 4's own step sequence and does not
block Step 2.

---

# Phase 4 Step 6 — Open Problem: official live Import preview overwrites live `description`/`notes`
that were never captured in `intent_sources.yaml`

Found while running Step 6's official `apply=false` `Import Intent Sources` Job against live
Nautobot (`report6.md`). Step 6 was stopped before requesting apply approval; recorded here for
an explicit user decision before apply.

## Where

- Live artifact: `.local/interface-contract/p4/20260726_step6/intent-import-result.json`
  (`nintent.intent-import.v1`, `mode: preview`, `totals: {create: 0, update: 13, unchanged: 9,
  conflict: 0}`).
- Field ownership: `nintent/nautobot_intent_catalog/importers.py:321-331`
  (`desired_node_update_fields()` excludes only `lifecycle` from the fields Import may overwrite
  on an existing `DesiredNode`; `description` and `notes` are not excluded). `DesiredEndpoint` and
  `DesiredIPRange` have no excluded fields at all, so their `description` is always in
  `update_fields`.
- Ledger check: `devdocs/big/interface_contract/p0/report7.md`'s "Ownership rules frozen" section
  names only `lifecycle` (create-only, nctl-owned after creation) and, separately, `DesiredService`
  `lifecycle`/`requirements`/`notes` (analysis-owned, preserved). It says nothing about
  `DesiredNode`/`DesiredEndpoint`/`DesiredIPRange` `description`/`notes` being safe to overwrite.

## What happens

`nauto/seed/intent_sources.yaml` has never carried a `description` or `notes` key for any
`desired_nodes`/`desired_endpoints`/`desired_ip_ranges` row (confirmed by reading the checked-in
file). The five live `DesiredNode` rows, however, carry human-written `description` values from
before this file existed:

| Node | Live `description` (would become `null` on apply) |
|---|---|
| `agbach` | "main macbook" |
| `agdnsmasq` | "dnsmasq should be running on VE or light PC" |
| `aghub` | "proxmox VE mini pc" |
| `agpc` | "powerful ubuntu with graphic card" |
| `agstudio` | "powerful mac studio" |

Because the plan engine (`import_plan.py:plan_upsert`) treats any `update_fields` key present in
`create_fields` but absent from the YAML row as `None`, and diffs that against the stored value,
each of these rows is planned as an `update` that nulls the field. The remaining 6 updates in the
same preview are cosmetic (`notes: '' -> None`, `DesiredEndpoint`/`DesiredIPRange`
`description: '' -> None`) and the 2 `IntentSource.source_config` updates are benign schema-default
population (`{} -> {computed defaults}`), not data loss. Only the 5 `DesiredNode.description`
values above are real content that would be silently erased.

## Why this wasn't fixed here

Plan Section 5.3 requires the preview to show "22 unchanged rows or only field updates already
authorized by Phase 0's disposition ledger," and Section 6 Step 6 requires the phase to stop
before apply on "any... unexplained field update." These 5 updates are exactly that: not
create/conflict/delete-like, but also not named anywhere in the Phase 0 ledger as an
authorized change, and their effect (erasing existing operator-written prose) is the kind of
silent loss the whole disposition-ledger exercise existed to prevent. Deciding unilaterally to
either (a) treat the clearing as acceptable and proceed to apply, or (b) change importer field
ownership to preserve `description`/`notes` the way `DesiredService` already preserves its
analysis-owned fields, is a data-ownership decision, not an implementation detail — hence stopping
here instead of choosing on the user's behalf.

## Decision needed

1. Add `description`/`notes` values to `intent_sources.yaml` matching the live values above (and
   equivalent blank-safe entries for `DesiredEndpoint`/`DesiredIPRange`) so the next preview is a
   true no-op, then re-run Step 6.
2. Change `desired_node_update_fields()` (and the `DesiredEndpoint`/`DesiredIPRange` equivalents)
   to exclude `description`/`notes` from Import's writable set, treating them as operator-owned
   free text the same way `DesiredService.notes` already is — then re-run Step 6.
3. Approve clearing these five `description` values as an intentional, acceptable one-time change
   and proceed to apply as previewed.
4. Something else — e.g. only preserve `DesiredNode.description`/`notes` and accept the cosmetic
   empty-string-to-null changes elsewhere.

This must be resolved before Step 6's apply approval request; Step 6 is otherwise ready (preview
executed, artifact captured, schema/zero-write verified) once a decision is made.

---

**2026-07-26 resolution**: user chose option 1 (add the live `description`/`notes` values to
`nauto/seed/intent_sources.yaml`). Fixed in `nauto` commit `1c78af8`, superproject pointer commit
`2fa125f`, both pushed. Candidate image rebuilt (`nic-p4-candidate:20260726c`,
`sha256:a4c20f6ad4b3d3d8b14cd483e8fb23c78943dd4701cef259f449cb1b065ad94a`) and redeployed live under
a fresh maintenance freeze; the re-run `apply=false` preview confirms zero `DesiredNode.description`
updates remain (previously 5 unauthorized). See
[report6b.md](report6b.md) for the full re-run record. This open problem is now closed; the
remaining 13 update actions in the preview are the pre-existing cosmetic/benign set report6.md
already classified as safe.

---

**2026-07-26 resolution (Phase 4 Step 1 mutation-evidence problem)**: option 2 was implemented
in the nctl worktree and verified locally; see [sidefix1/report4.md](sidefix1/report4.md). A
successful node-link PATCH now marks every subsequent GraphQL confirmation failure as
`success=false, mutated=true` at the ledger boundary, preserving the original bounded error code.
The executor propagates that marker without an error-code allowlist and accumulates round side
effects from `success or mutated`, so a partial IPAM apply receives the same final-drift safety
handling. Focused ledger/executor tests and the complete nctl suite pass. No live Nautobot write,
Job, deployment, commit, or push was performed for this repair.
