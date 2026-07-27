# P1 Step 7 — Re-prove behavior preservation and inertness

Status: blocked pending a local scratch-state decision.

## Completed checks

- `nctl/tests/test_compute_actuation_inert.py::test_valid_compute_collections_produce_no_drift_and_no_plan_actions` passed: **1 passed**. This is the manifested `compute-inert` proof.
- The fixed malformed compute/endpoint-row surface was executed against the frozen pre-Phase-1 nctl source and current nctl source. The resulting `code`, `scope`, `severity`, `message`, `blocked_consumers`, and `evidence` values are byte-identical; the retained private files are `source-issue-baseline.tsv` and `source-issue-after.tsv`.
- Read-only `nctl drift --json` completed successfully. No write, reconcile, collection, ingest, SSH, Ansible, or Proxmox operation was performed.

## Blocking artifact comparison

The required Phase 0 artifact byte/digest comparison cannot pass against the current scratch input. `dnsmasq-records.conf` is identical (`ac1f19a564bc1342d97741d4b2b9525b3259f78fb37bf997d7ee29c200ae99ec`), but the current live read marks `aghub` as `stale_actual_data`; production inventory changes from one included host to zero. Its report changes from 11,911 to 9,886 bytes and production inventory changes from 1,500 to 644 bytes.

The hosts-intent and production artifacts also contain per-render generation IDs/timestamps, so their complete byte digests differ from the Phase 0 capture even before considering the changed scratch observation. The production semantic difference is specifically the expired `aghub` actual observation, not the Phase 1 compute-contract source change.

Phase 1 Section 7 states that a changed artifact digest is a defect rather than an update. Resolving this requires a human decision: either restore/refresh the local scratch observation through an explicitly authorized workflow, or decide how this plan's literal byte-comparison requirement applies to artifacts with generation metadata and changed scratch inputs. The remaining Step 7 matrix and Step 8 have not been run, so this step is not complete.
