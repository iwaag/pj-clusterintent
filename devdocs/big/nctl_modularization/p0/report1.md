# P0 Step 1 — installed, migration, and VM state

Status: complete.

- Read-only Docker inspection: web, worker, and scheduler are `running` and `healthy`, all using image `sha256:a4c20f6ad4b3d3d8b14cd483e8fb23c78943dd4701cef259f449cb1b065ad94a` and package version `0.9.0`.
- Installed nintent commit is consistently `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf`; it differs from the frozen local worktree `055496d3e28d2ea6536f660a3ae352b8594279f3`. This is a Phase 1 matched-version rollout input, not a defect repaired in P0.
- Applied nintent migration head: `0016_remove_reconciliation_dashboard_surfaces`.
- Read-only counts: `DesiredComputePlatform=0`, `DesiredComputeInstance=0`; compute is unseeded and inert.
- VM Phase 3 has no completion report after `report3.7.md`; its coordinated deployment remains explicitly unstarted.
- Sanitized evidence: `installed-components.tsv`, `migrations.txt`, and `compute-row-counts.tsv` under the Step 0 evidence root.
