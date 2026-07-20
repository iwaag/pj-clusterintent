# Step 3 report — declare dnsmasq in the ledger (data entry, documented)

No nctl/ansible_agdev code changes in this step — data entry plus documentation, as the plan
specifies.

> **Superseded, 2026-07-21 (Better Usability Phase 4):** the `nautobot-server shell` step below
> was necessary only because Django admin/form views need a browser session, not the bearer
> token available to this transcript. The current recipe uses the Nautobot UI directly and needs
> no shell — see [`nctl/docs/add-a-basic-service.md`](../../../nctl/docs/add-a-basic-service.md).
> This transcript is left unchanged as a historical record.

## Live data entry

Created on the dev Nautobot instance (`http://localhost:8000/`), via `nautobot-server shell`
inside the `nautobot-nautobot-1` container (see "why shell, not REST/UI" below):

- `IntentSource` `manual` (`a55f0db1-0d25-49f7-ba92-9ade0d3fcd02`, `source_type=manual`) — did not
  exist yet; `DesiredService.intent_source` is a required (non-null) FK, so a manual-entry source
  had to be created first.
- `DesiredService` `dnsmasq` (`e31d3b99-d4ab-4646-913a-27b92ccfdf66`), `service_type=service`,
  `lifecycle=active`, `catalog_namespace=default`, `catalog_metadata_name=dnsmasq`.
- `DesiredServicePlacement` `dnsmasq` on node `agdnsmasq` (`597dafda-720a-4abd-8913-8b15dff1ace9`),
  `desired_state=active`, `deployment_profile=dnsmasq`, `config_schema_version="1"`, `config={}`
  (empty — the `dnsmasq_server` Ansible role's own defaults are safe: DHCP off, listens on
  `127.0.0.1` only; the recipe doc calls out which knobs to override for a real network).

The `agdnsmasq` `DesiredNode` and its `primary` endpoint (`mdns_name=agdnsmasq.local`) already
existed from prior scenario-1 setup — nothing to create there.

### Why `nautobot-server shell`, not REST or the UI

`ansible_agdev`/nintent's REST API (`nautobot_intent_catalog/api/urls.py`) only registers DRF
viewsets for `nodes`, `services`, `endpoints` — `IntentSource` and `DesiredServicePlacement` have
no REST endpoint, only Django admin/form views, which need a browser session + CSRF token rather
than the bearer token in `.local/localenv_memo.md`. Using the management shell against the same
dev-only Postgres the running Nautobot container reads is the direct equivalent of "UI/REST on the
live instance" the plan asked for, with the same end state (verified below), and is idempotent
(`get_or_create`, safe to re-run).

### Verification

`nctl render hosts-intent --json` against the live instance (see command below) now emits:
```json
"groups": ["dnsmasq_server", "ssh_hosts"],
"inventory": {"all": {"children": {
  "dnsmasq_server": {"hosts": {"agdnsmasq": {}}},
  "ssh_hosts": {"hosts": {"agbach": {...}, "agdnsmasq": {"ansible_host": "agdnsmasq.local", ...}, ...}}
}}}
```
confirming Steps 1–3 work together end to end: mDNS-connected `ssh_hosts` (Step 1) plus a
placement-derived `dnsmasq_server` group (Step 2) populated by the ledger data entered here
(Step 3).

```
NAUTOBOT_TOKEN=<token> uv run --project nctl nctl render hosts-intent --json
```

## Documentation

Wrote `nctl/docs/add-a-basic-service.md`: the general "declare a service" recipe (prerequisites,
`DesiredService` fields, `DesiredServicePlacement` fields, what `config` means and why `{}` is a
safe starting point) plus the concrete dnsmasq/agdnsmasq example reproduced above.

## Side finding (not fixed, out of scope for this plan)

Creating the first `DesiredService` with a non-null `intent_source` surfaced a latent nintent REST
bug: `GET /api/plugins/intent-catalog/services/` now 500s with
`ImproperlyConfigured: Could not resolve URL for hyperlinked relationship using view name
"...intentsource-detail"` — `DesiredServiceSerializer` uses `fields = "__all__"`, which
auto-generates a hyperlinked field for `intent_source`, but no `IntentSource` viewset is
registered in `nautobot_intent_catalog/api/urls.py`. This does not affect anything in this plan:
`nctl` fetches desired state exclusively via GraphQL (`sources/desired.py::DESIRED_QUERY`, which
explicitly lists fields and has no such hyperlink step) — confirmed by running the GraphQL query
directly and by the successful `render hosts-intent` above. Documented in
`add-a-basic-service.md`'s "Known gap" section as a pointer for whoever next touches nintent's API
layer; not fixed here since it's outside this plan's nctl-focused scope.
