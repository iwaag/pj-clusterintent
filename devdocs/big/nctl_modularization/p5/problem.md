# P5 runtime-gate problem report

Status: resolved. The cause was the gate wrapper, not Nautobot's migration set.

## What was reported

P5 Step 5 stopped because a named runtime proof could not initialize its
test-owned `test_nautobot` database. The first attempt failed on an
already-existing `virtualization_vminterface.role_id`; a `--clean` retry failed
on an already-existing `dcim_interface.vrf_id`. The report proposed choosing
between re-pinning the Nautobot runtime and repairing the runtime-gate
test-database setup.

## What the migration set actually does

Neither choice was needed. The pinned `networktocode/nautobot:3.1.3-py3.12`
migration set builds a database from empty without any duplicate column:

- a scratch database migrated with `nautobot-server migrate` applied all 476
  migrations cleanly;
- a test database created from empty by the installed App ran 288 cases;
- the local `nintent` checkout has no migration difference from the pinned
  installed commit `84ac0b1` — the only difference is one test module; and
- after the wrapper fix below, `--clean` dropped `test_nautobot`, rebuilt all
  476 migrations, and ran the named proof.

The duplicate-column failure is therefore not reproducible and not a property of
the migration graph. No data reset, no runtime re-pin, and no manual
`django_migrations` repair was required, and none was performed.

## The two wrapper defects

1. **A failed run kept its half-built database.** `--clean` dropped
   `test_nautobot` but still passed `--keepdb` to the test runner, so any run
   that was interrupted or that failed during database setup left the partially
   migrated database in place. Every later run inherited it and stopped on an
   already-existing column — at a later column each time, because each attempt
   advanced further. That is exactly the reported `role_id` then `vrf_id`
   progression, and it is why dropping the database once did not end it.
2. **A gate that collected zero cases exited `0`.** The named runtime tests are
   defined only when `nctl_core` imports, and Django exits `0` after
   `NO TESTS RAN`. A mislabelled or unstaged run therefore reported success
   without a case count — the reported "completed the migration check but gave
   no test case count" symptom.

## The fix

`devtests/test_strategy/run_nautobot_runtime_gate.sh` now:

- drops the test-owned database whenever the run does not reach its test body,
  including on interrupt and timeout, while keeping a database whose setup
  completed even if cases failed;
- parses the runner's `Ran N tests` line, fails with exit `3` when no case ran,
  and prints `runtime gate result mode=… label=… cases=N`; and
- refuses to start when another `nautobot-server test` is already running in the
  Nautobot container, since all runs share the one `test_nautobot`.

`README_DEV.md` records the matching prerequisite, evidence expectation, and
lesson. Step 5 resumed on this wrapper; `p5/report5.md` carries its result.
