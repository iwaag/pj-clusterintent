# Test Strategy Phase 3 — Step 3 Report: Real Ansible Boundary Gate

Parent: [plan.md](plan.md), Step 3.

Status: **`complete`**.

## Implemented gate

Added [test_ansible_conformance.py](../../../../devtests/test_strategy/test_ansible_conformance.py).
It generates a temporary two-host YAML inventory with synthetic DesiredNode UUIDs, explicit
loopback routes, non-default port metadata, UUID-derived aliases, and nctl-owned strict SSH
arguments. It validates the JSON produced by installed `ansible-inventory --list` and `--host`,
then passes the parsed host variables through nctl's real inventory-trust validator.

The fixture playbook—not the inventory—uses `connection: local`. A real `ansible-playbook` run
with `--check --limit p3-ansible-a` reports only that host and writes no marker; the apply run
with the same limit writes only that host's marker. The sibling is absent from output and remains
unmodified in both cases.

Every forbidden SSH policy override is injected one at a time and is rejected by nctl before the
test can start a playbook. The associated focused composer/trust suite remains the owner of the
full policy diagnostic matrix.

## Verification and cleanup

```text
uv run --project nctl pytest -q devtests/test_strategy/test_ansible_conformance.py  1 passed
cd nctl && uv run pytest -q tests/test_production_composer.py tests/test_inventory_trust.py  80 passed
```

All inventory, playbook, marker, and output state was under pytest's temporary directory and was
removed. No SSH connection, real inventory, Ansible mutation outside the fixture directory, or
external target was contacted.
