# Creative Workspace — Phase 2 Plan: Evaluation and the workspace view

Parent: [roadmap.md](../roadmap.md). Its Premises and Hard rules are the only prohibitions.
Everything below not marked **required** is a recommendation or a hint — deviate freely when the
code argues for it.

## Goal

Make the observations from Phase 1 mean something: add workspace evaluation to nctl —
convergent drift codes, an informational activity classification in a separate namespace, and an
on-demand `nctl workspaces` view — all computed fresh from the same snapshot, never persisted.

**Exit criteria (required):**
1. A live run shows `pj-voxel3dprint` on `agpc` as present, identity-matched, with a truthful
   activity class (user confirms the class matches the real tree state).
2. `nctl drift` and `nctl workspaces` derive from the same evaluation and cannot disagree.
3. Informational status never appears among convergent drift codes (hard rule 2).
4. nctl ordinary gate passes.

## Scope

**nctl only.** No nintent, nodeutils, or nauto change; no image rebuild, no Git Repository
re-sync, no node-side deploy. The live actions this phase are read-only computations against the
scratch Nautobot, so the only pause point is the push. This is the cheapest phase of the roadmap
to iterate on — a fix is edit + rerun.

## Key design facts discovered while planning

- **Everything Phase 2 reads already exists, verbatim names in
  [p1/report.md](../p1/report.md) §"Handed to Phase 2".** Desired side:
  `DesiredSnapshot.workspaces` (`sources/desired.py:292` — slug, lifecycle, `desired_presence`,
  `source_remote_url`, `expected_path`, `node_id`, `node_slug`). Actual side: the
  `observed_workspaces` Device custom field (JSON, keyed by workspace slug) — **no reader for it
  exists yet**; `ActualFacts` in `sources/actual.py` needs an `observed_workspaces` field mirroring
  the `observed_services` pass-through (`_observed_services` at `actual.py:150` is the template:
  dict-of-dicts, drop non-dict entries, no validation).
- **Drift plumbing is a registry of comparators.** `@register("<resource_type>")` in
  `drift/registry.py` makes a `(snapshot, context) -> Iterator[DiffRecord]` function run on every
  drift computation. `Target.kind` is deliberately an open string (`drift/model.py` docstring) —
  use `kind="workspace"` and the roadmap's codes; nothing else needs touching for findings to flow
  into `nctl drift`, target rollups, and JSON output.
- **Node → device resolution.** A workspace names a node (`node_slug`/`node_id`); the observation
  lives on that node's Device. `DesiredNode.realized_device_id` is the established link (see how
  `evaluation_snapshot.py` hands realized devices to service placement evaluation). No realized
  device ⇒ the observation is unreachable ⇒ observation-missing, with a reason.
- **Freshness precedent.** `drift/service_placement.py:116` — compare a per-entry timestamp
  against `now` with `stale_after_hours` (default 24, already threaded through
  `evaluation_snapshot.py`). Workspaces have their own `checked_at` per entry; use it, not the
  device-level ingest timestamp. Codes: `workspace_observation_missing` /
  `workspace_observation_stale`, mirroring the service pair.
- **The "cannot disagree" invariant is architectural, not a test.** `nctl relations` achieves it
  by being a pure projection over `fetch_and_compute_drift`'s output
  (`relations_render.py:73-79`). Copy that shape: one evaluation function produces per-workspace
  results; the drift comparator emits its convergent findings as `DiffRecord`s, and
  `nctl workspaces` projects the same results (plus the informational classification) into a
  view. Whether the classification is computed inside the shared function and merely *not*
  emitted as drift, or computed in the projection from the shared function's promoted facts, is
  your call — the former is simpler to keep honest.
- **Envelope pattern.** `build_relations` → `Envelope.build("nctl.relations.v1", data, errors)`,
  a `--json` flag, and a text renderer in a `*_render.py` module. `nctl workspaces` should be
  `nctl.workspaces.v1` in the same style; the CLI wiring is ~6 lines in `cli/main.py`
  (`relations` at line 221 is the template).

## Evaluation semantics (recommended, with the open edges called out)

Convergent drift codes (reconcile may act; actuation itself still absent this phase):

| code | condition | suggested severity |
|---|---|---|
| `workspace_missing` | desired present + observation says `present: false` | error |
| `workspace_identity_mismatch` | present + observed `remote_url` differs from declared `source_remote_url` | error |
| `workspace_retired_present` | desired absent + checkout present | warning, **report only** — never attach `recommended_actions` (hard rule 3: deletion stays behind an explicit boundary that doesn't exist yet) |
| `workspace_observation_missing` / `_stale` | standard freshness contract | warning (service precedent) |

Informational status (separate field/namespace — never a drift code, never a `DiffRecord`):
`active_development` (ahead > 0 and/or dirty), `behind_origin` (behind > 0, not active),
`idle` (otherwise). Include structured `reasons` (e.g. `{"ahead": 2, "dirty": true}`) so the
class is explainable from exactly the promoted fields it consumed.

Open edges — decide during implementation and document the choice in the step report:

- **Remote URL comparison.** Git remotes come in ssh/https flavors with optional `.git`. For one
  real workspace an exact string compare may genuinely suffice; if you normalize, keep it minimal
  (strip trailing `.git`, maybe unify `git@host:path` ↔ `https://host/path`) and test both
  directions. Don't reach for `normalize_endpoint_url` — that's HTTP-endpoint semantics.
- **Present but not a git repo** (`present: true`, no identity fields, `raw.is_git: false`).
  This is *unknown identity*, not a mismatch — don't emit `workspace_identity_mismatch` for it.
  Reasonable options: its own code (`workspace_identity_unknown`) or folding into the mismatch
  code with a distinguishing reason. Either is fine; unknown ≠ divergent is the line to hold.
- **No upstream** (`ahead`/`behind` absent). Divergence is unknowable; classify from `dirty`
  alone and say so in `reasons` rather than inventing a fourth class for one edge case.
- **Lifecycle filter.** Phase 1's probe hints only cover `active`+`present` workspaces, so a
  retired workspace typically has *no* observation entry. `workspace_retired_present` therefore
  fires mainly from a stale entry or a manually-hinted probe — implement it anyway (it's cheap
  and the roadmap names it), but don't contort the hint rendering to feed it.

`nctl workspaces` view, one row per declared workspace: node, presence, identity match, activity
class, observation freshness. `--json` for agents, text for humans. Computed on demand, never
persisted (roadmap non-goal: no persisted dashboard).

## Steps

One report + one commit per step (`p2/report_stepN.md`). Single pause marked.

### Step 0 — Baseline (read-only)

Run `uv run --project nctl nctl drift --json` against the live scratch Nautobot and fetch the
`agpc` Device's `observed_workspaces` custom field. Record: current findings (expect none for
workspaces — no evaluator exists), the observation's current promoted values, and how stale
`checked_at` is. If it's older than 24 h, note that Step 4's live proof will need one
`nctl reconcile agpc --refresh-observation` round first — that command is already proven
(Phase 1 Step 6) and is the intended freshness lever, not a workaround.

### Step 1 — Actual-state reader

Add `observed_workspaces` to `ActualFacts` in `sources/actual.py`, following the
`observed_services` pass-through exactly (raw dict per slug; evaluation, not the reader, decides
what fields mean). Tests: malformed entries dropped, absent field ⇒ `None`, well-formed round-trip.

### Step 2 — Shared evaluation + drift comparator

The core of the phase. A workspace evaluation module (suggested: `drift/workspace_evaluation.py`
beside its service sibling) that, per declared workspace, joins desired ↔ observation and
produces one result carrying: presence verdict, identity verdict, freshness verdict, activity
class + reasons, and the promoted facts consumed. A registered comparator turns the convergent
verdicts into `DiffRecord`s with `Target(kind="workspace", slug=..., name=..., id=...)`.

Tests (table-driven over fabricated snapshots is the cheapest shape here): each drift code fires
and doesn't; retired-present carries no recommended action; activity classes incl. the
no-upstream edge; stale vs fresh boundary; no realized device; **and a negative test that no
informational status string ever appears as a `DiffRecord.code`** — that's exit criterion 3 as a
regression guard.

### Step 3 — `nctl workspaces` view

`workspaces_render.py` in the relations style: `build_workspaces(cfg)` reuses
`fetch_and_compute_drift` (or the evaluation module directly — but then both paths must share the
snapshot fetch), projects per-workspace rows, `nctl.workspaces.v1` envelope, text + `--json`
renderers, CLI command in `cli/main.py`. Keep the text renderer honest about unknowns ("identity:
unknown (not a git repo)" beats a misleading ✓/✗).

Tests: projection from a canned snapshot+result; renderer snapshot-ish assertions kept loose
(README_DEV precedent: assert on content, not exact formatting).

### Step 4 — Gate, live proof, push  **(pause: ask the user to push)**

- nctl ordinary gate (`uv run pytest -q` in `nctl/`); this phase touches nothing else, so the
  README_DEV matrix ends there. No runtime gate — no nintent/nauto surface changed.
- Live proof (read-only): refresh observation first if Step 0 found it stale, then
  `nctl drift --json` and `nctl workspaces --json` against the scratch Nautobot. Positive
  evidence (README_DEV lesson 1): the workspace row shows present + identity-matched, and the
  activity class is confirmed against reality by the user (they know whether the tree is
  currently dirty/ahead — ask, don't assume). Also confirm no new unrelated finding appeared in
  drift.
- Commit nctl, update the superproject pointer, ask the user to push both.

### Step 5 — Phase report

`p2/report.md`: exit-criteria table with evidence, deviations, and a short "handed to Phase 3"
note: which raw fields (if any) the activity classification wanted but didn't have, and what the
one real workspace suggests about build-profile shape — Phase 3's pre-build rung feeds on exactly
those observations, and this phase closes the "minimal useful system" milestone, so later phases
are demand-driven.

## Known pitfalls, collected

- The custom-field JSON is agent-written ledger data — treat every field as possibly absent or
  mistyped in the reader/evaluator; a malformed workspace entry must degrade to
  observation-missing for that workspace, never crash the whole drift run (the `kind="global"`
  degradation note in `drift/comparators.py` is the house style).
- `ahead`/`behind` are only as fresh as the last `git fetch` on the node — a truthful
  `behind_origin: 0` may still be behind reality. That staleness is accepted by design (roadmap
  Phase 1 hint); don't try to compensate for it in the evaluator, and don't let the view imply
  more certainty than the data has.
- Don't leak service vocabulary: no reuse of `service_*` gap codes, `SERVICE_TARGET_TYPE`, or the
  service evaluation result rows for workspace findings — separate target kind, separate codes
  (roadmap Phase 2 hint, and the reason hard rule 2 is satisfiable at all).
- `desired_workspaces` decodes with `.get(...) or []` (Phase 1 deviation note) — existing test
  fixtures without workspaces keep working; new fixtures only need the key when the test is about
  workspaces.
- If drift output ordering matters to a test, note `registry._sort_key` sorts records —
  fabricate expectations accordingly rather than fighting the sort.
