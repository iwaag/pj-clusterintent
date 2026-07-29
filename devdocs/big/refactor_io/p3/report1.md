# Phase 3 Step 1 Report — nintent desired-writer cutover

## Result

Complete locally. The batch service now resolves `realized_device`,
`realized_ip_address`, `realized_cluster`, and `realized_vm` UUID values to
their Nautobot rows. Unknown UUIDs produce a conflict and explicit `null`
clears a link. Relationship comparisons now use primary keys, fixing the
false `update` plans discovered while exporting the current desired state.

The Import Intent Sources Job, YAML loader/importer/planner stack, desired
node/compute mutation serializers and viewsets, their router registrations,
and the obsolete `intent_sources_file` setting were removed. Desired-state
writes are therefore confined to the batch endpoint; GraphQL and the UI remain
readers. Documentation now describes the batch endpoint as the sole writer.

## Verification

`cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests`
completed with **124 passing**, **10 expected Nautobot-runtime skips**.

The runtime gate remains pending alongside the matched nintent/nctl deployment
in Step 4. Step 2's exported `.local/desired-state.yaml` was retained locally;
its required all-unchanged live verification will run after the fixed nintent
commit is deployed.
