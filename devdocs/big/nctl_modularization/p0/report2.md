# P0 Step 2 — structure and suite baseline

Status: complete.

- `nctl` tracked Python measurement: 68 `src/nctl_core` files / 17,783 lines; 72 `tests` files / 19,685 lines. The source total and lines match the roadmap; its 73-test-file count was corrected to 72 in the parent roadmap in this commit.
- Per-package totals and exact tracked file lists: `source-files.tsv`, `test-files.tsv`, and `package-totals.tsv` in `.local/nctl-modularization/p0/20260727T141512Z/`.
- `cd nctl && uv run pytest --collect-only -q`: 967 cases, 0.19 s.
- `cd nctl && uv run pytest -q --durations=20`: 967 passed, 0 skipped, 0 xfailed, 5.71 s; the slowest test was `test_git_submodule_status_uninitialized` (0.33 s).
- `compute_contract.py` and direct nintent consumer measurements are retained in `nintent-compute-consumers.tsv`.
- No source, test, fixture, or golden file changed.
