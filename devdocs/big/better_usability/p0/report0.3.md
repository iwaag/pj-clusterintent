# Phase 0 — Step 0.3 report: Classify fields by authority, not current implementation

Parent: [plan.md](plan.md) Step 0.3.

## What was done

Added `field-classification.md` §2's "Decision notes for difficult classification cases", covering
every topic the plan requires explicitly: node/service lifecycle semantics, node type vs. accepted
actual types, identity/name/slug/catalog metadata, endpoint fields and connection selection,
service requirements/dependencies/placement/config, actual-state policy and observed-vs-declared
hosts, expected/declared OS, SSH port/power/laptop, reconciliation and import-analysis caches, and
IP range policy/lifecycle/dnsmasq controls.

While closing the last of these, traced `nctl_core/dnsmasq.py` and `dnsmasq_query.py` (out of this
phase's originally-scoped file list) specifically to resolve an item left open in Step 0.1/0.2:
whether `DesiredIPRange.lifecycle` gates anything. **It does** — dnsmasq range export uses the same
`ELIGIBLE_NODE_LIFECYCLES` set as node bootstrap export (`dnsmasq.py:367-372`, code
`range_lifecycle_not_exportable`), which already includes `planned`. This closes the open question
the plan requires closed before Step 0.7's consistency review: a range at its model default is
already dnsmasq-exportable today, so no hidden-gate risk exists for this field. Updated the
corresponding table row and JSON appendix entry (`dnsmasq_options.lease_time` confirmed consumed at
`dnsmasq.py:341`) from "unverified" to a confirmed finding.

## Key decisions of record

- **`DesiredNode.lifecycle`** is the only lifecycle field this roadmap needs to default to `active`
  (Phase 3) — it is the sole field with real enforcement (bootstrap export gate + production
  gate). **`DesiredService.lifecycle`** gates nothing structurally (only a drift warning) and needs
  no default change; Phase 3 records this as a considered decision, not a gap.
- Identity fields (name/slug/display_name/catalog metadata) stay Intent everywhere even where a
  convenience default exists, because the system can guess a *value* but never the operator's
  *intent* to accept that guess — this is the dividing line between Intent-with-suggested-default
  and true Derived fields.
- Connection selection (`connection_path` + `local_endpoint`/`tailscale_endpoint`) is confirmed
  Derived and spans two models — endpoint topology (single usable endpoint / single designated
  primary / genuine ambiguity) drives it, never arbitrary selection. This is the rule Step 0.4 will
  specify in executable-quality detail.
- No open item from this step can change schema shape, tier, derivation, default, or phase
  ordering — the one item that could have (`DesiredIPRange.lifecycle`'s consumption) was traced and
  closed in this step rather than deferred.

No blocking surprises requiring human judgment.

## Next step

Step 0.4 — write the executable-quality derivation/override/provenance rulebook (§4) for every
Derived/Override row identified above, covering the roadmap's required scenario matrix (fresh
observed host, bootstrap-only node, missing/stale/unsupported OS, declared HAOS-like host, single
vs. ambiguous endpoints, forced Tailscale/non-standard port, unsafe OS/power combination), and
select the Phase 2 persistence shape (auto-materialize vs. dissolve) for
`DesiredNodeOperationalConfig`.
