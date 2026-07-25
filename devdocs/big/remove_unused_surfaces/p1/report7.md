# Phase 1 Step 7 — Prove a clean plain installation

Parent: [plan.md](plan.md), Step 7.

Private evidence directory: `.local/remove-unused-surfaces/p1/20260725-152425/`.

## Procedure

Used a fresh `mktemp -d` directory (not the developer `.venv`), removed after recording results:

1. `uv build --wheel --out-dir "$TMPDIR/dist"` — built `nctl-0.0.1-py3-none-any.whl` from the
   edited source.
2. `uv venv "$TMPDIR/venv"` — fresh virtual environment, Python 3.14.2.
3. `uv pip install --python "$TMPDIR/venv/bin/python" "$TMPDIR/dist/nctl-0.0.1-py3-none-any.whl"`
   — installed only the wheel and its **core** runtime dependencies; no dev group, no extra.
4. `"$TMPDIR/venv/bin/nctl" --help`.
5. Imported `nctl_core.cli.main`, `nctl_core.events`, `nctl_core.operations_index`,
   `nctl_core.ops_render` from that environment's interpreter.
6. `importlib.util.find_spec()` for `fastapi`, `starlette`, `uvicorn`, `websockets`, `httptools`,
   `uvloop`, `watchfiles`, and both `python_dotenv`/`dotenv` import-name spellings.
7. Inspected the built wheel's file list for any `nctl_core/serve/*` asset.
8. Removed only the validated `$TMPDIR` path (matched against a `mktemp`-shaped pattern before
   deletion) once results were recorded.

## Results

- Install: exactly **20 packages** resolved and installed
  (`annotated-doc`, `annotated-types`, `anyio`, `certifi`, `h11`, `httpcore`, `httpx`, `idna`,
  `markdown-it-py`, `mdurl`, `nctl`, `pydantic`, `pydantic-core`, `pygments`, `pyyaml`, `rich`,
  `shellingham`, `typer`, `typing-extensions`, `typing-inspection`) — no FastAPI/Starlette/
  uvicorn/WebSocket package anywhere in the list.
- `nctl --help`: exit 0, lists the same 12 retained commands (including `dashboard`), no `serve`.
- Retained imports (`nctl_core.cli.main`, `nctl_core.events`, `nctl_core.operations_index`,
  `nctl_core.ops_render`): all succeeded from the isolated interpreter.
- `importlib.util.find_spec()`: `fastapi`, `starlette`, `uvicorn`, `websockets`, `httptools`,
  `uvloop`, `watchfiles`, `python_dotenv`, `dotenv` all report **absent**.
- Wheel file list (`python3 -m zipfile -l`): no `nctl_core/serve/` entry of any kind (checked with
  an exact-path pattern, not a `serve` substring, to avoid the same false-positive
  `nctl_core/sources/observed.py` match Step 1's original CLI-surface test hit).

## Gate

The plain installed console script and every retained import work with no server package present
anywhere in the isolated environment or the wheel itself. Proceeding to Step 8.
