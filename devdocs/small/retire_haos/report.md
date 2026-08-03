# Retire Home Assistant OS (HAOS) support

## Status

**Implemented, not deployed.** All code, config, docs, and tests are changed and
passing locally across the affected submodules (`nintent`, `nctl`, `ansible_agdev`,
`nauto`). Nothing has been committed, pushed, or deployed to the live cluster —
that requires operator approval per `.local/localenv_memo.md` (`nintent` reaches
the live Nautobot only through a pushed commit + container rebuild).

## Scope and rationale

The user asked to remove Home Assistant OS (HAOS) support end-to-end, starting
from `ansible_agdev`, including any other HAOS-related code and tests, with no
backward-compatibility requirement. The underlying `homeassistant` VM (`aghaos`,
Proxmox VMID 102) was already destroyed and pruned from the ledger in
[`devdocs/small/vm_retire/report.md`](../vm_retire/report.md); this change
removes the *support surface* for that guest type, not infrastructure.

Investigation found that `DesiredNodeOperationalOverride.declared_host_os` only
ever had one valid value (`"haos"` — `DECLARED_HOST_OS_CHOICES` had a single
entry, "Home Assistant OS"). So "remove HAOS" meant removing the entire
declared/observed dual-policy concept from `nctl`'s operational-value
derivation, not just deleting one enum value — a real node's `host_os` is now
always derived from a fresh nodeutils observation (the `"required"` policy),
never declared.

## Changes by component

### `nintent`
- Removed `HOST_OS_HAOS` / `DECLARED_HOST_OS_CHOICES` and the `declared_host_os`
  field from `DesiredNodeOperationalOverride`, plus its HAOS-specific
  `power_control` validation rule.
- Removed `declared_host_os` from `batch.py`'s writer allowlist, `tables.py`,
  `filters.py`, and the read-only detail template.
- Added migration `0028_remove_desirednodeoperationaloverride_declared_host_os.py`
  (hand-written in the existing `RemoveField` style — `nautobot-server
  makemigrations` isn't runnable from this checkout since the dev container
  installs `nintent` from GitHub, not this working tree).
- Django-free fast suite: 130 tests, 10 expected skips, unchanged from baseline.

### `nctl`
- `production/derivation.py`: `resolve_operational_values` no longer branches
  on a declared override; `host_os`/`actual_state_policy` are always derived
  from realized-device facts. `OperationalOverride.declared_host_os` and the
  `"haos"` power-platform entry are gone.
- `production/composer.py` / `production/contract.py`: removed the `"haos"`
  core inventory group and OS-selector entry (now `linux`/`macos`/
  `power_managed` only).
- `production/routes.py` / `composer.py`: removed the dead
  `actual_state_policy == "declared"` route-resolution branch (a real desired
  `local_endpoint.ip_address` was previously used as a routable IP only for
  declared/HAOS nodes; observed nodes always route from `actual_local_ip`).
  `resolve_connection_variables` no longer takes an `actual_state_policy`
  argument.
- `drift/comparators.py`: `node_existence`'s `no_realized_object` check no
  longer has a declared-override exemption — a node without a
  `realized_device_id` is always drift now.
- `drift/service_placement.py`: removed the dead `actual_state_policy ==
  "declared"` early-return in `evaluate_active_placement`.
- `production/adapter.py`, `production/report.py`, `sources/desired.py`
  (GraphQL query + model): dropped `declared_host_os` end to end.
- `agent.py`: `_target_from_snapshot` no longer falls back to a declared OS
  for workdir resolution (that fallback could only ever resolve to `"haos"`,
  which never mapped to a workdir, so it was already dead in practice).
- Full suite: 1145 passed, 1 pre-existing unrelated failure (see below).

Tests were rewritten, not just deleted, where they exercised real behavior:
seven `test_reconcile_executor.py` fixtures used
`declared_host_os="haos"` purely as a shortcut to avoid supplying a realized
device + actual facts; these now use a real `realized_device_id` + a Linux
`ActualDevice` fixture (`_realized_node()` / `_linux_actual()` helpers), which
exercises the real observed-derivation path instead of the removed shortcut.
Tests that asserted HAOS-specific behavior with no non-HAOS equivalent
(`test_haos_composed_without_realized_object`,
`test_haos_declared_node_joins_service_group`,
`test_node_existence_allows_declared_policy_with_no_realized_object`,
`test_declared_node_is_observation_exempt`,
`test_target_resolution_uses_declared_os_before_first_observation`,
`test_target_resolution_uses_observed_os_before_declared_os`) were removed
outright.

### `ansible_agdev`
- Deleted `playbooks/power/generate_home_assistant_power_switches.yml`,
  `playbooks/power/deploy_home_assistant_power_switches.yml`, and
  `templates/home-assistant-power-switches.yaml.j2`.
- Removed the `home_assistant` entry from `vars/deployment_profiles.yml`
  (both `deployment_profiles` and `deployment_profile_reconciliation`).
- Removed the Home Assistant sections/commands from `README.md`, the
  `haos` group mention from `README_ADMIN.md`, and the `haos` group from the
  example inventory in `docs/production_inventory_contract.md`.
- `roles/nodeutils_pvesh_helper/tests`: 4 tests still pass (untouched, never
  HAOS-related).

### `nauto`
- `README.md`: reworded the operational-override example that cited
  "declared HAOS" as the canonical exception case, since that case no longer
  exists.
- No code changes — `nauto`'s only HAOS-adjacent content was fixture VM names
  (`"aghaos"` in `tests/test_proxmox_*` and `nodeutils/tests/test_proxmox_inventory.py`).
  Left as-is: these are just historical example hostnames in Proxmox
  ingest/inventory fixtures (matching the real, now-destroyed `aghaos` VM),
  not HAOS support code — renaming them is cosmetic and out of scope for a
  support-removal change.

## Verification

| suite | command | result |
|---|---|---|
| nintent Django-free fast | `python3 -m unittest discover -s nautobot_intent_catalog/tests` (in `nintent/`) | 130 tests, 10 expected skips |
| nctl ordinary | `uv run pytest -q` (in `nctl/`) | 1145 passed, 1 failed |
| ansible_agdev helper | `python3 -m unittest discover -s roles/nodeutils_pvesh_helper/tests` (in `ansible_agdev/`) | 4 passed |
| nauto ordinary | `python3 -m unittest discover -s tests` (in `nauto/`) | 112 passed |
| nodeutils ordinary | `uv run pytest -q --durations=20` (in `nodeutils/`) | 78 passed |
| compute conformance | `uv run --project nctl pytest -q devtests/test_strategy/test_compute_conformance.py` (superproject root) | passed |
| Ansible conformance | `uv run --project nctl pytest -q devtests/test_strategy/test_ansible_conformance.py` (superproject root) | passed |

The one nctl failure, `tests/test_reconcile_profiles.py::test_real_repo_file_validates`,
is **pre-existing and unrelated**: it fails identically on `main` before this
change (verified via `git stash`), because `ansible_agdev/vars/deployment_profiles.yml`'s
`deployment_profile_reconciliation` section names `comfyui` and `swarmui`, which
have no matching `deployment_profiles` entries reachable from
`test_reconcile_profiles.py`'s `_REPO_PROFILE_NAMES`. Left untouched — out of
scope for this change.

The Nautobot runtime gate (`run_nautobot_runtime_gate.sh`), OpenSSH conformance,
and mTLS conformance gates were not run: none of them touch code this change
modifies (no SSH/dnsmasq-content/mTLS boundary changed), and the Nautobot
runtime gate specifically requires a live migration apply this report
explicitly did not perform.

## Not done / left for the operator

- **Migration not applied.** `nintent`'s new migration
  (`0028_remove_desirednodeoperationaloverride_declared_host_os.py`) has not
  been run against the local scratch Nautobot DB, and `nintent` is not
  reachable from this working tree for a live rebuild (the dev container
  installs it from GitHub — see `.local/localenv_memo.md`). Applying it
  requires: commit + push `nintent`, rebuild the Nautobot container image,
  run `nautobot-server migrate`, and confirm no live
  `DesiredNodeOperationalOverride` row still has `declared_host_os` set
  (none should, since the only real HAOS node was already pruned).
- **Nothing committed or pushed** in any of the four submodules, per the
  house rule of not pushing without being asked.
- Cosmetic `"aghaos"` fixture hostnames in `nauto`/`nodeutils` tests were
  intentionally left in place (see above).
