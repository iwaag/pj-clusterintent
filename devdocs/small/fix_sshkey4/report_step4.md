# Report — Step 4: repair nodeutils project reproducibility

Date: 2026-07-22
Scope: `nodeutils` (submodule)
Status: **complete**

## Goal (plan.md Step 4 / outstanding problem #5)

`nodeutils/pyproject.toml` declared project version `0.2.0` while the
editable `nodeutils` package in `nodeutils/uv.lock` still said `0.1.0`.
Running the previously-documented test command
(`uv run --project nodeutils --with pytest pytest -q nodeutils/tests`,
per `fix_sshkey3/report_verification.md`) updated the tracked lockfile on
every run (pytest wasn't a real dependency, only an ephemeral `--with`
overlay uv still had to resolve and, it turned out, write back), so
verification was not reproducible from a clean checkout.

## Changes

### `nodeutils/pyproject.toml`

Added `"pytest>=8"` to `[dependency-groups] dev`, alongside the existing
`build`/`ruff` entries.

### `nodeutils/uv.lock`

Regenerated with the repository's installed `uv` (`uv 0.11.24`, Homebrew)
via `uv lock --project nodeutils`. The diff:

- the editable `nodeutils` package entry now reads `version = "0.2.0"`
  (was `0.1.0`), matching `pyproject.toml`;
- `pytest` (and its transitive deps `iniconfig`, `pluggy`, `pygments`,
  `exceptiongroup`, `typing-extensions`) are now real, pinned
  `dev`-group entries instead of an unpinned ephemeral overlay.

No other package changed.

## Verification

```
$ uv lock --project nodeutils --check
Resolved 17 packages in 6ms

$ uv run --project nodeutils pytest -q nodeutils/tests
20 passed in 0.03s

$ uv run --project nodeutils ruff check nodeutils
All checks passed!

$ git -C nodeutils status --porcelain
 M pyproject.toml
 M uv.lock
```

The only tracked diffs after running both the standard test and lint
commands are the two files this step intentionally edited — neither
command perturbed the tree further, confirming reproducibility from a
clean checkout. (The two-line status above is the working tree *before*
this step's own commit; it is empty immediately after.)

Both commands were run exactly as documented in `plan.md` Step 4/Step 5,
with no `--with` and from the repository root (`--project nodeutils`
resolves `nodeutils/pyproject.toml`/`uv.lock` regardless of `cwd`; no
root-level `pyproject.toml` exists in this repository).

No developer documentation (`nodeutils/README.md`) names the old
`--with pytest` invocation, so no doc edit was needed here;
`devdocs/small/fix_sshkey3/report_verification.md`'s historical record of
that command is preserved as-is and superseded by a note in Step 7 per
`plan.md`'s instruction not to rewrite historical evidence.

## Step 4 exit criteria

- [x] `pyproject` and lock both identify nodeutils `0.2.0`.
- [x] Standard verification (`pytest`, `ruff`) leaves the submodule clean.

## Handoff to Step 5

nodeutils reproducibility no longer blocks Step 5's full repository
verification run (`uv run --project nodeutils pytest -q nodeutils/tests`
without `--with`, plus `uv lock --project nodeutils --check`, are both
part of that step's required command list).
