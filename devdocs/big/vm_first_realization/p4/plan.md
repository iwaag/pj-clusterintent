# First Proxmox Guest Realization — Phase 4 Plan: Create and Start the Guest Once

Parent: [roadmap.md](../roadmap.md) — Phase 4. Predecessors: [p3/plan.md](../p3/plan.md) and
[p3/report0.md](../p3/report0.md) … [report8.md](../p3/report8.md).

## 1. Goal

Phase 3 produced one truthful dry plan and made zero Proxmox calls. Phase 4 runs it exactly once.

```text
current
  agfixture is desired node + static endpoint + compute instance (VMID 109), lifecycle approved
  + one dry plan: create_compute_instance:agfixture, host aghub, pinned pct grammar
  + no Proxmox guest, no realized device, no realized_vm link
  + the create path has zero tests, the playbook result file lands on the wrong host,
    and waiting_for_manual_initial_access does not exist (§3.1-3.3)

to
  one LXC container, VMID 109, created and started exactly once on aghub
  + freshly observed by nodeutils, ingested by nauto, linked as realized_vm
  + the agfixture node target reads waiting_for_manual_initial_access, not no_realized_object
  + a repeat reconcile plans no create, no start, no link
  + unrelated nodes and guests untouched
```

Not in this phase: guest-OS bootstrap (manual, Proxmox console), SSH enrollment of `agfixture`,
QEMU, any mutation of an existing guest, and the fixture disposition (Phase 5 — the operator
confirmed **retain** in p3 Step 1).

## 2. Boundary

This is the roadmap's only irreversible step: a created guest cannot be rolled back. Everything
before the apply gate is ordinary local work — rebuild the image, restart containers, write and
delete scratch rows, run tests, re-render inventories freely. Read-only Proxmox observation and
read-only `pct list`/`pct status` need no approval.

Prohibitions, minimal and complete:

1. **Ask the operator immediately before the apply**, showing the dry plan that will run. One apply.
2. **Create and start only.** No `pct stop|destroy|set|resize|migrate|clone`, no `qm`, no pvesh
   write — in code, in the playbook, in a role, or typed by hand through nctl.
3. **Never create a second guest** to recover from a partial or unidentified first one.
4. **Do not weaken SSH strictness** to reach `aghub` or the new guest.
5. No credentials, vault passwords, or key blobs in reports, artifacts, or tracked files.

Everything else — module layout, test structure, how the result file gets home, commit
granularity, step order, when to rebuild — is the implementer's call.

## 3. Findings that shape the plan

Measured on the tree at superproject `3661e4e`, nctl `d476def`, nauto `1b74d88`, nintent `0eae8a0`,
nodeutils `775ed7f`, ansible_agdev `1eec904`, 2026-07-28.

### 3.1 The create path has no tests

`grep -rl "compute_create\|create_compute_instance\|derive_compute_creations\|create_lxc"` over
`nctl/tests` returns nothing; 80 test files, zero of them reach the preflight, the reconciler, the
handler, or the playbook. p3 report3/report5 describe this coverage, but it is not in the tree —
the 990-case suite passes without exercising a single line of the create path.

Per `README_DEV.md` lesson 1 and the Tier A rule, going live on an untested mutation handler is
exactly the failure mode the test matrix exists to prevent. This lands **before** the apply.

### 3.2 The playbook writes its result file on the wrong host

[`create_lxc.yml:39-43`](../../../../ansible_agdev/playbooks/proxmox/create_lxc.yml#L39-L43) uses
`ansible.builtin.copy` with no `delegate_to`, so `result_path` is written on **aghub**, under a
path that only exists on the control machine
([`compute_create.py:15`](../../../../nctl/src/nctl_core/reconcile/actions/compute_create.py#L15)
builds it under the local operation artifacts). Live, this yields one of two outcomes, both after
`pct create` and `pct start` have already run:

- the remote parent directory does not exist → task fails → `exit_code != 0` → "create playbook
  failed", `mutated=True`; or
- it happens to be creatable → local `result_path.exists()` is False → "create playbook did not
  write a result file", `mutated=True`.

Either way: a real container is created and the operation reports failure. The sibling
[`deploy_dnsmasq_records.yml`](../../../../ansible_agdev/playbooks/dnsmasq/deploy_dnsmasq_records.yml)
already uses `delegate_to: localhost` for exactly this; the fix is one line, but it must be proven
by a test, because the fake runner in Phase 3 never had to transport anything.

### 3.3 `waiting_for_manual_initial_access` does not exist

`grep -r waiting_for_manual_initial_access nctl/` returns nothing. p3 §4.4 specified it; p3 report4
is titled "complete **for dry planning**" and it was not built. Without it, the moment the guest is
created the `agfixture` node target reports `no_realized_object` (ERROR, manual_review) plus a
production-blocking finding — i.e. Phase 4's successful terminal is indistinguishable from an
error, which is the roadmap's stated exit condition 5 and the whole point of the safe stop.

### 3.4 The post-create loop already works, unassisted

Verified by reading the executor: `requires_observation=True` on the create action makes
[`executor.py:539-551`](../../../../nctl/src/nctl_core/reconcile/executor.py#L539-L551) synthesize
one `post_actuation_observation` over `action_host_slugs` (= `["aghub"]`), which runs the nodeutils
collection **and** the nauto ingest Job. The next round's fresh drift then sees VMID 109 in the
Cluster and plans Phase 2's `link_compute_realization`. So one invocation should carry
create → observe → ingest → link. `reconcile.max_rounds` defaults to **3**
([`config.py:85`](../../../../nctl/src/nctl_core/config.py#L85)), which is the expected exact fit —
pass `--max-rounds 4` for headroom, or simply run `nctl reconcile agfixture --yes` a second time,
which is safe by construction (the create is gated on fresh absence).

### 3.5 Privilege and target facts

`become: true` resolves root on `aghub` through `ansible_become_password` from the vault
(`inventories/generated/group_vars/all/main.yml`); the `nodeutils-pvesh-read` sudoers fragment is
NOPASSWD for the read helper only and is deliberately not extended. `aghub` is present in the
generated production inventory (`linux`, `ssh_hosts`) with its HostKeyAlias, so `--limit aghub`
resolves. None of this has been exercised for a `become`-requiring playbook on `aghub` — Step 0
proves it read-only before the apply gate.

## 4. Design

No new architecture. Phase 4 closes three gaps and then runs the plan.

### 4.1 Tests for the create path (§3.1)

Tier A/B coverage of what already exists, at the highest practical layer:

| Case | Proof |
|---|---|
| each §4.2 preflight code (template, storage, bridge, VMID, MAC, IP, endpoint, control node, lifecycle) | only that code fires; the instance is not create-ready |
| create-ready instance | exactly one `compute_create` action, one `compute_instance` target, `host_slugs=["aghub"]`, no dependencies, exact pinned parameters |
| decline branches | existing candidate, existing `realized_vm`, any failure, awaiting manual access → `Fallback`, no action |
| handler happy path | exact `ansible-playbook … --limit aghub --extra-vars <pinned JSON>` argv and the exact `pct create`/`pct start` argv rendered from that JSON |
| parameters drifted between plan and execute | refused **before** the runner is touched |
| non-zero exit / missing result / malformed result / `created!=true` | failed action with `mutated=True` |
| scope | an unrelated guest or node is never named in any command |
| static | no stop/destroy/set/resize/migrate/clone string in the handler, the playbook, or any role it uses |

A fake command runner covers the runner boundary. Playbook rendering is proven against the real
`ansible-playbook` (syntax check plus a localhost run with a stubbed `pct` on `PATH`) so §3.2 cannot
regress — extend the existing Ansible conformance gate rather than inventing a new one.

### 4.2 Result-file transport (§3.2)

`delegate_to: localhost` on the result task (plus whatever makes the parent directory exist) is the
expected fix; `fetch`, or deriving success from parsed runner output, are acceptable alternatives if
either is cleaner. Requirements, not implementation: the handler's local `result_path` exists after
a successful run, its content states `created` and `started`, and a run that creates nothing never
produces it. Keep the VMID-occupied gate (`failed_when: pct_status.rc == 0`) as the execution-time
absence check.

### 4.3 `waiting_for_manual_initial_access` (§3.3)

Implement p3 §4.4 unchanged: a pure predicate, true only when **all four** hold — the compute
instance is linked to an observed guest, that guest is running, the node has no realized device,
and no nodeutils observation exists for it. Then `node_existence` emits
`waiting_for_manual_initial_access` (INFO) instead of `no_realized_object`; the production composer
excludes the node with that reason instead of a blocking code; the create planner refuses to plan
for it. One test per condition showing that dropping it restores `no_realized_object`. Nothing else
is suppressed — the node resumes ordinary evaluation once the operator finishes the console
bootstrap and the node is observed.

### 4.4 Failure handling at the live gate

Decide these before the apply, not during it:

| Outcome | Response |
|---|---|
| playbook fails before `pct create` | ordinary failed action; fix and re-run; nothing was created |
| `pct create` ran, `pct start` or the result step failed | **stop.** Record `mutated=true`, run a read-only observation, report exactly what exists as partial progress. Do not re-apply until the next round's fresh evidence explains it, and never create a second guest |
| created and started, but the refetch cannot identify it | report truthfully, keep the guest, leave the link unwritten, treat it as partial progress (roadmap decision 5) |
| created and linked, but the node target still says `no_realized_object` | §4.3 regression — fix and recompute drift; the guest stays |

An `agfixture` container that exists but is not linked is recoverable in a later round. A second
container at another VMID is not.

### 4.5 Unchanged

The fixture record (p3 Step 1, operator-confirmed); the pinned create grammar; every other diff
code, severity, and message; the dnsmasq render digest (`generate_dnsmasq: false`); nintent, the
compute contract, and its conformance fixture; every pre-existing action.

## 5. Steps

Merge or split freely. Real ordering constraints only: §4.1-4.3 land before the apply; the dry plan
is re-verified immediately before the apply; the apply is one operator-approved invocation.

0. **Baseline and live preconditions** (read-only). Revision tuple, deployed nintent/nauto commits,
   seed checksum, `nctl drift --json`, the three render digests, and the current guest/VMID set.
   Refresh the `aghub` observation if it is stale. Confirm read-only, through the ordinary
   inventory: `aghub` SSH-enrolled and reachable, `become` works, `pct status 109` reports absent,
   the template volid still present, and `192.168.0.9` / `bc:24:11:00:01:09` still unused.
1. **Create-path tests** (§4.1). Gate: nctl ordinary with a stated case count, up from 990.
2. **Result-file transport** (§4.2) with its test, and the Ansible conformance extension proving the
   real playbook renders the exact `pct` argv and lands the result locally.
3. **The manual-access terminal** (§4.3) with its four condition tests.
4. **Re-verify the dry plan.** `nctl reconcile agfixture --json` — one `create_compute_instance`
   action, VMID 109, host `aghub`, the same grammar as p3 Step 8, differing only in timestamps and
   operation ids. A whole-cluster dry plan touches nothing else. Zero Proxmox calls.
5. **The apply gate.** Present the Step 4 plan and the §4.4 failure table to the operator and get
   explicit approval. Then, once: `nctl reconcile agfixture --yes --max-rounds 4`. Capture the
   operation id and the per-round evidence as it goes.
6. **Verify the live transition** from the operation artifacts and fresh reads: `pct create` and
   `pct start` argv recorded and exit 0; the guest observed by nodeutils with VMID 109 and status
   running; the nauto ingest Job result; `realized_vm` linked to the observed VirtualMachine;
   `compute_instance/agfixture` converged; `node/agfixture` at `waiting_for_manual_initial_access`.
7. **Non-repetition and isolation.** Run `nctl reconcile agfixture` again: no create, no start, no
   link. Run a whole-cluster dry plan: `agdnsmasq`, `aghub`, and every other node plan exactly what
   they planned at Step 0. Diff the three render digests against Step 0 — dnsmasq unchanged,
   hosts-intent gains the fixture, production still excludes it pending manual access.
8. **Gates and report.** nctl ordinary, Ansible conformance, Nautobot runtime, and nauto ordinary if
   touched, each with its stated case count. Write `p4/report.md`, bump the `nctl` and
   `ansible_agdev` pointers, and hand off to Phase 5.

If the operator declines at Step 5, Steps 1-4 are reported as `implemented, not deployed` and the
phase status is `blocked` on that one decision — not `complete`.

## 6. What must be proven

| Area | Proof |
|---|---|
| the plan was unchanged | the Step 4 dry plan equals the applied plan except for timestamps and ids |
| the create ran | positive `pct create` and `pct start` argv in the operation artifacts, plus the result file — not merely absence of error |
| exactly once | one create action, one VMID, one guest; no second create in any later round |
| fresh-evidence gating | the create was planned from an observation showing no candidate, and the playbook's `pct status` gate agreed |
| identification | the guest was refetched, ingested, and linked — or the failure was reported truthfully with the guest recorded |
| the terminal is explicit | `node/agfixture` reports `waiting_for_manual_initial_access`, not `no_realized_object`, under all four conditions |
| non-repetition | the second reconcile plans no create, no start, no link |
| partial progress | the §4.4 branches are implemented and, if any fired, its evidence and `mutated=true` are preserved |
| target isolation | the whole-cluster dry plan is unchanged for every other node and guest |
| SSH boundary | the run used the existing strict trust and the generated production inventory; no option was relaxed |
| no deletion path | static check still finds no stop/destroy/resize/migrate anywhere in the create path |
| coverage | the create path is tested at Tier A, and the real playbook is exercised by the conformance gate |
| artifacts | the three digests differ from Step 0 only where the fixture explains it |
| gates | the four gates pass with stated case counts |

## 7. Reporting

`p4/report.md`: revision tuple; the three closed Phase 3 gaps (missing tests, result-file transport,
missing terminal) stated as deviations found and fixed, not as new features; the operation id and
round-by-round transition with its evidence; the exact `pct` argv issued; the observation and ingest
Job ids; the resulting link; the final drift for `agfixture` and for the cluster; gate results with
case counts; every §4.4 branch that fired; and a status that says **one Proxmox LXC container was
created**, never "a VM was created".

Per `README_DEV.md` lesson 9, an omitted or substituted check is visible and prevents an unqualified
`complete`. A safe stop at partial progress is reported as a safe stop.
