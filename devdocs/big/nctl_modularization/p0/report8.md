# P0 Step 8 — error taxonomy

Status: complete.

- AST inventory: 57 declared `*Error` classes; additionally `Envelope` is recorded as the non-`Error` public envelope type. `error-taxonomy.tsv` has 58 rows with declaration, raise/catch sites, caller behavior, preserved code boundary, classification, fold target, and phase.
- Classification counts: 22 load-bearing, 29 message-only, 7 unreachable. Every message-only type has its immediate retained base as its fold target; no current envelope code is changed by this P0 classification.
- The fail-closed SSH distinctions remain load-bearing: missing/store-read failure, corrupt store, unenrolled, unreachable, and mismatched key are not collapsed.
- Roadmap correction: `braindump.py` has 18 `BraindumpError`-named classes (base plus 17 subclasses), not 19 subclasses. The `^class .*Error` count remains 57.
