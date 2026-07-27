# P0 Step 9 — required searches

Status: complete.

- The prescribed 29-term search produced 4,482 classified matches: 2,338 retained contracts, 1,446 historical comments, 454 duplicated implementations, and 244 layering-violation inputs. `search-classification.tsv` retains repository/file/line/context/current consumer for each.
- `structure-asserting-tests.tsv` identifies 72 nctl test modules with import/patch structure coupling and assigns later-phase contract-test re-ownership; P0 performs no rename.
- Implementation-encoded test names, including `test_reconcile_executor.py`, are proposed to become contract-owned only when their behavior moves; the real multi-round convergence tests retain their single end-to-end identity.
