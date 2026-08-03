# Easier Next Time 2 — Phase 2 Plan

Status: planned 2026-08-04. Implements Phase 2 of
[`../roadmap.md`](../roadmap.md): the `nctl workflow-episode` command group
against the WorkflowEpisode API deployed in Phase 1.

## Goal and exit criteria

Add a `workflow-episode` command group to nctl: `create / list / show /
select / resolve / dismiss`, plus per-namespace writes (at minimum
`assessment` and `resolution`; `report` / `references` if it costs nothing
extra). **The key requirement:** given nothing but an episode ID, an agent can
fetch the full report / assessment / references content via
`nctl workflow-episode show <id> --json`.

Exit (fixed by the roadmap):

- The nctl ordinary suite passes (`cd nctl && uv run pytest -q --durations=20`).
- A full create → list → show → select → resolve round trip is smoke-verified
  against the live scratch Nautobot.

## Fixed constraints (everything else is implementer's discretion)

1. No secrets or tokens printed or written anywhere; the token comes from
   `nctl.toml` → `.local/secrets` resolution as usual.
2. No transcript or ops-evidence bodies pushed into `raw_data`; `references`
   values are stable IDs, not local paths.
3. No dry-run and no plan/apply boundary. These are plain CRUD commands,
   neither destructive nor external-reaching (README_DEV minimal dry-run
   policy; roadmap "Useful facts"). Confirmation prompts are unnecessary —
   note that even `braindump complete` has none; only `review-delete` gates.
4. Happy path only: if Nautobot is down, the command reports the connection
   error envelope and exits nonzero. No offline drafts, no retries.
5. No backward compatibility concerns — there is no old `workflow-episode`
   surface to preserve.

Command/option names, JSON input style, envelope field naming, and text-render
layout are free choices; fix them by what reads best against the Braindump
precedent.

## Phase 1 API surface (what you are calling)

Base: `/api/plugins/intent-catalog/workflow-episodes/`. Verified live in
[`../p1/report_step6.md`](../p1/report_step6.md).

- `POST /` — create. Body: `title` + optional `raw_data` (top-level keys
  restricted to `schema_version` / `report` / `assessment` / `references` /
  `resolution`; each namespace a dict, `schema_version` an int). Status always
  starts `candidate`; client-supplied status is not accepted.
- `GET /?status=<s>` — list with status filter. `GET /<id>/` — detail,
  includes full `raw_data`.
- `POST /<id>/select|resolve|dismiss/` — forward-only transitions
  (`candidate → selected → resolved|dismissed`, `candidate → dismissed`).
  Violation returns **409** with body like
  `{"status": ["invalid_transition: status: cannot transition from 'resolved' to 'selected'"]}`.
- `POST /<id>/report|assessment|references|resolution/` — replaces that one
  namespace wholesale, other namespaces untouched. Invalid namespace on any
  write returns **400** `{"raw_data": ["unknown_namespace: ..."]}`.
- `http_method_names = ["get", "post", "head", "options"]` — **no PATCH, no
  DELETE.** An episode cannot be deleted via the API; a mis-created one can
  only be `dismiss`ed. Design your smoke tests knowing every row you create
  is permanent (dismiss it at the end, or title it clearly as smoke).

A live seed already exists: episode `6569864c-8914-4e2e-9368-b7e04c64ac74`
("Live smoke: WorkflowEpisode p1 step6", status `resolved`, all of
report/assessment/references populated) — useful for `show`/`list` smoke
without creating anything.

## Precedent map (shortest path: copy the Braindump module family)

Braindump is the same species and its nctl side is the direct template. In
`nctl/src/nctl_core/`:

| concern | precedent |
|---|---|
| REST transport | `braindump_client.py` — thin functions per endpoint, raise typed errors on non-2xx, map 409 to a dedicated "ineligible" error |
| core ops + typed records | `braindump.py` — pydantic record/data models per command, input resolution (`--body` vs `--file`), UUID validation (`invalid_braindump_id`) |
| envelope build + text render | `braindump_render.py` — `nctl.braindump.<cmd>.v1` schema strings, one `_build()` helper catching `BraindumpError` / `NautobotError` into `EnvelopeError`s |
| error catalog | `braindump_errors.py` — error-code factory functions |
| CLI wiring | `cli/main.py:641` onward — a `typer.Typer` sub-app, `--json` option, `_braindump_exit_code()` mapping error codes to exit codes |
| tests | `tests/test_braindump.py`, `test_cli_braindump.py`, `test_cli_surface.py` (register the new group there), `test_sources_braindump.py` |

Suggested new files mirror that: `workflow_episode_client.py`,
`workflow_episode.py`, `workflow_episode_render.py`,
`workflow_episode_errors.py` (or fold errors into one module if small),
envelope schemas `nctl.workflow_episode.<cmd>.v1`.

## Design hints (advice, not requirements)

- **Read transport: plain REST GET is enough.** Braindump reads go through
  GraphQL (`sources/braindump.py`) because its list view computes derived
  fields (attention, review joins). WorkflowEpisode has no joins and
  `raw_data` is one JSON field the REST detail already returns verbatim —
  GraphQL adds a query, a source module, and JSONField-scalar handling for
  zero gain here. Recommended: REST for both reads and writes. (The model
  does have `@extras_features("graphql")` if you ever want it.)
- **`show --json` is the agent contract.** Put the episode's `raw_data` into
  the envelope untouched (don't re-shape report/assessment/references into
  bespoke fields — sub-structure is deliberately free-form and will evolve).
  Text render can pretty-print the four namespaces as sections, mirroring the
  GUI detail page.
- **`list`**: default to `status in {candidate, selected}` to match the GUI's
  default filter, with `--status` (repeatable or `--all`) to widen. Columns:
  id, title, status, created, last_updated.
- **`create`**: `--title` required; take the optional initial `report` /
  `references` as JSON via `--report` / `--references` (string) and/or
  `--file` for a whole `raw_data` document — pick one style and keep it
  consistent with the namespace-write commands. Braindump's
  `resolve_text_input` (arg vs `--file`, UTF-8 strict, conflict error) is
  reusable as-is for the file path.
- **Namespace writes**: one command or one `--namespace` flag — either is
  fine. If you add only `assessment` / `resolution` now (the two the
  improvement loop needs after creation), say so in the report; `report` /
  `references` writes can wait for a real need.
- **Transitions**: `select` / `resolve` / `dismiss` as top-level subcommands,
  each POSTing its action endpoint. Map HTTP 409 to a distinct error code
  (e.g. `workflow_episode_transition_ineligible`) so scripts can branch,
  mirroring `braindump_complete_ineligible` and its exit-code mapping.
- **Write confirmation**: braindump refetches after every write and raises a
  confirmation-mismatch error before reporting `changed=True`. That rigor is
  optional here — the API returns the updated object in the 2xx response
  body, and trusting it is acceptable in this experimental environment. A
  cheap middle ground: parse the response body into the record and echo the
  resulting status, no second round trip.
- **Error codes worth having**: invalid ID (pre-validate UUID like
  `invalid_braindump_id` does — saves a confusing 404), not found, transition
  ineligible (409), validation rejected (400), write rejected (other non-2xx),
  connection/token errors (free via the `_build` pattern).

## Test plan

All in the nctl ordinary suite; no nintent change is expected, so no Nautobot
runtime gate is needed. (If you do find a Phase 1 API gap that forces an
nintent change, that change re-enters the nintent flow: runtime gate, commit,
user pushes, `docker compose build --no-cache` with SHA check — see
`.local/localenv_memo.md`. Flag it early rather than working around it.)

- **Tier A**: each write command issues exactly the right request and reports
  `changed` only on 2xx; 409 on a transition surfaces the ineligible error
  code and nonzero exit; 400 on bad namespace surfaces the validation error.
  Use the existing `httpx`/transport-mocking style from `test_braindump.py`.
- **Tier B**: JSON input parsing (bad JSON, non-dict namespace payload,
  arg/`--file` conflict), UUID validation, status-filter handling.
- **Tier C**: text render smoke for list/show (sections appear, no crash on
  an episode with empty namespaces); `--json` output is valid JSON matching
  the envelope schema; `test_cli_surface.py` updated for the new group.

## Steps

One report + one commit per step (`p2/report_stepN.md`), in nctl (submodule
pointer bump in the superproject per step or at the end — your call). No step
here is live/hard-to-reverse: scratch-Nautobot rows are not a pause point
(`.local/localenv_memo.md`), and nctl runs from local source via
`uv run --project nctl`, so no deploy cycle exists. Ask the user to push nctl
at the end of the phase.

### Step 1 — Transport + reads (`list` / `show`)

Client module, record models, envelope/render for `list` and `show`, CLI
wiring, tests. This step alone satisfies the "agent fetches everything from
an ID" requirement — get it right first.

### Step 2 — Writes (`create`, namespace writes)

Create with initial report/references, namespace-write command(s), input
resolution, tests.

### Step 3 — Transitions (`select` / `resolve` / `dismiss`) + full suite

Transition commands, 409 mapping, exit codes; full nctl ordinary suite green;
record the test count in the report.

### Step 4 — Live smoke + phase report

Against the scratch Nautobot (token via config, never printed):

1. `show` + `list` on the Phase 1 seed episode (`6569864c-...`, resolved —
   use `--status`/`--all` since the default filter hides it).
2. Full round trip on a fresh episode: `create` (title marks it as smoke) →
   `list` (appears under default filter) → `show --json` (report/references
   present) → `select` → namespace write to `assessment` → `resolve` →
   `show --json` (all four transitions of state visible, other namespaces
   byte-identical).
3. One forbidden transition (`select` on the now-resolved episode) and one
   invalid namespace payload — expect the mapped error codes and nonzero
   exits.
4. The smoke episode stays (no DELETE); note its ID in the report.

Phase report states the two exit criteria with evidence, README_DEV
completion language.

## Out of scope for this phase

agentdocs `workflow-improvement` session type and policy.md/README_DEV
rewrite (Phase 3), the real improvement cycle (Phase 4), column promotion,
any import of `.local/evidence/workflow-episodes/`, GUI changes.
