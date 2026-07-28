# P5 runtime-gate problem report

Status: unresolved environment blocker.

P5 Step 5 requires the local Nautobot runtime gate in both `--keepdb` and
`--clean` modes, including named runtime proofs such as
`post-mutation-evidence` and `prose-authority`. The wrapper can stage exact
local sources and complete `makemigrations --check --dry-run`, but a named
Django test cannot initialize its test-owned `test_nautobot` database.

## Observed failure

The first named test setup failed while creating the test database because
`virtualization_vminterface.role_id` already existed. After a `--clean`
retry, it failed on the already-existing `dcim_interface.vrf_id`. These occur
before the test body runs, so no runtime proof or case count is available.

## Ruled out

- This is not retained test-database state: `test_nautobot` was dropped with
  `WITH (FORCE)` before a clean retry.
- This is not a P5 source change: the failure occurs in Nautobot core migration
  setup before staged nintent/nauto/nctl/nodeutils test code executes.
- The local image was rebuilt without cache from the pinned
  `networktocode/nautobot:3.1.3-py3.12` Dockerfile, recreating Nautobot,
  worker, and scheduler. Its pinned nintent commit verification passed, but a
  clean named-gate retry still stopped before the test body.

## Required follow-up

Do not manually drop duplicate columns or fake `django_migrations` rows: that
would invalidate migration coverage. Decide separately whether to align the
pinned Nautobot runtime/version to a known-good migration set or to repair the
runtime-gate test-database setup. P5 must remain blocked until one path is
chosen and the full runtime matrix can run.

