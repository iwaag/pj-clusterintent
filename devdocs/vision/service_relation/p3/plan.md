# Phase 3 Plan — Consumer-Side Actual Evidence

Goal (from [roadmap](../roadmap.md) Phase 3): observe each binding at the
consumer node — configured value + bounded reachability probe — ingest it
through the existing `observed_services` channel, and evaluate the five
idea-A §6 states (`unknown / unbound / misbound / unreachable / satisfied`)
so binding health folds into convergence.

Experimental environment: no backward compatibility. Everything outside
"Hard rules" and "Completion criteria" is a recommendation — implementer's
discretion.

## Scope

In: nodeutils binding observation, probe-config plumbing
(`deployment_profile_reconciliation` metadata → `render_probe_hints`), one
shared endpoint normalization, nctl binding-state evaluation folded into
drift/convergence, reconcile classification of the new gap codes, live
fault-injection verification.

Out (Phase 4): the `nctl relations` projection. nintent changes are expected
to be **zero** (the desired model is complete; evidence rides an existing
Device custom field). nauto changes are expected to be **zero** — see below.

## Facts gathered during planning

- **The observation pipeline, end to end:**
  `nctl_core/observation.py::run_observation` renders one probe-config YAML
  per host (`render_probe_hints`), runs
  `playbooks/nautobot/run_nodeutils_collect.yml` (which installs nodeutils at
  the exact commit `resolve_nodeutils_version` returns — the **superproject
  gitlink**, from GitHub), slurps the report, and ingests it via the nauto
  job `Ingest Nodeutils Inventory`. Triggered live by
  `nctl reconcile <slug> --refresh-observation`.
- **Evidence transport is already open:** the ingest job's
  `build_custom_fields` (`nauto/jobs/ingest_nodeutils_inventory.py` ~line
  645) copies `facts.services.observed_services` **wholesale** into the
  Device custom field, and nctl's `sources/actual.py::_observed_services`
  passes each entry through as a plain dict. A new `bindings` sub-key inside
  the consumer's `observed_services["node-agent"]` entry therefore reaches
  `ActualFacts.observed_services` with zero nauto and zero fetch-layer
  changes. This is exactly the "no parallel ledger" the roadmap demands.
- **Schema versions:** nodeutils emits `nodeutils.inventory.v2`;
  `nauto/seed/nodeutils_ingest.yaml` allowlists exactly that. An additive
  key inside an `observed_services` entry needs no bump. If you do bump,
  policy + collector must change together (see the v1→v2 comment at
  `nodeutils_collect.py:39`).
- **Probe-config pattern to copy:** `dnsmasq`'s `managed_files` is declared
  once in `ansible_agdev/vars/deployment_profiles.yml` under
  `deployment_profile_reconciliation`, validated by
  `nctl_core/reconcile/profiles.py::ProfileAction`
  (`extra="forbid"` — a new `bindings` field must be added to that model or
  loading fails), and copied verbatim into probe config by
  `render_probe_hints`. Declare the node_agent binding slot the same way;
  the metadata stays the single owner of the deployed path.
- **The consumer config slot** (`node_agent` / `llm_provider`):
  `~/.config/opencode/opencode.json`, JSON path
  `provider.ollama.options.baseURL`
  (`roles/opencode_agent/templates/opencode.json.j2`). The written value is
  the resolver's `_endpoint_url` output verbatim
  (`http://agstudio.home.arpa:11434/v1`), so desired and observed strings
  are normally byte-identical.
- **Home-relative path:** nodeutils' `managed_files_for_service` silently
  drops non-absolute paths. `opencode.json` lives under the login user's
  home, and nodeutils runs as that user — so the binding slot spec needs a
  deliberate `Path.expanduser()` (a documented deviation from the
  managed-files rule, not an accident).
- **Redaction/bounding:** `bounded_value` redacts any key containing
  token/secret/password/… and truncates strings >512 chars. The binding
  evidence keys below are safe; don't name anything `*_token`.
- **Probe precedent:** `probe_service_endpoint` in nodeutils already does a
  3-second `urllib` GET against ollama's `/v1/models` and `/api/tags`. The
  binding probe can reuse the same shape against the *configured* baseURL
  (it already ends in `/v1`, so `<configured>/models` works).
- **Freshness precedent:** `service_observation_max_age_hours` (config
  default 24, `config.py:93`) is wired into drift as `stale_after_hours`;
  `evaluate_active_placement` computes ages from
  `service_inventory_updated_at` / `checked_at` via `age_hours`. Reuse it.
- **Where evaluation folds in:** the `@register("service")` comparator
  (`drift/comparators.py:376`) → `evaluate_all_services`
  (`drift/evaluation_snapshot.py`) → `evaluate_placement_drift`
  (`drift/service_placement.py`). That function already has, per service:
  active placement rows, per-device `observed_services` facts, staleness,
  and a `satisfied`/`drift` status per service — i.e. **provider placement
  convergence is already computed there**, which requirement 3 of §6 needs.
  Desired-side binding resolution lives in
  `production/service_dependencies.py` (Phase 2) and is pure — callable from
  the evaluation with `build_production_node_inputs`, which
  `evaluate_all_services` already invokes.
- **Reconcile routing:** `reconcile/classify.py` maps gap/error codes to
  actions vs. manual review. New binding gap codes must be routed there or
  they land in the default bucket.
- **Deploy gotchas:** nodeutils is installed from **GitHub at the gitlink
  SHA** — an unpushed nodeutils commit is invisible to the collector, and
  the superproject gitlink must be moved to the new commit before live
  verification. (Known trap; it has bitten before.)
- **Test baselines:** nctl `uv run pytest -q` = 1053 passed; nodeutils tests
  live in `nodeutils/tests/` (`uv run pytest`); Ansible conformance gate =
  3 passed.

## Design decisions and recommendations

### Evidence shape (idea-A §5)

Attach a `bindings` map to the consumer's existing `observed_services`
entry, one record per binding name:

```yaml
observed_services:
  node-agent:
    state: active
    bindings:
      llm_provider:
        configuration_status: present   # present | absent | unreadable
        configured_endpoint: "http://agstudio.home.arpa:11434/v1"  # raw string as found
        reachability_status: reachable  # reachable | unreachable
        http_status: 200
        checked_at: 2026-08-01T...Z
```

`configuration_status`: `present` = file read and slot non-empty; `absent` =
file or slot missing/empty (§6 `unbound`); `unreadable` = file exists but
can't be read/parsed. Only the one allowlisted slot value is ever reported —
never the rest of the file (roadmap hard rule 3).

### Normalization — do it once, on the controller

Roadmap: "endpoint normalization must be identical on the desired and
observed sides." The cheapest correct way: **nodeutils reports the raw
configured string; nctl normalizes both sides with one function.** Add a
small pure `normalize_endpoint_url(str)` next to `_endpoint_url` in
`service_dependencies.py` (lowercase scheme+host, strip trailing slashes,
bracket IPv6 — nothing clever) and apply it to both the resolved desired URL
and the observed `configured_endpoint` at evaluation time. Two
implementations in two repos is exactly how `misbound` starts flapping;
don't build one in nodeutils.

### Probe

Runs on the consumer node (that is the point — the agstudio DNS incident is
the reference case), against the **configured** value, not the desired one,
bounded at ~3s, once per binding per collection round. Probe even when the
value will turn out misbound; the evaluation decides what the probe result
means. No configured value → no probe.

### Evaluation (pure function in nctl)

Precedence order, first match wins:

1. `unknown` — no evidence for the binding, evidence unreadable, or stale
   (age > `service_observation_max_age_hours`; write the threshold into the
   report/provenance so it's visible).
2. `unbound` — `configuration_status: absent`.
3. `misbound` — normalized configured ≠ normalized desired.
4. `unreachable` — values match, probe failed.
5. `satisfied` — values match, probe succeeded, evidence fresh.

Converged requires additionally that desired resolution succeeded (Phase 2
resolver; its errors already surface as node-local drift — don't duplicate
them) and the provider placement's own status in `evaluate_placement_drift`
is `satisfied`. Suggested gap codes on the consumer's service evaluation:
`binding_unknown`, `binding_unbound`, `binding_misbound`,
`binding_unreachable`, `binding_provider_not_converged` — with the binding
name, both endpoint values, and evidence age as gap fields. `unknown` is
**not** converged (severity `unknown` is fine, matching
`service_observed_facts_unknown`; it must still block convergence).

Wiring suggestion: extend `evaluate_all_services` (it already has every
input) rather than adding a new comparator; a separate
`drift/binding_evaluation.py` for the pure state function keeps it testable.
Implementer's choice.

### Reconcile classification

Route in `reconcile/classify.py`: `binding_unbound` / `binding_misbound` →
the consumer's `node_agent` action (rerunning `setup_opencode.yml` rewrites
the config from resolved desired state — that is the actual repair);
`binding_unreachable` / `binding_provider_not_converged` → provider-side /
manual review (the consumer playbook cannot fix a dead provider);
`binding_unknown` → observation refresh, not actuation.

## Steps

Follow the phase execution style: one report section + one commit per step;
pause for user judgment at live/hard-to-reverse actions.

1. **Metadata and probe-config plumbing.** Declare the binding slot under
   `node_agent` in `deployment_profile_reconciliation` (e.g.
   `bindings: {llm_provider: {config_file: ~/.config/opencode/opencode.json,
   json_path: provider.ollama.options.baseURL}}`), extend `ProfileAction` +
   `render_probe_hints` to copy it verbatim into probe config for active
   consumer placements. nctl suite green.
2. **nodeutils binding observation.** Read the slot (expanduser, bounded
   read, JSON parse), emit the evidence record, probe the configured
   endpoint. Unit tests in `nodeutils/tests/`. Keep schema v2. Commit in the
   nodeutils repo (do not push yourself).
3. **nctl evaluation.** `normalize_endpoint_url`, the five-state pure
   function, folding into `evaluate_all_services` with the new gap codes,
   `classify.py` routing, and any report-contract/allowlist updates the new
   provenance needs. Tests: state matrix (all five states + provider-not-
   converged + staleness boundary), one end-to-end drift test (doctored
   snapshot with a misbound value → consumer service shows
   `binding_misbound` in `nctl drift --json`). Full gates.
4. **Deploy and live baseline** (pause: ask the user to push nodeutils and
   agree the superproject gitlink move — the collector installs from GitHub
   at the gitlink SHA). Then `nctl reconcile <slug> --refresh-observation`
   for aghub/agpc/agstudio and confirm: evidence present for all three
   bindings, all `satisfied`, whole-cluster drift converged.
5. **Fault drills** (pause: get approval — this mutates a live node and
   stops the shared provider). (a) Hand-edit `opencode.json` on one consumer
   → refresh → `binding_misbound` drift; (b) stop Ollama on agstudio →
   refresh → `binding_unreachable` (and the provider's own
   `service_not_running`); (c) restore both, reconcile, refresh → cluster
   converged again. Record all outputs in `p3/report.md`.

## Hard rules (the only prohibitions)

- Observation returns only the allowlisted slot value — never the whole
  config file, other keys, or credentials (roadmap hard rule 3).
- Evidence travels through `observed_services` only; no parallel ledger, no
  new custom field (roadmap Phase 3 bullet 2).
- Binding state is computed at evaluation time, never stored or hand-edited
  (roadmap hard rule 1).
- One normalization applied to both desired and observed values — never two
  independent implementations.
- Do not push nodeutils/nctl/ansible_agdev yourself; ask the user.
- Pause for user approval before Step 4's deploy/gitlink move and Step 5's
  fault drills.

## Completion criteria (roadmap, restated)

- Mis-editing the OpenCode config on one node produces `misbound` drift on
  that consumer.
- Stopping Ollama produces `unreachable`.
- Restoring both and reconciling returns the whole cluster to converged.
- The freshness threshold is chosen, written down, and `unknown` (stale or
  absent evidence) is visibly not-converged.
- All gate runs with counts recorded in `p3/report.md`.
