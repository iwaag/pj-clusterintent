# Phase 1.5 Report — Step 4 (remove the nintent hosts-intent export Job)

Date: 2026-07-16. Implements [p1ex1/plan.md](plan.md) Step 4. This is the second commit unit
in the plan's suggested order and touches only the `nintent` submodule. The live parity gate
required before this deletion passed in [report1-3.md](report1-3.md).

## What changed

- Removed `ExportAnsibleHostsIntent` from `nautobot_intent_catalog/jobs.py`, including its
  renderer import, Job class, and `jobs` registration tuple entry.
- Deleted `nautobot_intent_catalog/ansible_inventory.py`. Rendering now exists only in
  `nctl_core.hosts_intent`, as established and parity-tested in Steps 1–3.
- Deleted `nautobot_intent_catalog/tests/test_ansible_inventory.py`; its portable behavior
  tests were moved to nctl in Steps 1–3 before the source implementation was removed.
- Bumped the distribution version in `pyproject.toml`, the Nautobot App version in
  `nautobot_intent_catalog/__init__.py`, and the local package entry in `uv.lock` from 0.7.0
  to 0.8.0.
- Removed the retired Job from `README.md` and `README_QUICK.md`, and added
  `nctl render hosts-intent --out ansible_agdev/inventories/generated` to the quick-reference
  nctl workflows. These small documentation edits keep the nintent commit internally
  consistent; broader parent/nctl/ansible documentation remains Step 5–6 work.

## Verification

- `cd nintent && uv run python3 -m unittest discover` — **80 tests passed**.
- `cd nintent && uv lock --check` — passed (`Resolved 2 packages`).
- Imported the installed editable package and asserted both
  `importlib.metadata.version("nautobot-intent-catalog")` and
  `IntentCatalogConfig.version` equal `0.8.0` — passed.
- Repository search found no remaining `ExportAnsibleHostsIntent`, display name
  `Export Ansible Hosts Intent`, `ansible_inventory`, or `0.7.0` references in active nintent
  files. Historical notes in `DEVLOG_PICKUP.md` were intentionally excluded from this check.
- `git diff --check` for both the parent and nintent worktrees — passed.

## Deployment verification after push

After the user pushed nintent commit `118a354` (`p1ex1 s4`):

- Ran `docker compose --env-file ../.env build --no-cache` and
  `docker compose --env-file ../.env up -d` from `devenv/nautobot`. The build resolved the
  GitHub dependency to `118a354`; the web, worker, and scheduler containers were recreated and
  the web container became healthy.
- The container reports nintent distribution version `0.8.0` and
  `IntentCatalogConfig.version == "0.8.0"`.
- The Nautobot Jobs API has no installed registration for `Export Ansible Hosts Intent`.
  Nautobot retains the historical database row with `installed=false`, as it does for other
  removed Jobs; it is no longer offered as an executable installed Job.
- `nctl status` returned `ok: True`: authenticated Nautobot, intent GraphQL, dumps, and all
  five submodules were green; nintent was reported clean at `118a354dfef1`.

## Commit boundary / next step

Step 4 is complete, including its post-push deployment verification. Step 5 is recorded in
[report5.md](report5.md).
