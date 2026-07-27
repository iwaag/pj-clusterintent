# P0 Step 4 — responsibility map

Status: complete.

- `module-responsibilities.tsv` covers all 19 modules over 300 lines, every required audit-area module, and all `*_render.py` modules; it records layers, consumers, import coupling, operational-value owner, decision, boundary, prevention case, phase, and admission check.
- Decisions: 6 `split`, 27 `keep`, 3 `defer`, 0 `merge`. Each split has independent change reasons and named owners/consumers.
- Material split decisions: executor/action execution; desired transport/compute contract/source-issue policy; drift resource evaluation/shared candidate rules; Braindump transport/operations/presentation; production composition/route resolution; production validation/canonical digest.
- The seven known ambiguities are resolved in private `ambiguities.md`; error and test-name results are explicitly cross-referenced to their owning later P0 steps.
- `dnsmasq` family ownership is retained as-is; `production.derivation.py` is a documented `keep` finding rather than a size-driven split.
