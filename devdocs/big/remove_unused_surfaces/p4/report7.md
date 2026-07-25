# Phase 4 Step 6 — Retained verification and repeatable measurements

Parent: [plan.md](plan.md) Step 6.

Executed 2026-07-25, after VM Phase 3 Step 6 completed. Evidence added to
`.local/remove-unused-surfaces/p4/20260725-172224/`: `step6-command-surface.txt`,
`step6-wheel-build.txt`, `step6-plain-install.txt`, `step6-measurements.txt`,
`step6-dependencies.txt`, `step6-doc-linecounts.txt`, `step6-deletion-search-final.tsv`.

## 0. Gate re-check: VM Phase 3 Step 6 is now complete

The user reported VM Phase 3 Steps 6–7 complete. Independently verified rather than taken on trust:

- `devdocs/big/vm/p3/report3.6.md` (Step 6, `complete`) and `report3.7.md` (Step 7, `complete`) both
  exist and are self-consistent internally.
- `nctl` `origin/main` now resolves to `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` (`git fetch` +
  `rev-parse`), matching report3.7.md §4's claimed final tuple — the Step 7 CLI-help fixup is
  pushed.
- `nintent` `origin/main` resolves to `c343c5a56047b0df9ad901dd4459863ef1954053` — this phase's own
  Step 2 documentation commit is pushed (report3.7.md recorded it as not-yet-pushed at Step 7
  planning time; it has been pushed since).
- Re-ran `uv run pytest -q` in `nctl` myself: **954 passed**, matching report3.6/3.7's cited count
  exactly (own re-run, not just the implementer's, per this repository's established verification
  convention).
- Re-ran `uv lock --check` in `nctl` myself: resolved cleanly, matching report3.7's claim.
- `git -C nintent diff --stat 0914ca4 c343c5a`: only `README.md`/`README_QUICK.md` changed — the
  final nintent tree differs from the Phase 3 252-test-proven tree by documentation alone.

VM Phase 3 Step 6/7 are confirmed complete and pushed. This phase's Steps 6–7 gate is now open.

## 1. Final pre-commit source state and VM Step 6 report/revisions

Superproject `1308074` at the start of this step (before this report's own commit). VM Step 6/7 were
recorded in root commit `7831b8f` ("vm p3 steps 6-7: record already-implemented desired-MAC dnsmasq
safety and pre-cutover review"), which bumped only the `nctl` submodule pointer to `ebe8a1d`; the
`nintent` pointer in root was already at this phase's own `c343c5a` and was untouched by that commit.

## 2. Full nctl suite

`uv run pytest -q`: **954 passed**, 0 failed/skipped, 5.38s. Matches the plan §2.5 handoff value and
VM Phase 3 Step 6/7's own count exactly.

## 3. `uv lock --check`

Resolved 26 packages, no drift between `pyproject.toml` and `uv.lock`.

## 4. Local nintent suite

`python3 -m unittest discover -s nautobot_intent_catalog/tests`: **187 passed**. Matches plan §2.5.

## 5. Nautobot-runtime proof: inherited, not rerun

Per plan §7.2 item 4, the Phase 3 252-test Nautobot-runtime proof may be cited only if the final
nintent diff after `0914ca4...` is documentation alone. Confirmed (§0 above): `git diff --stat
0914ca4 c343c5a` touches only `README.md`/`README_QUICK.md`. The Phase 3 252-test proof (see
[p3/report.md](../p3/report.md) §7) is inherited as final Phase 4 evidence rather than rerun against
disposable state, exactly as plan §7.2 item 5 permits for a documentation-only change.

## 6. Plain nctl wheel proof

Built with `uv build --out-dir <mktemp -d>`: `nctl-0.0.1-py3-none-any.whl` (227,563 bytes). Installed
into a fresh `uv venv` with only the wheel: 20 packages resolved
(`typer`/`httpx`/`pydantic`/`pyyaml` plus their transitive deps: `annotated-doc`, `annotated-types`,
`anyio`, `certifi`, `h11`, `httpcore`, `idna`, `markdown-it-py`, `mdurl`, `pydantic-core`, `pygments`,
`rich`, `shellingham`, `typing-extensions`, `typing-inspection`, plus `nctl` itself). Confirmed:

- `nctl --help` in the fresh venv shows the same 11 commands as the dev environment, no
  `dashboard`/`serve`.
- `import nctl_core.events, nctl_core.operations_index, nctl_core.ops_render` succeeds.
- `import nctl_core.serve` / `nctl_core.dashboard` / `nctl_core.dashboard_render` each raise
  `ModuleNotFoundError` — none installed.
- `find <venv> -iname '*serve*' -o -iname '*dashboard*'`: only `sources/observed.py` (a substring
  false-positive: "ob**serve**d" contains "serve"; no `serve`/`dashboard` module, template, or asset
  present).
- `pip show` for `fastapi`/`starlette`/`uvicorn`/`websockets`/`httptools`/`uvloop`/`watchfiles`/
  `python-dotenv`: none installed.

## 7. Command surface

`nctl --help`: 11 top-level commands — `status actual drift reconcile lifecycle render apply ops
braindump ssh session`. No `dashboard`, no `serve`. Identical in the dev environment and the fresh
plain-wheel install (§6).

## 8. Source/test/template/current-doc line counts (frozen path patterns)

| Metric | Command | Value |
|---|---|---:|
| nctl `src/` lines | `git -C nctl ls-files 'src/**/*.py' \| xargs wc -l` | 17,763 |
| nctl `tests/` lines | `git -C nctl ls-files \| grep '^tests/' \| grep '\.py$' \| xargs wc -l` | 19,380 |
| nctl collected pytest cases | `uv run pytest -q --collect-only` | 954 |
| nintent non-test Python incl. migrations | `git -C nintent ls-files 'nautobot_intent_catalog/*.py' 'nautobot_intent_catalog/**/*.py' \| grep -v /tests/ \| sort -u \| xargs wc -l` | 9,560 |
| nintent test lines | `git -C nintent ls-files 'nautobot_intent_catalog/tests/*.py' \| xargs wc -l` | 4,029 |
| nintent template lines | `git -C nintent ls-files 'nautobot_intent_catalog/templates/**/*.html' \| xargs wc -l` | 1,327 |
| nintent numbered migrations | `git -C nintent ls-files 'nautobot_intent_catalog/migrations/[0-9]*.py' \| wc -l` | 16 |
| current-document set (§5 16 files) tracked lines | `wc -l` over the exact §5.1/§5.2 file list | 5,417 |

All six nctl/nintent values are unchanged from the plan §2.5 handoff baseline exactly — expected,
since VM Phase 3 Step 6's code landed before this baseline was recorded (`cb655c6`, 2026-07-25
12:20:59, predates the plan's own 2026-07-25 snapshot) and this phase touched no nctl/nintent source.

## 9. Dependency inventory

`nctl/pyproject.toml` direct dependencies: `typer>=0.12`, `httpx>=0.27`, `pydantic>=2.7`,
`pyyaml>=6.0`. Dev group: `pytest>=8.0`, `respx>=0.21`. No `serve` optional extra. `uv.lock`: 26
locked packages total (listed in `step6-dependencies.txt`), none of `fastapi`/`starlette`/`uvicorn`/
`websockets`/`httptools`/`uvloop`/`watchfiles`/`python-dotenv`.

## 10. nauto/nodeutils/ansible_agdev

Unchanged by the coordinated VM work: `nauto` `251b056`, `nodeutils` `3a0fdf9`,
`ansible_agdev` `339d361` — identical to Step 0's recording and to `origin/main` for each.

## 11. Final search re-run after build/test activity

Re-ran the full 26-token, 6-repository search after the wheel build/install/lock-check activity
above. Diffed against Step 5's `deletion-search-after.tsv`: exactly 3 new files matched —
this phase's own `report.md`(not yet written when Step 5 ran)/`report5.md`, and VM's
`report3.7.md` line 42 ("No `nctl dashboard`/`nctl serve`/`dashboard_url` token exists..." — a
self-explanatory absence confirmation, allowed under plan §6.3). No other file's match set changed.
`git diff --check` re-run clean in all 6 repositories (no output).

## 12. Cleanup

The temporary wheel-build directory and the temporary venv directory (both under the OS `mktemp -d`
area, outside the repository) were removed after use; `ls` on each path confirms both are gone. No
tracked file, `.local/` evidence file, or repository state was touched by the build/install/cleanup
sequence — reconfirmed via `git status --porcelain` (clean) in the superproject and `nctl` after
cleanup.

## Gate

Final measurements are repeatable by Phase 5 (frozen path patterns recorded in §8), retained tests
pass (nctl 954, nintent 187, both independently re-run), the plain-wheel package proof is clean (no
server/dashboard code, module, asset, or dependency), and environment cleanup is complete. Step 6
gate met.
