# Fix report — nodeutils service detection: substring false positive and plain-process blind spot

Date: 2026-08-06 (JST)
Session type: `workflow-improvement` (agentdocs)
WorkflowEpisode: `2f2d3de6-039a-4a36-a6a6-152da8a92d51` (resolved)
Commit: `79641a2` (nodeutils) — `Fix systemd service-name false positives; generalize process probes`

## Symptom

`nctl drift --json` carried three permanent, unexplained findings: `swarmui`
and `comfyui` `service_missing` on agpc, and `prometheus`
`service_observed_on_wrong_node` + `service_has_no_active_placement`. The
first real workflow-agent run (plan → executor → report; 4 turns, 3 read-only
commands, no improvisation) confirmed all three hypotheses formed at planning
time: every finding was an observation defect, not a deployment defect. The
cluster itself needed no remediation.

## Root cause

- **prometheus false positive**: `important_service_name_from_systemd` in
  `nodeutils_collect.py` fell back to substring matching over
  `"<unit> <description>".lower()`. `prometheus-node-exporter.service`
  (description "Prometheus Node Exporter") therefore reported service
  `prometheus` on agpc, where no prometheus server exists. Description text is
  unsalvageable for this purpose — any tokenization of "Prometheus Node
  Exporter" still contains "prometheus".
- **swarmui/comfyui blind spot**: both actually run on agpc as plain user
  processes under `/home/eiji/StabilityMatrix/` — neither systemd units nor
  Docker containers, the only two things the collector could see. Declared
  observe_only placements of such services were permanently `missing`. A
  narrow precedent existed as an ollama-only hard-coded `pgrep` probe
  (macOS path only).

## Fix

`nodeutils` commit `79641a2`:

1. The systemd fallback now requires **exact unit-stem equality**
   (unit name minus `.service`, case-insensitive) and no longer reads the
   description. `prometheus.service` → `prometheus`;
   `prometheus-node-exporter.service` → no match without a hint. A service
   running under any other unit name declares an explicit
   `service_probe_hints.<name>.systemd_unit`, as before.
2. The ollama-only pgrep probe is generalized:
   `service_probe_hints.<name>.process` (`pgrep -x`, exact executable name)
   and `process_pattern` (`pgrep -f`, full command line — StabilityMatrix-style
   long paths) make plain-user-process services observable. Only hinted
   services are probed (no arbitrary process scanning); ollama keeps its
   implicit `process: ollama` default; process probes now also run on Linux
   (previously the macOS-only tail of the launchd path).
3. `example.self_inventory.yaml` documents both hint keys and the exact-stem
   matching rule.

Downstream needed no change: `normalize_observed_services` already merges
user-service entries with `source: "process"`.

## Verification

- nodeutils unittest suite: 81 tests OK, including new tests for
  exact-stem fallback (node-exporter unhinted → `None`; description
  containing "prometheus" → `None`; `prometheus.service` / case-insensitive
  `Nautobot.service` → matched) and for hinted process probes on Linux
  (`process` and `process_pattern` both exercised; unhinted services provably
  probe nothing).
- Honest limit: cluster-level acceptance — the three drift findings actually
  clearing — needs the follow-ups below and a fresh observation; it is not
  claimed here.

## Trade-off accepted

Units previously caught only by fuzzy substring match (e.g. a hypothetical
`postgresql.service` reported as `postgres`) now require an explicit
`systemd_unit` hint. Implicit fuzzy matching → explicit declaration is the
deterministic direction the easier-next-time policy prefers; if a real
service disappears from observation after this change, that is the signal to
add its hint.

## Not done here (separate reviewed sessions)

- Push nodeutils `79641a2` to GitHub (user-performed per local convention),
  then bump the superproject submodule pointer.
- Apply `process_pattern` hints for swarmui/comfyui to agpc and run
  `nctl reconcile agpc --refresh-observation` — improvement decisions do not
  write cluster state from a workflow-improvement session.
- Docker-side `important_service_name` keeps substring matching over
  name/image/compose labels: image strings like `prom/prometheus:v2` make
  substring matching reasonable there, and the episode reported no defect on
  that path.
