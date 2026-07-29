# Phase 4 Step 5 Report — Live rebuild handoff

## Status

Awaiting operator push before the live rebuild. This is the plan's explicit
pause point: the Dockerfile must be pinned to a pushed nauto revision before a
no-cache build can prove the image no longer contains the deleted seed.

## Pre-live verification

| Gate | Result |
|---|---|
| nauto ordinary | 110 passed |
| nintent Django-free | 124 passed, 10 expected runtime skips |
| nctl ordinary | 987 passed |
| compute conformance | 1 passed |
| Ansible conformance | 2 passed |

## Commits to push

- nauto: `3bd1820 Remove desired state seed from Git`
- nctl: `7c64438 Document private desired-state batch workflow` and
  `95afdd8 Sanitize desired-state test fixtures`
- nintent: `fdc76c9 Clarify desired state is not Git-held` and
  `d388049 Use synthetic compute conformance endpoint`
- superproject: `482241c Complete refactor IO phase 4 step 4`

After those commits are pushed, Step 5 will bump `NAUTO_COMMIT`, rebuild the
scratch image without cache, run `post_upgrade`, prove the deleted file is
absent, and re-check GraphQL, drift, and the all-unchanged private-document
dry run.
