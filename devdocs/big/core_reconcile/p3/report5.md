# Phase 3 Report — Step 5 (Live verification)

Date: 2026-07-16. Implements [p3/plan.md](plan.md) Step 5.

## Starting state

nctl Steps 1–3 (dashboard renderer, CLI, status write-back client) and nintent Step 4
(`reconciliation_status`/`reconciliation_checked_at` fields, `DesiredService` REST route,
table/detail UI, `dashboard_url` nav link) were already committed and pushed
(`nintent@ca25bb8`, including a `p3s4-fix1` commit not yet mentioned in report4 — "dashboard nav
link must go through a resolvable view"). The dev Nautobot container, however, had **not** been
rebuilt since `p3s4-fix1` landed: it was still running the `p3s4` image, one commit behind.

## Real deployment gap found and fixed

report4 flagged as an unverified risk: whether `nautobot.apps.ui.NavMenuItem.link` accepts a raw
external URL string. Confirmed live that it does **not** — the actual failure mode was more
fundamental than that risk description: `dashboard_redirect` (the resolvable-view fix
`p3s4-fix1` already applied to the source) was not present in the *running* container yet,
because it had never been rebuilt past `p3s4`. Reproduced with:

```
reverse('plugins:nautobot_intent_catalog:dashboard_redirect')
# ERROR: Reverse for 'dashboard_redirect' not found.
```

against the live container, alongside `pip show nautobot-intent-catalog` confirming `0.7.0` was
installed but `grep dashboard urls.py` inside the installed package coming back empty — i.e. the
image was built from a point in nintent's history *before* the fix commit, even though the
version string already said `0.7.0` (the version bump landed in the same `p3s4` commit as the
fields, one commit before the URL fix). Rebuilt without cache and restarted:

```
cd devenv/nautobot && docker compose --env-file ../.env build --no-cache && \
  docker compose --env-file ../.env up -d
```

After the rebuild, `reverse('plugins:nautobot_intent_catalog:dashboard_redirect')` resolved to
`/plugins/intent-catalog/dashboard/`, and requesting it returned `302 Found` with
`Location: http://192.168.1.50/nctl-dashboard/` — the placeholder LAN URL configured in
`devenv/nautobot/nautobot_config.py`'s `PLUGINS_CONFIG`. The fix works as designed once actually
deployed.

## Dashboard vs. live drift baseline

Ran `nctl dashboard --json` against the dev cluster (`NCTL_CONFIG=nctl.toml`, real
`NAUTOBOT_TOKEN`). Result:

- `summary`: `{"unknown": 2, "converged": 3}`; `severity_summary`: `{"error": 2, "warning": 9,
  "info": 0}`. Matches a same-moment `nctl drift --json` run exactly — five node targets, zero
  service targets (the live dataset still has zero `desired_services`, per Phase 2's report1/
  report2 finding; nothing to seed or push for services this run).
- Per-node status: `agdnsmasq` and `aghub` `unknown` (each carries an `error`-severity
  `missing_actual_node` diff, the Step 4 evaluation-matching code for "no actual Device/VM
  candidate could be linked"); `agbach`/`agpc`/`agstudio` `converged` (only `warning`-severity
  `actual_node_not_linked`/`missing_actual_ip_address` diffs, which don't affect status per the
  Step 3 status-derivation rule).
- Opened the generated `index.html` (read directly, no browser available in this environment;
  structurally verified instead — see below) and confirmed:
  - **Tile colors**: `.tile.status-unknown { border-left-color: var(--gray) }` /
    `.tile.status-converged { border-left-color: var(--green) }` present and correctly applied
    per the embedded envelope's `status-<value>` classes on each `<details class="tile ...">` —
    matches Decision 5's green/yellow/red/gray mapping exactly (no `converging`/`drifting`
    targets exist in this dataset to visually confirm those two colors, but the CSS rules for
    all four are present and were exercised structurally in Step 1's unit tests).
  - **Details on click**: each tile is a native `<details>/<summary>` (no custom JS needed for
    expand/collapse); diff `message`, `severity` badge, `code`, and non-empty `desired`/`actual`
    evidence blocks with a `sources:` line render inside. Confirmed the DOM-building code
    (`el()`/`textContent`, never `innerHTML` of payload strings) so hostile diff content can't
    inject markup.
  - **Sources footer**: `fetched_at`, `observed dumps: 1`, zero `observed_errors` — matches the
    live snapshot (one real nodeutils dump, `agstudio.local`, present in the configured
    `dumps_dir`).
  - **Embedded JSON round-trip**: the `<script type="application/json" id="nctl-drift">` block's
    content is byte-for-byte the same envelope `nctl dashboard` also wrote to `drift.json`
    (diffed the two, only the two independently-stamped `generated_at`/`fetched_at` timestamps
    differ, as expected from two separate runs).

## Nautobot write-back confirmed

- GraphQL confirms all five `desired_nodes` carry `reconciliation_status`/
  `reconciliation_checked_at` matching the dashboard run's `generated_at`
  (`2026-07-16T11:10:48.075090+00:00`) after a push (`status_push.updated: 5`, `failed: 0`).
- Rendered `DesiredNodeTable` server-side for `agbach` via `nautobot-server shell`: the
  `reconciliation_status` column renders `<span class="label label-success">Converged</span>` —
  confirms the Step 4 badge color mapping (green for converged) actually renders as Bootstrap
  markup, not just that the field holds the right string.
- Rendered `DesiredNodeView.get_extra_context()` for `agbach`: returns
  `{"dashboard_url": "http://192.168.1.50/nctl-dashboard/"}`, and the installed detail template
  (`desirednode.html`) contains the "(view dashboard)" anchor conditional on `dashboard_url`
  right next to the reconciliation-status row, and a `reconciliation_checked_at` row — confirmed
  by grepping the installed template inside the container post-rebuild, not just the source
  tree.
- `nctl status --json` stayed `ok: true` throughout (before and after the rebuild): Nautobot
  reachable/authenticated, `intent_graphql: true`, all five submodules `clean` — the plan's "the
  GraphQL types gained fields, lost nothing" claim holds live.

## Failure-path spot checks

- **Nautobot stopped** (`docker compose stop nautobot nautobot-worker nautobot-scheduler`, then
  `nctl dashboard --out <tmp>`): envelope came back `ok: false` with one `nautobot_fetch_failed`
  error (`Connection refused`); exit code `1`. The written `index.html` still rendered a full
  page: the embedded envelope carries `"ok":false` and the error, and the page's error panel
  (`#errors[hidden]` in the skeleton) is unhidden and populated by the client-side
  `renderErrors()` function — confirmed by inspecting the generated file directly, not just the
  JSON envelope. Restarted Nautobot and waited for the healthy check before continuing.
- **Bogus token via `--from`** (`NAUTOBOT_TOKEN=<invalid>` with `--from` pointing at the drift
  payload from the earlier successful run): envelope came back `ok: true`, exit code `0` — page
  generation and write succeeded — while `status_push` reported `failed: 5`, `updated: 0`, with
  one `"HTTP 403: {\"detail\":\"Invalid token\"}"` string per node target. Confirms Decision 4
  precisely: push failures degrade to per-target warnings inside `status_push`, never block
  generation or flip the top-level `ok`. Nothing in Nautobot was corrupted by this run (all five
  PATCH attempts were rejected before any write), confirmed by re-running with a valid token
  immediately after and seeing `updated: 5` again with the same values as before the bad-token
  run.

## Payload gap found (recorded, not fixed this phase)

Diff `message` strings produced by the Step 4 evaluation-matching comparators are currently
terse restatements of the code (e.g. `"agdnsmasq: missing_actual_node"`,
`"agbach: actual_node_not_linked"`) rather than the fuller prose the roadmap's Phase 2 vision
describes ("desired has a DHCP reservation, but actual has no MAC registered"-style sentences).
The dashboard renders whatever `message` it's given faithfully — this is a Phase 2 comparator
quality gap, not a Phase 3 rendering bug, and per Decision 1 the correct fix is an **additive**
improvement to the comparators that produce these messages, not a dashboard-side workaround.
Noting it here as the plan's Step 5 instructs ("any payload gaps found → additive
`nctl.drift.v1` follow-ups"); not in this phase's scope to fix.

## Cleanup

Removed all scratch output directories created during the failure-path checks
(`/tmp/nctl-p3-fail-out`, `/tmp/nctl-p3-badtoken-out`). Left the dev cluster in a clean,
verified-healthy state: final `nctl dashboard` run with a valid token shows `ok: true`,
`status_push: {updated: 5, failed: 0}`, and `nctl status` shows `ok: true` with all five
submodules clean. `uv run pytest -q` in nctl — **263 passed**, no regressions from the
container rebuild/restart cycle or the live poking done in this step.

## Exit criteria status

- [x] `nctl dashboard` generates a single self-contained static HTML file (plus `drift.json`)
  from the `nctl.drift.v1` payload: whole-cluster tiles colored per Decision 5 with drift
  details in prose (terse prose — see the payload gap above) on click, plus summary header and
  sources footer — verified live against the dev cluster.
- [x] The dashboard is regenerated by the routine command itself (drift computation + render in
  one `nctl dashboard` run) and re-renders a saved payload via `--from` (used for the bogus-token
  check above); `nctl drift` itself issued no write during any of this step's runs.
- [x] nintent 0.7.0 is deployed **and now actually running the `p3s4-fix1` commit** (the gap this
  step found and closed): reconciliation status fields + checked-at on DesiredNode/DesiredService
  written by nctl over REST, and a working configurable dashboard link (nav item + per-object
  "(view dashboard)" link), both confirmed live post-rebuild.
- [x] Status push degrades to warnings without blocking generation (bogus-token check), and the
  pushed values match the live payload after a clean `nctl dashboard` run (GraphQL + table
  rendering both confirmed).
- [x] `uv run pytest` passes in nctl (263 passed); nintent's loader-only suite was already
  confirmed in report4 (92 passed, DB/API-backed behavior only verifiable live, which this step
  did).

## Commit boundary

This step is verification-only plus one infrastructure action (the container rebuild/restart) —
no nctl or nintent source changed. The parent repo's `nintent` submodule pointer should now be
bumped to `ca25bb8` (already the case locally, per report4) and this report committed alongside
it, closing out the plan's "Steps 5–6" commit group's verification half.

**Not done yet, deliberately left for Step 6:**

- nctl README/docs: `nctl dashboard` usage, `[dashboard]` config, `nctl.dashboard.v1` schema,
  the "run `nctl dashboard`, not `nctl drift`" regeneration guidance, color/status legend.
- nintent README(s): the two derived-cache fields and `dashboard_url` setting.
- Parent README: add `nctl dashboard` to the normal entry points.
- Final `p3/report6.md` closing out the phase.

Next: Step 6 — docs and report closeout.
