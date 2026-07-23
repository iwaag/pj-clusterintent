# Permission Fix Step 7 Report: Live Control-Loop Proof

Date: 2026-07-23

## Status

**Complete. `aghub` is converged through the supported nctl workflow.**

## Dry plan

```bash
uv run --project nctl nctl reconcile aghub --refresh-observation
```

Operation `01KY7HXEN5HFBMKQB6N4ZNY15B`:

- `scope: aghub`
- `ssh_preflight: ready=[aghub]`
- `plan.json` contains exactly one action, `observe_node`, with `evidence.forced_refresh: true`
- `unsupported: []`
- no writes (plan mode)

## Apply

```bash
uv run --project nctl nctl reconcile aghub --refresh-observation --yes
```

Operation `01KY7HYJR07G52HHRA8YDDRQNS`:

```text
state: converged
ssh_preflight: ready=[aghub]
round 0: 2 action(s)
    [ok] observe_node
    [ok] regenerate_production_inventory
round 1: 3 action(s)
    [ok] link_actual_node:aghub
    [ok] observe_node
    [ok] regenerate_production_inventory
ok: True
```

Round 1 re-ran `observe_node` because linking the newly observed node to the desired `aghub`
target changed the drift picture enough to warrant one more pass before declaring convergence —
this is the normal multi-round reconcile behavior, not a repeat of the forced refresh (the forced
refresh itself only applies once, in round 0, per the `--refresh-observation` contract already
verified in `report1.md`/`report2.md`).

### Evidence checked against the plan's required list

1. **Helper preflight executed for aghub** — inherited from Step 6's live role application;
   confirmed again implicitly since collection succeeded (a missing/broken helper would have
   raised `ProxmoxInventoryError` and failed the `observe_node` action).
2. **nodeutils collection executed as `nodeutils_user`** — both `collection_started` events show
   `hosts: ["aghub"]`; the post-collection ownership assertions added in Step 3 (which now run on
   every collection) passed both times (no action failure reported).
3. **At least one allowlisted `pvesh` call executed through the helper** — confirmed by the
   resulting report content (below) and by Step 6's direct verification of the same collection
   path against the same pinned SHA.
4. **A fresh schema-v2 report was written** — `/var/lib/nodeutils/inventory.json` on `aghub`
   (verified content in Step 6) is `nodeutils.inventory.v2`.
5. **nctl retrieved and validated the report; controller cache atomically updated** —
   `observation_completed: {"ok": true}` fired twice (once per round), with no `DumpError` in
   either event log.
6. **The Nautobot ingest Job reached `success`** — both `Ingest Nodeutils Inventory` Jobs
   (`f106f4a9...` and `bed29efc...`) polled from `pending` to `success` and completed with an
   artifact (`nodeutils-ingest-summary.json`).
7. **The observation action recorded `collected=true` and the pinned SHA** —
   `collection_started` events both show `nodeutils_version:
   36e1c5752ba895780eea21b8e994926b93cc1c53`, which is the exact `nodeutils` gitlink recorded by
   the superproject `HEAD` at the time of this run (the Step 5 test-only commit; matches
   `resolve_nodeutils_version()`'s output confirmed in `report4`-equivalent Step 4 verification).
8. **Production inventory regeneration used the resulting actual state** —
   `regenerate_production_inventory` succeeded in both rounds, after `link_actual_node:aghub` in
   round 1.
9. **Fresh drift no longer reports the original missing-realization errors** — see below.
10. **The next normal reconcile does not repeat `observe_node`** — see below.

## Fresh drift after apply

`round-01/drift-final.json` from the apply operation:

```text
summary: {"converged": 4, "unknown": 2}
severity_summary: {"error": 3, "warning": 1, "info": 5}

aghub:      converged  (only info: intent_effect_summary)
agpc:       converged
agstudio:   converged
agdnsmasq:  converged  (one warning: missing_actual_ip_address, pre-existing/unrelated)
agbach:     unknown    (error: stale_actual_data -- known-unreachable host per .local/localenv_memo.md, unrelated)
dnsmasq:    unknown    (errors: service_config_mismatch, service_observation_stale -- unrelated service target, not a node)
```

`aghub` now has **zero** error- or warning-severity findings. The three original findings from
`problem.md` (`no_realized_object`, `no_realized_device`, `missing_actual_node`) are gone —
replaced by convergence, not by a different unresolved error. The remaining cluster-wide `error`
entries (`agbach`, `dnsmasq`) are pre-existing and unrelated to Proxmox/`pvesh`; per the plan, this
report claims only the `aghub` Proxmox observation transition, not whole-cluster convergence.

## No-repeat round

```bash
uv run --project nctl nctl reconcile aghub
```

Operation `01KY7J2GV0W7ZDVB9P801NKMK0`: `scope summary: converged=1`, `plan.json` actions: `[]`.

```bash
uv run --project nctl nctl drift --host aghub --json
```

`summary: {"converged": 1}`, `severity_summary: {"error": 0, "warning": 0, "info": 1}`.

A normal (non-forced) reconcile plans zero actions for `aghub`, and drift reports it fully
converged with no residual error or warning — the supported control loop is proven end-to-end.

## Not yet done (subsequent step)

- Step 8 (ownership and repeatability proof): compare `/opt/nodeutils`, `.venv`, `/var/lib/nodeutils`,
  and `inventory.json` before/after, and confirm a second `uv sync --frozen` and a second
  collection succeed without ownership repair.
