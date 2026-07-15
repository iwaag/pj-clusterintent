# Phase 1 Report — Step 2 (GraphQL fetch layer for the renderer)

Date: 2026-07-14. Implements [p1/plan.md](plan.md) Step 2. Continues from
[report1.md](report1.md) (the ported, mapping-based `nctl_core/dnsmasq.py` renderer).

## Risk resolved first (as the plan required)

Before pinning the query, checked the live dev Nautobot's GraphQL schema for the exact fields and
filterability the plan flagged as unverified:

- `DesiredEndpointType`, `DesiredIPRangeType`, `DesiredNodeType`, `IntentEvaluationType` all expose
  every field the renderer needs (`name`, `endpoint_type`, `ip_address`, `ip_policy`, `dns_name`,
  `mdns_name`, `vpn_dns_name`, `generate_dnsmasq`, `dnsmasq_record_type`, `id`; `start_address`,
  `end_address`, `dnsmasq_options`, `range_policy`, `lifecycle`; `target_type`, `target_id`,
  `reviewed_at`, `created`, `observed_facts`, `deterministic_summary`, `actual_refs`).
- `Query.intent_evaluations` **does** support a `target_type` filter (confirmed via introspection
  of `Query`'s field args), so the plan's client-side-split fallback wasn't needed — both
  evaluation sets are fetched pre-split via two aliased calls in one request.
- **Unplanned discovery**: Nautobot's GraphQL layer serializes Django `ChoiceField` values as their
  **uppercase enum name**, not the lowercase value stored in the DB and used throughout
  `dnsmasq.py`'s vocabulary. Live query results showed `"endpoint_type": "PRIMARY"`,
  `"ip_policy": "DHCP_RESERVED"`, `"lifecycle": "PLANNED"`, `"range_policy": "DHCP_DYNAMIC_POOL"`,
  `"target_type": "DESIRED_ENDPOINT"` where the renderer's constants
  (`ELIGIBLE_ENDPOINT_TYPES`, `SUPPORTED_RECORD_TYPES`, etc.) and the DB's own stored values are
  lowercase. Filtering `intent_evaluations(target_type: "desired_endpoint")` with a **lowercase**
  argument still worked correctly (confirmed both target types return the right rows) — only the
  echoed-back field value is uppercased, not the filter input. Free-form JSON fields
  (`observed_facts`, `actual_refs`, ...) are `GenericScalar` and round-trip in native case
  unaffected (e.g. `actual_node_ref.object_type` stayed `"dcim.device"`).
  This wasn't in the plan's risk list and would have silently produced an all-skipped export
  (every eligibility check compares against lowercase constants) had it gone unnoticed.

## What was built

- New module `nctl/src/nctl_core/dnsmasq_query.py`:
  - `DNSMASQ_QUERY` — one pinned GraphQL request: `desired_endpoints` (with the nested
    `desired_node { id name slug lifecycle }`), `desired_ip_ranges`, and two aliased
    `intent_evaluations` calls (`endpoint_evaluations` / `node_evaluations`) pre-filtered by
    `target_type`.
  - `fetch_dnsmasq_inputs(client) -> DnsmasqFetch` — runs the query and returns a dataclass
    (`endpoints`, `ip_ranges`, `endpoint_evaluations`, `node_evaluations`) shaped exactly for
    `nctl_core.dnsmasq.export_dnsmasq_records`. Normalizes the uppercase-enum fields
    (`endpoint_type`, `ip_policy`, `dnsmasq_record_type` on endpoints; `range_policy`, `lifecycle`
    on ranges and the nested node) back to lowercase; leaves JSON/free-form fields untouched.
  - `latest_evaluations(rows) -> dict[str, dict]` — client-side port of nintent's
    `_latest_evaluations`: groups by `target_id`, keeps one row per target ranked by
    `(-reviewed_at, -created)`, with ties (including both-null `reviewed_at`) falling back to
    first-occurrence order, matching the original queryset's `.order_by(...)` +
    `dict.setdefault(...)` behavior.

## Verification

- `uv run pytest tests/test_dnsmasq_query.py -q` — 6 passed: two `latest_evaluations` ordering
  cases (highest `reviewed_at` wins, `created` breaks a `reviewed_at` tie), one full-tie
  first-occurrence case, one null-`reviewed_at` case, one respx-mocked `fetch_dnsmasq_inputs` case
  asserting the lowercasing and evaluation split, and one query-shape assertion for the aliased
  filters.
- `uv run pytest -q` (full nctl suite) — 67 passed, 0 failures.
- **Live end-to-end smoke check** (not a committed test, exploratory only): ran
  `fetch_dnsmasq_inputs` against the dev Nautobot from `.local/localenv_memo.md`'s token, piped the
  result straight into Step 1's `export_dnsmasq_records` / `render_dnsmasq_records_conf`. Produced
  a plausible conf (5 `host-record`s, 3 `dhcp-host` reservations, 1 `dhcp-range`, 4 skipped details)
  from the 5 real desired endpoints and 3 desired IP ranges currently in dev Nautobot — confirms
  the fetch layer's output shape actually satisfies the renderer, not just its own unit tests.
  This is exploratory, not the plan's Step 3 parity gate (that needs `nctl render dnsmasq` to exist
  first and diffs against a fresh Job run byte-for-byte).

## Deviations from plan

- The uppercase-enum-serialization normalization (above) wasn't anticipated in the plan; handled
  entirely inside `dnsmasq_query.py` so `dnsmasq.py`'s vocabulary and tests from Step 1 stay
  untouched.
- Otherwise no deviation: fetched in one request as planned, both evaluation sets came pre-split
  via the FilterSet (no REST fallback needed), and `latest_evaluations` was unit-tested against
  tie cases per the plan's instruction.

## Commit boundary

Clean, self-contained: `dnsmasq_query.py` + its tests, full suite green, no dependency on anything
outside `nctl`. Still the same suggested-commit-order slot (commit 1 of 5, "nctl: renderer port +
GraphQL fetch + `render dnsmasq` + tests") — this closes the fetch-layer portion of it.

**Not done yet, deliberately left for the next commit(s):**
- Step 3 — `nctl render dnsmasq` CLI command (`--out`, `--json` envelope) and the parity gate: a
  fresh run of the live `Export dnsmasq Records` Job, diffed byte-for-byte against this fetch
  layer's output through Step 1's renderer, with the procedure and result recorded in the report.
- Steps 4-7 remain downstream of Step 3 per the plan's ordering rationale.

## Exit criteria status

- [ ] `nctl render dnsmasq` output matches the last Job export on live data — pending Step 3 (the
  fetch+render path now works end-to-end against live data per the smoke check above, but the
  byte-for-byte parity gate against a fresh Job run hasn't run yet).
- [ ] `nctl apply dnsmasq` — pending Step 6.
- [ ] `nintent` contains no dnsmasq rendering — pending Step 4.
- [ ] The dnsmasq playbook is deploy-only — pending Step 5.
- [x] `uv run pytest` passes in nctl, including the fetch-layer tests (67 passed).

Next: Step 3 — build `nctl render dnsmasq`, then run the parity gate against a fresh live Job
export before Step 4 deletes anything in nintent.
