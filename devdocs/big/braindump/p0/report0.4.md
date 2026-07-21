# Phase 0 Step 0.4 — Pin the freshness presentation contract

Parent: [plan.md](plan.md), Step 0.4.

## Check performed

Traced each timestamp source the plan's Step 0.4 requires, against the live nintent/nctl code
rather than assuming they exist.

| Source | Verified field | Location |
|---|---|---|
| Nautobot `PrimaryModel` timestamps | Serializers use `fields = "__all__"` (e.g. `api/serializers.py:21,61,80`), which exposes framework-owned `created`/`last_updated` automatically for any `PrimaryModel` subclass, including the future `BrainDumpDocument`/`AlignmentReview` — no explicit serializer field declaration is needed to get them. |
| nodeutils observation facts | `nctl_core/sources/observed.py`'s `ObservedFacts.collected_at: datetime`, read from `dump.collected_at` in `read_observed_facts()`. |
| Existing actual-state timestamps | `nctl_core/sources/actual.py`'s `ActualFacts.collected_at` (mapped from Nautobot custom field `"last_seen"`) and `ActualFacts.service_inventory_updated_at` — both already flow into `ActualSnapshot`. |
| `nctl drift`/source envelope | `nctl_core/sources/snapshot.py`'s `SourceSnapshot.fetched_at: datetime` is the top-level fetch timestamp already returned with every drift/status call. |

## Conclusion

All timestamps the plan's required baseline needs are already exposed by existing code paths with
no new plumbing:

- `BrainDumpDocument.last_updated` and `AlignmentReview.last_updated` will come for free from
  `PrimaryModel` + `fields = "__all__"`, the same way every other model in this app already exposes
  them.
- Desired/actual observation timestamps (`ActualFacts.collected_at`,
  `ActualFacts.service_inventory_updated_at`, `SourceSnapshot.fetched_at`) are already present in
  the snapshot Phase 2 will read — Phase 2 does not need to widen any existing source contract to
  compare "review vs. braindump vs. desired/actual freshness" as this step allows.

This confirms the plan's required baseline comparison is achievable with zero new fields:

```text
review missing                                  -> unreviewed
review.last_updated < braindump.last_updated    -> needs attention
otherwise                                       -> review present
```

and that a conservative `may_need_attention` extension (comparing against
`ActualFacts.collected_at`/`service_inventory_updated_at`/`SourceSnapshot.fetched_at`) is available
to Phase 2 without a new timestamp ledger, fingerprint store, or event listener — exactly the
constraint this step imposes. No edit to `plan.md` was required.
