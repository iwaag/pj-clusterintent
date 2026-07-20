# Step 5 report — `apply dnsmasq --inventory PATH`

## Change

- `nctl/src/nctl_core/dnsmasq_apply.py::build_dnsmasq_apply`: new optional `inventory: Path | None
  = None` parameter. When given, it's used everywhere the resolved inventory path is needed
  (`_validate_paths`, `_load_inventory`, both `ansible-playbook -i` invocations,
  `data.inventory_path`) instead of `cfg.ansible.resolved_inventory(cfg.source_path.parent)`.
  `_validate_paths`/`_load_inventory` now take the resolved inventory path as a parameter rather
  than each re-deriving it from `cfg`, so there is exactly one place (`build_dnsmasq_apply`'s
  `resolved_inventory = inventory if inventory is not None else cfg.ansible.resolved_inventory(...)`)
  that decides which inventory is in effect for the whole run.
- `nctl/src/nctl_core/cli/main.py`: `apply dnsmasq` gained `--inventory PATH`
  (`ApplyInventoryOption`), plumbed straight through to `build_dnsmasq_apply(cfg,
  apply_changes=yes, inventory=inventory)`.
- No silent fallback, as the plan specifies: omitting `--inventory` behaves exactly as before
  (the configured production inventory). `reconcile`'s `dnsmasq_config` action
  (`reconcile/executor.py`) still calls `build_dnsmasq_apply(cfg, apply_changes=True)` with no
  `inventory` argument — unaffected, always actuates against the production inventory it
  regenerates itself.
- Validation is unchanged in spirit: the *resolved* (possibly overridden) inventory must exist and
  resolve ≥1 host in `dnsmasq_server`, which Steps 2–3 now provide via `render hosts-intent` even
  before any production inventory exists.

## Documentation

- `nctl/README.md`: documented the two-playbook `apply dnsmasq` flow (setup then deploy, both
  `--check --diff` by default) and the `--inventory` override, with the concrete bootstrap
  sequence (`render hosts-intent --out` → `apply dnsmasq --inventory .../hosts_intent.yml` dry-run
  → `--yes`).

## Tests

`nctl/tests/test_dnsmasq_apply.py`:
- `test_inventory_override_replaces_configured_inventory`: asserts every `ansible-inventory`/
  `ansible-playbook` invocation uses the override path, none use the configured
  `ansible.inventory`, and `data.inventory_path` reports the override.
- `test_inventory_override_missing_file_is_a_pointed_failure`: a nonexistent override path fails
  with `ansible_inventory_missing`, same as the configured-inventory case.

`nctl/tests/test_cli_apply_dnsmasq.py`:
- `test_apply_dnsmasq_inventory_option_is_passed_through`: `--inventory PATH` reaches
  `build_dnsmasq_apply` as a `Path`.
- `test_apply_dnsmasq_without_inventory_option_passes_none`: omitting the flag passes `None`
  (preserving the no-silent-fallback default).
- Existing tests updated to accept the new `inventory=None` keyword on the stubbed
  `build_dnsmasq_apply`.

## Bug found and fixed during live verification

Live end-to-end testing (see `report6.md`) caught a real bug in the first version of this step:
`inventory if inventory is not None else cfg.ansible.resolved_inventory(...)` used the raw
`--inventory` argument unresolved, while `cfg.ansible.resolved_inventory(...)` always returns an
absolute, `.resolve()`d path. `AnsibleRunner` always runs `ansible-playbook`/`ansible-inventory`
with `cwd=playbook_dir`, so a relative `--inventory` path (the natural way to invoke it —
`nctl apply dnsmasq --inventory ansible_agdev/inventories/generated/hosts_intent.yml` from the
repo root) was silently resolved against `playbook_dir`, not the caller's cwd, producing a
double-nested nonexistent path and a misleading `dnsmasq_inventory_group_empty` (not a "file not
found") error. Fixed by resolving the override the same way: `inventory.expanduser().resolve()`
before use. Added `test_inventory_override_relative_path_resolves_against_cwd_not_playbook_dir` as
a regression test (`monkeypatch.chdir` to a directory other than `playbook_dir`, pass a relative
override, assert `data.inventory_path` is the correctly resolved absolute path).

## Verification

```
uv run pytest -q
```
514 passed (full nctl suite, no regressions; +5 for the new override tests, including the
relative-path regression test).

Live, against the dev Nautobot instance: `nctl render hosts-intent --out
ansible_agdev/inventories/generated` then `nctl apply dnsmasq --inventory
ansible_agdev/inventories/generated/hosts_intent.yml` (dry-run) correctly resolved the override,
found `agdnsmasq` in `dnsmasq_server`, and invoked the daemon-setup playbook against it — it failed
with `UNREACHABLE` (SSH host key verification), which is the already-documented, expected state of
`agdnsmasq.local` in `.local/localenv_memo.md`, not a code defect. See `report6.md` for the full
end-to-end verification writeup.
