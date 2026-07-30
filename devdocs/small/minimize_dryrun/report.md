# Minimize dry-run — Report

## Completed

- `nctl apply dnsmasq` without `--yes` is now a pure `plan` operation. It
  renders and persists the dnsmasq artifact and resolves `dnsmasq_server` from
  the generated YAML inventory, but does not invoke SSH, `ansible-inventory`,
  or Ansible check/diff. `--yes` owns inventory expansion, SSH preflight,
  daemon setup, and deployment.
- Removed dnsmasq dry-run-only events and Ansible error codes. The retained
  execution path reports `ansible_setup_failed` / `ansible_apply_failed`.
- Removed the `dry_run` Job input and rollback branches from `Ingest Nodeutils
  Inventory` and `Seed Home Cluster`. Both Jobs now have one normal persistence
  path. The ingest summary schema no longer publishes `dry_run`.
- Updated nctl observation submission and summary validation for the new
  ingest Job contract, along with CLI help and operator documentation.
- Replaced paired dnsmasq preview/apply tests with proof that a plan resolves
  targets without touching SSH or Ansible; retained apply tests assert the
  exact execution path and scope.

## Verification

| Command | Result |
| --- | --- |
| `cd nctl && uv run pytest -q --durations=20` | 1015 passed |
| `cd nauto && python3 -m unittest discover -s tests` | 110 passed |
| `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb` | 185 passed |
| `git -C nctl diff --check` and `git -C nauto diff --check` | passed |

The runtime gate used the persistent local scratch Nautobot database as
documented. It reported the existing three RawSQL constraint warnings, with no
test failures.

An initial broad pytest invocation from the superproject root collected
unrelated component tests with incompatible import paths; it was not used as
verification. The documented per-component commands above completed cleanly.
