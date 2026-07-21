# Phase 0 Step 0.3 — Complete the nctl boundary inventory

Parent: [plan.md](plan.md), Step 0.3.

## Check performed

Read the live `nctl/src/nctl_core/` source tree and confirmed each row of the plan's Step 0.3
table, plus the forbidden-integration list, against the actual current modules.

| Boundary | Verified current state |
|---|---|
| GraphQL read model | `nautobot.py` docstring states explicitly: "GraphQL for reads (Phase 1+)... REST writes (Phase 3+)"; `NautobotClient.graphql()` posts to `/api/graphql/` and `_check_intent_graphql()` introspects for intent-catalog GraphQL types. Confirms the read/write split the plan requires Braindump/Review to follow. |
| REST write model | Same client exposes `rest_get`, `rest_patch`, `rest_post`, `rest_download` as the write-capable methods, consistent with "GraphQL for reads, REST for writes." |
| `nctl_core` | No `braindump`-named module exists yet anywhere under `src/nctl_core/`; this is a genuinely new addition, not a rename. Existing modules follow one-file-per-concern (`drift/`, `reconcile/`, `sources/`, `dashboard/`, `serve/`), so a new `braindump.py` or `braindump/` package is the consistent place for Phase 2's operations. |
| CLI | `cli/main.py` (418 lines) is a single Typer `app` with thin `@app.command()`/sub-app (`render_app`, `apply_app`, `ops_app`) functions — `status`, `drift`, `dashboard`, `render dnsmasq/production/hosts-intent`, `ops list/show`, `apply dnsmasq`, `reconcile`, `lifecycle`, `serve`. No braindump command group exists yet; the plan's candidate `nctl braindump ...` subcommand group fits this existing thin-wrapper pattern directly. |
| Human output | Not yet applicable — no braindump renderer exists. Existing renderers (`drift_render.py`, `dashboard_render.py`, `production_render.py`, `hosts_intent_render.py`) confirm the established pattern of one dedicated `_render.py` module per command family, which Phase 2 should follow for the human-output requirement. |
| JSON envelope | `sources/snapshot.py`'s `SourceSnapshot(BaseModel)` — the model actually named in the plan's forbidden list — has exactly the fields `desired`, `actual`, `observed`, `observed_errors`, `fetched_at`. Confirmed: no Braindump field exists there and none should be added (see below). |
| Error handling | Not yet applicable to a nonexistent feature; existing `NautobotError`/`NautobotGraphQLError` in `nautobot.py` are the established base-exception pattern Phase 2 should extend for a Braindump-specific error, rather than inventing an unrelated exception hierarchy. |
| `nctl serve` | `cli/main.py` registers `serve` as a normal `@app.command()`; `nctl_core/serve/` (`app.py`, `artifacts.py`, `dashboard.py`, `runner.py`, `runtime.py`, `snapshots.py`) is a substantial existing subsystem. Confirms "no change until optional Phase 4" is a real scoping decision, not a formality — Phase 2 must not touch this directory. |

## Forbidden-integration check

Explicitly verified the modules the plan says must **not** receive a Braindump integration:

- `sources/snapshot.py` — `SourceSnapshot` fields listed above; no Braindump field present, none should be added.
- `sources/desired.py`, `sources/actual.py`, `sources/observed.py` — the three snapshot components; Braindumps must stay out of all three.
- `drift/` package (`comparators.py`, `engine.py`, `registry.py`, `status.py`, `model.py`, `evaluation.py`, etc.) — deterministic drift; the plan forbids adding Braindumps here.
- `reconcile/` package (`classify.py`, `executor.py`, `planner.py`, `registry.py`, etc.) — reconcile classification; likewise forbidden.
- `production/` package — production composition; likewise forbidden.
- `hosts_intent.py`/`hosts_intent_render.py` — Ansible inventory rendering; likewise forbidden (no Ansible rendering integration for Braindumps).

None of these currently reference anything Braindump-related (the feature doesn't exist yet), so
the check confirms there is nothing to remove — only a boundary to respect when Phase 2 is
implemented.

## Result

Every row in the plan's Step 0.3 table and every forbidden-integration point was checked against
the live nctl source tree. The GraphQL-read/REST-write split, the thin-Typer-command pattern, the
one-file-per-concern `nctl_core` layout, and the `SourceSnapshot` field set are all confirmed
accurate as described. No edit to `plan.md` was required.
