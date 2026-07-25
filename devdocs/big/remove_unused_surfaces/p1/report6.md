# Phase 1 Step 6 — Run focused verification and deletion searches

Parent: [plan.md](plan.md), Step 6.

Private evidence directory: `.local/remove-unused-surfaces/p1/20260725-152425/`.

## Focused verification

```bash
uv run pytest -q \
  tests/test_cli_surface.py tests/test_config.py tests/test_events.py \
  tests/test_operations_index.py tests/test_cli_ops.py \
  tests/test_compatibility_snapshots.py tests/test_cli_dashboard.py \
  tests/test_dashboard_render.py
```

**72 passed.**

## Deletion searches

Ran the plan's exact token list against tracked runtime source, tests, package metadata, example
config, and current nctl docs (`src/`, `tests/`, `pyproject.toml`, `uv.lock`, `example.nctl.toml`,
`README.md`, `docs/`):

```text
nctl serve, nctl_core.serve, nctl.serve.v1, ServeConfig, NCTL_SERVE_TOKEN, /api/v1, /api/v1/ws,
FastAPI, Starlette, uvicorn, WebSocket, subscribe(, Subscriber, _SubscriberEntry, _subscribers,
_publish(
```

First pass found one match: `tests/test_compatibility_snapshots.py:5`'s module docstring still
said `"...breaking change under an unchanged \`v1\`/\`/api/v1\` name."` — a leftover generic
example phrase from when the file also pinned the HTTP surface, no longer accurate now that
`/api/v1` doesn't exist. Fixed by rewording to `` `v1` `` only (no behavior change, docstring
only). Re-ran the full token list after the fix: **zero matches** across every token in the
in-scope tree.

A structural import trace (`grep -rn "import serve\|from nctl_core\.serve\|from \.\.serve\|from
\.serve" src/ tests/`) also found zero matches, confirming the string-search result isn't hiding
an aliased or indirect import.

## Expected out-of-scope matches (repository-wide, informational)

A broader repository grep for `nctl serve`/`nctl_core.serve`/`nctl.serve.v1` outside `nctl/` finds
matches only in: this roadmap and its own `p0`/`p1` reports, the parent `roadmap.md`, the
refactoring vision, and historical/other-initiative docs (`devdocs/big/braindump/`,
`devdocs/big/core_reconcile/`, `devdocs/big/vm/p3/plan.md`, `devdocs/small/fix_sshkey/plan.md`)
plus the root `README.md`. All of these are outside Phase 1's own scope (plan §5.4 names exactly
five nctl-internal doc files to edit in this phase; root `README.md` and cross-initiative
history/roadmap docs are Phase 4 work per the parent roadmap's "Deployment and current
documentation to edit" list). None is a Phase 1 regression.

Confirmed the explicitly keep-shared `ansible_agdev/api` FastAPI webhook
(`ansible_agdev/api/app/main.py`, `pyproject.toml`, `uv.lock`, `README.md`) is present and
untouched — it is a separate, unrelated FastAPI service, not `nctl_core.serve`.

## Full suite

`uv run pytest -q`: **980 passed**, unchanged from Step 3/4/5.

## Gate

Every active-scope match is either absent or a documented Phase 2/3/4 reference; no
server/subscriber runtime residue remains anywhere in `nctl/`. Proceeding to Step 7.
