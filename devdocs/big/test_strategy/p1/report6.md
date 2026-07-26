# Test Strategy Phase 1 — Step 6 Report: Component and Scratch Runtime Verification

Parent: [plan.md](plan.md), Step 6.

Status: **`complete`**.

## Results

- `cd nctl && uv run pytest -q --durations=20`: **966 passed** in 5.87 s.
- `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests`:
  **227 run, 14 skipped**, passed in 0.033 s.
- The final clean scratch App gate used the existing Nautobot container directly (no Compose
  entrypoint) with a copied local nintent checkout first on `PYTHONPATH`:
  `nautobot-server test nautobot_intent_catalog --keepdb -v 1` found **279 tests** and exited
  **0** against `test_nautobot`.

The Django-initialized proof resolved the package and all three modified canonical test modules
from that local temporary checkout. The scratch application database remained separately named
`nautobot`.

## Scratch ownership

A previous temporary source copy contained root-owned files and could not be removed by the normal
container user. The full gate therefore used a new exact `/tmp` path. After the import proof,
both exact Phase 1 source-copy paths were removed as container root and their absence verified.
`test_nautobot` remains as the declared reusable named test database; no application database,
external target, service startup path, or public telemetry path was used by the runtime command.
