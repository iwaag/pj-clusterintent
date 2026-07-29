# Phase 2 Step 3 Report — Local Gates and Deployment Handoff

## Result

Complete. The endpoint and contract-test commits are locally complete and all
Phase 2 pre-deployment gates pass. The first deployment is intentionally not
started: the local Nautobot image installs nintent from GitHub, so the user
must push the committed nintent revision before a rebuilt image can contain it.

## Gates

| Gate | Result |
|---|---|
| nintent Django-free | 127 passed, 14 expected skips |
| Nautobot runtime clean | scratch `test_nautobot` DB dropped/recreated; staged-source migration check passed (`No changes detected`) |
| nctl ordinary | 987 passed |

The focused staged runtime endpoint contract gate also passed: 5 cases.

## Commits awaiting push

- `af81386 Add desired state batch endpoint`
- `504e8a1 Test desired state batch endpoint`

After those nintent commits are pushed, Step 4 will back up the local scratch
database, rebuild and migrate the Nautobot image, then run only synthetic-row
live acceptance and `nctl drift --json`.
