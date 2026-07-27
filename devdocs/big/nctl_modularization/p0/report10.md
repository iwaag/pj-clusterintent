# P0 Step 10 — move and manifest impact

Status: complete.

- Six proposed moves map source boundaries to test modules, affected manifest IDs, structure assertions, and required gates in `move-impact.tsv`.
- `manifest-impact.tsv` accounts for every current manifest row. The recounted total is 27, not the plan's planning-time 26; the plan is corrected in this commit.
- `forced-observation-refresh` is flagged as the pre-existing weak row because it names only a module; Phase 3 must replace it with a precise test ID.
- The two real multi-round convergence tests remain indivisible planner/engine/executor tests during the Phase 3 split.
