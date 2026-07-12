# Nodeutils Restructuring Plan

## Goal

Refactor `nodeutils` from a host-side Nautobot writer into a host-side inventory collector.

The host utility should collect local facts and emit a bounded, validated report. It should not require or store a Nautobot API token for the normal inventory flow.

## Background

The current `nautobot-self-register` command collects useful local inventory and directly creates or updates Nautobot Devices through the Nautobot API. This is convenient, but it distributes Nautobot write credentials to every participating host.

That credential model is the main issue to address. A compromised workstation should not be able to write arbitrary Nautobot inventory data or leak a token with broader API access than the host itself needs.

## Target Design

- Keep local fact collection in `nodeutils`.
- Move Nautobot write responsibility out of `nodeutils`.
- Emit inventory as JSON first; YAML can be a convenience output if needed.
- Make the report format versioned and stable enough for a server-side ingestor.
- Treat local host input as self-reported evidence, not authoritative classification.
- Keep sensitive data out of the report.

Recommended flow:

```text
host
  nodeutils collect
    -> inventory report JSON/YAML
    -> local file, stdout, SSH collection, rsync/SFTP upload, or HTTPS submit

central side
  validate report
  map host identity to trusted Nautobot fields
  write to Nautobot with central-only API credentials
```

## Command Shape

Replace the current writer-oriented command with a collector-oriented command:

```bash
nodeutils collect --format json
nodeutils collect --format yaml
nodeutils collect --output /var/lib/nodeutils/inventory.json
```

Remove direct Nautobot write behavior from `nodeutils`. Do not keep aliases, hidden flags, or transitional entry points whose only purpose is preserving the old API-writing workflow.

## Report Schema

Add a top-level envelope around the collected facts:

```yaml
schema_version: nodeutils.inventory.v1
collector:
  name: nodeutils
  version: 0.1.0
  command: collect
identity:
  hostname: pc1
  fqdn: pc1.example.local
  serial_number: "..."
  machine_id: "..."
collected_at: "2026-06-21T..."
facts:
  system: Linux
  os_name: Ubuntu
  os_version: "..."
  hardware: {}
  cpu: {}
  memory: {}
  disk: {}
  network: {}
  gpu: {}
  software: {}
  services: {}
  proxmox: {}
self_reported:
  owner: eiji
  purpose: local-ai
  service_roles: []
  preferred_services: {}
```

Guidance:

- `identity` should contain data useful for matching a host, not trusted authorization.
- `facts` should contain observed local state.
- `self_reported` should contain local preference or intent, clearly separated from observed facts.
- Avoid letting the host report authoritative Nautobot fields such as final `role`, `location`, `status`, or `tags` unless the server side explicitly allows that value for the host.

## Sensitive Data Rules

Continue the current conservative collection policy:

- Do not collect environment variables.
- Do not collect secret files.
- Do not collect container logs.
- Do not collect bind-mounted file contents.
- Do not collect full process command lines if they may include tokens.
- Keep Docker collection limited to scheduler-facing facts.

Add explicit redaction and size bounds:

- Limit report size.
- Limit string length for service labels, image names, compose projects, and port summaries.
- Drop or redact suspicious keys if future collectors parse structured service metadata.
- Store local report files with mode `0600` when `--output` writes to disk.

## Transport Options

`nodeutils` should not own one mandatory transport. It should support collector output that multiple transports can reuse.

Supported first:

- stdout for Ansible SSH collection.
- local file output for later pickup.

Possible later:

- signed report file.
- HTTPS submit to a narrow central ingest endpoint.
- SFTP/rsync upload to a central drop directory.

For laptops or NAT/private hosts, push-based upload is often more reliable than central SSH pull. For always-on servers and Proxmox hosts, Ansible SSH pull is reasonable.

## Optional Signing

For stronger provenance, add detached or embedded Ed25519 signatures later:

```yaml
signature:
  algorithm: ed25519
  key_id: pc1-2026-01
  value: "base64..."
```

This is useful when reports are uploaded through an untrusted or semi-trusted path. It does not make self-reported facts authoritative; it only confirms which host key produced the report.

## Configuration Changes

Split config into two concerns:

- Local collection config:
  - enabled collectors
  - service probe hints
  - preferred services
  - owner/purpose hints
  - output path
- Server-side Nautobot ingest config:
  - belongs in `nauto`, not `nodeutils`
  - contains central mappings, allowlists, and Nautobot object defaults

Recommended file names:

- `self_inventory.yaml` remains host-local hints.
- `.env` should no longer be required for collection.
- Remove `NAUTOBOT_URL` and `NAUTOBOT_TOKEN` handling from the normal `nodeutils` configuration path.

## Implementation Steps

1. Extract collection output into a stable `build_inventory_report(config, inventory)` function.
2. Add `--format json|yaml` and `--output PATH` for collector output.
3. Remove Nautobot API client, token loading, and Device upsert behavior from the host-side command.
4. Add a schema version and top-level report envelope.
5. Add file write behavior with restrictive permissions.
6. Add unit tests for report shape, no-token collection, and output formatting.
7. Update `README.md` to describe collector-first operation.
8. Remove direct Nautobot write examples and `.env` token setup from the documentation.
9. Remove packaging entry points that expose the old writer-oriented command name unless they are renamed to the collector command without preserving old semantics.

## Acceptance Criteria

- A host can run inventory collection without `NAUTOBOT_URL` or `NAUTOBOT_TOKEN`.
- The generated report includes `schema_version`, `collector`, `identity`, `collected_at`, `facts`, and `self_reported`.
- The report does not include known secret sources.
- A central process can ingest the report without running host-local commands.
- `nodeutils` no longer contains a Nautobot write token path or direct Device upsert command.

## Open Questions

- Should reports use JSON only, or should YAML be supported as a first-class output?
- Should report signing be implemented immediately or after the basic central ingest works?
- What host identity should be primary for matching: serial number, machine-id, hostname, SSH host key, or a configured node ID?
- How much local preference should be allowed to influence Nautobot fields without central approval?
