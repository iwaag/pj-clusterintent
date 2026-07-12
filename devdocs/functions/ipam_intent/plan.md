# nintent IPAM Intent Implementation Plan

This plan turns the IPAM intent roadmap into concrete implementation steps.
The goal is to add address-range intent and endpoint IP policy without making
dnsmasq export mutate Nautobot IPAM state.

The implementation is allowed to be destructive. Do not add long-lived
compatibility fields, compatibility policy values, or legacy export paths only
to preserve old behavior. The desired end state should be explicit and clean:

- Add range intent as nintent desired state, not as an assumed Nautobot model.
- Let evaluation report policy/range mismatches before enforcing them hard.
- Extend dnsmasq export as a deterministic artifact producer only.
- Require explicit endpoint IP policy instead of inferring DHCP reservations
  from `generate_dnsmasq`.

## Step 1: Define the data model contract

### Goal

Introduce explicit IP allocation intent and remove the implicit coupling
between DNS export and DHCP reservation export.

### Changes

Add `DesiredEndpoint.ip_policy` with an initial choice set:

- `static`: endpoint uses a manually assigned address; DNS records may be exported, DHCP reservations should not be exported.
- `dhcp_reserved`: endpoint should be exported as a DHCP reservation when MAC and node facts are deterministic.
- `external`: endpoint is outside nintent/IPAM DHCP management.

Add a new `DesiredIPRange` model:

- `name`
- `slug`
- `start_address`
- `end_address`
- `range_policy`
- `lifecycle`
- `generate_dnsmasq`
- `dnsmasq_options`
- `description`
- optional future scope fields can be deferred

Initial `range_policy` choices:

- `static_pool`
- `dhcp_reservable_pool`
- `dhcp_dynamic_pool`
- `excluded`

Initial `lifecycle` choices should match the existing intent style:

- `planned`
- `approved`
- `active`
- `deprecated`
- `retired`

### Notes

Use plain string fields for addresses at the model boundary, matching
`DesiredEndpoint.ip_address`, but validate and normalize with Python's
`ipaddress` module in loaders, forms, evaluation, and export helpers.

Do not use the model name `IPRange`. The model should clearly be desired state,
for example `DesiredIPRange`.

### Completion criteria

- The schema contains `DesiredEndpoint.ip_policy` and `DesiredIPRange`.
- `ip_policy` has no compatibility-only value.
- Existing seed/YAML/test data is updated to set explicit endpoint policies.
- The admin/UI model layer can create and display `DesiredIPRange` rows.

## Step 2: Wire the model through Nautobot UI surfaces

### Goal

Make the new intent visible and editable through the same surfaces as existing
nintent objects.

### Changes

Update:

- `models.py`
- `forms.py`
- `tables.py`
- `filters.py`
- `views.py`
- `urls.py`
- `navigation.py`
- detail/list templates

For `DesiredEndpoint`, add `ip_policy` to:

- edit form
- detail page
- list table
- filter set
- quick-add flow if the field is useful there

For `DesiredIPRange`, add standard list, detail, create, edit, and delete views.

### Completion criteria

- A user can manually create a desired range such as `192.168.0.200` through `192.168.0.250` with `range_policy=dhcp_dynamic_pool`.
- A user can set a desired endpoint to `ip_policy=dhcp_reserved`.
- Endpoint pages show an explicit policy for every endpoint with IP intent.

## Step 3: Extend YAML loading and import

### Goal

Allow desired ranges and endpoint IP policies to be declared in source YAML.

### Changes

Update `loaders.py`:

- Add a `DesiredIPRangeEntry` dataclass.
- Parse a top-level `desired_ip_ranges` section.
- Validate required range fields.
- Validate `range_policy`, `lifecycle`, and `generate_dnsmasq`.
- Validate address strings enough to catch obvious bad input.
- Add `ip_policy` to `DesiredEndpointEntry`.

Update `importers.py`:

- Add identity/default helpers for `DesiredIPRange`.
- Include `ip_policy` in desired endpoint defaults.
- Reject missing endpoint `ip_policy` when the endpoint has IP intent. Prefer
  failing the import over silently inferring DHCP behavior.

Update `ImportIntentSources` in `jobs.py`:

- Import desired ranges before or alongside endpoints.
- Include range counts in the import summary.

Suggested YAML shape:

```yaml
desired_ip_ranges:
  - name: home-dynamic-dhcp
    slug: home-dynamic-dhcp
    start_address: 192.168.0.200
    end_address: 192.168.0.250
    range_policy: dhcp_dynamic_pool
    lifecycle: active
    generate_dnsmasq: true
    dnsmasq_options:
      lease_time: 12h

desired_endpoints:
  - name: primary
    desired_node: pcmain
    endpoint_type: primary
    ip_address: 192.168.0.120
    dns_name: pcmain.home.arpa
    generate_dnsmasq: true
    ip_policy: dhcp_reserved
```

### Completion criteria

- YAML import can create/update `DesiredIPRange` rows.
- YAML import can set endpoint `ip_policy`.
- YAML endpoint entries with IP intent are updated to include explicit `ip_policy`.
- Loader and importer unit tests cover required fields and invalid choices.

## Step 4: Add pure range classification helpers

### Goal

Keep address-range logic testable outside Nautobot/Django.

### Changes

Add pure helper functions, either in `evaluations.py` or a focused helper module:

- Normalize endpoint IP strings to host addresses.
- Normalize desired range start/end addresses.
- Determine whether an endpoint IP is inside a desired range.
- Return all matching ranges, sorted deterministically.
- Detect invalid range definitions.
- Detect overlapping ranges.

Recommended facts for a range match:

```json
{
  "desired_ip_range_id": "...",
  "name": "home-dynamic-dhcp",
  "slug": "home-dynamic-dhcp",
  "start_address": "192.168.0.200",
  "end_address": "192.168.0.250",
  "range_policy": "dhcp_dynamic_pool",
  "lifecycle": "active",
  "generate_dnsmasq": true
}
```

### Completion criteria

- Pure unit tests cover IPv4 range containment.
- Invalid endpoint IPs do not crash evaluation.
- Invalid range rows produce deterministic gaps or skipped export reasons.
- Overlapping matching ranges are detected.

## Step 5: Extend endpoint evaluation with IP policy and ranges

### Goal

Make `Evaluate Endpoint Intent` explain whether an endpoint IP belongs in the
right desired address range.

### Changes

Update `evaluate_endpoint_intent()`:

- Accept `range_candidates`.
- Add `ip_policy` to expected endpoint facts.
- Add matching range facts to `observed_facts`.
- Add gap codes for range and policy problems.

Initial gap codes:

- `missing_ip_policy_range`
- `ambiguous_ip_policy_range`
- `ip_policy_range_mismatch`
- `invalid_ip_policy_range`
- `static_endpoint_in_dhcp_pool`
- `dhcp_reserved_endpoint_in_dynamic_pool`

Update `dhcp_reservation_ready`:

- In `dhcp_reserved`, require a single MAC candidate and no blocking policy/range gap.
- In `static` and `external`, return false for DHCP reservation readiness.

Update `EvaluateEndpointIntent` job:

- Load active/planned/approved `DesiredIPRange` rows.
- Pass them into `evaluate_endpoint_intent()`.

### Completion criteria

- Evaluation tests are updated to use explicit `ip_policy` values.
- A `dhcp_reserved` endpoint inside a `dhcp_reservable_pool` can be DHCP-ready.
- A `dhcp_reserved` endpoint inside a `dhcp_dynamic_pool` gets a warning/partial gap and is not DHCP-ready.
- A `static` endpoint does not become DHCP-ready even if a MAC candidate exists.

## Step 6: Extend dnsmasq export

### Goal

Generate DNS records, DHCP reservations, and DHCP ranges from explicit intent.

### Changes

Update `dnsmasq.py`:

- Add `dhcp_ranges` to `DnsmasqExport`.
- Add desired ranges as an input to `export_dnsmasq_records()`.
- Generate `dhcp-range=` lines from `DesiredIPRange.range_policy=dhcp_dynamic_pool` and `generate_dnsmasq=True`.
- Keep DHCP reservations tied to `DesiredEndpoint.ip_policy=dhcp_reserved`.
- Stop exporting DHCP reservations from DNS intent alone.
- Include skipped range details in export output.

Potential `dhcp-range=` format:

```text
dhcp-range=192.168.0.200,192.168.0.250,12h
```

The lease time should come from `dnsmasq_options.lease_time` when present.
If absent, either omit it or use a conservative default configured in nintent.

Update renderers:

- `render_dnsmasq_records_conf()` should include `dhcp-range=` lines.
- `dnsmasq_export_payload()` should include `dhcp_ranges`.
- Bump `DNSMASQ_EXPORT_SCHEMA_VERSION`.

Update `ExportDnsmasqRecords` job:

- Load desired ranges.
- Pass ranges to export.
- Log range counts.

### Completion criteria

- DNS record export tests pass after updating fixtures to explicit IP policies.
- Static endpoints do not produce `dhcp-host=`.
- DHCP reserved endpoints produce `dhcp-host=` only when evaluation says they are ready.
- Dynamic desired ranges produce stable `dhcp-range=` lines.
- JSON payload separates `dns_records`, `dhcp_reservations`, `dhcp_ranges`, and `skipped`.

## Step 7: Update Ansible consumption

### Goal

Let dnsmasq range configuration come from nintent export artifacts instead of
fixed Ansible parameters.

### Changes

Decide between two deployment shapes:

1. Keep a single `dnsmasq-records.conf` artifact containing records, reservations, and ranges.
2. Split into `dnsmasq-records.conf` and `dnsmasq-ranges.conf`.

The first shape is simpler and matches the current playbook.
The second shape is cleaner if service settings remain in `ansible.conf` while
all nintent-generated DHCP/DNS statements live under separate files.

Update `ansible_agdev/playbooks/deploy_nintent_dnsmasq_records.yml` as needed:

- Download the new or updated artifact.
- Install it under `/etc/dnsmasq.d/`.
- Keep `dnsmasq --test --conf-file=%s` validation.

Update docs to state that static `dnsmasq_dhcp_ranges` is no longer the normal
source of truth once `DesiredIPRange` export is enabled.

### Completion criteria

- Running the playbook deploys the generated `dhcp-range=` lines.
- An empty desired range set renders no `dhcp-range=` lines and remains valid.
- Ansible validation catches malformed generated config.

## Step 8: Add IPAM reconcile as a separate job

### Goal

Optionally reflect nintent desired state into Nautobot IPAM without coupling
that side effect to dnsmasq export.

### Changes

Add a future `Reconcile Desired IPAM Intent` job.

Initial responsibilities:

- Create or link `IPAddress` objects for `DesiredEndpoint.ip_policy=dhcp_reserved`.
- Use `IPAddress.type=DHCP` or the environment's equivalent if available.
- Avoid automatic overwrite when an existing IP has conflicting DNS name, assignment, or type.
- Report actions and conflicts through logs and evaluation facts.

Later responsibilities:

- Convert `DesiredIPRange` rows into Nautobot Prefix rows where possible.
- Split arbitrary ranges into CIDR prefixes only during Nautobot IPAM reconcile.
- Attach role/tag metadata to represent dynamic vs reservable pools.

### Completion criteria

- Export remains side-effect free.
- Reconcile can be dry-run before commit.
- Conflicts never auto-overwrite existing IPAM data.

## Step 9: Close the applied-state loop

### Goal

Evaluate whether generated intent has actually reached dnsmasq and the network.

### Changes

This can be deferred until range and endpoint intent are stable.

Potential checks:

- Store export hash and JobResult ID after Ansible deployment.
- Compare the dnsmasq host's installed file checksum against the latest export.
- Confirm DNS answers with `dig`.
- Inspect dnsmasq lease files for MAC/IP/name matches.
- Compare nodeutils observed primary IP/MAC against desired endpoint and IPAM facts.

### Completion criteria

- nintent can distinguish "desired", "exported", "deployed", and "observed".
- Evaluation output tells the user which stage is missing or stale.

## Test plan

Add or update tests in these areas:

- `test_loaders.py`: `desired_ip_ranges`, required endpoint `ip_policy`, invalid choices.
- `test_importers.py`: range identity/defaults and endpoint `ip_policy` persistence.
- `test_evaluations.py`: range containment, policy mismatch gaps, DHCP readiness changes.
- `test_dnsmasq.py`: `dhcp_ranges`, static endpoints, explicit DHCP reserved endpoints, and removal of implicit DHCP reservation export.
- Template tests: list/detail rendering for new fields where existing tests cover templates.

Prefer pure unit tests for range and export logic. Nautobot integration behavior can stay
behind model/job tests where the local test environment supports it.

## Destructive change rules

- Do not introduce `unspecified` or another compatibility-only policy value.
- Update existing seed, example, and test YAML to use explicit `ip_policy`.
- Remove implicit DHCP reservation export from `generate_dnsmasq=True`.
- Keep `generate_dnsmasq` scoped to dnsmasq DNS record generation.
- Use evaluation gaps for design warnings, but fail or skip export when output
  would be ambiguous or invalid.

## Open decisions

- Whether `dhcp-range=` lines should live in the current `dnsmasq-records.conf` or a separate artifact.
- Whether `dhcp_reservable_pool` should ever generate a dnsmasq range with special options, or remain validation-only.
- Whether range overlap should be `conflict` globally, or only when an endpoint lands in overlapping ranges.
- Whether the final endpoint policy name should be `static` or `manual_static`.
- Whether `DesiredIPRange` needs scope fields immediately, or can start global and add scope later.
