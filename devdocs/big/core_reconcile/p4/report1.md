# Phase 4 Report — Step 1 (shared operation, Ansible, and Nautobot Job transports)

Date: 2026-07-16. Implements [p4/plan.md](plan.md) Step 1. This is the first suggested
commit boundary; changes are confined to nctl plus this parent-repository report. Phase 4 Step 2
collection/ingest behavior and the old Ansible orchestration path are intentionally untouched.

## What was built

### Private atomic operation artifacts

New `nctl/src/nctl_core/artifacts.py` provides `OperationArtifacts`:

- one resolved root at `<events.log_dir>/<operation_id>/`;
- directory mode `0700` and file mode `0600` (also enforced on existing paths);
- atomic same-directory temporary write + `fsync` + `os.replace` for text/JSON artifacts;
- rejection of absolute paths and `..` traversal outside the operation root;
- `ensure_writable()` preflight using a real atomic probe, exposed as typed `ArtifactError`.

`nctl apply dnsmasq` now establishes this directory before rendering and writes its existing
`artifacts/dnsmasq-records.conf` through the helper. Failure still returns the established
`artifact_write_failed` envelope error and a failed terminal event.

### Shared shell-free Ansible runner

New `nctl/src/nctl_core/ansible.py` owns the generic code factored from
`dnsmasq_apply.py`:

- `AnsibleRunner` invokes argument arrays with `shell=False` (the `subprocess.run` default), a
  configured timeout, captured text stdout/stderr, and an injectable runner seam for tests;
- timeout is a bounded result (`exit_code=124`, `timed_out=true`) rather than an uncaught
  `TimeoutExpired`; an executable/OS failure is likewise a typed result;
- `AnsibleRunResult` carries the sanitized command, recap, sorted failed/unreachable hosts,
  timeout flag, and optional stdout/stderr artifact paths;
- sensitive `key=value`, JSON-shaped extra vars, and `--vault-password-file` values are redacted
  from the recorded command while the original argument array is passed to Ansible;
- `load_inventory`, recursive/cycle-safe `inventory_group_hosts`, and `parse_recap` are shared
  helpers.

`dnsmasq_apply.py` now consumes these services. Its public schema name, dry-run/apply modes,
target selection, error codes, text rendering, and event order remain unchanged. It additionally
writes private `ansible/dnsmasq.stdout` and `.stderr` evidence and uses
`[reconcile].ansible_timeout_seconds`. The two old private helper names imported by existing tests
(`_inventory_group_hosts`, `_parse_recap`) remain compatibility aliases; the subprocess test seam
moved to the actual owner module.

### Generic Nautobot Job runner

New `nctl/src/nctl_core/jobs.py` provides `NautobotJobRunner` and typed
`NautobotJobError`/`NautobotJobResult`:

1. query `/api/extras/jobs/?q=...` and require exactly one exact display-name match;
2. POST `{"data": ..., "commit": ...}` to the Job run endpoint;
3. extract the JobResult ID from all historical Nautobot response variants used by this
   repository: nested `job_result`/`result` ID or PK, a JobResult URL string, or the `Location`
   header;
4. poll `/api/extras/job-results/<id>/` with monotonic timeout and explicit
   success/failure/cancel terminal vocabularies;
5. persist a sanitized final JobResult as `jobs/<job-result-id>.json`;
6. optionally require exactly one named FileProxy associated with that JobResult, download it as
   UTF-8, and atomically install it at a caller-supplied confined artifact path.

Submitted Job data is never emitted. JobResult fields that can echo variables/arguments or
credentials (`data`, `task_kwargs`, `kwargs`, token/password/secret-shaped keys, etc.) are replaced
with `<redacted>` both in the returned model and stored JSON. HTTP failure details retain only the
status code, not a possibly echoing response body. Events contain only Job/JobResult IDs, status,
poll count, and artifact path: `job_started`, `job_poll`, `job_completed`, or `job_failed`.

`NautobotClient` gained the two narrow primitives needed by this transport: `rest_post()` and
`rest_download()`. GraphQL remains the read path for desired/actual data; these methods are for
transactional Job execution and its result artifact.

### Strict reconcile configuration

`Config` gained an optional strict `[reconcile]` section:

- `max_rounds = 3` (bounded 1–10);
- `job_poll_interval_seconds = 2`;
- `job_timeout_seconds = 300`;
- `ansible_timeout_seconds = 1800`;
- absolute `remote_report_path = "/var/lib/nodeutils/inventory.json"`;
- `lock_path = "~/.local/state/nctl/reconcile.lock"` with expansion helper.

The settings are present now so every later Phase 4 transport has one validated source. Unknown
keys, non-positive/out-of-range timeouts/rounds, and a relative remote report path are rejected.
`InventoryConfig.dumps_dir` now has the controller-side default
`~/.local/state/nctl/dumps`; `example.nctl.toml` uses it and no longer suggests that the remote
`/var/lib/nodeutils` path is also the controller cache. An existing config with an explicit
`dumps_dir` remains valid and unchanged.

## Tests

New focused suites:

- `test_artifacts.py`: private modes, atomic cleanup, path confinement, unwritable preflight;
- `test_ansible.py`: timeout propagation, recap/failed/unreachable extraction, artifact output,
  sensitive command redaction, inventory child cycles;
- `test_jobs.py`: all supported JobResult reference shapes, pending→success polling, terminal
  failure, monotonic timeout, auth/connection failure, zero/duplicate Job match, wrong/duplicate
  FileProxy rejection, exact artifact download, result sanitization, event data non-leakage.

Existing config and dnsmasq tests were extended/repointed for the strict settings and shared
runner. The Step 1 net increase is 23 tests (Phase 1.5 closeout: 285; now 308).

Verification:

- `cd nctl && uv run pytest -q` — **308 passed**.
- `cd nctl && uv run python -m compileall -q src tests` — passed.
- parent and nctl `git diff --check` — passed.

## Live Nautobot verification

The local Nautobot 3.1 environment was checked without exposing the configured token:

- read-only Job lookup for `Ingest Nodeutils Inventory` returned exactly one installed/enabled
  row with the expected `id`, `name`, `module_name`, `job_class_name`, and detail URL. This confirms
  exact display-name selection against the real list shape;
- `OPTIONS` on the Job run endpoint returns HTTP 405 in this deployment, so it cannot document the
  POST response shape without a real invocation;
- therefore the new runner executed the retained `Reconcile Desired IPAM Intent` Job once with
  `commit_changes=false`, `include_inactive=false`. This creates the normal JobResult/FileProxy but
  makes no IPAM ledger changes.

Live result:

- JobResult: `06150cad-c0ba-4316-8d9d-f0a9ac486750`;
- terminal status: `success` after 2 polls;
- the sanitized final JobResult artifact was written successfully;
- exact `ipam-reconcile-summary.json` lookup/download succeeded;
- parsed top-level keys were `plans` and `summary`, and
  `summary.commit_changes` was confirmed `false`.

This closes the Step 1 response-shape/poll/FileProxy risk against the actually running server,
rather than relying only on the historical deleted Ansible helper and mocked variants.

## Boundary and deliberate non-work

This is a clean commit boundary because the new modules are independently tested and one existing
consumer (`apply dnsmasq`) proves the Ansible/artifact refactor without depending on future
reconcile code. Nothing in this step changes desired/actual state semantics.

Not done yet (Step 2+):

- no `nctl reconcile` command or planner/executor;
- no nodeutils collection, Ansible slurp, controller dump-cache update, ingest batch, or ingest
  summary artifact;
- no nintent/nauto/nodeutils/ansible_agdev source change;
- no deletion or modification of
  `collect_nodeutils_and_ingest_nautobot.yml`;
- no change to `converging`, service observation, deployment-profile metadata, dashboard refresh,
  IPAM scope, or ledger linking;
- the ignored local `nctl.toml` still has its operator-selected explicit dumps path; Step 2 live
  cutover must point it at a writable controller cache before collection is exercised.

## Files changed in this boundary

nctl:

- added `src/nctl_core/artifacts.py`, `ansible.py`, `jobs.py`;
- updated `config.py`, `nautobot.py`, `dnsmasq_apply.py`, `example.nctl.toml`;
- added `test_artifacts.py`, `test_ansible.py`, `test_jobs.py`;
- updated `test_config.py`, `test_dnsmasq_apply.py`.

Parent repository:

- added this report; `p4/plan.md` remains the implementation contract and its phase-level exit
  checkboxes remain unchecked.

No commit was created. The nctl changes plus this report are ready for review as the first Phase 4
commit unit.
