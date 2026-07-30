# Retire core Phase 4 report

Status: **complete**. Steps 0–6 are recorded in `report0.md` through `report6.md`.

Phase 4 added the per-run `--allow-destroy` capability, terminal refusal when absent, a pinned one-LXC destroy handler and playbook, SSH enrollment gating, and controller-owned result evidence. The approved live run destroyed only `agfixture` VMID `109` on `aghub`; a fresh complete observation/ingest recorded it absent, and the repeated enabled reconcile did not plan or execute a second destroy.

The final gates passed: nctl 1005, compute conformance 1, and Ansible conformance 3. See `report5.md` for operation evidence and `report6.md` for limitations and Phase 5 handoff.
