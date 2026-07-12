# Batch Nodeutils Ingest Implementation Plan

This plan replaces file-path based Nautobot ingestion with a single API-driven
Job run that can process multiple nodeutils reports at once.

The implementation is allowed to be destructive. Do not keep compatibility-only
variables, duplicate playbook paths, or legacy file-copy behavior just to
preserve the current flow. The desired end state should be explicit and clean:

- Nodeutils keeps writing the latest report on each managed host.
- Ansible reads those host reports and submits them to Nautobot through the API.
- Nautobot does not read nodeutils reports from local server paths.
- One Nautobot Job execution can validate and ingest multiple reports.
- Nautobot container filesystem layout is not part of the ingest contract.

## Target Flow

```text
Managed host:
  /var/lib/nodeutils/inventory.json

Ansible control node:
  reads the report from each target host
  builds one batch payload
  calls the Nautobot Job API once

Nautobot:
  receives report_batch
  validates each report independently
  applies server-side ingest policy
  logs per-report results in one JobResult
```

## Step 1: Redefine the Nautobot Job input contract

### Goal

Make batch API input the only supported ingestion interface.

### Changes

Update `nauto/jobs/ingest_nodeutils_inventory.py`:

- Remove `report_path`.
- Remove local file and directory reading helpers.
- Replace `report_text` with a required batch-oriented input, for example
  `report_batch`.
- Define `report_batch` as JSON or YAML text with this shape:

```yaml
reports:
  - source: agpc
    text: |
      {"schema_version": "nodeutils.inventory.v1", "...": "..."}
  - source: agstudio
    text: |
      {"schema_version": "nodeutils.inventory.v1", "...": "..."}
```

Keep the parsed internal representation close to the existing `ReportInput`
dataclass:

```python
@dataclass(frozen=True)
class ReportInput:
    source: str
    text: str
```

### Completion Criteria

- The Job no longer accepts or mentions `report_path`.
- The Job can parse a batch payload containing multiple report entries.
- Each report keeps a stable `source` label for logs and error messages.
- The Job rejects an empty batch and malformed batch entries.

## Step 2: Preserve per-report validation and failure isolation

### Goal

One bad host report should not prevent valid reports in the same batch from
being evaluated.

### Changes

Keep the existing report-level validation behavior:

- parse each report independently
- enforce `max_report_bytes` per report
- enforce schema version policy per report
- enforce `collected_at` freshness per report
- log skipped reports with a clear reason

Add a lightweight batch summary in the Job logs:

- total reports received
- reports ingested
- reports skipped
- dry-run state

Do not add durable staging models or compatibility tables for uploaded reports.
The source of truth after ingest remains Nautobot Device state and JobResult
logs.

### Completion Criteria

- A batch with one valid and one invalid report ingests or dry-runs the valid
  report and logs the invalid report as skipped.
- Oversized report handling still applies to each individual report.
- Dry run still rolls back all Device mutations.
- Job logs clearly identify the host/source for each report result.

## Step 3: Update the Ansible collection playbook

### Goal

Remove the Nautobot-server copy stage and submit one batch payload through the
Nautobot API.

### Changes

Update `ansible_agdev/playbooks/collect_nodeutils_and_ingest_nautobot.yml`:

- Keep the existing `run_nodeutils_collect.yml` import so each host refreshes
  `/var/lib/nodeutils/inventory.json`.
- Remove the play named `Copy nodeutils reports to the Nautobot server`.
- Replace Nautobot `report_path` Job data with the new `report_batch`.
- Build the batch from the collected host reports.

Preferred implementation:

- Use `slurp` to read `nodeutils_output_path` from each target host after
  collection.
- Store decoded report text in hostvars.
- On localhost, build:

```yaml
reports:
  - source: "{{ inventory_hostname }}"
    text: "{{ decoded_report_text }}"
```

- Submit the batch in a single Job API request.
- Use `no_log: true` around raw report content and the API request body.

Optional local debug artifact:

- Keep a local staging directory only if it is useful for troubleshooting.
- Do not make it part of the Nautobot ingest contract.
- Do not copy anything to the Nautobot server or container host.

### Completion Criteria

- Running the playbook performs only one Nautobot Job API call for the batch.
- No task copies reports to a Nautobot server path.
- The playbook works whether Nautobot runs directly on a host or inside a
  container.
- Raw reports are not printed in normal Ansible output.

## Step 4: Update documentation and examples

### Goal

Make the documented workflow match the new API-only ingest design.

### Changes

Update `ansible_agdev/README.md`:

- Describe the flow as host report generation followed by API batch ingest.
- Remove instructions that say reports are copied to the Nautobot server.
- Remove references to `nautobot_nodeutils_report_dir`.
- Keep the note that host-local
  `/var/lib/nodeutils/inventory.json` is the latest local snapshot.

Update `nauto/README.md`:

- Replace the "copy reports to the Nautobot server" section.
- Document the new batch input shape.
- Clarify that the Job does not need access to any host or container filesystem
  path for nodeutils reports.

Update any playbook comments or variable names that imply server-side report
directories.

### Completion Criteria

- Docs no longer describe SSH/SFTP/rsync to the Nautobot server as part of the
  primary ingest path.
- The batch payload shape is documented once with a small example.
- Variable names and descriptions match the new API-only behavior.

## Step 5: Update tests

### Goal

Lock in the new batch behavior and prevent accidental reintroduction of
server-local file ingestion.

### Changes

Update or add tests for `nauto/jobs/ingest_nodeutils_inventory.py`:

- batch parser accepts multiple reports
- batch parser rejects missing `reports`
- batch parser rejects entries without `source` or `text`
- batch parser rejects non-string report text
- valid and invalid reports in one batch are handled independently
- `max_report_bytes` is enforced per entry

Update Ansible-related validation where practical:

- Add a syntax check target or documented command for the updated playbook.
- If existing project tests cover generated task data, adjust expected Job body
  fields from `report_path`/`report_text` to `report_batch`.

### Completion Criteria

- Nautobot Job unit tests pass.
- Nodeutils tests remain unaffected.
- Ansible playbook syntax check passes.
- No test fixture depends on `/var/tmp/nodeutils-reports`.

## Step 6: Remove obsolete variables and cleanup

### Goal

Leave the repositories in the new shape without compatibility clutter.

### Changes

Remove or rename variables that only supported Nautobot-server local copies:

- `nautobot_nodeutils_report_dir`
- `nautobot_nodeutils_report_owner`
- `nautobot_nodeutils_report_group`
- `nodeutils_report_local_dir` if it is no longer used

Remove obsolete documentation references to:

- Nautobot server report directories
- copying reports into containers
- running the ingest Job against a server-local path

Keep variables that still describe the host-side report:

- `nodeutils_output_path`
- `nodeutils_target_hosts`
- `nodeutils_collect_args`

### Completion Criteria

- `rg 'nodeutils-reports|report_path|nautobot_nodeutils_report_dir'` has no
  remaining references except in historical notes, if any are intentionally
  kept outside runtime docs.
- The runtime playbook has one clear ingestion path.
- The Nautobot Job has one clear external input format.

## Verification Commands

Run these after implementation:

```bash
cd nauto
python -m pytest
```

```bash
cd nodeutils
uv run pytest
```

```bash
cd ansible_agdev
ansible-playbook --syntax-check playbooks/collect_nodeutils_and_ingest_nautobot.yml
```

For an end-to-end dry run:

```bash
cd ansible_agdev
NAUTOBOT_URL=https://nautobot.example.local \
NAUTOBOT_TOKEN=your-nautobot-api-token \
ansible-playbook playbooks/collect_nodeutils_and_ingest_nautobot.yml \
  -e nautobot_ingest_dry_run=true
```
