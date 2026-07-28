# P2 Step 3 — Move compute collections and source-issue policy

Status: complete.

`nctl_core.compute.collection` now owns compute row decoding, collection
assembly, endpoint-MAC validation, and all `DesiredSourceIssue` classification.
It imports desired nodes/endpoints only under `TYPE_CHECKING`; the compute
package therefore remains free of transport, Nautobot, CLI, and HTTP imports.
`sources/desired.py` now owns the GraphQL query, transport models, row decoders,
snapshot construction, and its decode-time malformed-MAC tolerance only.

The source-issue assertions moved without deletion or weakening to
`tests/test_compute_collection.py`; transport assertions remain in
`tests/test_sources_desired.py`. The module-boundary test now covers
`compute.collection` in addition to the model and contract modules.

The Phase 1 source-issue corpus was recaptured into private evidence and its
diff against the Step 0 baseline is empty. The named `compute-inert` proof
passed, confirming valid compute collections still create no drift or plan
actions.

Gates passed: focused collection/transport/boundary/conformance/inertness
tests `18 passed`; nctl ordinary `971 passed in 5.64s`; superproject
compute-conformance freshness gate `1 passed`; `git diff --check` clean.
No fixture, source-issue field/value, compute semantics, drift/planning/
actuation behavior, or external state changed.
