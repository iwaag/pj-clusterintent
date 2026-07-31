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

## Step 3 — nctl evaluation

`production/service_dependencies.py`: added `normalize_endpoint_url`
(lowercase scheme+host, strip trailing path slash, bracket a bare IPv6
host — applied identically to both sides, per the roadmap's "one
normalization" requirement) and `resolve_all_bindings` (keyed by
`placement_id -> binding_name`, resolves every binding independently rather
than stopping at the first per-node error like `resolve_service_dependencies`
does for inventory rendering — drift needs to show every binding's own
health).

New `drift/binding_evaluation.py`: pure `evaluate_binding_state` implementing
the idea-A §6 precedence exactly as specified (first match wins): `unknown`
(no evidence / unreadable / stale), `unbound` (`configuration_status:
absent`), `misbound` (normalized endpoints differ), `unreachable` (match,
probe failed), `satisfied` (match, probe ok, fresh) — with `satisfied`
additionally gated on `provider_converged`, emitting
`binding_provider_not_converged` as a non-converging gap even when the
binding's own five states are otherwise healthy. Freshness threshold is
`service_observation_max_age_hours` (config default 24h), reused unchanged
from `service_placement.py`'s existing staleness plumbing, and the exact
threshold is written into every binding's evidence dict
(`stale_after_hours`) so it's visible in `nctl drift --json`.

Wired into `drift/service_placement.py`: `evaluate_active_placement` gained
a `binding_checks` parameter and a new `_evaluate_bindings` helper — one more
independent actual-state dimension alongside process-state and managed-file
content, following the exact `ContentSpec` precedent already established for
`fix_sshkey3`.

Wired into `drift/evaluation_snapshot.py`'s `evaluate_all_services` via a
**two-pass** evaluation: pass 1 runs `evaluate_placement_drift` without
binding checks purely to learn each service's own convergence status (a
provider's own process/content drift, independent of any consumer's
binding); pass 2 re-runs it with `binding_checks_by_placement_id` built from
`resolve_all_bindings` plus those now-known provider statuses. A binding
whose desired resolution itself errored (ambiguous provider, cycle, ...) is
skipped in both passes — it already surfaces as node-local
production-composition drift via `production/composer.py`'s
`LocalCompositionError` path, so this avoids the roadmap's "don't duplicate
them."

`reconcile/classify.py` routing, exactly per the plan: `binding_unbound` /
`binding_misbound` → `AUTOMATIC` / `service_profile` (rerunning
`setup_opencode.yml` is the real repair — reuses the existing
`_SERVICE_PROFILE_CODES` reconciler, no new one needed); `binding_unreachable`
/ `binding_provider_not_converged` → `MANUAL_REVIEW` (the consumer playbook
cannot fix a dead or non-converged provider); `binding_unknown` →
`OBSERVATION` / `observe_node`.

Tests added: `test_binding_evaluation.py` (14 — full five-state matrix,
precedence ordering, both staleness-boundary directions, evidence-field
assertions); `test_service_dependencies.py` (+9 — `resolve_all_bindings`
keying and non-stop-at-first-error behavior, `normalize_endpoint_url`
case/slash/IPv6 handling and desired/observed-form equality);
`test_reconcile_classify.py` (+5 parametrized routing tests, plus the new
codes added to `_DYNAMIC_CODES` since they're emitted from a variable, not a
literal, so the source-scan pin needed updating); one end-to-end
`test_drift_render.py` test (`test_misbound_binding_surfaces_in_service_drift`)
with a doctored snapshot — hand-mismatched `configured_endpoint` in
`observed_services["node-agent"].bindings.llm_provider` against the
resolved desired ollama endpoint — proving `binding_misbound` reaches
`nctl drift --json` on the `node-agent` service target.

Gate: `uv run pytest -q --durations=20` (nctl) — **1085 passed** (was 1058
after Step 1; 27 net new). Ansible conformance gate
(`devtests/test_strategy/test_ansible_conformance.py`) — 3 passed
(unaffected, as expected).

Commit: nctl `d72d873`.

## Next

Step 4 — deploy and live baseline (pause for user approval: push
nodeutils/nctl, agree the superproject gitlink move, then
`nctl reconcile <slug> --refresh-observation` for aghub/agpc/agstudio).
