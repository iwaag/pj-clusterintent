# Creative Workspace — Phase 0 Plan: Desired model and declaration

Parent: [roadmap.md](../roadmap.md). Read its Premises and Hard rules first; they are the only
prohibitions. Everything below that is not marked **required** is a recommendation or a hint —
deviate freely when the code argues for it.

## Goal

Add `DesiredWorkspace` as a first-class nintent model, wire it into the batch desired-state
writer and GraphQL, and declare the one real workspace (`pj-voxel3dprint` on `agpc`) through the
normal `nctl desired apply` flow.

**Exit criteria (required):**
1. Batch apply (dry preview, then `--yes`) creates the `pj-voxel3dprint` row.
2. A GraphQL query against the local Nautobot returns it.
3. nintent test gates pass (Django-free fast gate + Nautobot runtime gate; `--clean` once because
   this phase adds a migration).

## Scope

nintent only, plus `.local/desired-state.yaml` and the superproject submodule pointer. No
nodeutils, nauto, or nctl evaluation changes — observation is Phase 1, evaluation is Phase 2.
Whether to also extend nctl's `DesiredSnapshot` (`nctl/src/nctl_core/sources/desired.py`) now or
in Phase 2 is implementer's choice; nothing in Phase 0 consumes it, so deferring is fine.

## Proposed model shape

One model, placement embedded (per roadmap: exactly one placement per workspace; do not build a
separate placement model until a real multi-node pattern exists):

| field | notes |
|---|---|
| `name`, `slug` | slug unique — same pattern as `DesiredService` |
| `lifecycle` | reuse the existing 6-value vocabulary (`proposed`…`retired`) verbatim |
| `source_remote_url` | plain CharField; the declared identity anchor for Phase 2 matching |
| `desired_node` | FK, `on_delete=PROTECT`, `related_name="desired_workspaces"` |
| `expected_path` | absolute path on the node, plain CharField |
| `desired_presence` | present/absent — reuse the `DesiredComputeInstance` choice constants |

Deliberately absent (hard rule 1): any desired branch, commit, or cleanliness field.

Exact field names are yours. Do not add fields beyond these — the roadmap's
"promote on consumption" rule applies to desired state too.

## Steps

One report + one commit per step (`p0/report_stepN.md` next to this plan). Pause for user
judgment at the marked points.

### Step 0 — Confirm the real workspace facts

Get the actual checkout path and remote URL of `pj-voxel3dprint` on `agpc`. `agpc.local` is
reachable; direct SSH with `~/.ssh/ansible_key` is allowed after confirming with the user
(`.local/localenv_memo.md`), or simply ask the user. Read-only; record both values in the step
report. Don't guess the path — the declared path becomes the Phase 1/2 identity target.

### Step 1 — Model + migration (nintent)

- Add `DesiredWorkspace` to `nintent/nautobot_intent_catalog/models.py` inside the existing
  `try/except ImportError` block, decorated `@extras_features("graphql")` like every sibling —
  that decorator alone gives you the GraphQL exposure; there is no separate schema file.
- Node-retirement protection (required by roadmap): mirror the compute-platform rule in
  `DesiredNode.clean()` (models.py ~line 206: retired node with `controlled_compute_platforms`
  raises) — a retired lifecycle with attached non-retired workspaces (or any workspaces; your
  call, but document it) is a `ValidationError`. That validation-error level is *enough*; no
  extra machinery.
- Generate migration `0027_*` (current head is `0026_braindumpdocument_completed_status`).
  Generate it inside the Nautobot container (`nautobot-server makemigrations`), since local
  Python has no Nautobot.
- Optional but cheap: admin/UI list+detail following the `DesiredService` pattern
  (views/tables/templates/navigation/urls). `test_ui_contract.py` enumerates models explicitly,
  so skipping UI won't break gates — decide by whether you want to see workspaces in the web UI
  during Phase 1 debugging. If you skip it, say so in the report.

### Step 2 — Batch writer wiring (nintent)

All in `nintent/nautobot_intent_catalog/batch.py`; the pattern is fully table-driven:

- `KIND_ORDER`: add `desired_workspace`. Position only matters relative to `desired_node`
  (upserts run in `KIND_ORDER`, deletes reversed) — appending at the end works.
- `_KEYS`: `("slug",)`. `_FIELDS` / `_CREATE_REQUIRED`: from the model shape above.
- `_REFERENCE_KIND`: `desired_node` is already mapped — reusing that field name gets slug
  resolution for free.
- `_DELETE_BLOCKERS["desired_node"]`: add `("desired_workspaces", "desired_workspace")` so a
  node delete is blocked by hosted workspaces, consistent with the retirement rule.
- Extend `tests/test_batch.py` (Django-free) with the new kind: create-required validation,
  unknown-field rejection, delete-blocker case. Table-style, matching the existing tests.

`nctl desired apply` needs **no change**: `.local/desired-state.yaml` is already the raw batch
envelope passed through verbatim (`nctl/src/nctl_core/desired_apply.py`), and unknown kinds are
validated server-side.

### Step 3 — Local gates (before any rebuild)

Per the roadmap hint, run the pure-domain tests before touching the container:

```bash
cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests   # 10 expected skips
```

Commit Steps 1–3 in nintent. **Pause: ask the user to push nintent** (the Dockerfile installs
from GitHub; local commits are invisible to the image).

### Step 4 — Rebuild, migrate, runtime gate

- Rebuild per `.local/localenv_memo.md`: `cd devenv/nautobot && docker compose --env-file ../.env
  build --no-cache` — **`--no-cache` is required and verify the resolved nintent SHA in the build
  log** (known silent-stale-cache gotcha). Then `up -d` and `nautobot-server migrate` in the
  container. Scratch environment: restarts/migrations here are routine, not live mutations.
- Runtime gates from superproject root:
  ```bash
  ./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb   # iterate
  ./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean    # once, migration proof
  ```
  Check the stated `cases=` count — a gate that ran zero cases proves nothing (README_DEV
  lesson 1).

### Step 5 — Declare pj-voxel3dprint  **(pause: desired-state write)**

Append one operation to `.local/desired-state.yaml`:

```yaml
- op: upsert
  kind: desired_workspace
  key: {slug: pj-voxel3dprint}
  values:
    name: pj-voxel3dprint
    lifecycle: active
    source_remote_url: <Step 0 value>
    desired_node: agpc
    expected_path: <Step 0 value>
    desired_presence: present
```

Preview (`nctl desired apply -f .local/desired-state.yaml`), show the user the plan (expected:
one `create`, everything else `unchanged`), then `--yes`. The existing `DesiredService` rows for
pj-voxel3dprint stay untouched — their removal is Phase 1's coordinated rollout.

### Step 6 — GraphQL proof + phase report

Query the local Nautobot GraphQL endpoint (token per `.local/secrets`) for the new type — the
auto-generated plural follows the model meta (verify the exact name via GraphiQL at
`http://localhost:8000/graphql/` if unsure):

```graphql
{ desired_workspaces { slug lifecycle source_remote_url expected_path desired_presence desired_node { slug } } }
```

Record the response (it may be redacted to field presence) in `p0/report.md`, alongside gate
results and any deviations from this plan. Update the superproject nintent pointer (commit;
push on user request).

## Known pitfalls, collected

- nintent → container only via commit → push (user) → `--no-cache` rebuild; no volume mount.
- Batch document top-level keys are exactly `{dry_run, operations}`; `nctl desired apply`
  overwrites `dry_run` from the `--yes` flag, so the YAML's own value is cosmetic.
- `full_clean()` runs on every batch upsert (`batch.py` apply loop), so model-level validation
  is automatically the batch-writer validation — put rules on the model, not in the endpoint.
- If a runtime-gate run dies mid-setup, drop `test_nautobot` before rerunning; a half-built
  schema fails later runs with misleading duplicate-column errors.
