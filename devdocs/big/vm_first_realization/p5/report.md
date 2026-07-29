# First Proxmox Guest Realization — Phase 5 Report

Status: **complete**. The first-realization path is documented and reviewed. It proves that **one
Proxmox LXC container** was created and started once; it does not claim QEMU VM creation.

Run date: 2026-07-29 (JST).

## Revision tuple and Phase 5 changes

| Component | Revision | Phase 5 state |
|---|---:|---|
| superproject | `b33663b` | report added |
| nctl | `e983733` | README updated, uncommitted |
| nintent | `0eae8a0` | canonical-seed count test updated, uncommitted |
| nauto | `1b74d88` | clean |
| nodeutils | `775ed7f` | clean |
| ansible_agdev | `133ef14` | clean |

`nctl/README.md` now documents the three seams with compute as the worked example and gives the
ordinary bounded LXC workflow: confirmed structured intent, dry plan, separately authorized
apply, re-observation/link recovery, and the manual-initial-access gate. It explicitly directs an
operator to stop on a missing template, collision, stale ledger, ambiguous endpoint, or unreachable
platform, and never to recover with direct `pct` or a second create.

The Phase 3 seed added `agfixture`, but nintent's checked-in canonical-source assertion still
described the preceding five-node/one-instance set. The assertion now names the six nodes, six
endpoints, and two compute instances, including `agfixture`/VMID 109. This fixes the root matrix
failure without changing desired-state semantics.

## Alignment Review and retained fixture

The confirmed Braindump `9cda91ef-9d86-4667-b61b-771a146f54b7` now has Alignment Review
`5eed799c-1150-43c8-8eed-b130510c75ac`. It records the created-and-started `agfixture` LXC,
the observed VirtualMachine `3a6aa5b1-f128-4d23-82f7-9c97acff3a68`, its stable desired-compute
link, the no-repeat result, and the manual-access boundary.

The Phase 0/3 cleanup decision was **retain**. Consequently no cleanup action was required or
performed. The guest remains running on `aghub`; this is not an nctl deletion capability and no
out-of-band deletion occurred.

## Fresh end-state evidence

Fresh `nctl drift --json` reports `compute_instance/agfixture` converged, matched by its explicit
realized VM link. `node/agfixture` is also converged and carries exactly the informational,
successful terminal `waiting_for_manual_initial_access`; production composition excludes it for
that explicit reason.

Fresh host-scoped dry operation `01KYNGF6CEMATR03BT7EG15W14` has scope `agfixture`, two
converged scoped targets, no SSH preflight target, no manual review, no unsupported finding, and
no actions. The corresponding whole-cluster dry operation `01KYNGF6XK9GWE3QXRY986FSE9` contains
no action targeting `agfixture`. This is the non-repetition and sibling-isolation proof; neither
operation invoked Proxmox or Ansible.

The dnsmasq render's configured records and ranges remain unchanged from Phase 0: its ordinary
stdout form has the same digest,
`305e17dc3be75f208eb18728b16fb8e44e8a28389504727cb6580dc1d71bb9a1`. The fixture deliberately
has `generate_dnsmasq: false`. Fresh deterministic render artifacts include `agfixture` only in
hosts-intent and exclude it from production for the manual-access reason. The output-directory
artifacts (whose dnsmasq writer omits the terminal stdout newline) had these digests:

| Artifact | SHA-256 |
|---|---|
| dnsmasq | `ac1f19a564bc1342d97741d4b2b9525b3259f78fb37bf997d7ee29c200ae99ec` |
| hosts-intent inventory | `560f45c42fa345c959950abba5bc3e11e1dfe2bc2d33e3959211f7414d60e029` |
| production inventory | `cb62678317a4af82a4a69ea9f45b684f911f6e9f82ea4417b476cd0db0434413` |

The Phase 0 hashes for the latter two predate the fixture, so their difference is explained by the
confirmed desired `agfixture` entry and its intentional production exclusion; the dnsmasq content
has no fixture change.

## Verification

All `devtests/test_strategy/MANIFEST.md` test paths resolve. The root matrix was exercised with
the following results:

| Gate | Result |
|---|---|
| nctl ordinary | 1005 passed |
| compute conformance | 1 passed |
| nintent Django-free | 236 run, 14 expected skips |
| nauto ordinary | 110 run |
| nodeutils ordinary | 54 passed |
| Ansible helper ordinary | 4 run |
| OpenSSH conformance | 2 passed |
| Ansible conformance | 2 passed |
| privileged-helper integration | 1 passed |
| Nautobot runtime reuse and clean | 299 collected cases each; exact-local staged sources and clean test database path exercised |
| measurement (`--runtime`) | runtime measurement invoked; ordinary collection: nctl 1005, nintent 236, nauto 110, nodeutils 54, ansible helper 4 |

The Nautobot runtime gate emitted its usual model warnings for RawSQL-backed JSON check
constraints; they are warnings, not skips or failures. No credentials, raw keys, or managed-file
contents are recorded in this report.

## Proven and deferred handoff

Proven: the confirmed Braindump became structured desired state; a dry plan named the exact LXC;
the approved Phase 4 path issued `pct create` and `pct start` once; fresh observation/ingest found
the guest; a separate recovery linked it; and repeat planning does not create, start, or link it.

The next roadmap must treat the guest's console bootstrap, networking, SSH enrollment, and first
guest nodeutils observation as a separate ordinary-reconcile continuation. QEMU creation, resource
mutation, stop/delete/replace/migrate, automatic bootstrap, multi-NIC support, VMID/MAC allocation,
and provider-general lifecycle management remain unsupported. No stop, deletion, resize, or
replacement path was added.
