# Phase 1 Report — Step 6 (`nctl apply dnsmasq`)

Date: 2026-07-15. Implements [p1/plan.md](plan.md) Step 6. Continues from
[report5.md](report5.md), which introduced the deploy-only Ansible playbook.

## What changed

- Added `nctl_core.dnsmasq_apply` and the CLI command
  `nctl apply dnsmasq [--yes] [--json]`.
  - Default mode renders once, stages the conf, and invokes Ansible with `--check --diff`.
  - `--yes` skips the dry-run and invokes the real play directly, as allowed by the plan.
  - Both modes return the stable `nctl.apply.dnsmasq.v1` envelope and exit 0 only when the
    selected Ansible run exits 0. A dry-run reporting changes remains successful.
- Added a strict `[ansible]` config section:
  - `playbook_dir` is the `ansible_agdev` checkout, relative to `nctl.toml` unless absolute;
  - relative `inventory` paths resolve inside that checkout; absolute files/directories work too.
- Every operation now:
  - gets a ULID and JSON Lines event log;
  - writes `<events.log_dir>/<operation_id>/artifacts/dnsmasq-records.conf` with the operation ID
    in its header;
  - records the artifact/event/inventory paths, selected target hosts, render summary, Ansible
    exit code, stdout/stderr, and parsed PLAY RECAP in the final envelope.
- Added the Step 6 event vocabulary:
  `started`, `rendered`, `dry_run_completed`, `apply_started`, `apply_completed`, `failed`, and
  terminal `finished`.
- Added preflight checks for the checkout, deploy playbook, inventory path, Ansible executables,
  inventory parsing, and a non-empty `dnsmasq_server` group. The group check uses
  `ansible-inventory --list` and follows child groups, preventing Ansible's normal zero-target
  no-op from being reported as a successful deployment.
- Updated `README.md`, `example.nctl.toml`, `docs/event-log.md`, and `docs/output-format.md`.
- Updated the local ignored `nctl.toml` with `[ansible]` settings for development.

## Inventory correction relative to the plan

The Step 6 plan names `inventories/generated/hosts_intent.yml` as the apply inventory and says it
provides `dnsmasq_server`. The checked-in generated file and `ansible_agdev/README.md` establish
the opposite: `hosts_intent.yml` is a bootstrap inventory and deliberately carries no service
groups. The service-placement group belongs to the production inventory.

Accordingly the documented/default development setting now uses
`inventories/generated/production.yml`. Until Phase 2 moves production composition into nctl, a
missing file points to the current `export_nintent_production.yml` generation path. This avoids
documenting a configuration that can never select a dnsmasq target.

## Tests

- Added `tests/test_dnsmasq_apply.py`:
  - default check+diff command and real `--yes` command construction;
  - artifact path/header and exact event sequences;
  - recursive inventory group membership;
  - empty group rejection;
  - failed Ansible exit code and recap preservation;
  - PLAY RECAP parsing.
- Added `tests/test_cli_apply_dnsmasq.py` for default/`--yes` routing, JSON schema, and exit codes.
- Extended config tests for strict `[ansible]` parsing and path resolution.
- Extended render tests to verify operation ID injection without changing standalone render output.

Verification results:

- `uv run pytest -q` — **90 passed**, 0 failures.
- `uv lock --check` — passed.
- `git diff --check` — passed.
- `uv run nctl apply dnsmasq --help` — exposes the expected `--yes`, `--json`, and `--config`
  options.

## Live development check

Ran the default apply command against the live Nautobot GraphQL data, supplying the local token
without writing it into configuration or command output.

- GraphQL render succeeded: 5 DNS records, 3 DHCP reservations, and 1 DHCP range.
- The operation-specific schema `4.0` artifact was written with its operation ID.
- JSON Lines contained `started` → `rendered` → `failed` → `finished` with monotonic sequence
  numbers and terminal `ok: false`.
- With `hosts_intent.yml`, the new guard correctly returned
  `dnsmasq_inventory_group_empty` before invoking Ansible.
- After correcting configuration to `production.yml`, the command correctly returned
  `ansible_inventory_missing` with the current generation instruction, again before invoking
  Ansible.

No target host was changed. The actual check+diff and `--yes` end-to-end runs remain pending
because `ansible_agdev/inventories/generated/production.yml` is not currently generated. The
known dnsmasq host is also documented as unreachable in `.local/localenv_memo.md`.

## Commit boundary

This is the fourth suggested Phase 1 commit: **nctl: `apply dnsmasq`, `[ansible]` config, events,
and tests**. It is intentionally stopped before Step 7's final CLI documentation
commit.

Next: generate/select a production inventory and run the real dry-run when the dnsmasq host is
reachable; independently, Step 7 can close the client-neutral CLI documentation and Phase 1 report.
