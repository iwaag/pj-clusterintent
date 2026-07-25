# Phase 4 Step 1 — Freeze the current-document manifest

Parent: [plan.md](plan.md) Step 1.

Executed 2026-07-25. Evidence added to
`.local/remove-unused-surfaces/p4/20260725-172224/`: `deletion-search-before.tsv` (full raw
`git grep` output for all 26 §6.1 tokens across all 6 repositories, unfiltered).

## 1. §5 file existence

All 16 files named in plan §5.1/§5.2 exist: root `README.md`, `README_DEV.md`; `nintent/README.md`,
`nintent/README_QUICK.md`, `nintent/README_DEV.md`; `devdocs/big/core_reconcile/roadmap.md`,
`devdocs/big/braindump/roadmap.md`, `devdocs/big/vm/roadmap.md`, `devdocs/big/vm/p3/plan.md`;
`nctl/README.md`, `nctl/docs/output-format.md`, `nctl/docs/compatibility.md`,
`nctl/docs/usage_example.md`, `nctl/docs/event-log.md`, `nctl/example.nctl.toml`;
`devenv/nautobot/nautobot_config.py`. No new current document was found while tracing links from
these files (§1.4 below).

## 2. Token search results, filtered to actionable rows

Ran the 26-token §6.1 set (required + structural) across the superproject and all five submodules,
6×26 = 156 searches. 131 distinct files matched at least one token. Of those, 125 are one of:
completed Better Usability/Braindump/core-reconcile(`p3`/`p5`)/VM/SSH-fix/`service_placement`/
`ipam_policy`/`permission_fix`/early-commits/restructuring plans-reports (historical), remove-
unused-surfaces Phases 0–3 plans/reports and this phase's own `plan.md`/`report0.md` (initiative-
evidence), `nintent` migrations `0009`/`0010`/`0016` (migration), `nintent`'s
`test_remove_unused_surfaces.py` (negative-test), `nctl`'s `test_operations_index.py`
(opaque-history fixture), `nctl`'s `test_events.py`/`test_reconcile_executor.py` (prose/identifier
false positives — "subscriber/listener" prose, `observe_node`/`observed_services` identifiers, and
explicit negative assertions that no dashboard write/PATCH occurs — no dashboard/serve residue),
`ansible_agdev/api/*` (unrelated FastAPI webhook service, plan §6.1's own named example), and
`nauto`/`nodeutils` `*published_ports*` identifiers (substring false positive on `publish`).

The remaining 6 files are the actionable current-document set, all matching plan §5.1's inventory
exactly:

| File | Matched tokens (current instructions) |
|---|---|
| root `README.md` | `nctl dashboard` (2 command lines + prose), `nctl serve` (command line + prose) |
| `nintent/README.md` | `dashboard_url`, `dashboard_redirect`, `reconciliation_status`, `reconciliation_checked_at`, `nctl dashboard` |
| `nintent/README_QUICK.md` | `nctl dashboard`, `dashboard_url`, `reconciliation_status`, `reconciliation_checked_at` |
| `devdocs/big/core_reconcile/roadmap.md` | `nctl dashboard`, `nctl serve`, dashboard/WebSocket vision text (Phase 3/5 sections) |
| `devdocs/big/braindump/roadmap.md` | `nctl serve`, dashboard (optional Phase 4 goal) |
| `devdocs/big/vm/roadmap.md` | `dashboard` (Phase 4/9 and definition-of-done vocabulary) |

`devdocs/big/vm/p3/plan.md` matched `dashboard`/`nctl serve`/`nctl dashboard`, but every occurrence
is inside the already-amended Phase 0 supersession note (lines 16–28) or later text that already
says "no dashboard or serve output" (line 970) / "dashboard compute tiles... superseded" (line 216)
— review-only per plan §5.2, not an edit-current row; see §3 below for the one wording gap found in
that note.

`nctl/README.md`, `docs/output-format.md`, `docs/compatibility.md`, `docs/usage_example.md`,
`docs/event-log.md`, `example.nctl.toml`, `nintent/README_DEV.md`, root `README_DEV.md`, and
`devenv/nautobot/nautobot_config.py` matched **zero** tokens — confirmed `verified-current`, matching
plan §2.4's planning-time observation exactly.

## 3. Link-tracing beyond exact tokens

Read root `README.md` in full (not just token matches): its "Developer Docs" section and Phase 3/5
references link to `devdocs/vision/core_reconcile/...`, a path that does not exist (`ls
devdocs/vision/` shows only `refactor/`; the real path is `devdocs/big/core_reconcile/...`). This is
a pre-existing broken link, not itself a removed-surface token match, but it sits inside the same
paragraphs Step 2 must edit for the dashboard/serve sections — folded into Step 2's root-README edit
rather than treated as a separate manifest row, per plan §2.9 ("check links and anchors").

`devdocs/big/vm/p3/plan.md`'s supersession note (line 21) says the removed surfaces "are being
removed" (present-progressive) rather than reflecting that local removal (Phases 0–3) is now
implemented and only live deployment is pending. Plan §4.5 explicitly permits updating "only its top
supersession status if needed to say that local removal is implemented and live deployment is
pending" — folded into Step 3 (not Step 2, since this file is a Step 3/§5.1-adjacent review target,
not a Step 2 root/component-README edit).

## 4. Classification summary

| Classification | Count | Examples |
|---|---:|---|
| `edit-current` | 6 | root `README.md`, `nintent/README.md`, `nintent/README_QUICK.md`, `core_reconcile/roadmap.md`, `braindump/roadmap.md`, `vm/roadmap.md` |
| `verified-current` (no change) | 9 | `nctl/README.md`, `nctl/docs/*.md` (4), `nctl/example.nctl.toml`, `nintent/README_DEV.md`, root `README_DEV.md`, `devenv/nautobot/nautobot_config.py` |
| `edit-current` (narrow wording only) | 1 | `devdocs/big/vm/p3/plan.md` (supersession-note tense) |
| `migration` | 3 | `nintent` migrations `0009`, `0010`, `0016` |
| `negative-test` | 1 | `nintent/nautobot_intent_catalog/tests/test_remove_unused_surfaces.py` |
| `initiative-evidence` (opaque-history fixture) | 1 | `nctl/tests/test_operations_index.py` |
| `keep-unrelated` (false positive) | ~5 | `ansible_agdev/api/*`, `nauto`/`nodeutils` `published_ports`, `nctl` `observe_node`/subscriber-prose |
| `historical` | ~105 | completed phase plans/reports across Better Usability, Braindump, core-reconcile, VM, SSH-fix, and remove-unused-surfaces Phases 0–3 |

No unknown or unclassified row remains.

## 5. Frozen intended changed-file list for Steps 2–3

1. root `README.md` — remove `nctl dashboard`/`nctl serve` commands and prose sections; fix the
   broken `devdocs/vision/core_reconcile` link.
2. `nintent/README.md` — remove cache-writer REST description and reconciliation-status/dashboard-
   link section.
3. `nintent/README_QUICK.md` — remove dashboard command/config/PATCH instructions.
4. `devdocs/big/core_reconcile/roadmap.md` — supersede Phase 3/5 dashboard/realtime-API goals.
5. `devdocs/big/braindump/roadmap.md` — supersede optional Phase 4 serve/dashboard integration.
6. `devdocs/big/vm/roadmap.md` — replace operative dashboard/status vocabulary with retained
   evidence contract.
7. `devdocs/big/vm/p3/plan.md` — update only the supersession-note tense (local removal implemented,
   live deployment pending); no other change.

This matches plan §5.1 exactly, with one addition (the root-README broken link, folded into row 1)
and one narrowing (row 7 is a one-line tense fix, not a broader edit, since the rest of that file's
dashboard/status vocabulary already reflects the retained contract).

## Gate

Every current document and every token match has one owner and disposition; no unknown row remains.
Step 1 gate met.
