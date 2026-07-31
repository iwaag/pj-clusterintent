# Phase 3 Report — Consumer-Side Actual Evidence

Status: **in progress** (Step 4 binding baseline complete; whole-cluster
baseline and Step 5 fault drills remain open).

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

## Step 4 — Deploy and live baseline

Run live on 2026-08-01 JST from the repository root:

```text
uv run --project nctl nctl reconcile aghub --refresh-observation --yes
uv run --project nctl nctl reconcile agpc --refresh-observation --yes
uv run --project nctl nctl reconcile agstudio --refresh-observation --yes
```

The three collection, service-profile, and post-actuation observation paths
all completed successfully. The operation results were:

- `aghub`: operation `01KYWQ1EZ8AGBBYEM8S61RS7WY`; the node itself was
  converged, but the command exited non-zero with `no_progress` because its
  scoped service included binding drift on the other consumer placements.
- `agpc`: operation `01KYWQ4QHAPHDS4A8DK07H60XQ`; its original
  `agstudio.local` binding was repaired. The command exited non-zero with
  `no_progress` because unrelated service drift and the then-unrepaired
  `agstudio` binding remained in the scope.
- `agstudio`: operation `01KYWQ6T6KNBWVNFB6017RM2XH`; converged successfully
  with `scope summary: converged=3` and `ok: True`.

Fresh nodeutils evidence was present for all three consumers under
`facts.services.observed_services["node-agent"].bindings.llm_provider`:

| Node | Checked at (UTC) | Configured endpoint | HTTP | Reachability |
| --- | --- | --- | --- | --- |
| `aghub` | `2026-07-31T18:31:10+00:00` | `http://agstudio.home.arpa:11434/v1` | 200 | reachable |
| `agpc` | `2026-07-31T18:32:36+00:00` | `http://agstudio.home.arpa:11434/v1` | 200 | reachable |
| `agstudio` | `2026-07-31T18:33:25+00:00` | `http://agstudio.home.arpa:11434/v1` | 200 | reachable |

The desired endpoint was the same value for every placement. The final
`node-agent` service target was `converged` with no `binding_*` diffs, so all
three bindings evaluated as `satisfied` (satisfied is represented by absence
of a binding gap rather than a stored state).

The final whole-cluster result was not converged:

```json
{
  "generated_at": "2026-07-31T18:33:40.700533+00:00",
  "summary": {"drifting": 3, "converged": 10, "unknown": 3},
  "severity_summary": {"error": 6, "warning": 5, "info": 6},
  "node_agent": {"status": "converged", "binding_diffs": []}
}
```

The remaining gaps are outside the Phase 3 binding implementation:
`agdnsmasq` compute-primary-endpoint/observation staleness, `agbach`
observation staleness, missing `pj-voxel3dprint`, and a `prometheus`
placement mismatch. Consequently Step 4's binding-evidence and satisfied-state
checks are complete, while its literal whole-cluster convergence check remains
open.

### Re-check (later the same session)

A follow-up `nctl drift --json` no longer shows all three bindings
`satisfied`: `agstudio`'s own `node-agent` placement (bound to the ollama
instance running on the same node) now shows `binding_unreachable` —
`configured_endpoint` still equals `desired_endpoint`
(`http://agstudio.home.arpa:11434/v1`, `configuration_status: present`,
so not `misbound`), but `reachability_status: unreachable` from a fresh
`checked_at` (`2026-07-31T18:39:15+00:00`, `age_hours` ~0.02, well under the
24h threshold — not `unknown`). `aghub`/`agpc`'s bindings are still
unaffected (no `binding_*` diff on their placements). This is unplanned —
not a Step 5 fault drill — and reads as a real, live signal that agstudio's
Ollama was briefly unreachable from itself at that probe moment, exactly the
kind of evidence this phase exists to surface. Left unresolved for now: not
investigated further pending the user's direction on Step 5.

## Next

Step 5 — fault drills. This still requires separate explicit approval because
it deliberately edits a live consumer configuration and stops the shared
Ollama provider. Given the unplanned `agstudio` `binding_unreachable` above,
the user may want to look into that first, since it could double as (or
interfere with) drill (b)'s expected `binding_unreachable` result. After
restoration, the pre-existing non-binding cluster gaps above also need
resolution before literal whole-cluster convergence can be recorded.
