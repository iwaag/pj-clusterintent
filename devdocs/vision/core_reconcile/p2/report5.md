# Phase 2 Report — Step 5 (`nctl drift` CLI)

Date: 2026-07-15. Implements [p2/plan.md](plan.md) Step 5.

## What was built

New module `nctl/src/nctl_core/drift_render.py` — the `Config`/`Envelope` glue around Step 3's
`engine.compute_drift`, mirroring `production_render.py`'s/`dnsmasq_render.py`'s role for their
respective cores:

- `build_drift(cfg, *, host=None, service=None) -> Envelope[DriftData]` — resolves the Nautobot
  token, loads `vars/deployment_profiles.yml` (via the Step 2 `load_deployment_profiles`),
  fetches a `SourceSnapshot`, builds a `DriftContext`, and runs `compute_drift`. Two failure modes
  are handled differently, deliberately:
  - A bad token or an unreachable/failing Nautobot fetch is a real run failure — `envelope.ok`
    goes `false`, matching `render dnsmasq`'s/`render production`'s `nautobot_token_error`/
    `nautobot_fetch_failed` convention.
  - A missing or invalid `deployment_profiles.yml` is **not** treated as a run failure: profiles
    degrade to `{}`, the same "no profiles, so `production_policy` yields nothing" path
    `comparators.py` already has internally (`if not context.profiles: return`). A drift command
    that goes fully dark because one unrelated ansible_agdev file is missing would be worse than
    one that just runs every comparator except `production_policy`. This is documented in the
    module's top docstring as the reasoning behind the plan's "drift is a successful answer, not
    an error" exit-code rule.
- `DriftData` (schema `nctl.drift.v1`): `generated_at`, `summary` (counts by `Status`, e.g.
  `{"converged": 3, "unknown": 2}` — only statuses that actually occur are keyed, matching
  `engine.py`'s own `_summarize`, recomputed here over the possibly-filtered target list rather
  than reused verbatim from `DriftResult.summary`), `severity_summary` (counts by `Severity`
  across all diffs in the filtered target list, always present with all three keys even at zero —
  this is Step 5's own addition; `engine.DriftResult` only ever tracked status counts, and the
  plan's "summary (counts by status/severity)" wording asks for both), `targets`
  (`list[TargetStatus]`, reusing `engine.py`'s pydantic model directly), `sources`
  (`DriftSourcesData`: `fetched_at`, `observed_dump_count`, `observed_errors` — the fetch
  timestamps/dump errors the plan's Step 5 bullet asks for, read off `SourceSnapshot`).
- `--host SLUG` / `--service NAME` filtering: implemented by filtering `DriftResult.targets` post
  hoc (`kind == "node" and slug == host` / `kind == "service" and name == service`) and then
  recomputing both summaries **over the filtered set**, not the full one — so `--host agbach`'s
  JSON `summary` describes exactly the one target in `targets`, not the whole cluster. This reads
  more useful for the stated consumer ("AI reads just the drift JSON") than a summary that
  disagrees with what's actually in the payload.
- `render_drift_text`: one line per target (`{slug}  {status}  {n} diff(s)`) followed by one
  indented line per diff (`    [{severity}] {message}`), then a trailing `summary: status=count
  ...` line (or `summary: (no targets)` when the filtered set is empty) — the plan's "a rendering
  of the JSON" convention, same shape as `render_status_text`/`render_production_summary_text`.

CLI wiring in `nctl/src/nctl_core/cli/main.py`: `nctl drift [--host SLUG] [--service NAME]
[--json] [--config PATH]` as a **top-level** command (not under `render`/`apply`), per the plan's
literal spelling. Exit code `0` whenever the run itself succeeded, regardless of whether any
target came back `drifting`/`unknown` — matching the plan's "drift is a successful answer, not an
error" rule; `1` only on a run failure (bad token, unreachable Nautobot). No operation ID or
event log: drift reads the Phase 0 events directory (via `DriftContext.events_dir`, feeding the
Step 3 `converging` rule) but never writes to it, same synchronous-read convention as `render
dnsmasq`/`render production`.

## Tests

- `tests/test_drift_render.py` (11 tests, respx-mocked GraphQL against a real `SourceSnapshot`
  fetch): empty-desired-state envelope shape; per-node/per-service status end to end (two nodes —
  one with a resolvable `realized_device`, one with a dangling one — plus one service, confirming
  `agok` → `converged`, `agmissing` → `unknown` via both `missing_actual_node` and
  `realized_device_missing`, and `web` → `unknown` via `service_observed_facts_unknown`, since no
  observed-facts source is wired into service evaluation yet — a real, not a test-only, gap
  documented inline); `--host`/`--service` filtering scoping both `targets` and the recomputed
  `summary`; `sources` metadata (`fetched_at`, `observed_dump_count`, `observed_errors`); the
  Nautobot-failure degradation path; the "no profiles file, no failure" degradation path; text
  rendering (targets, diff lines, summary line, the no-targets case, the not-ok error-lines case);
  and a JSON round-trip asserting the exact top-level `data` key set.
- `tests/test_cli_drift.py` (4 tests, `CliRunner` + monkeypatched `build_drift`, mirroring
  `test_cli_render_dnsmasq.py`'s pattern): default text output, `--json` output, `--host`/
  `--service` values passed through to `build_drift` unchanged, and exit code 1 on a failed
  envelope.

## Live check against the dev Nautobot instance

Ran `nctl drift` (text, `--json`, `--host agbach`, and `--service nonexistent`) against the real
dev Nautobot instance (`http://localhost:8000`) with the current dataset (5 desired nodes, 0
operational configs/placements/services beyond one now-irrelevant fixture — see below, 1
nodeutils dump for `agstudio.local`):

```
agdnsmasq  unknown  2 diff(s)
    [warning] agdnsmasq: missing_actual_ip_address
    [error] agdnsmasq: missing_actual_node
agbach  converged  2 diff(s)
    [warning] agbach: actual_node_not_linked
    [warning] agbach: missing_actual_ip_address
aghub  unknown  3 diff(s)
    [warning] aghub: missing_actual_ip_address
    [error] aghub: missing_actual_node
    [warning] aghub: missing_interface_candidate
agpc  converged  2 diff(s)
    [warning] agpc: actual_node_not_linked
    [warning] agpc: missing_actual_ip_address
agstudio  converged  2 diff(s)
    [warning] agstudio: actual_node_not_linked
    [warning] agstudio: missing_actual_ip_address
summary: converged=3 unknown=2
```

This is the expected shape given report4's Parity Gate A findings (3 nodes have a single strong
actual-node candidate but aren't explicitly linked → `warning`-only → `converged`; 2 have no
candidate at all → `error` `missing_actual_node` → `unknown`) — `nctl drift` and the Step 4
comparators it runs unchanged agree by construction, since `drift_render.py` adds no comparison
logic of its own, only `Config`/`Envelope` plumbing. `--json` produced a well-formed
`nctl.drift.v1` envelope with the same five targets and a `severity_summary` of
`{"error": 2, "warning": 9, "info": 0}`. `--host agbach` correctly scoped both `targets` and
`summary` to the one node. `--service nonexistent` correctly returned an empty target list,
`summary: (no targets)`, and exit code `0` (a filter matching nothing is not a run failure).

No live `deployment_profiles.yml` issue was hit (the file exists and loads cleanly per Step 2's
report), so the "missing profiles" degradation path was verified only via the unit test, not live
— documented here so a future step doesn't assume it was live-checked.

## Verification

- `uv run pytest -q` — **236 passed** (15 new: 11 `test_drift_render.py` + 4 `test_cli_drift.py`;
  221 pre-existing from Phases 0–1 and Steps 1–4, no regression).
- Live check — see above; text, `--json`, `--host`, and `--service` all exercised against the
  real dev Nautobot instance and produced internally consistent, expected output.

## Deviations from plan

- `severity_summary` is a Step 5 addition not present in Step 3's `DriftResult` — `engine.py` was
  read, not modified, to keep this step's blast radius to the CLI/envelope layer only (per the
  plan's own Step 3/Step 5 split, reaffirmed in report3's "Deviations" section). Recomputing both
  summaries here (rather than exposing `DriftResult.summary` directly) is what makes `--host`/
  `--service` filtering keep the JSON internally consistent — see "What was built" above.
- No CLI `--check`-style gating flag was added; the plan explicitly defers it ("`--check`-style
  gating can come later if a caller needs it"), so it stays out of scope here too.

## Real bugs/surprises

One incidental finding, not a code bug: the live dev database still has `desired_services`
representing one seeded service (used in this step's live check to exercise the `--service`
filter and the `kind="service"` seeding path), but it has no wired-up observed-facts source, so
`service_intent_matching` always emits `service_observed_facts_unknown` and the service can never
resolve to `converged` under the current comparator wiring. This is expected given Step 4's scope
(no consumer yet calls `evaluate_service_intent` with real `observed_facts`) — not a defect, but
worth flagging for whoever picks up service-observation wiring later (out of scope for this
phase; nothing in `p2/plan.md` calls for it).

## Commit boundary

CLI wiring, envelope schema, filtering, text rendering, and full test coverage all landed
together, fully green, with a live check across every flag — committed as one self-contained
unit (`nctl` commit `p2s5`, 4 files changed, 510 insertions). This is commit 5 of the plan's
suggested order ("nctl: `nctl drift` CLI + envelope + tests").

**Not done yet, deliberately left for the next commit(s):**

- Step 6 — the single nintent push cycle deleting both proto-drift-engines
  (`ExportProductionInventory`, `SyncDeploymentProfiles`, the three Evaluate Jobs,
  `IntentEvaluation`/`DeploymentProfileProjection` models, their UI/API surface). This is the
  first step that touches anything outside `nctl`.
- Step 7 — ansible_agdev cleanup (including the `vars_files` bug in
  `export_nintent_production.yml` documented in report2, moot once the playbook is deleted) and
  the deferred Phase 1 live-apply proof.
- Step 8 — docs and report closeout.

Next: Step 6 — the single nintent push cycle (delete both proto-drift-engines, bump nintent to
0.6.0, ask the user to push and rebuild the dev Nautobot container).
