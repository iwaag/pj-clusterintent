# Phase 1.5 Implementation Plan: hosts-intent export in nctl, retire the last Job-export path

Parent: [roadmap.md](../roadmap.md) — Phase 1.5: apply the Phase 1 pattern (pure renderer +
GraphQL fetch + parity gate + Job deletion) to the `ExportAnsibleHostsIntent` export.

Note on ordering: this phase was deferred past Phases 2–3 (drift engine, dashboard), which is
why the plan below leans on Phase 2 infrastructure that the roadmap entry — written before
Phase 2 landed — could not anticipate. That makes this phase *smaller* than Phase 1, not
larger: the fetch layer and the inventory-validation pattern already exist.

## Current state (as of 2026-07-16)

- Phases 0, 0-EX1, 1, 2, 3 are complete. `nctl` has `status`, `drift`, `dashboard`,
  `render dnsmasq`, `render production`, `apply dnsmasq`. The hosts-intent export is the **last
  remaining Nautobot-Job export path** in the system.
- Rendering today lives in `nintent`:
  - `nautobot_intent_catalog/ansible_inventory.py` — pure functions (`export_hosts_intent`,
    `render_hosts_intent_yml`, `render_hosts_intent_json`, `hosts_intent_payload`), schema
    `2.0`. Deterministic: nodes sorted by `(slug, name)`, eligibility gates
    (`ELIGIBLE_NODE_LIFECYCLES` = planned/approved/active, `ELIGIBLE_NODE_TYPES` =
    device/virtual_machine/service_host), mDNS endpoint selection (prefer `primary`, then
    `management`, then any, tie-break `(endpoint_type, name)`), inventory-hostname validation
    (non-empty slug, no whitespace/colon), a fixed `skip_reasons` vocabulary
    (`node_lifecycle_not_exportable`, `node_type_not_exportable`, `missing_mdns_name`,
    `invalid_inventory_hostname`), and a single `ssh_hosts` group carrying per-host
    `nintent_*` hostvars with `nintent_inventory_stage: reserved_name`,
    `name_reserved_only: true`. Inputs are read via `getattr` on ORM objects.
  - `jobs.py::ExportAnsibleHostsIntent` — feeds those functions from
    `DesiredNode.objects.prefetch_related("desired_endpoints")` and publishes
    `hosts_intent.yml` + `hosts-intent-export.json` as JobResult files. **Verified: the Job and
    `tests/test_ansible_inventory.py` are `ansible_inventory.py`'s only consumers.**
- `ansible_agdev/playbooks/nautobot/export_nintent_hosts_intent.yml` runs the Job, downloads
  the artifact via file-proxy regex, asserts schema `2.0`, then stages + validates with
  `ansible-inventory --list` + atomically replaces `inventories/generated/hosts_intent.yml`.
  The validate-then-atomic-replace behavior is the part worth keeping (and nctl already
  reimplemented it for `render production` — see below).
- **This playbook is the last consumer of `playbooks/tasks/nautobot_run_job.yml` and
  `playbooks/tasks/nautobot_download_file.yml`** (verified by grep;
  `collect_nodeutils_and_ingest_nautobot.yml` carries its own inline Job plumbing, which is
  Phase 4 territory). Both shared task files can be deleted in this phase.
- nctl infrastructure this phase reuses instead of rebuilding:
  - `sources/desired.py::fetch_desired_snapshot` (Phase 2) — one pinned, live-verified GraphQL
    query already returning **every field the renderer reads**: nodes
    (`id/slug/name/lifecycle/node_type`) and endpoints
    (`id/name/endpoint_type/mdns_name/desired_node{id,slug}`), with ChoiceField
    UPPERCASE→lowercase normalization already handled. **No new GraphQL query is needed**;
    the Phase 1 "verify field availability first" risk does not exist here.
  - `production_render.py::write_production_artifacts` (Phase 2) — the staged
    `ansible-inventory --list` validation + atomic replace pattern, ready to factor/reuse.
  - Output envelope (`output.py::emit`), Typer `render` sub-app, respx/pytest test seams.
- Consumers of the generated `hosts_intent.yml` (unchanged by this phase, but their docs
  reference the playbook): `ansible_agdev/Makefile` (`bootstrap-inventory` target runs the
  playbook; `collect-ingest` runs against the file), `README.md`, `README_ADMIN.md`,
  `ansible.cfg` comment, `docs/production_inventory_contract.md`.
- One piece of roadmap intent is **already satisfied structurally**: `nctl apply dnsmasq`'s
  configured inventory is `inventories/generated/production.yml`, which nctl itself renders
  since Phase 2 — the apply path no longer depends on this playbook at all. What remains is a
  stale error message in `dnsmasq_apply.py` (`"generate the inventory first (currently via
  export_nintent_production.yml)"`) pointing at a playbook deleted in Phase 2; fix it here.
- Deployment constraint (`.local/localenv_memo.md`): dev Nautobot installs nintent from
  GitHub — verifying nintent changes costs a push + `docker compose build --no-cache` +
  restart cycle. As in Phase 1, sequence so nintent needs **one** push cycle, only after
  parity is proven.

## Approach

Same template as Phase 1: port the renderer as pure functions into `nctl_core`, prove **output
parity** against the live Job, then cut over — delete the Job path in nintent (single push
cycle), delete the playbook and the now-orphaned shared Job-plumbing task files in
ansible_agdev, and repoint the Makefile/docs at the nctl command.

**Naming deviation from the roadmap**: the roadmap says `nctl render inventory`, named before
Phase 2 introduced `nctl render production` — which also renders an inventory. To keep the two
unambiguous, this phase uses **`nctl render hosts-intent`** (matching the artifact name
`hosts_intent.yml` and the established "bootstrap vs production inventory" vocabulary in
ansible_agdev's docs). Record the deviation in the report.

## Step 1 — Port the renderer into `nctl_core` (pure, snapshot-model-based)

- New module `nctl/src/nctl_core/hosts_intent.py`: port `export_hosts_intent`,
  `hosts_intent_payload`, `render_hosts_intent_yml`, `render_hosts_intent_json`, and the
  private helpers from `nintent/nautobot_intent_catalog/ansible_inventory.py`.
  - Input shape: consume the Phase 2 snapshot models (`sources/desired.py::DesiredNode`,
    `DesiredEndpoint`) instead of ORM objects — the caller passes the node list plus the
    endpoint list, and the module groups endpoints by `node_id` client-side (replacing the
    ORM's `prefetch_related("desired_endpoints")`). Everything else — eligibility gates,
    endpoint selection order, sort keys, `skip_reasons` vocabulary, group/hostvars structure,
    YAML/JSON serialization options — stays output-identical.
  - Header changes, mirroring Phase 1's dnsmasq conventions: `# Generated by nctl` instead of
    the Job banner; drop `job_result_id` (render is synchronous — no operation ID either, as
    with `render dnsmasq`); bump `ANSIBLE_HOSTS_INTENT_SCHEMA_VERSION` to `3.0` (the generator
    changed; the playbook's schema assert dies with the playbook, so the header is
    informational for humans and Phase 2+).
- Port `nintent/nautobot_intent_catalog/tests/test_ansible_inventory.py` (232 lines) to pytest
  with snapshot-model fixtures — same expected hosts, groups, hostvars, and skip reasons — so
  the vocabulary survives the move.

## Step 2 — Fetch + adapter (reuse the Phase 2 snapshot)

- No new GraphQL query. Fetch via `fetch_desired_snapshot(client)` and feed
  `snapshot.nodes` / `snapshot.endpoints` to the Step 1 renderer. If profiling ever shows the
  full snapshot is too heavy for this command, a trimmed query is a later optimization — do
  not fork a second desired-state query now (Phase 2 deliberately unified them).
- One semantic to verify while porting: the ORM path exported endpoints in
  `prefetch_related` default order, and `_select_mdns_endpoint` tie-breaks deterministically
  anyway — confirm with a unit test that endpoint-list order does not affect output (it
  shouldn't, given the sort in `_select_mdns_endpoint`).

## Step 3 — `nctl render hosts-intent` + parity gate

- CLI: `nctl render hosts-intent [--out DIR] [--json]` on the existing `render` sub-app.
  - Default: print the inventory YAML to stdout (pipeable), summary to stderr-style text as
    the other render commands do.
  - `--out DIR`: write `<DIR>/hosts_intent.yml` using the staged `ansible-inventory --list`
    validation + atomic replace pattern — factor the mechanism shared with
    `production_render.py::write_production_artifacts` into a small helper rather than
    copy-pasting it. On validation failure the previous file is untouched (preserving the old
    playbook's rescue semantics). Also write `<DIR>/hosts-intent-export.json` alongside, as
    the Job did.
  - `--json`: envelope `nctl.render.hosts_intent.v1` — `data` = the export payload (summary,
    inventory, hosts, skipped, schema_version, plus the rendered YAML text), same relationship
    to the YAML as `render dnsmasq`'s envelope has to the conf.
  - Fast/synchronous: no operation ID or event log.
- Tests: renderer unit tests (Step 1), CLI test with respx-faked GraphQL + a stub
  `ansible-inventory` (same seams as `test_cli_render_production.py`).
- **Parity gate (before Step 4 deletes anything)**: run the live `Export Ansible Hosts Intent`
  Job once more, download `hosts_intent.yml` + `hosts-intent-export.json`, and diff against
  `nctl render hosts-intent` output on the same live data — inventory body and JSON
  `hosts`/`skipped`/`summary` must match exactly (headers, `generated_at`, `job_result_id`,
  `schema_version` excluded). Record the comparison commands and result in the report; do not
  store generated artifacts under `devdocs`. Any mismatch is a Step 1/2 bug to fix first.

## Step 4 — Delete the Job-export path in nintent (single push cycle)

- Delete `ExportAnsibleHostsIntent` from `jobs.py` (class, the line-10 import, and its entry
  in the `jobs` tuple), `ansible_inventory.py`, and `tests/test_ansible_inventory.py`.
- Bump nintent to 0.8.0; run `uv run python3 -m unittest discover` locally.
- Commit, ask the user to push, rebuild dev Nautobot
  (`docker compose --env-file ../.env build --no-cache && ... up -d`), verify the Job list no
  longer shows "Export Ansible Hosts Intent" and `nctl status` stays green.

## Step 5 — Delete the playbook and orphaned Job plumbing in ansible_agdev

- Delete `playbooks/nautobot/export_nintent_hosts_intent.yml` — nctl now writes
  `inventories/generated/hosts_intent.yml` directly with the same validation guarantees.
- Delete `playbooks/tasks/nautobot_run_job.yml` and `playbooks/tasks/nautobot_download_file.yml`
  — their last consumer is gone (re-verify with grep at execution time; the collect playbook's
  inline ingest plumbing is untouched, Phase 4 owns it).
- `Makefile`: `bootstrap-inventory` target becomes
  `$(NCTL) render hosts-intent --config ../nctl.toml --out inventories/generated`
  (the `NCTL` variable already exists for `production-inventory`); `pipeline` keeps working
  end to end.
- Update the references that describe the old path: `README.md` (setup step and the playbook
  catalog entry), `README_ADMIN.md`, the `ansible.cfg` comment,
  `docs/production_inventory_contract.md`'s bootstrap mention.

## Step 6 — Fix the stale inventory pointer in `apply dnsmasq`, docs, report

- `dnsmasq_apply.py`: the `ansible_inventory_missing` message still says "currently via
  export_nintent_production.yml" — change it to point at `nctl render production --out ...`.
  This closes the roadmap's "apply no longer points the user at a playbook" item; automatic
  regeneration inside `apply` is unnecessary now that both inventories are one nctl command
  away (note this reasoning in the report).
- `nctl --help` / `nctl/README.md` / parent `README.md`: document `nctl render hosts-intent`
  alongside the other commands.
- Write `devdocs/vision/core_reconcile/p1ex1/report*.md` in the established style, including
  the parity procedure/result and the `hosts-intent` naming deviation.

## Out of scope

- The collect→ingest orchestration (`collect_nodeutils_and_ingest_nautobot.yml` and its inline
  Job plumbing) — Phase 4.
- Any enrichment of the bootstrap inventory (service groups, `host_os`, connection vars) — it
  stays the minimal mDNS reserved-name inventory; the detailed inventory is
  `render production`'s job.
- Changes to `sources/desired.py`'s pinned query or the drift engine.
- `ReconcileDesiredIPAMIntent` and the import/analyze Jobs — correctly ledger-side per the
  migration map.

## Exit criteria (from roadmap, made checkable)

- [ ] `nctl render hosts-intent` output matches the last Job export on live data (inventory
  body, hosts, skipped, summary; procedure and result recorded in the report).
- [ ] `nctl render hosts-intent --out inventories/generated` validates with
  `ansible-inventory --list` before atomically replacing `hosts_intent.yml`, leaving the
  previous file intact on failure.
- [ ] `nintent` contains no hosts-intent export: `ExportAnsibleHostsIntent`,
  `ansible_inventory.py`, and `test_ansible_inventory.py` are deleted; nintent's test suite
  passes; the dev Nautobot Job list no longer offers the export.
- [ ] `export_nintent_hosts_intent.yml`, `tasks/nautobot_run_job.yml`, and
  `tasks/nautobot_download_file.yml` are deleted; `make pipeline`'s bootstrap stage uses nctl;
  no Job/file-proxy plumbing remains anywhere in `ansible_agdev`.
- [ ] `nctl apply dnsmasq`'s missing-inventory error points at an nctl command, not a playbook.
- [ ] `uv run pytest` passes in nctl, including the ported hosts-intent vocabulary tests.

## Suggested commit order

1. nctl: renderer port + snapshot adapter + `render hosts-intent` + write/validate helper +
   tests (Steps 1–3; parity gate run against live before proceeding).
2. nintent: delete the Job-export path, version bump (Step 4; the single push/rebuild cycle).
3. ansible_agdev: delete playbook + shared Job-plumbing task files, Makefile + docs updates
   (Step 5).
4. nctl + parent repo: `apply dnsmasq` message fix, CLI/README documentation, submodule
   pointer bumps, `p1ex1/report*.md` (Step 6).
