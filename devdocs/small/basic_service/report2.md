# Step 2 report — hosts-intent: service groups from placements

## Changes

- `nctl/src/nctl_core/hosts_intent.py`
  - `export_hosts_intent` gained two optional keyword args: `placements: Iterable[DesiredServicePlacement]`
    and `profile_groups: dict[str, str]` (deployment_profile name → Ansible group name — the
    same mapping `production/composer.py` builds from `deployment_profiles.yml`).
  - Active placements (`desired_state == "active"`) whose node was successfully exported to
    `ssh_hosts` are added to `group_members[group]` with **empty host objects**, mirroring the
    production contract's rule that service-group members carry no vars.
  - A placement whose `deployment_profile` isn't in `profile_groups`, or whose node was skipped
    (no mDNS endpoint / ineligible), is appended to `skipped` as
    `item_type: desired_service_placement` with `reasons` (`unknown_deployment_profile` and/or
    `node_not_exported`) — reported, not silently dropped, per the plan.
  - `HOSTS_INTENT_SCHEMA_VERSION` bumped `3.0 → 4.0` (payload shape changed: new group(s) possible
    in `inventory`, new skip item type).
- `nctl/src/nctl_core/hosts_intent_render.py`: `build_hosts_intent_render` now loads
  `deployment_profiles.yml` via `production.profiles.load_deployment_profiles` (using
  `cfg.ansible.resolved_playbook_dir`, same as `production_render.py`), builds
  `profile_groups = {name: profile["group"] for name, profile in profiles.items()}`, and passes
  `snapshot.placements` + `profile_groups` into `export_hosts_intent`. A profiles-file error now
  fails the render with `deployment_profiles_invalid` (same pattern as `render production`).

## Design notes

- No new schema/contract module was added for hosts-intent — it keeps its existing looser,
  self-contained validation style (`_placement_skip_entry`) rather than importing
  `production/contract.py`'s stricter `_require_slug`/closed-document validator, since hosts-intent
  was already validation-light by design (bootstrap output, not the production contract).
- `_inventory()` was not touched: it already special-cased "only `ssh_hosts` gets host_vars,
  everything else gets `{}`" — the new service groups reuse it unchanged.

## Tests

`nctl/tests/test_hosts_intent.py`: bumped schema-version assertions to `4.0`; added
`test_active_placement_adds_bare_service_group`, `test_inactive_placement_is_ignored`,
`test_placement_with_unknown_profile_is_reported_not_dropped`,
`test_placement_on_skipped_node_is_reported_not_dropped`.

`nctl/tests/test_hosts_intent_render.py`: `_fake_config()` now exposes `ansible`/`source_path`;
added `test_build_hosts_intent_render_fails_on_invalid_deployment_profiles`; existing test
monkeypatches `load_deployment_profiles` to return an empty profile map.

`nctl/tests/test_cli_render_hosts_intent.py`: bumped schema-version literals to `4.0` (cosmetic —
these tests stub `build_hosts_intent_render` directly).

## Verification

```
uv run pytest -q
```
508 passed (full nctl suite, no regressions).
