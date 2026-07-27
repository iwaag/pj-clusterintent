# P1 Step 7 — Re-prove behavior preservation and inertness

Status: complete.

## Completed checks

- `nctl/tests/test_compute_actuation_inert.py::test_valid_compute_collections_produce_no_drift_and_no_plan_actions` passed: **1 passed**. This is the manifested `compute-inert` proof.
- The fixed malformed compute/endpoint-row surface was executed against the frozen pre-Phase-1 nctl source and current nctl source. The resulting `code`, `scope`, `severity`, `message`, `blocked_consumers`, and `evidence` values are byte-identical; the retained private files are `source-issue-baseline.tsv` and `source-issue-after.tsv`.
- Read-only `nctl drift --json` completed successfully and reports an empty `source_issues` array. The envelope shape and contents are unchanged.

## Scratch observation refresh and artifact comparison

The initial comparison detected that the local `aghub` observation had expired. After user approval, the scoped operation `01KYJTKZKE4NKYETBKTEQ0XWM1` ran only the planned `observe_node` action: nodeutils collection and Nautobot ingest for `aghub`. It finished `converged`; no Ansible/service configuration action was planned or run.

The refreshed production render again includes one host, as in Phase 0. `dnsmasq-records.conf` is byte-identical (`ac1f19a564bc1342d97741d4b2b9525b3259f78fb37bf997d7ee29c200ae99ec`). The hosts-intent and production render diffs contain only their declared volatile metadata: `generated_at`, generation ID/report path, and `aghub`'s newly collected observation timestamp. After excluding those runtime metadata fields, each retained artifact's content is byte-identical to the Phase 0 capture; there is no semantic artifact change from the Phase 1 source change.

## Local verification matrix

| gate | result |
|---|---|
| nctl ordinary | 968 passed |
| nintent Django-free | 236 run, 14 skipped |
| nauto ordinary | 110 run |
| nodeutils ordinary | 54 passed |
| Ansible helper ordinary | 4 run |
| OpenSSH conformance | 2 passed |
| Ansible conformance | 1 passed |
| privileged-helper integration | 1 passed |
| compute-conformance freshness | 1 passed |

## Gate verdict

Complete: the explicitly named inertness proof passes, malformed source-issue behavior is identical to the frozen pre-Phase-1 source, the stale scratch observation was refreshed through the scoped approved operation, artifact content is unchanged apart from declared runtime metadata, and the required local matrix is green.
