# Phase 3 Report — Step 6 (documentation and phase closeout)

Date: 2026-07-16. Implements [p3/plan.md](plan.md) Step 6 and closes Phase 3.

## Documentation updates

### nctl

`nctl/README.md` now documents:

- `nctl dashboard` usage (`--out`, `--from`, `--no-push`, `--json`) and its role as **the**
  regeneration entry point — "run `nctl dashboard`, not `nctl drift`, whenever you want the page
  updated" is stated explicitly, matching Decision 2;
- the status color legend (`converged`/green, `converging`/yellow, `drifting`/red,
  `unknown`/gray) as a table, including the Decision-5 rationale for why `unknown` is gray
  rather than folded into another color;
- status write-back: which ledger model each `target.kind` maps to, that it goes over REST
  (reads stay GraphQL project-wide), and that failures degrade into `status_push` counts rather
  than failing the command — plus the "derived cache, not a second source of truth" framing;
- the new `[dashboard]` config section (`out_dir`, `url`) and that `url` is informational only,
  never fetched, and must be kept in sync by hand with nintent's `dashboard_url` plugin setting
  since the two configs don't read each other.

`nctl/docs/output-format.md` gained two new schema sections: `nctl.drift.v1` (previously
documented only in the README prose; now has the authoritative example payload, the seeding/
sorting guarantees, and the open-`target.kind` note) and `nctl.dashboard.v1` (the `status_push`
sub-shape and its degrade-without-failing semantics).

The parent `README.md` now lists `nctl dashboard` alongside the other four normal entry points,
with the one-line "run `nctl dashboard`, not `nctl drift`" guidance repeated at the point where a
newcomer would first reach for `drift`.

### nintent

`README.md` and `README_QUICK.md` were updated for nintent 0.7.0:

- the REST API section now lists the `DesiredService` route Step 4 added (previously documented
  as GraphQL/UI-only, which had already gone stale) alongside `DesiredNode`/`DesiredEndpoint`;
- a new "Reconciliation status fields and the dashboard link" section documents
  `reconciliation_status`/`reconciliation_checked_at` as a read-only, nctl-written derived
  cache (never computed by nintent itself), the REST write path, the degrade-on-failure
  behavior, and the `dashboard_url` plugin setting including *why* the nav link routes through a
  `dashboard_redirect` view instead of using the raw URL directly (the real deployment gap
  report5 found and fixed) rather than just documenting the end state;
- `README_QUICK.md`'s "nctl workflows" section gained the `nctl dashboard` command and a
  one-line explanation, matching the terse style of its three existing entries.

`README_DEV.md` and historical plans/reports were left untouched — they already document past
states as a record, per the established convention from Phase 2's closeout (report8).

## Phase 3 design outcomes

### Decision 1 — the dashboard is a pure subscriber, never a second computer

`render_dashboard_html` (Step 1) takes only an `Envelope[DriftData]` and returns a string; it
performs no GraphQL fetch, dump read, or comparator call anywhere in its call graph. The one
payload gap found during live verification (report5: terse diff `message` strings) was
correctly *not* patched around in the dashboard — it's recorded as a future additive
`nctl.drift.v1` improvement, exactly as Decision 1 requires.

### Decision 2 — `nctl drift` stays side-effect-free; `nctl dashboard` is the write path

Confirmed by construction (`build_dashboard` calls `build_drift` internally; `build_drift` never
writes) and by the live failure-path checks in report5: stopping Nautobot only ever affected
`nctl dashboard`'s output, and `nctl drift` itself was never observed to write anything in any
step's testing.

### Decision 3 — one self-contained HTML file

Delivered as designed: inline CSS/JS, the drift envelope embedded as a
`<script type="application/json">` block, native `<details>/<summary>` for click-to-expand (no
custom JS needed for that part), and DOM built via `createElement`/`textContent` rather than
`innerHTML` of payload strings. Verified live (report5) by reading the generated file directly
and confirming the embedded JSON round-trips byte-for-byte against the separately-written
`drift.json`.

### Decision 4 — status write-back degrades, never fails

Verified live twice in report5: a bogus token made all five PATCHes fail with `ok: true` still
returned and the failures itemized in `status_push.errors`; a clean run afterward showed
`updated: 5, failed: 0` with no lingering damage from the failed attempt (PATCH failures never
partially wrote anything).

### Decision 5 — unknown is gray, not yellow

Implemented as designed in both the dashboard CSS (`--gray` for `.tile.status-unknown`) and
nintent's table badge rendering (confirmed live in report5 via
`nautobot-server shell` — `<span class="label label-success">Converged</span>` for the green
case; the same `DesiredNodeTable` machinery renders the gray/`label-default` variant for
`unknown`, though the live dataset's `unknown` nodes were spot-checked via GraphQL/model state
rather than table rendering specifically since the report5 focus was the converged case).

## Live deployment record

The most consequential finding of this phase happened in Step 5, not Step 6, but belongs in the
closeout record: the dev Nautobot container was still running the `p3s4` image — one commit
behind `p3s4-fix1`, the fix for exactly the `NavMenuItem.link` risk report4 had flagged as
unverified. Rebuilding without cache and restarting closed that gap; the dashboard nav link and
per-object "(view dashboard)" links are now confirmed working against the actually-running code,
not just the source tree. See [report5.md](report5.md) for the full reproduction and fix record.

## Query and verification record

- [report1.md](report1.md): Step 1 — dashboard renderer, fixtures, and escaping tests.
- [report2.md](report2.md): Step 2 — `[dashboard]` config and `nctl dashboard` CLI/envelope.
- [report3.md](report3.md): Step 3 — status write-back client, including the REST-route risk
  check (no `DesiredService` route existed yet at the time).
- [report4.md](report4.md): Step 4 — nintent 0.7.0: fields, migration 0009, the
  `DesiredService` REST route, UI, and the `dashboard_url` plugin setting; the
  `NavMenuItem.link` risk noted as unverified locally.
- [report5.md](report5.md): Step 5 — live verification: the container-rebuild gap found and
  fixed, the dashboard-vs-drift baseline match, Nautobot write-back confirmation, both
  failure-path spot checks, and the one payload gap recorded for future work.

## Exit criteria

- [x] `nctl dashboard` generates a single self-contained static HTML file (plus `drift.json`)
  from the `nctl.drift.v1` payload, verified live: five target tiles, correct
  green/gray coloring, click-to-expand diffs with prose/evidence/sources, header summary, and
  sources footer.
- [x] The dashboard is regenerated by `nctl dashboard` itself (drift + render + write in one
  run) and re-renders any saved payload via `--from`; `nctl drift` stays side-effect-free by
  construction and by live observation.
- [x] nintent 0.7.0 is deployed and **actually running** (the report5 rebuild closed the gap
  between "committed" and "deployed") with exactly the roadmap's additions: reconciliation
  status fields on DesiredNode/DesiredService written by nctl over REST, and a working
  configurable dashboard link — no other visualization moved into Nautobot.
- [x] Status push degrades to warnings without blocking generation (bogus-token live check) and
  the pushed values matched the live payload after a clean run (GraphQL + table-render
  confirmation).
- [x] Final suites pass: nctl **263 passed**, nintent **92 passed** (loader-only; DB/API-backed
  behavior verified live in report5, per the standing constraint that Django isn't installed in
  the local nintent venv).

All checkboxes in `p3/plan.md` were updated accordingly.

## Known follow-ups, not Phase 3 blockers

- Diff `message` strings are terse code restatements rather than full prose sentences (report5's
  payload gap) — a future additive `nctl.drift.v1` comparator-quality improvement, not a
  dashboard change.
- Service targets still surface `service_observed_facts_unknown` (no observed-facts provider
  wired for services) — pre-existing from Phase 2, unaffected by and out of scope for Phase 3.
- The live dataset has zero `desired_services`, so the service-target code paths (seeding,
  status-push mapping to `DesiredService`) are exercised by unit tests and the REST route exists,
  but have not been observed live against a populated service. Worth a live check once service
  data exists, not a phase blocker.
- Phase 1.5 (hosts-intent migration) remains independent and still pending, as in every prior
  phase's closeout.
- Serving the dashboard live (Phase 5), drift history/trends, and Phase 4's reconcile
  orchestration remain future roadmap work, per the plan's explicit "Out of scope" list.

## Commit boundary

Step 6 consists of documentation-only changes in the nctl and nintent submodules, the parent
README, the completed `p3/plan.md` checklist, and this report. No commit was created. Per the
plan's suggested commit order, the nctl and nintent documentation commits land first, followed by
the parent repository's submodule-pointer bump (nintent → `ca25bb8`, nctl → current) and
documentation/report commit.
