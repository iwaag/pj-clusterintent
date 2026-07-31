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

## Step 2 — nodeutils binding observation

`nodeutils/nodeutils_collect.py`: added `_read_json_path` (dot-path walk),
`probe_binding_endpoint` (bounded ~3s GET against `<configured>/models`,
mirroring `probe_service_endpoint`'s ollama shape — an `HTTPError` still
yields its status code, since any HTTP response is reachability evidence
regardless of status range), `observe_binding` (reads only the one
allowlisted JSON key via `Path(config_file).expanduser()`, bounded to
`MAX_BINDING_CONFIG_BYTES` = 1 MiB, classifies `configuration_status` as
`present`/`absent`/`unreadable`, probes only when present), and
`bindings_for_service` (the `managed_files_for_service` twin). Wired into
`normalize_observed_services` with the same attach-and-create pattern as
`managed_files` — a binding's evidence is observable even when its own
service entry wasn't independently detected by docker/systemd. Schema
stays `nodeutils.inventory.v2` (additive key inside an existing
`observed_services` entry, no bump needed).

`configured_endpoint` passes through `bounded_value` before being stored,
so a slot value over 512 chars is truncated same as everywhere else in the
report; nothing named `*_token`/`*_secret`/etc. is ever a binding-slot key.

Tests added to `tests/test_inventory_report.py` (9 new): present+reachable
(asserts the exact `<endpoint>/models` probe URL), unreachable on probe
failure, absent on missing file, absent on missing JSON key, unreadable on
malformed JSON, `~`-expansion via `Path.expanduser`, `bounded_value`
truncation applied to an oversized configured endpoint, malformed-spec
rejection in `bindings_for_service`, and one `normalize_observed_services`
integration test proving a `node-agent` entry is created from a binding
alone (`source: probe`).

Gate: `uv run pytest -q --durations=20` (nodeutils) — **68 passed** (was 59
before this step; 9 net new).

Commit: nodeutils `7030bbd`.

## Next

Step 3 — nctl evaluation (`normalize_endpoint_url`, the five-state pure
function, folding into `evaluate_all_services` with new gap codes,
`classify.py` routing, tests).
