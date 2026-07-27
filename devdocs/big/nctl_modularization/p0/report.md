# NCTL modularization P0 final report

Status: complete.

Evidence root: `.local/nctl-modularization/p0/20260727T141512Z/`.

The frozen nctl/nintent tuple was preserved: nctl `55f1a4bad9baffc998203a5003eee1cbcc005462`, nintent `055496d3e28d2ea6536f660a3ae352b8594279f3`; their tracked Python digest set is unchanged. The local Nautobot image remains on installed nintent `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf`, migrations are through `0016_remove_reconciliation_dashboard_surfaces`, and desired compute platform/instance counts remain zero.

Measured nctl structure is 68 source files / 17,783 lines, 72 test files / 19,685 lines, and 967 collected tests. The parent roadmap was corrected for the 72-file count and duplicated `PROVENANCE_*`; the plan was corrected for 27 manifest rows. The responsibility map records 6 splits, 27 keeps, and 3 defers, resolving all seven known ambiguities. The selected compute owner is nintent with generated conformance fixtures; the action seam is a static registered handler interface with executor-owned rounds/evidence.

The error inventory records 57 `*Error` classes plus `Envelope` (22 load-bearing, 29 message-only, 7 unreachable). Search, move, and manifest maps are complete. All ordinary/conformance gates passed; Nautobot runtime clean and reuse modes each passed 290 tests. The runtime measurement completed with 290 runtime cases. Deterministic dnsmasq, hosts-intent, and production artifact bytes/digests are retained in `artifact-baseline.tsv`; no tracked nctl golden/snapshot files exist.

Deviation: after explicit user authorization, `8950837` repaired the runtime gate's detached-result collection without changing test selection, isolation, assertions, or pass/fail semantics. The original Redis reset was resolved by restarting only the local scratch Nautobot services. No external state was mutated.
