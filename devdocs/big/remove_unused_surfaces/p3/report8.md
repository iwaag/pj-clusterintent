# Phase 3 Step 8 — Prepare commits and matched revision tuples

Parent: [plan.md](plan.md) Step 8.

Executed 2026-07-25.

## 1. Final nintent diff reviewed as one coherent deletion

Reviewed as a whole (Step 7 §5's 12-file inventory): four duplicated reconciliation
constant/choice blocks and four model fields removed, migration `0016` added, every
filter/table/template/view/URL/navigation/App-default/serializer-comment reader removed, one new
32-test focused module added. No file outside this inventory changed. Committed across four
reviewable nintent commits (one per implementation step, matching this initiative's established
per-step commit convention — see `p2/report8.md` §3 for the identical precedent):

| nintent commit | Step | Content |
|---|---|---|
| `339b7464ec018bf9cc71ef5f41b185d21e308950` | 1 | New `test_remove_unused_surfaces.py` (pre-change) |
| `55be38b4eaccb3c68edbe6d7551a2c1b50169e93` | 2 | `models.py` fields removed, migration `0016` added |
| `fc9488756ecc2af4509fc2237ff8b34d81cc33b8` | 3 | filters/tables/templates/views/urls/navigation/`__init__.py`/serializer edits |
| `0914ca496dc9c72319c8c1e2e1bcc2bf7e418a7e` | 6 | compute UI/REST/GraphQL retention proof added to the test module |

**Final nintent commit for this phase: `0914ca496dc9c72319c8c1e2e1bcc2bf7e418a7e`.**

## 2. Matched nctl revision

`nctl` was byte-for-byte unchanged throughout this phase (Step 0/Step 4/Step 7 all confirmed HEAD
`7a0f2cf035179fbea5deed4cacb05573f8c8dffa`, clean) — this is exactly the Phase 2 final revision
(`p2/report8.md` §2), already CLI-only/dashboard-free/no-PATCH, and needs no further change to be
compatible with the nintent commit above.

## 3. Superproject pointer and development config

Both already committed in reviewable per-step units (Steps 1-3, 6-7 root commits bumping the
`nintent` submodule pointer; Step 7's root commit also carries the `devenv/nautobot/
nautobot_config.py` deployment-config edit). No squash was performed; each commit is independently
reviewable and its own step's report is the record of what it verified.

## 4. Matched revision tuple for the later coordinated deployment (Phase 5)

```text
nintent: 0914ca496dc9c72319c8c1e2e1bcc2bf7e418a7e  (this phase's final commit; not yet pushed)
nctl:    7a0f2cf035179fbea5deed4cacb05573f8c8dffa  (Phase 2 final; unchanged)
root:    b149185250522650c11be31f140581228a2ba50b  (this phase's Step 7 commit; superproject pointer + report inventory)
```

## 5. Deployed (pre-change) revision and rollback tuple

```text
deployed nintent:     ad9d36397d23c269ad748e13acbccc532fa29f52  (0.9.0, migrations through 0014)
deployed migration:   0014_braindump_exchange_diary (0015/0016 both unapplied live)
paired nctl (live):   7a0f2cf035179fbea5deed4cacb05573f8c8dffa  (same nctl revision, unchanged)
```

Because `nctl` did not change in this phase, the "rollback tuple" is simply: keep the currently
deployed nintent commit (`ad9d363...`) and the current nctl revision active; do not build/deploy
the new nintent commit until Phase 5's coordinated maintenance window. No pre-window database
backup is required yet because no live migration has been attempted (plan §4.5/§9).

## 6. Push authorization

Per `.local/localenv_memo.md` and this initiative's own precedent (`p1/report8.md`,
`p2/report8.md`), pushing the nintent commit is explicitly the user's own step, never performed by
this agent. **Not pushed.** Asking the user to push `nintent` (`main`, HEAD
`0914ca496dc9c72319c8c1e2e1bcc2bf7e418a7e`) to `https://github.com/iwaag/nprojects.git` now.

## 7. Live non-mutation confirmed

No rebuild, restart, migration, Job, desired write, `nctl` apply, Ansible, or host mutation
occurred at any step of this phase (Step 0/Step 7 both reconfirmed live nintent unchanged at
`ad9d363...`/`0014`).

## Gate (partial — push pending)

Exact matched and rollback tuples are recorded and the nintent commit is ready for the later
GitHub-based rebuild; the commit is **not yet pushed**, so this phase's status is
`implemented, awaiting push`, not `complete`, per plan §7 Step 8's own instruction.
