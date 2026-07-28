# P2 Step 6 — Apply the error taxonomy

Status: complete.

All E2 Braindump, lifecycle, and session subclasses were folded into their
retained base types (`BraindumpError`, `LifecycleError`, and `SessionError`).
Named factories preserve each public code, message, and detail payload;
callers now assert the retained type and its code rather than an internal
subclass. No error type was deleted, and no caller distinguishes one of the
folded errors by Python type.

The focused operation and CLI surface tests passed (`94 passed`), including
confirmation, authorship, destructive-confirmation, and usage-versus-failure
paths. The nctl ordinary suite passed (`970 passed in 5.83s`) and
`git diff --check` was clean. The complete code-producing input surface
remains covered by the existing CLI envelope tests; no envelope code, message,
detail shape, or exit-code mapping changed.

The private taxonomy evidence remains under
`.local/nctl-modularization/p2/20260728T120000Z/`; its final disposition is
58 declared taxonomy rows plus `Envelope`, with 23 E2 subclass types folded,
their three base types retained, and zero deletions. No external state changed.
