# Phase 1 Step 4 — Remove dependencies and regenerate the lock

Parent: [plan.md](plan.md), Step 4.

Private evidence directory: `.local/remove-unused-surfaces/p1/20260725-152425/`.

## Edits

`pyproject.toml`:

- removed `[project.optional-dependencies].serve` (`fastapi>=0.115`, `uvicorn[standard]>=0.34`)
  entirely; the `serve` extra no longer exists;
- removed `fastapi>=0.115` and `uvicorn[standard]>=0.34` from `[dependency-groups].dev`, leaving
  `pytest>=8.0` and `respx>=0.21`.

## Lock regeneration

`uv lock` (no `--upgrade` flag) resolved 26 packages (was 35) and reported only removals:

```text
Removed click v8.4.2
Removed fastapi v0.139.2
Removed httptools v0.8.0
Removed python-dotenv v1.2.2
Removed starlette v1.3.1
Removed uvicorn v0.51.0
Removed uvloop v0.22.1
Removed watchfiles v1.2.0
Removed websockets v16.1
```

`git diff uv.lock` is a pure-deletion diff: **378 lines removed, 0 added** across
`pyproject.toml`/`uv.lock` combined. No existing package (including `typer`, `httpx`, `pydantic`,
`pyyaml`, `pytest`, `respx`) changed version — confirmed by inspecting the full diff, not just the
`uv lock` summary. `click` disappearing along with the FastAPI/uvicorn/Starlette chain shows it was
reachable only through that chain in this lock graph, not through `typer` (current `typer v0.26.8`
has no `click` edge in the regenerated tree).

`uv lock --check`: passes (resolved 26 packages, no diff against `pyproject.toml`).

## Reachability proof

`uv tree --locked` (full, in evidence) shows exactly two top-level runtime dependencies
(`httpx`, `pydantic`, `pyyaml`, `typer`) plus two dev-group packages (`pytest`, `respx`), with no
FastAPI/Starlette/uvicorn/WebSocket edge anywhere in the graph.

Per-package reverse-tree checks:

- `uv tree --locked --invert --package httpx`: reachable via `nctl` (core Nautobot client) and
  `respx` (dev group) — both retained owners, confirmed unchanged from the plan's §4.4 expectation.
- `uv tree --locked --invert --package respx`: reachable via `nctl` (dev group) only.
- `uv tree --locked --invert --package fastapi` / `click` / `uvicorn`: empty (package absent from
  the lock).

No suspected server-only transitive package (`fastapi`, `starlette`, `uvicorn`, `websockets`,
`httptools`, `uvloop`, `watchfiles`, `python-dotenv`) remains reachable.

## Environment proof

`uv sync` uninstalled exactly the 9 removed packages (`click`, `fastapi`, `httptools`,
`python-dotenv`, `starlette`, `uvicorn`, `uvloop`, `watchfiles`, `websockets`) from the developer
`.venv` and installed nothing new besides the rebuilt `nctl` wheel itself.
`uv run pytest -q`: **980 passed** with those 9 packages actually absent from the environment (not
merely absent from the lock file) — the strongest available proof short of the isolated-install
test reserved for Step 7.

## Gate

Metadata and lock contain no server dependency root and no unexplained server-only transitive
package; `httpx`/`respx` remain with their retained owners; the lock diff is pure reachability
removal with zero unrelated version changes. Proceeding to Step 5.
