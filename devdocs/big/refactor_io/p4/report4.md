# Phase 4 Step 4 Report — Private-file operator workflow

## Result

Complete. The root README now gives the required preview/apply and standard-
input commands for `nctl desired apply`. It explicitly states the ownership
boundary: database = current desired state, batch REST = only writer, GraphQL
= reader, and Git = framework and policy. The nauto README points to that
workflow from its desired-state section.

`.local/localenv_memo.md` now records that `.local/desired-state.yaml` is an
ignored operator input, not a backup, and that PostgreSQL dumps under
`.local/backups/` are the recovery material. This local-environment document
is ignored and deliberately not committed.

## Verification

`nctl desired apply --help` confirms `-f -` accepts standard input and that
`--yes` is the explicit atomic-commit switch. Git confirms both the private
document and its Step 1 backup are ignored.
