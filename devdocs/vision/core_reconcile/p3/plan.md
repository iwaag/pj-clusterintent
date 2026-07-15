# Phase 3 Implementation Plan: Visualization dashboard

Parent: [roadmap.md](../roadmap.md) — Phase 3: let humans grasp the situation from a single
screen without touring Nautobot. `nctl dashboard` generates static HTML from the Phase 2 drift
JSON; on the Nautobot side, nintent gains only a reconciliation status field and a link to the
dashboard.

## Current state (as of 2026-07-16)

- Phase 2 is complete ([p2/report8.md](../p2/report8.md)): `nctl drift --json` returns the
  `nctl.drift.v1` envelope — `generated_at`, `summary` (counts by status), `severity_summary`,
  `targets` (per node/service: `target` kind/slug/name/id, `status`
  `converged|drifting|converging|unknown`, `diffs` with `code`/`severity`/`message`/
  `desired`/`actual`/`sources`), and `sources` (fetch timestamp, dump count, dump errors).
  The plan's stated intent — "this payload is the Phase 3 dashboard input" — is now cashed in.
- Live baseline from the Phase 2 closeout: five nodes (three `converged`, two `unknown`, two
  error and nine warning diffs); service targets currently surface
  `service_observed_facts_unknown` because no observed-facts provider is wired for services.
  The dashboard renders these as-is — fixing service observation is not Phase 3 work.
- nctl today: `status` / `drift` / `render dnsmasq` / `render production` / `apply dnsmasq`;
  `Config` sections `[nautobot]`, `[inventory]`, `[events]`, `[ansible]`, `[repo]` (strict —
  new sections need explicit model fields); `Envelope` output convention; atomic
  write-then-replace pattern from the production render; JSON Lines events reserved for
  long-running operations (drift is a synchronous read with no operation ID).
- nintent is at 0.6.0 with the proto-drift-engines deleted: models `IntentSource`,
  `DesiredService`, `DesiredDependency`, `DesiredNode`, `DesiredEndpoint`,
  `DesiredServicePlacement`, `DesiredNodeOperationalConfig`, `DesiredIPRange`, five retained
  Jobs, and the CRUD/REST/GraphQL surface. Per the Phase 0-EX1 split, **reads = GraphQL,
  writes = REST**, and the roadmap explicitly reserved the intent-catalog REST ViewSets for
  "writes such as the Phase 3 reconciliation status field".
- Deployment constraint (`.local/localenv_memo.md`): nintent changes cost commit → user push →
  `docker compose build --no-cache` → restart. As in Phases 1–2, all nintent work lands in
  **one** push cycle.
- Known migration noise (report8): `makemigrations --check` under Nautobot 3.1 proposes broad
  inherited-field alignment for all surviving models. The Phase 3 migration must stay scoped to
  the new fields only, same as migration 0008 did.

## Decisions taken head-on

**1. The dashboard is a pure subscriber of `nctl.drift.v1` — it never computes.** The
generator is a pure function `drift envelope → HTML string`. It performs no GraphQL fetch, no
dump read, no comparator call. If something a human needs is missing from the page, that is a
gap in the drift payload, fixed by an **additive** change to `nctl.drift.v1` (additions are
cheap, renames are expensive — the Phase 2 contract), never by the dashboard reaching around
the engine. This is the roadmap's "future frontends are just subscribers" convention made
concrete: the Phase 5 live dashboard replaces the transport (WebSocket instead of a file), not
the data model.

**2. `nctl drift` stays side-effect free; `nctl dashboard` = drift + render + write + push.**
"Regenerate on every reconcile/drift run" is satisfied by making `nctl dashboard` the routine
entry point for humans (it runs the same `build_drift` internally), not by giving `nctl drift`
a write side effect — drift remains the fast, pure read that AI and scripts call. Phase 4's
`nctl reconcile` will call the same dashboard code path after each run rather than shelling
out. For decoupled use, `nctl dashboard --from FILE` renders a previously saved
`nctl.drift.v1` envelope without touching the network.

**3. One self-contained HTML file, no toolchain.** Single `index.html` with inline CSS and
vanilla inline JS; the drift envelope is embedded as a `<script type="application/json">`
block and the page renders itself client-side. No CDN, no npm build, no external assets — it
must work as a `file://` open and over dumb LAN static serving (the roadmap's hosting bar),
offline. The exact drift envelope is also written alongside as `drift.json`, so the dashboard
directory serves humans (HTML) and AI (JSON) from the same generation.

**4. Status write-back is a REST PATCH that degrades, never fails.** After writing the HTML,
`nctl dashboard` PATCHes each node/service's reconciliation status into nintent via the
existing intent-catalog ViewSets (the write path 0-EX1 reserved). Nautobot being unreachable
for the write, or a target having no ledger row, downgrades to a warning in the envelope —
the dashboard is the primary deliverable and must generate even when the ledger write cannot
land. The fields are documented as a **derived cache of the last nctl run** (the drift engine
remains the single source of truth); `reconciliation_checked_at` makes staleness visible.

**5. Status colors: green = `converged`, yellow = `converging`, red = `drifting`, gray =
`unknown`.** The roadmap says green/yellow/red; `unknown` ("I cannot see this node") is
deliberately distinct from `converging` ("change in flight") and gets gray, because painting
blindness yellow would misreport observability gaps as progress. Recorded here as the one
deviation from the roadmap's literal wording.

## Approach

Steps 1–3 touch only nctl (renderer → CLI command + config → status-push client) and are fully
testable offline against fixture payloads. Step 4 is the single nintent push (fields +
migration + UI + link). Step 5 verifies the whole loop live. Step 6 closes out docs and the
report. No parity gate is needed this phase — nothing is being ported or deleted; the risks
are UI usefulness (checked live in Step 5) and the REST write path (checked at the start of
Step 3).

**Risks to verify first:**
- At the start of Step 3: that the existing DesiredNode/DesiredService REST serializers accept
  PATCH for new writable fields (nintent's ViewSet/serializer style), and how a drift target
  maps back to a ledger row (`target.id` should be the Nautobot UUID — confirm it is populated
  for both kinds in live payloads; slug/name fallback otherwise).
- At the start of Step 4: that adding two fields to two models under Nautobot 3.1 produces a
  scoped migration (the report8 `makemigrations` noise must not leak into it).

## Step 1 — Dashboard renderer (`nctl_core/dashboard/`)

- `render_dashboard(envelope: Envelope[DriftData]) -> str` — pure function, one HTML document
  out. Contents:
  - **Cluster overview**: one tile per target (nodes first, then services), colored by the
    Decision-5 mapping, showing slug/name, status word, and diff count. The `summary` /
    `severity_summary` counts and `generated_at` render as a header strip — the "single
    screen" answer is readable without any interaction.
  - **Details on click**: clicking a tile expands the target's diffs — per diff the prose
    `message` (the roadmap's "drift details in prose"), `severity` badge, `code`, and the
    `desired` / `actual` evidence values with their `sources`. Rendering is escaped text, not
    innerHTML of payload strings.
  - **Sources footer**: fetch timestamp, observed dump count, and dump errors — so "why is
    this node gray" is answerable from the page itself.
  - **Failed-run rendering**: an envelope with `ok: false` still renders a page showing the
    errors, so a broken dashboard regeneration doesn't silently leave yesterday's greens up
    without comment. (The stale file staying up when nctl never ran at all is accepted;
    `generated_at` in the header is the staleness signal.)
- Template lives as a package resource (one HTML skeleton with inline CSS/JS); Python's job is
  embedding the JSON safely (escape `</script>` and U+2028/29) and stamping the header. All
  layout/interaction logic is client-side JS reading the embedded envelope — one rendering
  code path, per the Phase 0 "text is a rendering of the JSON" convention.
- Tests: golden-marker tests over fixture envelopes covering all four statuses, the failed-run
  page, escaping of hostile strings in `message`/evidence, and embedded-JSON round-trip
  (extract the script block, parse, compare to input).

## Step 2 — `nctl dashboard` CLI and `[dashboard]` config

- Config: new optional section
  `[dashboard] out_dir = "~/.local/state/nctl/dashboard"` (default), `url` (optional string —
  where the directory is served on the LAN, if anywhere; used only as the link target pushed
  into documentation/nintent config, never fetched by nctl).
- CLI: `nctl dashboard [--out DIR] [--from FILE] [--no-push] [--json]`.
  - Default: run `build_drift` (full cluster — no host/service filter; a partial dashboard
    would misreport cluster health), render, write `index.html` + `drift.json` to the out dir
    via the existing atomic write-then-replace pattern, then push statuses (Step 3).
  - `--from FILE`: skip drift computation, render a saved `nctl.drift.v1` envelope (schema
    field is validated). Enables offline/AI-side regeneration and testing.
  - `--no-push`: generate only, skip the ledger write. `--from` pushes too (no staleness
    guard): `reconciliation_checked_at` is set from the payload's `generated_at`, so a stale
    push is visibly stale rather than silently rejected.
  - Envelope `nctl.dashboard.v1`: `data` = `html_path`, `drift_json_path`, `generated_at`,
    `summary`, `severity_summary`, `status_push` (`attempted` / `updated` / `skipped_no_row` /
    `failed`, with per-target error strings), `dashboard_url` (from config, may be null).
    `ok` follows the drift run and the file write; push failures are warnings inside
    `status_push`, per Decision 4. Text mode prints the paths and the summary line.
  - Synchronous read+write of local files — no operation ID / event log (same rationale as
    drift; the long-running commands stay `apply`/`reconcile`).
- Tests: CLI-level tests with a fixture drift payload (`--from`), out-dir writing/atomicity,
  `--no-push`, and envelope golden.

## Step 3 — Status write-back client (`nctl_core/dashboard/push.py`)

- Map drift targets to ledger rows: `target.kind == "node"` → DesiredNode, `"service"` →
  DesiredService, by `target.id` (UUID) with slug/name lookup as fallback; targets with other
  kinds (the open `Target.kind` set — e.g. global diagnostics) are skipped and counted as
  `skipped_no_row`.
- PATCH `reconciliation_status` + `reconciliation_checked_at` through the intent-catalog REST
  ViewSets (writes = REST). One failure doesn't abort the rest; results aggregate into
  `status_push` per Step 2. No-op short-circuit (skip the PATCH when the remote values already
  match) is a nice-to-have, not required.
- This step's code merges before Step 4 deploys, but its **live** verification happens in
  Step 5; unit tests run against respx-mocked REST.

## Step 4 — nintent 0.7.0: status fields and dashboard link (single push cycle)

- Model change: `reconciliation_status` (CharField, choices exactly the nctl status vocabulary
  `converged/drifting/converging/unknown`, plus blank = never pushed) and
  `reconciliation_checked_at` (DateTimeField, null) on **DesiredNode and DesiredService** —
  drift targets both kinds, and the pair is symmetric and cheap. One scoped migration (0009),
  nothing else in it (the report8 inherited-field noise stays out).
- Surface: fields writable in the REST serializers (this is the Step 3 write path); shown
  read-only in detail templates and as a badge column in the node/service tables. **No
  GraphQL/UI editing** — the fields document themselves as "written by nctl, derived cache of
  the last run" in help_text.
- Dashboard link: a `dashboard_url` plugin setting (`PLUGINS_CONFIG`), rendered as a
  navigation menu link (and on the node/service detail pages next to the status badge) when
  set. A plugin setting, not a model — the URL is deployment config, and per the roadmap we
  "accept that Nautobot is the ledger and visualization lives outside it".
- Bump nintent to 0.7.0; run the nintent suite locally; commit; ask the user to push; rebuild
  dev Nautobot without cache; restart; `nctl status` stays green (the GraphQL types gained
  fields, lost nothing).

## Step 5 — Live verification (the exit-criteria proof)

- Run `nctl dashboard` against the dev cluster. Open the generated `index.html` locally and
  confirm against the live `nctl drift` baseline: every target tile matches its drift status,
  the two `unknown` nodes are gray with their missing-source diffs readable in prose, error
  and warning diffs show their evidence, and the header answers "is the cluster healthy" at a
  glance.
- Confirm in Nautobot that the pushed `reconciliation_status` / `reconciliation_checked_at`
  match the payload for all five nodes and the service rows, and that the dashboard link
  appears with `dashboard_url` configured in the dev `PLUGINS_CONFIG`.
- Failure-path spot checks: `nctl dashboard` with Nautobot stopped (page renders the failed
  envelope), and with a bogus token (push degrades to warnings when generation came from
  `--from`).
- Record the procedure, screenshots/paths, and any payload gaps found (→ additive
  `nctl.drift.v1` follow-ups) in the report.

## Step 6 — Docs and report

- nctl README/docs: `nctl dashboard` usage, the `[dashboard]` config section, the
  `nctl.dashboard.v1` schema, the Decision-2 regeneration model ("run `nctl dashboard`, not
  `nctl drift`, when you want the page updated"), and the color/status legend.
- nintent README(s): the two derived-cache fields, who writes them, and the `dashboard_url`
  setting.
- Parent README: add `nctl dashboard` to the normal entry points.
- `p3/report*.md` in the established style: live verification record, the Decision-1..5
  outcomes as implemented, and the exact REST write path used.

## Out of scope

- Serving the dashboard (HTTP/WebSocket, live updates) — Phase 5; this phase's hosting story
  is "a directory you can open or point a static server at".
- Wiring dashboard regeneration into an automatic loop — Phase 4's `nctl reconcile` calls the
  Step 1/2 code path; cron/notification is the roadmap's Phase 4 optional item.
- Drift history / trends (the out dir keeps only the latest generation) and any 3D/voice UI.
- Fixing `service_observed_facts_unknown` (wiring a service observed-facts provider) — a
  comparator/source change independent of visualization; the dashboard shows it honestly.
- Phase 1.5 (hosts-intent migration) — still independent and still pending.
- Any non-additive change to `nctl.drift.v1`.

## Exit criteria (from roadmap, made checkable)

- [ ] `nctl dashboard` generates a single self-contained static HTML file (plus `drift.json`)
  from the `nctl.drift.v1` payload: whole-cluster tiles in green/yellow/red/gray with drift
  details in prose on click, plus summary header and sources footer — verified live against
  the dev cluster, sufficient on its own to understand cluster health and drift details.
- [ ] The dashboard is regenerated by the routine command itself (drift computation + render
  in one `nctl dashboard` run) and can re-render any saved payload via `--from`; `nctl drift`
  remains side-effect free.
- [ ] nintent 0.7.0 is deployed with exactly the roadmap's additions: reconciliation status
  fields (+ checked-at) on DesiredNode/DesiredService written by nctl over REST, and a
  configurable dashboard link — no other visualization moved into Nautobot.
- [ ] Status push degrades to warnings without blocking generation, and the pushed values
  match the live payload after a `nctl dashboard` run.
- [ ] `uv run pytest` passes in nctl including the renderer/CLI/push suites; nintent's suite
  passes with the field additions.

## Suggested commit order

1. nctl: dashboard renderer + fixtures + tests (Step 1).
2. nctl: `[dashboard]` config + `nctl dashboard` CLI + envelope + tests (Step 2).
3. nctl: status write-back client + mocked-REST tests (Step 3).
4. nintent: fields + migration 0009 + serializers/UI + `dashboard_url` link, 0.7.0 bump
   (Step 4; the single push/rebuild cycle).
5. Parent repo: live verification record, submodule bumps, docs, `p3/report*.md`
   (Steps 5–6).
