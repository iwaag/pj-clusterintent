# Phase 3 Step 0 — Reconfirm the Phase 2 handoff and non-mutation boundary

Parent: [plan.md](plan.md) Step 0.

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p3/20260725-162655/` (mode `0700`, files `0600`), containing
`revisions.txt`, `live-baseline.txt`, `local-baseline.txt`, `step0-baseline-deletion-search.txt`.

## 1. Revisions and dirty state

| Repository | Revision | Dirty state |
|---|---|---|
| superproject | `f30db90d5e26dd2d2ede7174be2affacfaf53f41` | 1 dirty file: `devdocs/big/remove_unused_surfaces/p3/plan.md` |
| `nctl` | `7a0f2cf035179fbea5deed4cacb05573f8c8dffa` | clean |
| `nintent` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | clean |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | clean |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean |

The one dirty file is a pre-existing user edit to this phase's own plan (refining Step 8.4/Step 9
wording around evidence privacy and report commit sequencing — the content already matches the
plan text read at the start of this step). It is not part of Step 0's scope and was left untouched.
All submodule revisions match the plan §2.1 snapshot exactly.

## 2. Phase 2 handoff confirmed intact

- `nctl --help`: 11 commands (`status actual drift reconcile lifecycle render apply ops braindump
  ssh session`) — no `dashboard`, no `serve`. Matches plan §2.1/p2/report8.md exactly.
- `grep -rn dashboard nctl/src/`: zero matches.

## 3. Live installed nintent state (read-only)

- `nautobot-intent-catalog` 0.9.0, installed Git commit
  `ad9d36397d23c269ad748e13acbccc532fa29f52` — matches plan §2.2.
- `nautobot-server showmigrations nautobot_intent_catalog`: applied through
  `0014_braindump_exchange_diary`; `0015` **not** applied.
- All three Nautobot containers healthy (`nautobot-nautobot-1`, `-worker-1`, `-scheduler-1`).
- Most recent of 330 job results has status `SUCCESS`; no running job observed.

## 4. Cache row recount (aggregate only, no row contents copied)

| Model | Total | Nonblank `reconciliation_status` | Nonblank `reconciliation_checked_at` |
|---|---|---|---|
| DesiredNode | 5 | 5 (`converged`) | 5 |
| DesiredService | 6 | 1 (`converged`) | 1 |

Unchanged from the plan §2.2 baseline recorded 2026-07-25.

## 5. Local migration graph and VM Phase 3 coordination

- Local `0015_compute_platform_instance_and_endpoint_mac.py` directly follows `0014` and has no
  local `0016` yet.
- `devdocs/big/vm/p3/` contains reports through `report3.5.md` only — VM Phase 3 Step 6 has not
  produced a conflicting nintent/nctl commit, matching plan §2.1.

## 6. Deletion-token search (pre-removal baseline, expected non-empty)

Ran the plan §7 Step 7 eight-token search
(`reconciliation_status`, `reconciliation_checked_at`, `RECONCILIATION_`, `dashboard_url`,
`dashboard_redirect`, `nctl Dashboard`, `nctl dashboard`, `view dashboard`) across `nintent/` and
`devenv/`, excluding `migrations/0009_reconciliation_status.py`. All matches are in current
runtime source (`models.py`, `filters.py`, `tables.py`, `views.py`, `navigation.py`, `urls.py`,
`__init__.py`, both detail templates, `api/serializers.py`), `devenv/nautobot/nautobot_config.py`'s
concrete `dashboard_url`, `migrations/0010_...py`'s dependency-name reference to `0009`, and
`nintent/README.md`/`README_QUICK.md` (Phase 4 territory). No unexplained match. This is the
pre-deletion reference point for Step 7's final clean search.

## 7. Local test/measurement baseline

- `python3 -m unittest discover -s nautobot_intent_catalog/tests`: **187 passed**, matching plan
  §2.3 exactly.
- Tracked non-test Python (incl. migrations): 9,665 lines (8,128 non-migration + 1,537 migrations).
- Tracked test lines: 3,633. Tracked template lines: 1,353. 15 numbered migrations + `__init__.py`.
  All match plan §2.3.

## 8. Secrets and evidence-directory handling

`.local/secrets` confirmed ignored (`git check-ignore -v` → `.gitignore:2`); not read or copied.
Evidence directory created at mode `0700`, all four files at `0600`. No token, header, or row
content was written to tracked or private files.

## Gate

The Phase 2 handoff is intact (11-command CLI, no dashboard/serve residue in nctl), live remains on
`0014` with the same installed commit, cache counts are unchanged from the Phase 0/plan baseline,
the local migration graph has no unexpected `0016`, VM Phase 3 Step 6 has not started, dirty-state
ownership is known (one pre-existing user edit to the plan itself, untouched), and no mutation
occurred. Step 0 gate met.
