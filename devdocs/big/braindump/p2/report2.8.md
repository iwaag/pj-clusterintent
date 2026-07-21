# Step 2.8 — Run live synthetic CRUD, verify isolation, and close the phase

Status: complete. Phase 2 exit criteria all pass.

## 1. Revisions

- nintent: `0.9.0`, commit `aa5a052dfef07e7749b501b6c016eff2fbe10271` (unchanged from Phase 1;
  migration `0014_braindump_exchange_diary` applied).
- nctl: commit `d33c58e0a238b8113115800c523cffc2a002b7ae` (heads/main, local; matches the parent
  submodule pointer already recorded at Step 2.7 — no further nctl code changed in this step).

## 2. Final commands, schemas, REST paths, GraphQL query names

Seven commands: `nctl braindump {list, show, create, update, delete, review, review-delete}`.
Seven envelope schemas: `nctl.braindump.{list,show,create,update,delete,review,review_delete}.v1`.
REST: `/api/plugins/intent-catalog/braindumps/` and `/api/plugins/intent-catalog/alignment-reviews/`
(POST/PATCH/DELETE). GraphQL: `braindump_documents`/`braindump_document` with nested
`alignment_review` (`nctl_core.sources.braindump.LIST_QUERY`/`SHOW_QUERY`, unchanged since Step 2.2).

## 3. Test counts

```
uv run --project nctl pytest -q nctl/tests
733 passed, 1 warning in 5.10s
```

Unchanged from Step 2.6/2.7; re-run after the live smoke window below with the same result.

## 4. Live synthetic CRUD (against the running local Nautobot; token never printed)

All steps used a single uniquely titled row, `nctl-p2-step2.8-synthetic-smoke-1784645673`
(later renamed to `...-updated`), created from a UTF-8 file containing Japanese multibyte text,
multiline content, surrounding whitespace, an HTML-looking `<script>` tag, shell-looking
`$(...)`/backtick/`;` content, and a prompt-injection-looking sentence — none of it interpreted.

1. **Baseline `list --json`**: `{"items": [], "count": 0}` — zero current real records; no
   modification.
2. **Create** from the UTF-8 file: REST POST + GraphQL confirmation succeeded; response `body`
   compared byte-for-byte against the source file in Python (`exact match: True`, 200/200 bytes).
3. **Show via GraphQL**: title, `created`, `last_updated` matched the create response exactly.
4. **Update, literal then file**:
   - literal `--title` only: body/authorship/timestamps for other fields preserved verbatim
     (compared full stored body string byte-for-byte in the JSON response — unchanged).
   - `--file` body only: title/authorship preserved (`nctl-p2-step2.8-synthetic-smoke-updated`,
     `user_direct`), only `body`/`last_updated` changed.
5. **Review create → replace**: create returned `action: "created"`, `attention:
   "review_present"`. Replace returned `action: "replaced"` with the **same review `id`**
   (`b6fd9261-...`), unchanged review `created`, and advanced `last_updated` — confirming
   replacement-in-place rather than a new history row, and the required timestamp refresh even
   though this replacement also happened to change the summary text.
6. **Review-only delete**: `deleted: true`, `review_id` returned; the Braindump's own
   `review_present`/`attention` flipped to `false`/`"unreviewed"` while `title`/`body` stayed
   intact.
7. **Recreate review, then Braindump delete `--yes`**: recreate returned a new review id
   (`dca5fb87-...`, `action: "created"`); the subsequent `braindump delete --yes` returned
   `deleted: true, review_deleted: true` — cascade confirmed.
8. **Safety checks, no partial row**:
   - unknown ID (`00000000-...`) on `show` → `braindump_not_found`, exit 2, `ok: false`;
   - whitespace-only `--body` on `create` → `invalid_text`, exit 2, `ok: false`; a follow-up
     `list --json` immediately after confirmed `{"items": [], "count": 0}` — no partial row was
     ever written.
9. **Cleanup confirmed two ways**: `nctl braindump list --json` → `count: 0`, and direct
   (non-nctl) REST reads of both collections —
   `GET /api/plugins/intent-catalog/braindumps/` and `.../alignment-reviews/` — both returned
   `{"count": 0, ..., "results": []}`. No synthetic row remains by any path.

## 5. Drift isolation, pre/post CRUD window

```
uv run --project nctl nctl drift --json   # before: Step 2.1 baseline; after: post-CRUD run
```

- schema: `nctl.drift.v1` both before and after.
- `summary`: `{"converged": 2, "unknown": 4}` — identical.
- `severity_summary`: `{"error": 6, "warning": 4, "info": 5}` — identical.
- 6 targets both runs; identical target identities, `status` per target
  (`agdnsmasq`/`agbach` converged, `aghub`/`agpc`/`agstudio`/`dnsmasq` unknown), and identical
  sorted diff-code sets per target.
- The only byte-level difference across the entire before/after JSON (excluding top-level
  `generated_at`/`sources.fetched_at`) was one evidence field, `age_hours` on a
  `service_observation_stale` finding for `dnsmasq` (28.96 -> 29.47), which is the ordinary
  wall-clock aging of an existing stale-observation finding between the two ~30-minute-apart runs —
  not a schema, identity, status, or diff-code change, and not something the Braindump feature
  could have caused (it never reads or writes actual-observation data).

This confirms zero coupling between the Braindump exchange diary and the deterministic
desired/actual/drift domain, both statically (Step 2.6's `grep` isolation check) and now via live
before/after evidence.

## 6. Cleanup confirmation

No synthetic row remains. Confirmed via `nctl braindump list --json` (`count: 0`) and direct REST
GETs of both `/api/plugins/intent-catalog/braindumps/` and `.../alignment-reviews/` (`count: 0`
each), immediately after the delete step and again at report time.

## 7. nctl commit and parent submodule pointer

nctl commit `d33c58e0a238b8113115800c523cffc2a002b7ae` — this is already the parent repository's
`nctl` submodule pointer (set at Step 2.7; unchanged by this step, since Step 2.8 performed live
verification only, no code change).

## 8. Exit criteria

- [x] The final seven CLI commands are implemented exactly once with no aliases or hidden
      authorship default.
- [x] List/show use the deployed GraphQL schema and expose IDs, authorship, exact prose,
      timestamps, review presence, and the three-state attention hint.
- [x] Create/update accept exactly one literal-or-UTF-8-file prose source, preserve accepted text
      exactly, and write only through REST.
- [x] Review is a confirmed create-or-replace operation that leaves at most one current row and
      refreshes its timestamp even when the text is unchanged (live-verified above; unit-verified
      in Step 2.4).
- [x] Braindump deletion requires explicit confirmation and confirms cascade deletion; review-only
      deletion preserves the Braindump and makes it visibly unreviewed.
- [x] Every write/delete is refetched through GraphQL and fails closed on a mismatch.
- [x] All commands emit documented typed `nctl.braindump.*.v1` envelopes in JSON mode and readable
      output from the same data in human mode.
- [x] Missing review is normal; unknown ID, invalid input, API/auth/server failures, conflicts, and
      confirmation mismatches have tested stable errors and exit codes.
- [x] Unicode, multiline, surrounding whitespace, validation, replacement, deletion, race,
      transport, JSON, and CLI/core separation cases are covered by passing tests (733/733).
- [x] Diary code has no import or behavior path into drift, reconcile, dashboard, serve, Jobs,
      nodeutils, Ansible, or actuation (static `grep` + live drift-isolation evidence).
- [x] Live synthetic CRUD passes against nintent `0.9.0`, all smoke rows are removed, and pre/post
      deterministic drift content is unchanged (modulo ordinary evidence aging).
- [x] nctl documentation, compatibility snapshots, local commit, parent submodule pointer, and
      `report2.1.md` through `report2.8.md` record the completed implementation without tokens or
      private diary prose.

## Discrepancies

None. Phase 2 is complete. Phase 3 (proving the conversational workflow on the live cluster) is
next per `devdocs/big/braindump/roadmap.md`, not started.
