# Phase 2 Sidefix1 Step 3 Report: Sanitize Preview Evidence

Status: implemented, not deployed. No live-state change was made or authorized by this step.

This report covers [`problem_fixplan.md`](problem_fixplan.md) Step 3 ("Sanitize preview
evidence").

## 1. ID audit result (fixplan Section 5.4)

Re-audited every field `proxmox_upsert._section()` returns (the only builder of the Job's public
`proxmox` result section) and everything it can nest: `identity_source`, `scope_key`,
`cluster_name`, `cluster_id`, `observation_state`, `object_counts` (integers only),
`changed_fields` (field-name strings, keyed by `"cluster"` or the Proxmox-native
`"vm:{guest_type}:{vmid}"`, never a DB id), and `guest_errors` (`scope_id` values are either the
literal `"cluster"` or that same Proxmox-native `"{guest_type}:{vmid}"`/`scope_key` string, again
never a DB id). **`cluster_id` is the only database primary key ever exposed in the returned
section** — no VM, VMInterface, or IPAddress id is present anywhere in the returned dict. The
per-interface `ip_id` recorded in `proxmox_managed_ip_evidence` lives only inside the
`custom_field_data` written onto the (rolled-back, in preview) VMInterface row itself; it is never
copied into the Job's returned/logged/persisted summary, so it needs no separate sanitization step.

## 2. Sanitization implementation (fixplan Section 5.4)

Added `sanitize_created_ids: bool = False` to `proxmox_upsert.ingest_proxmox_platform()`. It
changes only what value is *reported*, never what gets written — Step 1 already made every
`save_fn()` call unconditional, and this step does not reopen that:

- `cluster_is_new = match.obj is None` is captured immediately after `match_cluster()`, i.e. before
  any create/update happens — the same "did an object exist before this call" test the plan
  requires ("retain IDs only for objects that existed in the before image").
- `reported_cluster_id = None if (sanitize_created_ids and cluster_is_new) else getattr(cluster,
  "pk", None)` is computed once after the Cluster upsert and used by both `_section()` return
  points that follow (the `stale_evidence`/`conflicting_same_generation` early return and the final
  return) — a pre-existing Cluster keeps its real id even when the caller asks for sanitization; a
  Cluster created for the first time by *this* call reports `cluster_id: null` when
  `sanitize_created_ids=True`.
- `_section()`'s existing `str(cluster_id) if cluster_id is not None else None` already avoided the
  `"None"`-string bug the plan calls out; no change was needed there.
- `ingest_nodeutils_inventory.py`'s call into `ingest_proxmox_platform()` now passes
  `sanitize_created_ids=self.dry_run` — the Job's own preview flag, not a new lower-layer write
  suppression.

## 3. Tests

Added `SanitizeCreatedIdsTests` to `test_proxmox_cluster_vm_upsert.py`:

- `test_newly_created_cluster_id_is_none_when_sanitized` — a first-time Cluster create with
  `sanitize_created_ids=True` still allocates a real in-memory `pk` (proving the write itself is
  unaffected) but `result["cluster_id"]` is `None`.
- `test_newly_created_cluster_id_is_present_when_not_sanitized` — the existing default
  (`sanitize_created_ids=False`, i.e. apply mode) still reports the real id, unchanged from before
  this step.
- `test_preexisting_cluster_id_is_retained_even_when_sanitized` — a Cluster created by a prior call
  keeps reporting its real `cluster_id` on a second call even with `sanitize_created_ids=True`,
  proving the sanitization is scoped to "created by this call," not "any preview call."

## 4. Verification

```
cd nauto
python3 -m py_compile jobs/*.py
# no output (success)
python3 -m unittest discover -s tests
# Ran 95 tests in 0.009s
# OK
```

All 95 tests pass (92 from Step 2 + 3 new). `git diff --check` reported nothing; only
`jobs/proxmox_upsert.py`, `jobs/ingest_nodeutils_inventory.py`, and
`tests/test_proxmox_cluster_vm_upsert.py` changed.

## Gate

- No temporary ID is presented as apply-stable: proven — a Cluster created inside the current call
  reports `cluster_id: null` under `sanitize_created_ids=True`, and no other DB id is ever present
  in the returned section (Section 1 audit above).
- Preview remains reviewable without raw evidence: proven — `scope_key`, `cluster_name`, counts,
  `changed_fields`, and `guest_errors` are all retained unchanged; only the ephemeral row id is
  withheld.

Step 3 is satisfied. Proceeding to Step 4 (prove real transaction safety: side-effect audit plus
the real ORM Round A preview) remains gated behind this step's own review — Step 4 is the first
step in this fix plan that touches the local Nautobot environment, per
`.local/localenv_memo.md`.
