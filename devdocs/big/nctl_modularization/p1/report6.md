# P1 Step 6 — Prove the gate fails on divergence

Status: complete.

All three temporary, uncommitted injections failed their predicted gate and were restored:

1. Changing nctl `VMID_MIN` from 100 to 101 failed the consumer replay on the pinned constant.
2. Changing owner MAC normalization to upper case failed the freshness gate; regenerating only for
   the proof then failed nctl's replay on `mac-ok`, proving propagation into a consumer gate.
3. Hand-editing the fixture's expected MAC result failed the freshness gate.

After each revert, the relevant freshness and consumer tests passed. Commands and sanitized failure
logs are retained in the private evidence root; no injected divergence was committed.

## Gate verdict

Complete: consumer divergence, owner divergence, and fixture tampering each fail independently
and all working trees were restored to their committed contents.
