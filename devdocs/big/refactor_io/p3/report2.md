# Phase 3 Step 2 Report — One-time desired-state export

## Result

Complete. Before the loader removal, the current
`nauto/seed/intent_sources.yaml` was normalized once into the ignored private
file `.local/desired-state.yaml`. It contains **27** Phase 0 batch operations.

The first verification exposed the batch planner's relationship-object versus
UUID comparison defect. Step 1 corrected that comparison. After the matched
nintent deployment, an authenticated `dry_run: true` POST returned exactly
**27 `unchanged`** operations and no create, update, delete, or conflict.

The local file is therefore a lossless Phase 4 input for repopulating the
scratch database; it is ignored and was never committed or printed.
