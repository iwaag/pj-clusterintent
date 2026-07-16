# Phase 4 Report — Step 8 (Cut over Ansible entry points and remove old orchestration)

Date: 2026-07-17. Implements [p4/plan.md](plan.md) Step 8, the eighth suggested commit boundary.
With Step 7's `nctl reconcile` proven as a bounded executor, this boundary removes the
Ansible-side collect/ingest orchestration it replaces and repoints the operator-facing entry
points (`Makefile`, `README.md`, `README_ADMIN.md`) at it. No nctl/nauto/nintent/nodeutils code
changed in this boundary — it is documentation and Ansible-repo cutover only.

## What was built

### Deleted `ansible_agdev/playbooks/nautobot/collect_nodeutils_and_ingest_nautobot.yml`

This playbook's three-play sequence (run `run_nodeutils_collect.yml`, ad-hoc `slurp` each host's
report, then look up/run/report the Nautobot `Ingest Nodeutils Inventory` Job over inline
`ansible.builtin.uri` tasks) is exactly the orchestration `nctl_core.observation.run_observation`
already performs since Step 2, with the improvements the plan required it to have and the old
playbook never did: monotonic-timeout Job polling to a terminal state (Step 1's
`NautobotJobRunner`), a validated structured `nodeutils-ingest-summary.json` cross-check (Step 2)
instead of trusting an unpolled fire-and-forget Job response, and byte-limit/identity/duplicate
validation on each report before it enters the batch. Keeping both would have left two divergent
implementations of the same sequencing logic, which Decision 4 rules out explicitly. The playbook
is removed with `git rm`, not just its Makefile/README callers, per the plan's literal instruction.

`run_nodeutils_collect.yml` is untouched and remains directly runnable
(`ansible-playbook playbooks/nautobot/run_nodeutils_collect.yml --limit <host>`) for diagnostics —
it still only clones/updates nodeutils, installs the optional probe-hints config, and writes the
local `/var/lib/nodeutils/inventory.json` report. It takes no Nautobot variables and makes no REST
call, so nothing about it needed to change for the cutover.

### `Makefile`

The old `pipeline: bootstrap-inventory collect-ingest production-inventory` chain called three
separate subprocesses, the middle one being the now-deleted playbook. `pipeline` is now one line,
`$(NCTL) reconcile --config ../nctl.toml --yes` — the single bounded operation that performs
drift, bootstrap collection, report-cache installation, ingest Job polling, ledger links,
full production-inventory regeneration, service/dnsmasq actuation, and re-observation itself.

`bootstrap-inventory` and `production-inventory` targets are kept verbatim (per the plan's
"Keep explicit bootstrap/production inventory targets for diagnostics and manual recovery") but
their Makefile comments now say explicitly that `nctl reconcile` does not shell out to either of
them — confirmed by reading `nctl_core/observation.py`: `run_observation` renders its own
operation-scoped `bootstrap/hosts_intent.yml` under the operation's artifact directory via
`export_hosts_intent`/`render_hosts_intent_yml` and never touches
`inventories/generated/hosts_intent.yml`. Running `make bootstrap-inventory` afterward would
overwrite a file `reconcile` never read, which is why the comment calls both targets diagnostics-
only rather than implying they are prerequisites. The `collect-ingest` target and its
`ANSIBLE_PLAYBOOK`/`BOOTSTRAP_INVENTORY` variables (only referenced by that target) are removed;
`ANSIBLE_PLAYBOOK` is no longer referenced anywhere in the Makefile since no target invokes
`ansible-playbook` directly anymore.

### `README.md` / `README_ADMIN.md`

- `README.md`'s dedicated collect+ingest usage example (`ansible-playbook
  playbooks/nautobot/collect_nodeutils_and_ingest_nautobot.yml`, plus its `-e
  nautobot_ingest_dry_run=true` preview variant) is replaced with the `nctl reconcile --yes`
  invocation from the parent checkout, matching the `Makefile`'s `pipeline` target.
- The per-playbook notes bullet that described `collect_nodeutils_and_ingest_nautobot.yml`'s
  behavior is replaced with a bullet stating plainly where the responsibility now lives: Ansible
  has no task that calls `/api/extras/jobs/` or reads a Nautobot token, and `vars/nautobot.yml` /
  the vault `nautobot_url`/`nautobot_token` variables are unused by any playbook in the repository
  — kept only as reference since `nctl` reads `NAUTOBOT_URL`/`NAUTOBOT_TOKEN` from the environment
  itself.
- `README_ADMIN.md`'s `make pipeline` walkthrough is rewritten to describe the one bounded
  operation instead of the removed three-stage sequence, and a note is added to the Vault setup
  section clarifying that `nautobot_url`/`nautobot_token`/`nautobot_validate_certs` are not
  consumed by any current playbook — they remain as scaffolding for a future Ansible task that
  might need direct Nautobot API access, not as something the routine pipeline depends on.
- `docs/production_inventory_contract.md` needed no change: it already described `nctl render
  production` and `make pipeline`'s stage order in terms that don't name the deleted playbook.

## Verification

- Repository-wide search (`grep -rn`) confirms zero remaining references to
  `collect_nodeutils_and_ingest_nautobot` anywhere under `pj-clusterintent` (checked
  `ansible_agdev`, `nctl`, `nauto`, `nintent`, `nodeutils`, and `devdocs`); the historical mentions
  in `devdocs/functions/*` and `devdocs/vision/core_reconcile/{roadmap,p1ex1,p2}/*` are dated
  reports of earlier phases and are left as history, not live documentation.
- `grep -rn "extras/jobs"` under `ansible_agdev` returns no matches — no Ansible task calls the
  Nautobot Jobs API.
- `grep -rln "nautobot_token\|NAUTOBOT_TOKEN"` under `ansible_agdev` now only matches `vars/
  nautobot.yml` (the unused variable definitions), the generated `group_vars/all/main.yml`/
  `vault.example.yml` scaffolding, and doc/README lines that either explain the vars are unused or
  show a `NAUTOBOT_TOKEN=...` environment prefix for an `nctl` command — no remaining Ansible task
  reads a Nautobot token.
- `grep -rn "collect-ingest\|collect_ingest"` under `ansible_agdev` returns no matches.
- `ansible-playbook --syntax-check` against every playbook under `ansible_agdev/playbooks/` (22
  files, the full tree) passes, confirming the deletion left no dangling
  `import_playbook`/`include` reference.
- `make -n pipeline`, `make -n bootstrap-inventory`, `make -n production-inventory` each print
  exactly the intended single command line.
- `git diff --check` / `git diff --cached --check` in `ansible_agdev` — clean, no whitespace
  errors.
- `cd nctl && uv run pytest -q` — **420 passed**, unchanged from Step 7 (this boundary touches no
  nctl source).

## Deliberate non-work

- no nctl/nauto/nintent/nodeutils code changes — this boundary is Ansible-repo and doc cutover
  only, as the plan scopes Step 8;
- no live run of `nctl reconcile --yes` against the real local Nautobot/Ansible environment — the
  already-known local-token 403 (Steps 3/6/7) still blocks that, and Step 9 is where live rollout
  happens;
- `vars/nautobot.yml` and the vault `nautobot_url`/`nautobot_token` scaffolding are documented as
  unused rather than deleted, since no current plan step calls for removing them and a future
  Ansible task could still legitimately need direct Nautobot API access;
- no change to `ansible_agdev/docs/production_inventory_contract.md`, `README_DEV.md`, or
  `README_HOST.md` — none of them referenced the deleted playbook, the Job API, or a Nautobot
  token;
- no commit, push, or Nautobot deployment.

## Files changed in this boundary

ansible_agdev (submodule working tree; not yet committed):

- deleted `playbooks/nautobot/collect_nodeutils_and_ingest_nautobot.yml` (staged via `git rm`);
- updated `Makefile` (`pipeline` now calls `nctl reconcile --yes`; `collect-ingest` target and its
  unused `ANSIBLE_PLAYBOOK`/`BOOTSTRAP_INVENTORY` variables removed; `bootstrap-inventory`/
  `production-inventory` kept with clarifying comments);
- updated `README.md` (collect+ingest usage example and per-playbook notes bullet);
- updated `README_ADMIN.md` (`make pipeline` walkthrough and a Vault-setup clarification note).

Parent repository:

- added this report. No commit was created in either the parent or the `ansible_agdev` submodule.
