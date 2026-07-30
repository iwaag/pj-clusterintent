# Proxmox Desired-Intent Usability Fix — Report

Date: 2026-07-30

## Result

Completed the operator-path usability fix without changing the actionable LXC
endpoint contract or adding apply-time validation to dry-run planning.

- Added the one authoritative, copyable LXC desired-state batch to
  `nctl/README.md`. It contains an active container node, one static primary
  endpoint with canonical MAC and mDNS name, and the complete LXC compute
  instance configuration. It also documents preview/commit commands, the
  non-actionable lifecycle exception, and atomic apply-time model validation.
- `nctl desired apply` now catches `DesiredWriteError`. A valid HTTP 409 batch
  artifact is emitted intact as JSON with `--json`; text mode keeps the HTTP
  error and adds the server transaction error plus every reported operation
  conflict reason. Both paths exit nonzero. Invalid or missing artifacts retain
  the previous concise fallback.
- Added nctl CLI tests using the `DesiredStateBatchView` artifact shape.
  They prove the raw JSON artifact is preserved, text output exposes
  `compute_primary_endpoint_missing`, and both failures have exit status 1.
- Added nintent runtime contract coverage for an otherwise valid active LXC
  batch. Omitting its primary endpoint MAC rolls back all three rows and
  reports `compute_primary_endpoint_missing`; including the MAC commits node,
  endpoint, and compute instance atomically.

## Verification

| Command | Result |
| --- | --- |
| `cd nctl && uv run pytest -q --durations=20` | 1017 passed |
| `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests` | 127 passed, 10 expected skips |
| `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb` | 189 passed |
| `git -C nctl diff --check` and `git -C nintent diff --check` | passed |

The runtime gate used the persistent local scratch Nautobot database and
reported only the pre-existing three RawSQL constraint warnings. Its test-only
stage exercised the nintent atomic apply path; no Proxmox, SSH, Ansible, or
external target was contacted.

An initial ordinary nctl invocation from the superproject root collected
unrelated component tests and failed import collection. The documented command
from `nctl/` above completed cleanly and is the verification result.

## agdummy replay

The corrected input was previewed twice, including after the negative replay:

```text
desired_node: create
desired_endpoint: create
desired_compute_instance: create
totals: create=3, conflict=0
transaction: dry_run, committed=false
```

For the negative check, a test-owned copy with only `mac_address` omitted was
submitted with `--yes` to the local scratch API. It exited with HTTP 409 and
displayed:

```text
transaction error: ValidationError: {'__all__': ['compute_primary_endpoint_missing']}
```

The transaction rolled back and the temporary input was deleted. The corrected
`agdummy` intent was not committed; its two replays were read-only previews.
