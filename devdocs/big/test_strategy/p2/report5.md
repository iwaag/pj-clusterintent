# Test Strategy Phase 2 — Step 5 Report: Goldens and Ownership Cleanup

Parent: [plan.md](plan.md), Step 5.

Status: **`complete`**.

## Golden ownership

The only checked-in byte golden is the deterministic dnsmasq v5 records file. Its identical copies
in `nctl` and `nodeutils` intentionally serve different consumers:

- nctl proves exact renderer bytes and digest; and
- nodeutils proves content-free managed-file observation of that digest.

Both copies have SHA-256 `c25e51c4efce07281e580dcfb1ecad73d666a70310f87cd28ad448241215e592`.
They each have semantic companion assertions, so neither is a snapshot-only proof. The recorded
update procedure requires an intentional renderer-contract change and an exact cross-repository
byte/digest review.

No other checked-in golden or snapshot artifact has a byte consumer, and no fixture/helper has
lost its final consumer. Nothing was deleted.

Verification passed: nctl dnsmasq suite **25 passed**; nodeutils inventory-report suite **16
passed**. The private golden and fixture consumer ledgers are under
`.local/test-strategy/p2/20260726T144434Z/`.
