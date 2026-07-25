# Phase 2 Step 0 — Recapture boundary, environment evidence, and static baseline

Parent: [plan.md](plan.md) — Step 0.

This step recaptures the environment state, revision baseline, static search matches, GraphQL digests, test suite baseline, and disposable test environment definition prior to making any Phase 2 code edits.

## 1. Execution environment and revision baseline

- **Execution Timestamp:** 2026-07-26T00:15:00+09:00
- **Evidence Directory:** `.local/interface-contract/p2/20260726_001500/` (permissions 0700)
- **Git Status:** Clean (0 unstaged / 0 staged / 0 untracked in superproject and all submodules)

### Submodule Revision Tuple

| Submodule | Revision | Branch | Status |
|---|---|---|---|
| superproject | `cedba743d0fa83446b451d8a0c0cc70d76a48577` | `main` | Clean |
| `nintent` | `185479d2217f7530249a3cc5e9187e11fd9a295f` | `main` | Clean |
| `nctl` | `ebe8a1d5b731adaea4241fb2c3ccbcaca54302a9` | `main` | Clean |
| `nauto` | `2635e648469d6e6bad87af113f7427b878b0a387` | `main` | Clean |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | `main` | Clean |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | `main` | Clean |

## 2. Test Suite Baseline

- **`nintent` Unit Tests:** 222 passed in 0.041s (`cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests`)
- **`nctl` Test Suite:** 954 passed in 6.36s (`cd nctl && uv run pytest`)

## 3. Pinned GraphQL Query SHA-256 Digests

The normalized SHA-256 digests of the four pinned GraphQL queries in `nctl_core` match Phase 0 report7 exactly:

| Query | Source File | SHA-256 Digest | Match Phase 0 |
|---|---|---|---|
| `DESIRED_QUERY` | `nctl/src/nctl_core/sources/desired.py` | `e6e34a9f6dd1a561f6a446e7ac464dc62b9566c989d96df0d3561cbfded17357` | YES |
| `ACTUAL_QUERY` | `nctl/src/nctl_core/sources/actual.py` | `f2b8808491d5cc80f5cbe65cfc05841bb18d82ad13cdbeee3f50a97c234e879a` | YES |
| `LIST_QUERY` | `nctl/src/nctl_core/sources/braindump.py` | `e276ec2a13eebe7fc0e416e9ff08d785bb6a122d14a006e020afa0f048f2c19d` | YES |
| `SHOW_QUERY` | `nctl/src/nctl_core/sources/braindump.py` | `003a5ffec0e00c7abb0a8a6e85af355abb2a34599bc845ff35e9cbd7b4aebe70` | YES |

## 4. Static Code & Document Search Baseline

- **`fields = "__all__"` in `nintent`:** 7 occurrences in `api/serializers.py`
- **GraphQL-registered `@extras_features("graphql")` models in `nintent`:** 12 models in `models.py` (including `IntentSource`)
- **REST ViewSets in `nintent`:** 7 registered ViewSets in `api/views.py` / `api/urls.py`
- **`rest_get` in `nctl`:**
  - 1 domain caller: `nctl_core.reconcile.ledger:_get_node` (to be replaced by GraphQL in Phase 2)
  - 3 Job protocol callers: `nctl_core.jobs:fetch_job_result`, `fetch_job_artifact`, `get_job_by_name` (retained protocol)
  - 1 helper definition: `nctl_core.nautobot:NautobotClient.rest_get`

## 5. Live Environment Safety Attestation

- No live Jobs are running or pending in Nautobot.
- Live database and container endpoints (`http://localhost:8000/`) will NOT be mutated or accessed during Phase 2 development and testing.
- A dedicated disposable testing environment config will be isolated for all integration and runtime checks.

## 6. Gate Status

Step 0 gate passed cleanly. Baseline verified and evidence captured. Proceeding to Step 1.
