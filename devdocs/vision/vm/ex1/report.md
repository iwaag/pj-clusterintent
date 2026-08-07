# vm/ex1 report — iso storage evidence + first live QEMU creation

Date: 2026-08-07
Status: **complete** — all five plan steps exercised and passed; live exit
criterion of `devdocs/big/vm/roadmap.md` Phase 6 met. This supersedes the
"implemented, not deployed" status of [`../report.md`](../report.md) for the
creation path's live proof.

Per-step evidence: [report1.md](report1.md) [report2.md](report2.md)
[report3.md](report3.md) [report4.md](report4.md) [report5.md](report5.md).

## What happened

1. **nodeutils** (`ae26207`): storage-content collection generalized to the
   closed set `{vztmpl, iso}` — one listing fetch per storage, one scope per
   (storage, content_type); `LIMIT_VZTMPL_ITEMS_PER_STORAGE` renamed to
   `LIMIT_CONTENT_ITEMS_PER_STORAGE`; per-scope failure isolation kept.
   91 pytest cases green.
2. **nauto** (`60ce8a2`): `_validate_storage_scope` accepts the same closed
   set; unknown types still reject as `invalid_content_type`. 113 unittest
   cases green; cross-component Nautobot runtime gate `cases=258` green.
3. **Live evidence**: Ubuntu 24.04.4 live-server ISO (sha256-verified twice,
   locally and on aghub) placed in aghub's `local` storage via the approved
   Ansible path; both submodules pushed and deployed (Nautobot Git Repository
   re-synced to `60ce8a2`; observation deployed pinned `ae26207`).
   `nctl reconcile aghub --refresh-observation --yes` converged; cluster
   evidence now holds complete `aghub:local:iso` and `aghub:local:vztmpl`
   scopes side by side.
4. **First live QEMU create**: desired triple for `agautolab1` applied
   (preview create:3/conflict:0, then `--yes`); dry plan showed the single
   pinned `create_compute_instance` with `guest_type: qemu`, vmid 109; the
   approved apply converged in two rounds — created + started, post-create
   observation linked the VirtualMachine, repeat dry reconcile plans **zero
   actions**.
5. **Handoff**: VM is running the installer ISO; OS install, SSH keys, and
   Claude login are the user's manual work per the autodev Step 5 decision.

## Structural outcome

The one structural gap named by the plan — iso storage-content evidence was
never collected — is closed end to end (collector → ingest validation →
ledger → create gate), and the previously implemented kind-aware QEMU create
path is proven live through the full control loop with no repeated action.
