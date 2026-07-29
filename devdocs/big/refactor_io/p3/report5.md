# Phase 3 Step 5 Report — Live acceptance

## Deployment

The scratch image was rebuilt without cache and installed the pushed nintent
commit `305e457433be57f0ce60e54eff681ac7304008fa`; the build's installed-revision
check passed. Containers restarted healthy and `post_upgrade` completed with
no migrations. The stale Import Intent Sources Job row was removed. Its exact
scratch-only dependencies were 19 JobResults, 76 log entries, 19 file proxies,
and one queue assignment; no unrelated Job row was touched.

## Acceptance

- `nctl desired apply -f -` dry-ran a synthetic `p3-smoke-node` create, then
  `--yes` committed it; GraphQL returned the active synthetic node.
- `nctl lifecycle p3-smoke-node active` changed planned to active once; the
  immediate repeat reported no change.
- A synthetic `dcim.Device` was created, linked via the nctl ledger batch
  writer, and confirmed through GraphQL.
- PATCH to the removed desired-node REST route returned HTTP 404.
- `nctl drift --json` returned `ok: true`; dry `nctl reconcile` completed.
  Existing cluster drift findings were read-only pre-existing state and were
  not actuated.
- The synthetic desired node was deleted through a batch, then the synthetic
  Device was deleted; follow-up queries found neither row.

No token, private desired-state document, or synthetic row remains.
