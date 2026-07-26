# Test Strategy Phase 1 — Step 2 Report: Stopped During Local-Source Disposable Harness Check

Parent: [plan.md](plan.md), Step 2.

Status: **`blocked`** — the required safety boundary was crossed; human direction is required.

## Work prepared but not accepted

The nintent worktree has uncommitted test-only changes prepared for the planned consolidation:

- added `test_model_contract.py` for the two desired models' current ORM and migration-state
  contract;
- added the two removed GraphQL field cases to `test_api_contract.py`;
- added dashboard route/path and table/filter/settings absence rows to
  `test_ui_contract.py`; and
- removed the historical `test_remove_unused_surfaces.py` module from the working tree.

The Django-free local discovery command completed with `15 run, 14 skipped`; it cannot validate
the runtime contracts. No nintent commit or superproject pointer update has been made, and these
uncommitted changes must not be treated as an accepted Step 2 result.

## Stop finding

To prove that the disposable runner imported the local checkout, I used the intended one-shot
Compose command family with a read-only bind mount and `PYTHONPATH`. The service's normal
entrypoint ran before the supplied import command. Its output showed that it:

1. performed its standard migration/job-refresh startup work against the configured Nautobot
   connection; and
2. sent the Nautobot installation metric to a public Nautobot endpoint.

The requested import proof itself succeeded: `nautobot_intent_catalog.__file__` resolved under
the read-only local checkout mount. However, that does not make the command an acceptable
disposable test harness. It violated the plan's explicit no-public-network and no-live-mutation
boundaries before any Phase 1 runtime tests were run.

I did not run the changed tests in that harness, run a live Job/REST/SSH/Ansible action, rebuild
or restart the long-running services, or commit the nintent changes.

## Required decision

Choose one of the following before continuation:

1. authorize a separate, bounded cleanup/assessment of the startup side effects and a safe
   runner design that bypasses the service entrypoint and blocks installation metrics; or
2. direct me to discard the uncommitted nintent test changes and end Phase 1 as blocked.

The current plan cannot truthfully reach `complete` after this public-network/live-startup
deviation without an explicit revised safety decision.
