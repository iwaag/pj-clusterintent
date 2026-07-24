# Phase 2 Step 6 Report: nctl Typed Actual Proxmox State and Read-Only Diagnostic

Status: implemented, not deployed (local code + local test-suite runs against real `nctl`
dependencies via `uv run pytest`; no live Nautobot GraphQL execution).

This report covers [`plan.md`](plan.md) Step 6 ("Extend nctl typed actual state and add
read-only diagnostic"), grounded in Section 5.6 ("nctl typed actual snapshot and diagnostic").

## 1. What changed

`nctl`:

- `src/nctl_core/sources/actual.py` — extended `ACTUAL_QUERY` with a `clusters` root, an
  expanded `virtual_machines` selection (`cluster`, `status`, `role`, `vcpus`, `memory`, `disk`,
  `_custom_field_data`), a new `vm_interfaces` root pinned separately from the DCIM `interfaces`
  root (plan.md 5.6: "it must not assume that the DCIM `interfaces` root also contains
  VMInterfaces"), and `vm_interfaces { id }` on `ip_addresses`. Added strict
  (`extra="forbid"`) Pydantic models — `ProxmoxObservationError`, `ProxmoxObservationDetail`,
  `ProxmoxLxcRootfs`, `ProxmoxInterfaceDiagnostic`, `ProxmoxInterfaceEvidenceEntry`,
  `ProxmoxManagedIpEntry`, `ProxmoxManagedIpEvidence`, `ProxmoxClusterFacts`,
  `ProxmoxVirtualMachineFacts`, `ProxmoxVMInterfaceFacts`, `ProxmoxFactsReadError` — plus
  `ActualCluster`, `ActualVMInterface`, and an expanded `ActualVirtualMachine`. `ActualSnapshot`
  gained `clusters`, `vm_interfaces`, and `proxmox_read_errors`, additively; `devices`,
  `virtual_machines` (existing fields unchanged, only extended), `interfaces`, and `ip_addresses`
  keep their prior shape and meaning.
- `src/nctl_core/actual_render.py` (new) — `build_actual(cfg)` fetches via `NautobotClient` +
  `fetch_actual_snapshot`; `render_actual_data(snapshot)` is a pure function (no network) that
  joins clusters → VMs → VMInterfaces → managed-vs-unrelated IP relations into the
  `nctl.actual.v1` typed graph; `render_actual_text(envelope)` renders the observer → cluster →
  guest → interface tree.
- `src/nctl_core/cli/main.py` — added `nctl actual [--json]`, wired identically to the existing
  `status` command's `_load_config`/`build_*`/`emit`/`Exit` pattern.
- `tests/test_sources_actual.py` (extended, +7 tests), `tests/test_actual_render.py` (new, 6
  tests), `tests/test_cli_actual.py` (new, 4 tests).

## 2. Design

### Field provenance (verified against the writer, not guessed from plan.md prose)

The `proxmox_*` custom-field shapes were read directly out of the Steps 4-5 writer code
(`nauto/jobs/proxmox_upsert.py`, `nauto/jobs/proxmox_interfaces.py`), not re-derived from
plan.md's illustrative envelope alone, so the typed models match what is actually written. Two
notable divergences from a literal plan.md reading:

- `proxmox_observation_detail` is the flat `{state, omitted_error_count, errors}` shape from
  `build_observation_detail()`, not the nested per-section `sections` map shown in plan.md
  Section 5.2's *nodeutils report* envelope — that richer shape belongs to nodeutils' report, not
  to nauto's summarized ledger field. `ProxmoxObservationDetail` matches the ledger field as
  written.
- `proxmox_managed_ip_evidence` matches `proxmox_interfaces.sync_interface_ips()`'s exact output:
  `{"managed": {"<address>/<prefix>": {"ip_id", "evidence_observed_at"}}, "evidence_observed_at"}`.

### Strict allowlisted reading (Section 5.6, Section 2 exit criteria)

`_CLUSTER_PROXMOX_FIELDS`, `_VM_PROXMOX_FIELDS`, and `_VMINTERFACE_PROXMOX_FIELDS` are closed
`{model_field: custom_field_key}` maps. `_select_allowlisted()` copies only these documented keys
out of `_custom_field_data` before validation — `inventory_raw_json` and any other unrelated
custom field is never read. Every nested model uses `extra="forbid"`, so an unknown key inside a
`proxmox_*` value (a schema drift or corruption case) fails `model_validate()`; `_read_proxmox_facts()`
catches that `ValidationError` and records a `ProxmoxFactsReadError` (object_type, object_id,
field, message) instead of raising out of the fetch or silently dropping the object. The owning
Cluster/VM/VMInterface is still returned with `proxmox=None` in that case, and the read error
surfaces in both `ActualSnapshot.proxmox_read_errors` and the `nctl actual --json` envelope's
`errors` list (code `proxmox_facts_invalid`).

### Additive `ActualSnapshot` (Section 5.6 "preserve current Device/interface/IP consumers")

`clusters`, `vm_interfaces`, and `proxmox_read_errors` are new fields with `[]` defaults;
`devices`, `interfaces`, `ip_addresses` keep their previous meaning, and `virtual_machines` keeps
its previous `id`/`name` fields while adding new optional ones. No existing field was removed or
renamed. The full 999-test `nctl` suite (977 pre-existing + 22 new) passes, confirming `nctl
status`, drift, dashboard, and observation-summary code paths — none of which were touched — still
behave as before.

### `nctl actual` diagnostic (Section 5.6)

`render_actual_data()` builds a typed `ActualData` (list of `ActualClusterData`, each with a
`guests: list[ActualGuestData]`, each with `interfaces: list[ActualGuestInterfaceData]`) purely
from an already-fetched `ActualSnapshot`, so it is testable with fixture data and shared between
the live `build_actual()` path and tests. Interface rows compute `managed_ip_count` from
`proxmox_managed_ip_evidence.managed` and separately list `unrelated_ip_ids` — native
VMInterface↔IPAddress relations present in Nautobot but not in the ingestor-managed set — so the
diagnostic can show "managed vs. unrelated" without ever claiming an unrelated relation as fresh
Proxmox evidence (Section 5.6: "remain visible ... but are not labeled as fresh Proxmox-observed
IP evidence"). `render_actual_text()` renders:

```
observer aghub
└─ cluster aghub-proxmox  complete  observed <time>
   └─ lxc  vmid=108  agdnsmasq  running  node=aghub
ok: True
```

The observer line resolves the Cluster's `proxmox_observer_device_id` to that Device's `name` via
`ActualSnapshot.devices` (an addition made during review of the initial implementation, which had
rendered the raw Device UUID instead of the hostname the plan's example shows); it falls back to
the UUID if the Device isn't present in the snapshot for some reason. `nctl actual` never emits
`aghub-pve` (Phase 3's future desired Cluster slug) and has no write path — `build_actual()` only
calls `fetch_actual_snapshot()` and pure rendering functions.

## 3. Explicit non-goals held

- Storage-content reading was **not** implemented. No step through Step 5 writes
  `proxmox_storage_content` to any Nautobot ledger object (Step 2 built only the read-only
  nodeutils/helper path; no ORM consumer of storage-content evidence exists yet), so there is
  nothing live for nctl to read. This remains open for whichever later step adds a
  storage-content ledger writer.
- `nctl status`, drift semantics, production composition, and dashboard behavior are unchanged —
  confirmed by the unmodified pre-existing 977 tests all passing alongside the 22 new ones.
- No live Nautobot GraphQL call was made; no `nodeutils`, `ansible_agdev`, or `nauto` file was
  touched in this step.

## 4. Tests

```
$ uv run pytest tests -q
999 passed, 1 warning in 6.14s
```

(The one warning is a pre-existing `StarletteDeprecationWarning` in `test_serve_ws.py`, unrelated
to this step.) 22 new/extended tests across three files:

- `tests/test_sources_actual.py` (+7): a fixture builds `aghub-proxmox` / `agdnsmasq` VMID 108
  through the full GraphQL-row → `fetch_actual_snapshot` → typed-model path, asserting the guest
  is positively present with correct identity/scope/observation fields; a malformed
  `proxmox_observation_detail` (unknown nested key) produces a `ProxmoxFactsReadError` rather than
  raising or being silently accepted; an unrelated custom-field key (e.g. `inventory_raw_json`)
  never reaches any Proxmox model.
- `tests/test_actual_render.py` (6): builds the typed cluster→guest→interface graph from a
  fixture snapshot, confirms managed vs. unrelated IP relation display, confirms the text
  renderer's shape, and confirms `aghub-pve` never appears in either JSON or text output.
- `tests/test_cli_actual.py` (4): `nctl actual` and `nctl actual --json` exit codes and output via
  the same monkeypatch pattern `test_cli_status.py` already uses; confirms no raw/unrelated custom
  data leaks into CLI output.

Because `nctl`'s dependencies (`pydantic`, `typer`, etc.) are installed in this environment via
`uv`, tests ran for real (not just `py_compile`), unlike the Django-dependent `nauto` steps.

## 5. What Step 6 does not yet cover / open risk

- **GraphQL root name for VMInterface is unverified against a live schema.** `report2.0.md`'s
  Step 0 introspection confirmed the *REST* endpoint `virtualization/interfaces/` and the GraphQL
  root names for Cluster (`cluster`/`clusters`) and VirtualMachine (`virtual_machine`/
  `virtual_machines`), but did not separately confirm a GraphQL root name for VMInterface. This
  implementation uses `vm_interfaces` as a best-fit inference consistent with Nautobot's naming
  convention elsewhere in this query, not a live-confirmed name. **This must be checked against
  the live GraphQL schema no later than Step 8's live prerequisite check** — if the real root
  differs, `ACTUAL_QUERY` and the `data.get("vm_interfaces", [])` lookup in
  `fetch_actual_snapshot()` are the only places to fix.
- No live execution of `ACTUAL_QUERY` against a real Nautobot instance; all proof is
  fixture/fake-client-based, consistent with the same limitation Steps 3-5 recorded for their own
  live-unverified assumptions (e.g. Step 4's `VirtualMachine.memory`/`disk` unit assumption).
- Storage-content typed reading (see Section 3 above).

## Gate

Query fixture and CLI tests positively contain `agdnsmasq` VMID 108 under `aghub-proxmox`, and
raw/unrelated custom data does not enter the typed output — the Step 6 gate — proven by
`test_sources_actual.py`'s fixture test and `test_cli_actual.py`'s no-leakage assertion, entirely
without a live Nautobot dependency.

Proceeding to Step 7 (full automated and fixture-backed verification).
