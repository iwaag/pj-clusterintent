# P2 Step 5 — Split Braindump transport, operations, and presentation

Status: partially complete.

`braindump_client.py` now owns the REST write endpoints and their existing
HTTP-status-to-code translations. `braindump_errors.py` owns the unchanged
code-carrying error vocabulary; no error code, message, or detail shape changed.
`braindump.py` uses the transport client for its operations and retains the
input validation, confirmation, race recovery, and record mapping. The CLI now
imports its seven builders and renderers from `braindump_render.py`, whose
single `_build()` helper is the error-to-envelope translation and closes a
created client on every non-token-error path.

Focused Braindump/CLI/current-consumer tests passed (`86 passed`), followed by
the nctl ordinary suite (`970 passed in 5.75s`) and a clean whitespace check.
The confirmation, authorship, destructive-confirmation, and exit-code cases
are included in those focused and CLI suites.

This step is deliberately not marked complete: the old builder/renderer
definitions remain in `braindump.py` as currently unused duplicate code. They
must be removed, and the Braindump tests split by ownership, before the Step 5
gate can be claimed. No external state changed.
