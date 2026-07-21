# Step 2.1 — Freeze the baseline, commands, and live API handoff

Status: complete.

## 1. nctl baseline

- nctl submodule commit: `f211c9ec70c02141b8180f95132c7541a9b00cc1` (heads/main), working tree
  clean.
- Python `3.14.2`; `uv 0.11.24`.
- Focused test command and result:

  ```
  uv run --project nctl pytest -q nctl/tests
  617 passed, 1 warning in 4.83s
  ```

  Matches the plan's recorded baseline exactly (617 tests, one Starlette deprecation warning).

## 2. Deployed nintent/migration confirmation

- Installed package: `nautobot-intent-catalog @ git+https://github.com/iwaag/nprojects.git@aa5a052dfef07e7749b501b6c016eff2fbe10271`
  (`pip freeze` inside `nautobot-nautobot-1`) — matches the plan's recorded nintent `0.9.0` /
  `aa5a052`.
- `nautobot-server showmigrations nautobot_intent_catalog` shows `0001_initial` through
  `0014_braindump_exchange_diary`, all applied `[X]`.
- Containers `nautobot-nautobot-1`, `nautobot-nautobot-worker-1`, `nautobot-nautobot-scheduler-1`
  all `Up (healthy)`.

## 3. Live REST/GraphQL handoff check (read-only, no rows created)

REST collections, both empty (`count: 0`), confirming exactly the two deployed collections named
in the plan:

```
GET /api/plugins/intent-catalog/braindumps/          -> {"count":0,"next":null,"previous":null,"results":[]}
GET /api/plugins/intent-catalog/alignment-reviews/    -> {"count":0,"next":null,"previous":null,"results":[]}
```

GraphQL, against the empty live dataset:

```graphql
query { braindump_documents { id title body authorship created last_updated
  alignment_review { id summary created last_updated } } }
```
→ `{"data":{"braindump_documents":[]}}` — empty-list behavior confirmed.

```graphql
query($id: ID!) { braindump_document(id: $id) { id title } }
```
with a random UUID → `{"data":{"braindump_document":null}}` — null-singular-result behavior
confirmed, matching the plan's `braindump_not_found` semantics.

No discrepancy: field names (`braindump_documents`, `braindump_document`, `alignment_review`) and
null/empty behavior match Decision 3 and the Phase 1 handoff exactly.

## 4. Existing runtime name search

```
rg -i 'braindump|alignment_review|alignment-review' nctl/src nctl/tests nctl/README.md nctl/docs
```

No output. No abandoned client prototype or compatibility shape to preserve; the Phase 2 work is
purely additive.

## 5. Frozen command/schema/error-code spellings

Recorded exactly as specified in `p2/plan.md` Decisions 1, 5, and 8 (seven `braindump` subcommands,
seven `nctl.braindump.*.v1` envelope schemas, and the four-tier error-code table). No changes taken
at this step. `SourceSnapshot` will not be widened — the new GraphQL reader lives in
`nctl_core.sources.braindump`, called only by Braindump operations (Decision 3).

## 6. `nctl drift --json` pre-implementation baseline

```
NAUTOBOT_TOKEN=... uv run --project nctl nctl drift --json
```

`ok: true`, schema `nctl.drift.v1`, `generated_at: 2026-07-21T14:24:58.801128+00:00`.

- summary: `{"converged": 2, "unknown": 4}`
- severity_summary: `{"error": 6, "warning": 4, "info": 5}`
- targets: 6 (unchanged shape from the Phase 1 baseline in `p1/report1.1.md`)

Full JSON (747 lines) saved locally to the session scratchpad only, not committed — contains real
cluster target/finding data but no token and no Braindump content (the feature has no rows yet).
Reserved for the Step 2.8 post-CRUD isolation comparison.

## Discrepancies

None. Baseline matches `p2/plan.md`'s "Current state" section and the Phase 1 handoff contract
exactly. Proceeding to Step 2.2.
