# Phase 2 Step 7 — Run the full suite and final measurements

Parent: [plan.md](plan.md) Step 7.

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p2/20260725-155334/`, additionally containing `final-tests.txt`,
`final-collect.txt`, `final-lock-check.txt`, `final-help.txt`, `final-measurements.txt`,
`final-repo-status.txt`.

## 1. Full suite / collection / lock

- `uv run pytest -q`: **954 passed**, 0 failed.
- `uv run pytest --collect-only -q`: **954 tests collected**.
- `uv lock --check`: `Resolved 26 packages` — clean, no drift from the committed lock.

## 2. Help and removed-command recheck

- `nctl --help`: 11 commands (`status actual drift reconcile lifecycle render apply ops braindump
  ssh session`) — no `dashboard`, no `serve`.
- `nctl dashboard`: exit 2, `Error: No such command 'dashboard'.`
- `nctl serve`: exit 2, `Error: No such command 'serve'.`

## 3. Model-field recheck

Reconfirmed (same command as Step 6, rerun here for the final state): `Config.model_fields` has
no `dashboard`/`serve`; `ReconcileData.model_fields` is exactly the 16 frozen fields with no
`dashboard`.

## 4. Deletion-search recheck

Rerunning the same 16-token search against the final tree reproduces exactly Step 6's result: 14
tokens zero matches, `reconciliation_status` only in the historical fixture, `[dashboard]` and
`index.html` only in the two new absence-proving tests. No new match appeared between Step 6 and
Step 7.

## 5. Final measurements

| Metric | Baseline (Step 0) | Final | Delta |
|---|---|---|---|
| `nctl --help` top-level commands | 12 | 11 | −1 (`dashboard` removed) |
| Collected tests | 980 | 954 | −26 |
| Tracked source lines (`src/`) | 18,137 | 17,763 | −374 |
| Tracked test lines (`tests/`) | 20,025 | 19,380 | −645 |
| Source `.py` file count | — | 68 | — |
| Test `.py` file count | — | 72 | — |

The −26 test delta reconciles exactly: −29 dedicated dashboard tests (Step 2) −1
dashboard-degradation test (Step 3) +3 net new contract tests (Step 1: `test_dashboard_is_an_
unknown_command_not_a_compatibility_path`, `test_dashboard_section_is_rejected_as_unknown`,
`test_reconcile_data_fields_are_exactly_the_frozen_set_with_no_dashboard_field`) +1 new artifact/
no-PATCH test (Step 5) = −29 −1 +3 +1 = −26. These are diagnostic measurements, not quotas, per
plan §2.2.

## 6. `pyproject.toml`/`uv.lock` unchanged confirmation

Reconfirmed unchanged since Phase 1 (commit `183e894`); no orphan dependency was found requiring
a lock regeneration in this phase, matching the plan's own prediction.

## 7. `git diff --check` and diff-hygiene inspection

`git diff --check 73096304abcf18bb8fd9d504e9df9166fd959919 HEAD` (nctl, comparing the Phase 1
ending revision to the current Phase 2 HEAD): clean, no whitespace errors.

Full Phase 2 nctl diff: **24 files changed, 113 insertions(+), 1562 deletions(-)**. Every changed
path maps directly to the plan's §5.1–§5.4 inventory: the five deleted implementation files, four
deleted dedicated test files, `cli/main.py`/`config.py`/`example.nctl.toml` (command/config
removal), `reconcile/executor.py` (terminal decoupling), `drift_render.py`/`sources/desired.py`/
`test_vm_p3_compute_stays_inert.py` (wording), `README.md`/`docs/compatibility.md`/
`docs/output-format.md`/`docs/usage_example.md` (current docs), and
`test_cli_surface.py`/`test_compatibility_snapshots.py`/`test_config.py`/
`test_reconcile_executor.py` (shared tests). No nintent, VM, drift/planner comparator, SSH-policy,
or actuation file appears in the diff — confirmed by the file list itself containing no path
outside those exact categories.

## 8. Final revisions and status

| Repository | Revision | Dirty state |
|---|---|---|
| superproject | `5db19964774577064fde6c64dea2b683ac3cb3b5` | clean |
| `nctl` | `7a0f2cf035179fbea5deed4cacb05573f8c8dffa` | clean |
| `nintent` | `ad0c6424141cea62bf731288ed1f0ca0df4e4711` | clean, **unchanged** (matches plan §3.3: nintent's cache/UI/link residue is explicitly Phase 3 territory) |

## Gate

Full suite, lock check, deletion searches, package proof (Step 6), model-field checks, and diff
hygiene all pass. Step 7 gate met.
