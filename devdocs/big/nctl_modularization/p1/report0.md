# P1 Step 0 — Freeze the tuple and create private evidence

Status: complete.

Evidence root: `.local/nctl-modularization/p1/20260728T000000Z/`.

## Frozen input and environment

All Section 4.1 governing inputs were re-read, including the Phase 0 decision/evidence,
the behavior manifest, compatibility policy, local scratch-environment policy, and the latest
VM Phase 3 report. The VM report confirms that compute remains unseeded; no VM realization work
was started during this step.

The six repository worktrees were clean at capture time. The frozen revisions are:

| repository | revision |
|---|---|
| superproject | `55166ffaeca2aa9ce6c899179fa458dcad661a67` |
| nctl | `55f1a4bad9baffc998203a5003eee1cbcc005462` |
| nintent | `055496d3e28d2ea6536f660a3ae352b8594279f3` |
| nauto | `6dab422a725a2e2e4e24e98079e992d1111c0ef1` |
| nodeutils | `775ed7fad5110a96186a737147b87d3bf450ced2` |
| ansible_agdev | `66b31c89986d1b2ecfa187a72209d8bd96838fd4` |

The local Nautobot scratch stack was healthy. Its image label identifies installed nintent
`e8732f17ae35d8c72d4d593e8d7311bd234fc0bf`; this remains deliberately behind the local nintent
checkout and is deployment evidence for Step 9, not a reason to alter the image now. The applied
Intent Catalog migrations run through `0016_remove_reconciliation_dashboard_surfaces`.
Read-only ORM counts were `DesiredComputePlatform=0` and `DesiredComputeInstance=0`.

## Reproduced baseline gates

| gate | result |
|---|---|
| `nctl: uv run pytest -q --durations=20` | 967 passed in 5.83s |
| `nintent: python3 -m unittest discover -s nautobot_intent_catalog/tests` | 227 run, 14 skipped, pass |

Both results match the Phase 0 baseline. Raw command records, sanitized logs, revision data,
container status, migration state, and row counts are retained only in the private evidence root.
No write, deployment, reconcile, collection, ingest, Ansible, SSH, Proxmox, or seed action was
performed.

## Gate verdict

Complete: one clean frozen tuple was captured; compute is still unseeded; and both repeated fast
baseline gates reproduced their Phase 0 counts.
