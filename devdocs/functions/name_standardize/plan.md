# Desired node name normalization and default endpoint names

## Motivation

The current intent workflow assumes that a desired node can be matched to an
actual Nautobot `Device` or `VirtualMachine` by name-like fields. In practice,
nodeutils may report device names as mDNS-style names such as `pc1.local`, while
the desired node is usually entered as the short PC name, such as `pc1`.

This causes two user-visible problems:

- `DesiredNode.name=pc1` may not match an actual `Device.name=pc1.local`.
- DHCP reservations may not be generated because endpoint evaluation cannot
  find a single actual node/interface/MAC candidate.

The common home-lab case is also intentionally simple: one PC normally has one
primary endpoint. For that case, the user should not need to manually type the
standard DNS names every time. If a PC is named `pcmain`, the default desired
endpoint names should be:

- DNS: `pcmain.home.arpa`
- mDNS metadata: `pcmain.local`

These defaults should be soft defaults. Explicit user values must always win.

## Migration and compatibility stance

This work is in a destructive-change phase. Backward compatibility is not a
goal. Avoid adding compatibility shims, legacy aliases, transitional fields, or
multi-version behavior that would remain as long-term artifacts.

If a schema migration becomes larger than the feature warrants, prefer clearing
development data and starting from a clean state. The implementation should
optimize for the desired final model and workflow, not for preserving current
test or local Nautobot data.

Do keep raw observed names in evaluation facts and imported inventory metadata
when they are useful for auditability and troubleshooting. That is not a
backward-compatibility requirement; it is operational evidence.

## Requirements

### Node identity matching

- Treat `pc1` and `pc1.local` as the same node identity for desired-vs-actual
  matching.
- Normalize only known local suffixes. Use `.local` and `home.arpa` as the
  built-in home-lab identity suffixes for this phase.
- Do not blindly strip every domain suffix. Names such as
  `db01.prod.example.com` must not accidentally collapse to `db01`.
- Use the same normalization rule for:
  - candidate scoring
  - explicit link mismatch checks
  - default endpoint name generation
- Preserve raw observed names in Nautobot and evaluation facts for auditability.
  Normalization is a comparison/generation behavior, not a destructive ingest
  behavior.

### Default endpoint names

- Apply default DNS name generation to the simple one-host/one-primary-endpoint
  path first.
- For `Quick Host Add`, if `dns_name` is blank, generate
  `<canonical-node-name>.home.arpa`.
- For `Quick Host Add`, if `mdns_name` is blank, generate
  `<canonical-node-name>.local`.
- Never overwrite explicitly provided `dns_name` or `mdns_name`.
- Limit automatic generation to the primary endpoint initially:
  - `endpoint_name=primary`
  - `endpoint_type=primary`
- Keep normal `DesiredEndpoint` CRUD flexible. It should not silently rewrite
  fields while editing arbitrary endpoints.
- YAML import may apply the same defaults only when the endpoint is primary and
  the field is missing or blank.

### DHCP reservation flow

- A name-normalized desired node match should be usable by endpoint evaluation.
- Endpoint evaluation should be able to use the latest node evaluation facts, so
  a node found by candidate matching can contribute interface and MAC candidates.
- `Export dnsmasq Records` should remain a deterministic consumer of evaluation
  data. It should not perform its own name matching.

## Design notes

Introduce a small shared helper for host identity normalization and default name
generation. Keep it separate from the model definitions so it can be used by
loaders, importers, operations, and evaluation helpers without creating model
side effects.

Suggested helper responsibilities:

- trim and lowercase host-like names
- strip a configured local suffix only when the suffix is known
- return a host label suitable for default DNS/mDNS generation
- generate `home.arpa` and `.local` endpoint names from that canonical label

The first implementation can hard-code the conservative defaults in code:

- local identity suffixes: `local`, `home.arpa`
- default DNS suffix: `home.arpa`
- default mDNS suffix: `local`

Do not add configuration indirection unless there is an immediate requirement.
For this phase, fixed policy is cleaner than a compatibility/configuration layer.

## Implementation plan

### Step 1: Add shared name helper

- Add a module such as `nautobot_intent_catalog/names.py`.
- Implement:
  - `canonical_node_name(value)`
  - `default_dns_name(node_name, suffix="home.arpa")`
  - `default_mdns_name(node_name)`
- Keep behavior conservative:
  - `pc1` -> `pc1`
  - `PC1.local` -> `pc1`
  - `pc1.home.arpa` -> `pc1`
  - `db01.prod.example.com` -> `db01.prod.example.com`
- Add focused unit tests for normalization and default generation.
- Do not add legacy aliases, compatibility maps, or data migration helpers for
  old name forms.

### Step 2: Use canonical names in node evaluation

- Update `_node_candidate_score()` in `evaluations.py` to compare canonical
  node names for name/hostname fields.
- Update `_node_mismatches()` so hostname mismatch checks use the same
  canonicalization.
- Keep serial, UUID, and platform comparisons unchanged.
- Add tests proving:
  - `DesiredNode.name=pc1` matches `Device.name=pc1.local`
  - an explicit realized link with `pc1` vs `pc1.local` is not a hostname
    conflict
  - unrelated FQDNs are not collapsed unexpectedly

### Step 3: Soft defaults in Quick Host Add

- Update `operations/hosts.py` so
  `create_desired_node_with_primary_endpoint()` fills blank `dns_name` and
  `mdns_name` only for the primary endpoint.
- Use the canonical node name, not the raw display name, when generating:
  - `dns_name=<canonical>.home.arpa`
  - `mdns_name=<canonical>.local`
- Preserve explicit `dns_name` and `mdns_name`.
- Add tests for:
  - blank values are filled
  - explicit values are preserved
  - non-primary endpoint values are not auto-generated

### Step 4: Soft defaults in YAML import

- Update import flow so `desired_endpoint_defaults()` can see the resolved
  desired node when deciding defaults.
- Apply the same primary-endpoint-only rule for missing or blank `dns_name` and
  `mdns_name`.
- Keep loader behavior mostly structural. Prefer applying defaults at importer
  or operation boundary where the referenced node is already resolved.
- Do not preserve old YAML behavior through alternate roots or compatibility
  switches. Missing/blank primary endpoint names should follow the new default
  policy.
- Add tests for:
  - YAML endpoint with blank/missing names gets defaults
  - explicit YAML values are preserved
  - non-primary YAML endpoint is not auto-filled

### Step 5: Make endpoint evaluation consume node evaluation facts

- Adjust `EvaluateEndpointIntent` so it uses the latest stored node evaluation
  for the endpoint's desired node when available.
- Avoid re-running `evaluate_node_intent()` with empty candidate sets as the
  only source of node facts.
- Ensure endpoint evaluation can read interface facts from a node evaluation
  that found a single candidate by normalized name.
- Add tests around endpoint MAC candidate discovery from node evaluation facts.

### Step 6: Documentation and examples

- Update `README.md` Quick Host Add section:
  - explain `pcmain.home.arpa` and `pcmain.local` defaults
  - state that explicit values are preserved
- Update the Intent Source YAML section:
  - mention primary endpoint defaulting when fields are omitted
  - keep examples either explicit or add a minimal omitted-field example
- Update `CONCEPT.md` if it describes endpoint naming boundaries.

### Step 7: Verification

- Run local unit tests for `nintent`.
- Run a focused manual scenario in Nautobot:
  - ingest actual device as `pcmain.local`
  - create desired node `pcmain` with Quick Host Add and blank DNS/mDNS fields
  - run node evaluation
  - run endpoint evaluation
  - export dnsmasq records
- Expected result:
  - desired node has primary endpoint DNS `pcmain.home.arpa`
  - desired endpoint has mDNS metadata `pcmain.local`
  - node evaluation finds exactly one actual node
  - endpoint evaluation finds exactly one MAC candidate
  - dnsmasq export contains both `host-record=` and `dhcp-host=` when IP and
    MAC facts are available
