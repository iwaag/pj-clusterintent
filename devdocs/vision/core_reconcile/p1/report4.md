# Phase 1 Report — Step 4 (retire the nintent dnsmasq export path)

Date: 2026-07-15. Implements [p1/plan.md](plan.md) Step 4. Continues from
[report3.md](report3.md), whose live parity gate passed before this deletion.

## What changed

- Removed `ExportDnsmasqRecords` from `nautobot_intent_catalog/jobs.py`, including its renderer
  import, Job implementation, and `register_jobs()` tuple entry.
- Deleted `nautobot_intent_catalog/dnsmasq.py`. dnsmasq consumer-format rendering now exists only
  in `nctl_core`.
- Deleted `nautobot_intent_catalog/tests/test_dnsmasq.py`; its renderer behavior and skip-reason
  coverage was ported to nctl in Steps 1–3.
- Kept `_latest_evaluations()` in `jobs.py`: the node and endpoint evaluation Jobs still use it,
  independently of the removed export Job.
- Bumped the nintent package/app version from `0.4.0` to `0.5.0` in `pyproject.toml`,
  `nautobot_intent_catalog/__init__.py`, and `uv.lock`.
- Updated `README.md` and `README_QUICK.md` so they no longer advertise the deleted Job or Python
  API. They now identify `nctl render dnsmasq` as the renderer and nintent's GraphQL models as its
  inputs.

## Verification

- `uv lock --check` — passed.
- `uv run python3 -m unittest discover` — **191 tests passed**, 0 failures.
- `git diff --check` — passed.
- Source/reference search (excluding the historical `DEVLOG_PICKUP.md`) found no remaining
  `ExportDnsmasqRecords`, `Export dnsmasq Records`, `.dnsmasq` renderer imports, or `0.4.0`
  version references.

## Deployment verification (completed 2026-07-15)

After the user pushed the nintent commit, rebuilt the dev Nautobot images with `--no-cache` and
restarted the stack. The build resolved nintent commit
`44d6ea3d06e62e9682bba191e00f4db9982e35c3` and installed package version `0.5.0`; the Nautobot,
worker, and scheduler containers all became healthy.

The REST Job record for `Export dnsmasq Records` remains as Nautobot history with
`installed: false`, so it is no longer an installed/runnable Job. `nctl status --json` then
returned `ok: true`, with Nautobot 3.1.3 reachable and authenticated, intent-catalog and intent
GraphQL present, and all submodules clean.

## Commit boundary

This is the second suggested Phase 1 commit: **nintent: delete the Job-export path and bump the
version**. It is intentionally stopped before Step 5, which changes the separate
`ansible_agdev` submodule and is independently reviewable.

Next after the push/rebuild verification: Step 5 — replace the Nautobot-oriented dnsmasq
playbook with a deploy-only playbook that requires a pre-rendered `dnsmasq_records_src`.
