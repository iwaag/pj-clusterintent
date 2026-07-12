# Step 6 report: documentation and examples

## Summary

Step 6 is complete.

Updated user-facing documentation:

- `nintent/README.md`
- `nintent/CONCEPT.md`

## README updates

### Quick Host Add

Documented that blank DNS and mDNS fields on the primary endpoint are soft
defaulted from the canonical node name.

Covered example:

- node `pcmain`
- `dns_name: pcmain.home.arpa`
- `mdns_name: pcmain.local`

Also documented that names such as `PCMAIN.local` and `pcmain.home.arpa`
canonicalize to `pcmain`, and that explicit form values are never overwritten.

### Intent Source YAML

Added a minimal one-host/one-primary-endpoint YAML example where `dns_name` and
`mdns_name` are omitted.

Documented import result:

- `dns_name: pcmain.home.arpa`
- `mdns_name: pcmain.local`

Also documented that explicit YAML values are preserved and non-primary
endpoints are not auto-filled.

### dnsmasq and evaluation workflow

Documented the intended job order when DHCP reservations depend on discovered
node/interface facts:

1. `Evaluate Node Intent`
2. `Evaluate Endpoint Intent`
3. `Export dnsmasq Records`

Added explanation that endpoint evaluation consumes latest stored node
evaluation facts, so normalized node matches such as desired `pcmain` to actual
`pcmain.local` can provide interface and MAC candidates for DHCP export.

### Intent Evaluations

Updated node evaluation documentation to mention conservative home-lab suffix
normalization:

- `pcmain` and `pcmain.local` can match
- unrelated FQDNs such as `db01.prod.example.com` are not collapsed to `db01`

Updated endpoint evaluation documentation to mention interface facts from the
latest stored node evaluation, not only realized node links.

## CONCEPT updates

Updated `DesiredEndpoint` concept notes to describe primary endpoint DNS/mDNS
soft defaults and the non-primary/explicit-value boundaries.

Updated `IntentEvaluation` concept notes to describe:

- deterministic node evaluation against actual Nautobot Device/VM rows
- conservative name normalization
- endpoint evaluation consuming node evaluation facts for interface/MAC
  candidates

Updated stale current-boundary text that said evaluation jobs were not
implemented. The document now states that deterministic node, endpoint, and
service evaluation jobs exist, while optional AI review is not implemented yet.

## Verification

Executed the full local unit test suite from `nintent/`:

```text
python3 -m unittest discover nautobot_intent_catalog/tests
```

Result:

```text
Ran 61 tests in 0.005s
OK
```
