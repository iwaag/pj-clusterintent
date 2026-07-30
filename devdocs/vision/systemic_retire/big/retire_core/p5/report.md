# Retire core Phase 5 report — end-to-end verification and documentation

Status: **complete** (2026-07-30).

## Control-loop proof

The automated contract now covers the negative-intent safety boundary as well as the pure
disposition and handler paths. `nctl/tests/test_reconcile_executor.py` verifies that a successful
`destroy_compute_instance` is retained as `mutated=true` when the following complete observation
fails: the observation action is recorded as failed, the round has side effects, and the executor
returns `observation_failed` rather than a convergence claim. Together with the existing real
drift/planner disposition cases and the destroy handler's pinned-result cases, this covers:

```text
present -> retired + desired_presence=absent -> destroy required
        -> one pinned destroy -> complete observation records absent -> converged
```

It also preserves the required failure branch:

```text
destroyed -> incomplete/failing observation -> retained partial-progress evidence,
not convergence and not an automatic second destroy
```

## Designated disposable-LXC acceptance

The designated fixture is the already-consumed disposable LXC `agfixture` (VMID `109` on
`aghub`). No replacement was created and no second destruction was attempted: recreating it solely
to repeat a destructive acceptance would violate the narrow one-shot fixture boundary.

The durable evidence was re-read in this phase:

| Evidence | Verified fact |
|---|---|
| `01KYRQS6N4X9NV1V71JZAM27BP` / `01KYRQS75JW285QVYXX453M5CY` | ordinary and `--allow-destroy` dry plans each carried the same one pinned destroy; neither mutated. |
| `01KYRQS7TWDN6H316EX2PNR9KG` | `--yes` without capability refused with `destroy_capability_not_enabled`. |
| `01KYRR92T751HFE65AYTCPGPS0` | the planned destroy ran once against `agfixture`; its durable result records `mutated=true`, followed by successful `aghub` observation/ingest. The then-current controller artifact was unreadable after the irreversible command, so that action truthfully reported failure rather than false success. |
| `01KYRRCZRCAQGMB4SAEHG49ZH8` | a fresh complete control-node observation and ingest converged, recording the retained VM as `proxmox_presence=absent`. |
| `01KYRREJYGVQKAF84PEE2M0YYS` | repeat enabled reconcile planned zero actions and therefore performed no second destroy. Its existing informational presentation remains `manual_intervention_required`; the scoped removal state is still converged and no actuation is repeated. |

The artifact-ownership defect exposed by the one-shot run was fixed before this phase
(`ansible_agdev 99a3b2c`): the result artifact is controller-owned. The current handler and
Ansible conformance test require that boundary, while the original operation remains truthful
historical evidence of the mutation and its recovery observation.

## Gates

| Gate | Result |
|---|---|
| nctl ordinary | 1006 passed |
| nintent Django-free | 127 passed, 10 expected skips |
| nauto ordinary | 112 passed |
| nodeutils ordinary | 54 passed |
| Ansible helper ordinary | 4 passed |
| compute conformance | 1 passed |
| Ansible conformance | 3 passed |
| OpenSSH conformance | 2 passed |
| Nautobot runtime reuse | 181 passed |
| Nautobot runtime clean | migration check and 181 passed |
| test-strategy measurement | nctl 1006; nintent 127; nauto 112; nodeutils 54; Ansible helper 4; runtime 181 |

The Nautobot runtime gates emitted the three pre-existing `models.W045` RawSQL check warnings;
they did not skip cases or fail the gates.

## Operator documentation

The root README and `nctl/README.md` now describe the current removal workflow: user confirmation
is transcribed through the canonical Desired writer as `retired + desired_presence=absent`; a dry
plan is reviewed; only `--allow-destroy --yes` can execute the pinned LXC action; normal
observation/ingest proves absence; and retained Desired/Actual/Braindump records are not pruned.
The systemic-retirement overview and discussion now identify this narrow LXC path as complete
instead of describing canonical Desired retirement or LXC destruction as unimplemented.

## Remaining non-goals

No Braindump text or supersession status executes anything. This phase adds no pruning, scheduling,
retention policy, QEMU destruction, physical-machine destruction, generic provider disposal, or
deletion of Braindump, Desired, VirtualMachine, or Device records.
