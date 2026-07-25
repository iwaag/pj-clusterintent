# Step 7 — Pre-cutover review and matched commits

Status: `complete`.

## 1. Test suites

- `nctl` (`uv run pytest -q`): **954 passed**, 0 failed/skipped. Re-run after the Step 7 fixup
  commit below.
- `nctl` (`uv lock --check`): resolved cleanly, no drift between `pyproject.toml` and the lock.
- `nintent` local Django-free suite (`python3 -m unittest discover -s nautobot_intent_catalog/tests`):
  **187 passed**, matching the current handoff baseline
  (`devdocs/big/remove_unused_surfaces/p4/plan.md` §2.5).
- Configured lint/type checks: none exist for `nctl` (`pyproject.toml` has no `ruff`/`mypy` in
  `[dependency-groups]`; invoking either fails with "No such file or directory", confirming they
  are genuinely absent rather than misconfigured). Per plan §8.1 ("do not invent a command that is
  not configured"), no lint/type step is recorded as run. `git diff --check` passed with no output
  (exit 0) in the root, `nctl`, and `nintent` trees.

## 2. Review

- **Config-key closure**: `DesiredComputePlatform`/`DesiredComputeInstance` config validators
  (nintent `compute_contract.py`, nctl's Django-free port in `sources/desired.py`) both reject
  unknown keys; unchanged since Step 5's report.
- **Schema-version parity**: `config_schema_version` defaults to `v1` and rejects any other
  explicit value identically across nintent model/form/REST/YAML and nctl's parser — unchanged
  since Steps 2-5.
- **Target isolation**: `test_vm_p3_compute_stays_inert.py` (Step 5) plus Step 6's malformed-vs-
  healthy-sibling assertions still pass; a blocked dnsmasq render or a `desired_mac_mismatch` gap
  affects only its own node/endpoint, never an unrelated target.
- **Migration reversibility**: `0015_compute_platform_instance_and_endpoint_mac.py` and
  `0016_remove_reconciliation_dashboard_surfaces.py` are unchanged since the commits that
  introduced them (`34795b2`, `55be38b` — confirmed via `git log --oneline` on each file: exactly
  one commit apiece).
- **dnsmasq safety**: see `report3.6.md` §3-5 — blocked renders never produce an authoritative
  artifact/digest, never reach SSH/Ansible, and `desired_mac_mismatch` is manual-review-only.
- **Secret handling**: no command in this step read `.local/secrets`, printed a token, or touched
  live Nautobot; all evidence gathering was local git/pytest/grep.
- **Legacy field / dual-read / alias search**: `grep -rn realized_vm nctl/src` shows only the new,
  differently-scoped `DesiredComputeInstance.realized_vm(+_source)` field and explanatory
  comments/docstrings about the Step 5 removal — no `DesiredNode.realized_vm` reference remains
  anywhere in active nctl source. `grep -rn "DesiredNode.*realized_vm"` in nintent's active
  `nautobot_intent_catalog/*.py` returns nothing. No `nctl dashboard`/`nctl serve`/`dashboard_url`
  token exists in nctl source/docs (already removed by `remove_unused_surfaces` Phases 1-2).
- **Old render output schema**: `nctl.render.dnsmasq.v3` is the only render-dnsmasq schema in
  `docs/compatibility.md` and `tests/test_compatibility_snapshots.py`; the separate
  `nctl.apply.dnsmasq.v2` schema is unrelated (apply, not render) and correctly still `v2`. One
  stale `v2` reference *was* found and fixed — see §3.

## 3. Fixup commit

`cli/main.py`'s `RenderJsonOption` help string still said
`"Print the nctl.render.dnsmasq.v2 envelope as JSON."` after Step 6 bumped the actual schema
constant to `v3` in the same commit — a copy-paste the original commit missed (found by the
legacy-name grep above, not by a test — no test asserted the CLI help text). Fixed and committed
locally as `nctl` commit `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9`
("vm p3 step 7 (fixup): correct stale nctl.render.dnsmasq.v2 CLI help text"), on top of the
already-committed Step 1-6 work. Not pushed (per §3.3 mutation-boundary rule: "The agent must not
push").

No nintent changes were needed in this step — its Steps 1-4 commits (`09f38b9`, `34795b2`,
`3510794`, `ad0c642`) plus the `remove_unused_surfaces` Phase 3/4 work on top were already the
final reviewable state, and nothing found in this review touched nintent.

## 4. Matched and rollback tuples

Exact final matched tuple (Step 7 planning-time HEADs, all local commits already pushed to their
respective `origin/main` except the one nctl fixup commit above):

| Repository | Revision | Remote status |
|---|---|---|
| superproject | `a58d908d887d19aa3b895e196fb7b22d4a0c555e` | pushed (submodule pointer for `nctl` will move once this report's commit updates it) |
| nctl | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | **not yet pushed** — one local fixup commit ahead of `origin/main` (`7a0f2cf`) |
| nintent | `c343c5a56047b0df9ad901dd4459863ef1954053` | pushed; `origin/main` confirmed at the same commit via `git fetch` |
| nauto | `251b056549f1b01f604b42b486fdc12d667db521` | pushed, unchanged by this step |
| nodeutils | `3a0fdf9817d970935847aafd46c35bf07133c20c` | pushed, unchanged by this step |
| ansible_agdev | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | pushed, unchanged by this step |

Live rollback tuple (unchanged by this documentation-only/local-fixup step — no live mutation
occurred and none was in scope):

```text
nintent: ad9d36397d23c269ad748e13acbccc532fa29f52 (live installed commit)
migration state: through 0014_braindump_exchange_diary
nctl/root: the actual pre-window tuple in place before the eventual maintenance window
database backup: not created here (Phase 5/remove_unused_surfaces Phase 5 owner)
```

This matches the parent `remove_unused_surfaces/p4/plan.md` §4.7 contract, which VM Phase 3 Step 7
was defined to share one revision review with (that plan's §2.3).

## 5. What is still outstanding before the coordinated deployment

Per plan §3.3 gate 2 and Section 9, Step 8 (coordinated breaking deployment) is a separately
approved, live, hard-to-reverse maintenance-window action — explicitly out of this step's and this
session's scope. Before it can run:

- the user must push the local nctl fixup commit `ebe8a1d` (the only currently unpushed revision
  in the matched tuple);
- `remove_unused_surfaces` Phase 4's own remaining gates (its Step 6 measurement pass and Step 7
  commit/push sequencing, which explicitly depends on this VM Step 6/7 completion per its plan
  §2.3) still need to run using this now-complete VM Phase 3 state;
- the actual maintenance window (stop writes, assert legacy-link zero count, rebuild/restart,
  apply `0015`+`0016`, activate the matching nctl revision, resume) is unstarted and requires
  separate explicit operator approval at each gate in plan §3.3.

## Gate

Both final revisions (nintent `c343c5a5`, nctl `ebe8a1d5`) are ready and reviewed; no
compatibility-only artifact, dual reader, or stale-schema reference remains that this review could
find; nintent is remotely available; nctl has one small local-only fixup commit awaiting the user's
push. No rebuild, restart, migration, Job, desired write, seed, reconcile apply, Ansible run, or
host mutation occurred in this step.
