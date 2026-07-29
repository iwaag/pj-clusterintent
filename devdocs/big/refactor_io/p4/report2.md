# Phase 4 Step 2 Report — Remove the seed and build path

## Result

Complete. `nauto/seed/intent_sources.yaml` was deleted in nauto commit
`3bd1820`. The Nautobot Dockerfile no longer copies or hashes a desired-state
file, while its nintent/nauto revision pins and `build_info.json` remain
unchanged. The nauto and nctl operator documents now direct desired-state
changes to the private batch document and `nctl desired apply`; nintent's
description now refers to a Git-held desired-state file generically rather
than preserving the deleted filename.

## Verification

- The removed path is absent from the nauto checkout.
- The Docker Compose build definition parses.
- A working-tree scan for `intent_sources` and
  `/opt/nautobot/intent_sources`, excluding `devdocs/`, finds only
  `nauto/tests/test_seed_home_cluster_ownership.py`. Its assertions are kept:
  they prove the prerequisite seed Job does not own desired state.

## Component commits

- nauto: `3bd1820 Remove desired state seed from Git`
- nctl: `7c64438 Document private desired-state batch workflow`
- nintent documentation: `fdc76c9 Clarify desired state is not Git-held`
