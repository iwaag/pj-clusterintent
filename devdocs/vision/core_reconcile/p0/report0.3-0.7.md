# Phase 0 Report — Steps 0.3–0.7 (Nautobot client, envelope/events, `status`, tests)

Date: 2026-07-14. Continues from [report0.1-0.2.md](report0.1-0.2.md) (scaffolding + config).
This commit completes [plan.md](plan.md) Steps 0.3 through 0.7 — the rest of Phase 0 — in one
unit, since building `status` end to end required the envelope/event modules regardless of the
suggested commit split, and stopping midway would have left an untestable half-wired command.

## What was built

- `src/nctl_core/output.py` (Step 0.4) — `Envelope[T]` pydantic model (`schema`/`generated_at`/
  `ok`/`data`/`errors`), `EnvelopeError`, and `emit(envelope, json_mode, render_text)`. `schema` is
  aliased from the field `schema_name` to avoid colliding with pydantic's own `.schema()`.
- `src/nctl_core/events.py` (Step 0.5) — `OperationLog` writing JSONL to
  `<log_dir>/<operation_id>.jsonl`, plus a dependency-free ULID generator (Crockford base32, no
  new package needed). Write failures warn once to stderr and never raise.
- `docs/output-format.md`, `docs/event-log.md` — the specs the plan asked for, written against the
  actual implementation rather than up front.
- `src/nctl_core/nautobot.py` (Step 0.3) — `NautobotClient` wrapping httpx; `graphql()` for future
  phases; `ping()` hits `/api/status/` (auth + real version string) and, if the intent-catalog app
  is installed, probes `/api/plugins/intent-catalog/nodes/?limit=1`. Typed errors:
  `NautobotConnectionError`, `NautobotAuthError`, `NautobotGraphQLError`.
  - Deviation from plan: the plan's Step 0.3 sketch says "GET `/api/` (version, authenticated)" —
    but `/api/` only lists API namespaces, it carries no version field. `/api/status/` does
    (`nautobot-version`, `nautobot-apps`), so `ping()` uses that single endpoint for both checks
    instead.
- `src/nctl_core/dumps.py` (Step 0.3) — `load_dump()` (hard-requires
  `schema_version == "nodeutils.inventory.v1"`, supports both `.json` and `.yaml`/`.yml` via a new
  `pyyaml` dependency) and `scan_dumps()` (one bad file collects an error string, doesn't abort the
  scan).
- `src/nctl_core/status.py` (Step 0.6) — `build_status()` assembles `StatusData` (nautobot / dumps
  / submodules), each check independently degrading into an `EnvelopeError` rather than aborting;
  `render_status_text()` for the human view. Submodule state comes from parsing
  `git submodule status` prefixes (`-`/`+`/`U`/clean) plus a `git status --porcelain` dirtiness
  check per submodule (clean → "modified" if the working tree is dirty).
- `src/nctl_core/cli/main.py` — `status` now calls `build_status()` + `emit()` and exits
  `0`/`1` based on `envelope.ok`, replacing the Step-0.1 stub.
- Tests (Step 0.7): 46 tests across `test_output.py`, `test_events.py`, `test_nautobot.py`
  (respx-mocked: ok / unauth / connection-refused / GraphQL errors), `test_dumps.py` (valid, wrong
  schema_version, malformed, YAML, mixed-valid-dir scan), `test_status.py` (real git repos with an
  actual submodule to exercise clean/modified/uninitialized parsing; `build_status()` wired with a
  monkeypatched `NautobotClient` to verify independent degradation; a golden-shape assertion on the
  serialized envelope's top-level and `data` keys), `test_cli_status.py` (CliRunner, exit codes,
  text-vs-JSON rendering).

## A real bug found and fixed via live testing

Manually running `NAUTOBOT_TOKEN=wrong uv run nctl status` against the local dev Nautobot
(`http://localhost:8000`, see `.local/localenv_memo.md`) surfaced a gap the unit tests hadn't
covered: `ping()` returns a normal `NautobotInfo(authenticated=False)` on a 401/403 rather than
raising, so `_check_nautobot()` only ever produced an `EnvelopeError` on connection failure — an
auth failure silently left `ok: true`. Fixed by having `_check_nautobot()` also emit a
`nautobot_unauthenticated` error when `info.authenticated` is `False`, and added
`test_build_status_not_ok_when_nautobot_unauthenticated` to cover it.

## Verification

- `uv run pytest` — 46 passed.
- Live against local dev Nautobot (real token from `.local/localenv_memo.md`, real
  `/var/lib/nodeutils/inventory.json`, real submodules in this repo):
  - `nctl status` / `nctl status --json` — `ok: true`, correct version (`3.1.3`), `intent_catalog:
    true`, one dump host with a real `age_hours`, five submodules correctly classified (`nctl`
    itself showed `modified` during this work, as expected).
  - Bad token → `nautobot_unauthenticated` error, `ok: false`, exit 1.
  - Bad URL (`localhost:9999`) → `nautobot_unreachable` error; dumps check still ran and
    succeeded independently, confirming the "each check degrades independently" requirement.
  - Missing config file → plain stderr error, exit 2, no JSON envelope printed (as designed —
    usage/config errors precede envelope construction).
  - Confirmed `<log_dir>/<operation_id>.jsonl` is written on every run and its `operation_id`
    matches `data.operation_id` in the envelope.

## Deviations from plan

- Nautobot version/auth check uses `/api/status/` instead of `/api/` (see above — `/api/` has no
  version field).
- ULID implementation is hand-rolled instead of adding a `ulid`/`python-ulid` dependency; Step 0.1
  didn't list one and a 15-line Crockford-base32 encoder avoided pulling in a new package for
  something this small.
- `pyyaml` was added as a runtime dependency (not listed in Step 0.1's dependency set) since
  `dumps.py`'s spec explicitly requires reading `.yaml` dumps.
- Combined Steps 0.3 through 0.7 into a single commit rather than following the plan's suggested
  4-commit split (scaffold+config / envelope+events / nautobot+dumps / status+tests) — building
  `status` incrementally against real envelope/event modules was more coherent as one unit, and
  splitting further would have meant committing dead code paths.

## Exit criteria — all met

- [x] `uv run nctl status` and `uv run nctl status --json` work against the local dev Nautobot.
- [x] `status --json` matches the `nctl.status.v1` schema (golden-shape test in `test_status.py`;
  live-verified).
- [x] Envelope and event log formats documented in `nctl/docs/`; `status` emits a real event log.
- [x] All three checks (Nautobot, dumps, submodules) degrade independently with correct `ok`/exit
  codes (live-verified with bad token and bad URL).

Phase 0 is complete. Next per the roadmap is Phase 0-EX1 (expose `nintent` models via Nautobot
GraphQL, switch the intent-catalog probe in `ping()` to GraphQL introspection).
