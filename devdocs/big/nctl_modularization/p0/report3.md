# P0 Step 3 — import graph and layering

Status: complete.

- AST extraction found 231 intra-`nctl_core` import edges across 68 modules; `import-edges.tsv` retains importer, imported module, symbols, and module/deferred placement.
- `module-coupling.tsv` records fan-in/fan-out. Highest measured fan-in: `config` 18, `nautobot` 17, `output` 15, and `sources.snapshot` 12. The graph includes no deferred intra-core imports.
- Provisional layer audit found 10 true downward imports: eight from `drift.comparators` into transport/orchestration collaborators, one from `production.derivation` into `sources.actual`, and one from `sources.desired` into `nautobot`. CLI-to-operation imports are normal adapter delegation, not a presentation-layer violation.
- `reconcile.executor` has 25 direct intra-core dependencies (not the roadmap's orientation count of 20): 10 orchestration/evidence dependencies, 9 action-execution dependencies, and 6 source/production/drift dependencies needed to coordinate the current flow. The exact import list is retained in `import-edges.tsv` and drives Steps 4 and 7.
- No code changed; the layer assignments are explicitly provisional and the responsibility decisions follow in Step 4.
