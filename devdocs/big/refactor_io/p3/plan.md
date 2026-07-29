# Phase 3 Plan — Cut All Desired-State Writers Over

Status: **planned** (implementation not started).

Input contracts: [`../p0/report.md`](../p0/report.md) (wire contract, identities, cutover order),
[`../p1/plan.md`](../p1/plan.md) (the in-memory batch service) and [`../p2/plan.md`](../p2/plan.md)
(the deployed endpoint). Neither is restated here.

## Goal

`POST /api/plugins/intent-catalog/desired-state/batch/` becomes the only supported way to change
structured desired state. nctl's lifecycle and realization-link writes go through it, the
file-driven Import Job and the per-model PATCH routes are deleted, and `nctl drift`/`reconcile`
still complete their current paths against the deployed result.

## Scope

In scope:

- nctl `lifecycle` and ledger link writes reissued as batches over the endpoint.
- A thin operator client (`nctl desired apply`) replacing the Import Intent Sources Job.
- nintent: resolve actual-object link references inside the batch service (see Decision 3).
- nintent deletions: Import Job, the YAML file-loading stack, the three desired-model REST
  mutation surfaces, and their tests/serializers/docs.
- One coordinated nintent+nctl deployment to the scratch Nautobot, then a live smoke.

Out of scope: removing `nauto/seed/intent_sources.yaml`, its Dockerfile copy, and the real-data
examples (Phase 4); the narrative documentation rewrite (Phase 5). The `Reconcile Desired IPAM
Intent` Job, Braindump/AlignmentReview APIs, and actual-state ingest are different domains and stay
exactly as they are. The nintent UI is already read-only — no UI work is expected.

## Design decisions to implement

Everything not listed here — module layout, naming, error wording, helper structure — is the
implementer's choice.

### 1. One nctl batch writer

Add one small nctl module (suggested `nctl_core/desired_write.py`) that owns the envelope, the POST,
and the interpretation of the result artifact. `lifecycle.py` and `reconcile/ledger.py` call it; no
other module builds a batch by hand and no `rest_patch`/`rest_post` call to
`/api/plugins/intent-catalog/*` desired collections remains outside it.

Interpretation rules for a caller:

| artifact | meaning |
|---|---|
| HTTP 200 and `transaction.status == committed` | write landed; per-operation `action` says `create`/`update`/`unchanged` |
| HTTP 200, `dry_run: true` | plan only |
| HTTP 409 (`blocked`/`rolled_back`) | nothing was written; surface the per-operation `reason` |
| HTTP 4xx | nothing was written |

`mutated` evidence for reconcile actions is derived from `transaction.committed`, not guessed from
an error code.

### 2. `nctl lifecycle`

Same command, same envelope, same idempotence (no request when the node already has the requested
state). The write becomes:

```json
{"dry_run": false,
 "operations": [{"op": "upsert", "kind": "desired_node",
                 "key": {"slug": "agpc"}, "values": {"lifecycle": "active"}}]}
```

Keep the GraphQL refetch confirmation and the fail-closed mismatch error: `committed` plus a
confirmed read is the success condition. Error codes may be renamed to transport-neutral names;
if so, update `nctl/docs/output-format.md`, which currently lists them.

### 3. Ledger link writes

`execute_link_actual_node` and `execute_link_compute_realization` keep their GraphQL preconditions
(never clear, never replace another object's link) and their GraphQL confirmation. Only the write
changes:

```json
{"op": "upsert", "kind": "desired_node", "key": {"slug": "agpc"},
 "values": {"realized_device": "<device-uuid>"}}
```

The compute writer becomes **one** batch of two operations
(`desired_compute_platform` keyed by `slug`, `desired_compute_instance` keyed by its node slug), so
platform-committed/instance-failed partial progress becomes impossible. Delete the error paths and
tests that only described that partial state; keep `platform_write`/`instance_write` reporting by
reading each operation's `action` (`update` vs `unchanged`).

**Required nintent fix:** `batch._orm_values()` resolves only desired-state references
(`_REFERENCE_KIND`). `realized_device`, `realized_cluster`, `realized_vm`, and
`realized_ip_address` are passed straight to a Django FK attribute, so a UUID string currently
raises inside apply. Resolve these four by primary key to their Nautobot model instance, and treat
explicit `null` as clearing the link. Without this, no ledger write can succeed.

### 4. Operator client replacing the Import Job

`nctl desired apply -f FILE` (`-f -` reads standard input), dry by default, `--yes` to commit,
`--json` for the raw artifact. It posts the document unchanged — it neither rewrites operations nor
keeps a second copy of the submitted state. Note the existing `nctl apply` Typer group is Ansible
actuation; use a separate group name.

The client accepts the Phase 0 batch envelope only. Converting the legacy per-root
`intent_sources.yaml` shape is a one-time job, not a supported client feature (Step 2).

### 5. nintent removals

- `ImportIntentSources` Job, `IMPORT_SCHEMA_VERSION`/artifact constants, `_configured_source_file()`
  and the `intent_sources_file` App-config read (and the now-dead key in
  `devenv/nautobot/nautobot_config.py`).
- `loaders.py`, `importers.py`, `import_plan.py`, and `batch.document_from_load_result()` — after
  Step 2's export, nothing else imports them.
- `DesiredNodeViewSet`, `DesiredComputePlatformViewSet`, `DesiredComputeInstanceViewSet`, their
  serializers, and their router registrations. Delete rather than make read-only: reads go through
  GraphQL and the UI, and no consumer remains. Their filtersets stay — the UI list views use them.
  `braindumps` and `alignment-reviews` are untouched.
- The matching tests in `tests/test_api_contract.py` become "these routes are gone" assertions
  alongside the existing removed-route cases.
- Update `nintent/README.md`, `README_DEV.md`, `README_QUICK.md`, and `nauto/README.md` where they
  document the Import Job or the PATCH routes.

## Steps

One commit and one short report entry per step, as usual.

### Step 1 — nintent: link resolution and the removals

Decision 3's reference fix plus every deletion in Decision 5, in one commit. Django-free and runtime
tests for: a `realized_*` UUID resolving, an unknown UUID being a conflict, explicit `null` clearing
a link, and the deleted routes/Job being absent.

### Step 2 — Export the current YAML as a batch document (before deleting the loader)

While `loaders.load_intent_sources` and `document_from_load_result` still exist, convert
`nauto/seed/intent_sources.yaml` once into a Phase 0 batch document and write it to
`.local/desired-state.yaml` (ignored, private). It is the Phase 4 input and the only way to
repopulate a rebuilt scratch database once the Job is gone. Verify it by posting it with
`dry_run: true` against the current deployment and confirming every operation reports `unchanged`
— any `create`/`update`/`conflict` means the conversion is lossy and must be fixed before Step 1's
deletions are pushed.

Order this step's *execution* before Step 1's deletion commit; the report order can stay numeric.

### Step 3 — nctl: batch writer, lifecycle, ledger, operator client

Decisions 1–4 in nctl, with the tests rewritten to assert the exact POST body and path instead of
the PATCH routes (`tests/test_lifecycle_contract.py`, `tests/test_reconcile_ledger.py`,
`tests/test_cli_lifecycle.py`, `tests/test_cli_surface.py`). Keep the existing positive-evidence
assertions: exactly one request, exact envelope, no request when idempotent, confirmation failure
still fails closed. Add coverage for a 409 artifact leaving the action failed-and-unmutated.

### Step 4 — Gates, commit, coordinated deploy

Run the gate table, commit both submodules, then **stop and ask the user to push `nintent`** (and
`nctl`). After the push:

1. `cd devenv/nautobot && docker compose --env-file ../.env build --no-cache`, then confirm the
   resolved nintent SHA in the build log matches the pushed commit — advance the pin in
   `devenv/nautobot/Dockerfile` if it is stale, as in Phase 2.
2. `docker compose --env-file ../.env up -d`.
3. `docker exec nautobot-nautobot-1 nautobot-server post_upgrade`.
4. Delete the stale `ImportIntentSources` `JobModel` row if it lingers in the UI.

nintent and nctl are deployed as one matched pair: the PATCH routes disappear in the same rollout
that stops nctl from using them. No migration is expected in this phase.

This step is the phase's only hard-to-reverse action. Pause before it and report the result before
continuing.

### Step 5 — Live acceptance and report

Against the deployed instance, using synthetic identities (`p3-smoke-*`) and the token from
`.local/secrets` (never echo it):

1. `nctl desired apply -f` a small document — dry first, then `--yes` — creating a synthetic node;
   confirm GraphQL returns it.
2. `nctl lifecycle p3-smoke-node active` twice: first reports the change, second reports no change
   and sends no write.
3. Exercise one ledger link over HTTP against synthetic rows (a scratch `dcim.Device`, or a
   synthetic compute platform/instance pair) and confirm the link through GraphQL. If no safe live
   target can be created, say so explicitly in the report and name the runtime-gate case that
   covers it instead — do not silently substitute the unit test.
4. `curl` a PATCH to `/api/plugins/intent-catalog/nodes/<uuid>/` and confirm it is now 404/405.
5. `uv run --project nctl nctl drift --json` and `nctl reconcile` (no `--yes`) still succeed.
6. Delete the synthetic rows with a `delete` batch and confirm GraphQL no longer returns them.

Record results in `devdocs/big/refactor_io/p3/report5.md` and close the phase.

## Gates

| gate | working directory | command |
|---|---|---|
| nintent Django-free fast | `nintent` | `python3 -m unittest discover -s nautobot_intent_catalog/tests` |
| nctl ordinary | `nctl` | `uv run pytest -q --durations=20` |
| Nautobot runtime clean | superproject root | `./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean` |
| compute conformance | superproject root | `uv run --project nctl pytest -q devtests/test_strategy/test_compute_conformance.py` |

Deleting the loader stack changes the Django-free suite's expected skip count; update the number in
`README_DEV.md` if it moves.

## Prohibitions

Only these:

1. After this phase, one supported desired-state mutation surface exists: the batch endpoint. No
   PATCH route, Job, or ORM write survives as an alternative operator/nctl path.
2. nctl builds desired-state batches in exactly one module.
3. Neither nctl nor nintent stores a copy of a submitted document or its artifact.
4. A 409/4xx artifact must never be reported as a successful or partially successful write.
5. The live smoke touches only synthetic rows it creates and deletes.

Everything else is at the implementer's discretion.

## Exit criteria

- Repository search finds no desired-state write outside the batch endpoint (fixture ORM setup in
  tests excepted).
- `nctl lifecycle`, both ledger linkers, and `nctl desired apply` work against the deployed
  endpoint, with confirmation and idempotence preserved.
- The Import Job, the loader stack, and the three per-model mutation routes are gone, and their
  absence is asserted by tests.
- `.local/desired-state.yaml` reproduces the current cluster state as a `dry_run` of pure
  `unchanged` operations.
- `nctl drift` and a dry `nctl reconcile` still complete against the deployed image; all gates pass
  and every worktree is clean.

## Known risks

- **Unresolvable realization links.** If Decision 3's fix is missed or incomplete, every ledger
  action fails at apply time with a rolled-back transaction. Test it Django-free *and* in the
  runtime gate before deploying.
- **Losing the ability to repopulate the scratch database.** The Import Job is the only current
  bulk loader; Step 2's export must exist and be verified before Step 1's deletions are pushed.
- **Build cache pinning a stale nintent commit.** Verify the SHA in the build log; do not trust a
  successful build alone.
- **No live target for a ledger link.** Real cluster rows are already linked and must not be
  relinked. Plan for a synthetic target or an honest gap statement, not a real-row experiment.
