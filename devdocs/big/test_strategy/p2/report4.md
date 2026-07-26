# Test Strategy Phase 2 — Step 4 Report: Read-Only UI Presentation Disposition

Parent: [plan.md](plan.md), Step 4.

Status: **`complete`**.

## Disposition

The nintent UI suite already separates the required authority and presentation boundaries, so no
tests were merged or removed:

- `test_ui_contract.py` retains the full route, permission, and no-POST authority manifest:
  22 retained routes, 39 removed mutation routes, literal-path 404 checks, and absence of table
  action/dashboard surfaces.
- Its runtime matrix retains one permission-backed list/detail rendering proof for every retained
  model.
- `test_braindump.py` remains independent because its Braindump/Alignment Review panels have
  distinct reviewed/unreviewed, escaping, inert-prose, and no-mutation-control semantics.
- `test_templates.py` retains the small object-template existence manifest.

Replacing these runtime method and permission checks with source inspection, snapshots, or a
shared label table would lose the distinct authority or template semantics. The private
`ui-render-manifest.tsv` records the owners and disposition.

The ordinary nintent fast suite passed: **227 run, 14 skipped**. No framework-owned code changed,
so this read-only disposition did not require a local-source Nautobot runtime gate.
