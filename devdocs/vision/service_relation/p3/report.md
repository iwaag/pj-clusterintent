# Phase 3 Report — Consumer-Side Actual Evidence

Status: **in progress**.

## Step 1 — Metadata and probe-config plumbing

`ansible_agdev/vars/deployment_profiles.yml`: declared the `node_agent`
binding slot under `deployment_profile_reconciliation.node_agent.action.bindings`:

```yaml
bindings:
  llm_provider:
    config_file: ~/.config/opencode/opencode.json
    json_path: provider.ollama.options.baseURL
```

`nctl/src/nctl_core/reconcile/profiles.py`: added `BindingSlotSpec`
(`config_file`, `json_path`) and a `bindings: dict[str, BindingSlotSpec]`
field on `ProfileAction`, symmetric with the existing `managed_files`
mechanism but restricted the other way — `bindings` is forbidden on
`dnsmasq_config` actions (validator raises), allowed only on `playbook`
actions. `config_file` validation deliberately accepts `~/`-relative paths
in addition to absolute ones (unlike `ManagedFileSpec.path`, which requires
absolute) — the documented `Path.expanduser()` deviation the plan calls for,
since the OpenCode config lives under the login user's home.

`nctl/src/nctl_core/observation.py::render_probe_hints`: copies
`ProfileAction.bindings` verbatim into the rendered probe-config YAML under
a new `bindings` key per service hint, alongside the existing
`managed_files` key, for active consumer placements only.

Tests added: `test_reconcile_profiles.py` (bindings forbidden on
`dnsmasq_config`, config_file must be absolute-or-home-relative rejection,
empty json_path rejection, home-relative path accepted, plus the real-repo
fixture now asserts `node_agent`'s `llm_provider` binding slot);
`test_observation.py` (`bindings` copied into probe hints for an active
`node_agent` placement).

Gate: `uv run pytest -q --durations=20` (nctl) — **1058 passed** (was 1053
at Phase 2 completion; 5 net new tests).

Commits: ansible_agdev `9b3afae`, nctl `f5719f7`.

## Next

Step 2 — nodeutils binding observation (read the slot, expanduser, bounded
JSON parse, probe the configured endpoint, emit the evidence record).
