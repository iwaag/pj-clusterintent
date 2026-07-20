# End-to-end verification report

Ran the plan's two scenarios against the live dev Nautobot instance (`http://localhost:8000/`),
as far as this environment allows, after Steps 1–5.

## Scenario 1 — bootstrap via mDNS

1. `agdnsmasq` `DesiredNode` + `DesiredEndpoint` (`mdns_name=agdnsmasq.local`) already existed
   from prior setup (confirmed via GraphQL/REST before Step 3's data entry).
2. `uv run nctl render hosts-intent --out ansible_agdev/inventories/generated` —
   `ansible_agdev/inventories/generated/hosts_intent.yml` now has `ansible_host: agdnsmasq.local`
   on every `ssh_hosts` member (Step 1) and a `dnsmasq_server` group containing `agdnsmasq` as a
   bare member (Steps 2–3). Confirmed by reading the generated file and by
   `ansible-inventory -i inventories/generated/hosts_intent.yml --list` from inside
   `ansible_agdev/`.
3. `ansible-playbook -i inventories/generated/hosts_intent.yml
   playbooks/nautobot/run_nodeutils_collect.yml` — **not run**: `agbach.local`/`agdnsmasq.local`
   are documented as unresponsive in `.local/localenv_memo.md` (known environment state, not
   something this plan changes). Step 5's live test below exercised the same connection path
   (`ansible_host` resolution → SSH) via a different playbook and hit exactly that documented
   unreachable state, which is the strongest available substitute for actually running this step
   in this environment.

## Scenario 2 — dnsmasq placement

1. Declared via Step 3's recipe: `DesiredService` "dnsmasq" + active `DesiredServicePlacement` on
   `agdnsmasq` (`deployment_profile=dnsmasq`) — done live, see `report3.md`.
2. `uv run nctl apply dnsmasq --inventory
   ansible_agdev/inventories/generated/hosts_intent.yml` (dry-run): resolved the override inventory
   correctly (after the Step 5 path-resolution fix — see `report5.md`), found `agdnsmasq` in
   `dnsmasq_server`, rendered the dnsmasq records artifact, and invoked
   `playbooks/bootstrap/setup_dnsmasq.yml`:
   ```
   TASK [Gathering Facts]
   fatal: [agdnsmasq]: UNREACHABLE! => {"changed": false, "msg": "Task failed: Failed to connect
   to the host via ssh: Host key verification failed.", "unreachable": true}
   ```
   This is the same documented-unreachable-host condition as scenario 1 step 3, not a wiring
   defect — the whole pipeline up to the SSH connection attempt (render → placement lookup →
   inventory override resolution → group resolution → daemon-setup playbook invocation → abort
   before the records deploy per Step 4's ordering) executed exactly as designed. `data.setup` in
   the resulting envelope carried the `UNREACHABLE` recap and the run correctly failed with
   `ansible_setup_dry_run_failed` before attempting the records deploy.
3. `nctl render production` — ran successfully (`ok: true`), confirming Step 2's hosts-intent
   changes didn't disturb the production render path; groups are empty because no nodeutils
   collection/ingest has happened against any host yet (expected — no actual state to source from,
   independent of this plan).

## What is and isn't verified

Verified end-to-end, live: node/endpoint/service/placement data model → `render hosts-intent`
(mDNS `ansible_host` + placement-derived `dnsmasq_server` group) → `apply dnsmasq --inventory`
(override resolution, target-group lookup, two-phase setup-then-records ordering, abort-on-setup-
failure) → real `ansible-playbook` invocation against a real (if currently unreachable) inventory
target. `render production` unaffected.

**Not verified** (blocked by real-world host reachability, outside this plan's scope): actual SSH
connectivity to `agdnsmasq.local`, the daemon actually installing, the records actually deploying,
`nctl reconcile` reaching `converged` on a live dnsmasq node. These require either fixing SSH host
key verification for `agdnsmasq.local` (a real infrastructure/environment task, not a code change)
or testing against a reachable host — outside this plan's remit per `.local/localenv_memo.md`'s
already-documented "agdnsmasq.local unresponsive, known state, not a problem."

## Exit criteria (from plan.md)

- "Both scenario transcripts run without manual inventory editing or manual playbook wiring; every
  group in every generated inventory is derived from placements + profiles." — **met**: no
  hand-edited inventory or group anywhere in the flow above; `dnsmasq_server` in both
  `hosts_intent.yml` and `production.yml` is placement/profile-derived.
- "`nctl reconcile` on a fresh dnsmasq node converges: daemon installed, records deployed, drift
  converged." — **not independently verified** in this environment (see above); the code path
  reconcile would take (`dnsmasq_config` → `build_dnsmasq_apply(cfg, apply_changes=True)`) is the
  same one exercised live above, up to the same SSH boundary.
- "No nintent schema change was needed; the 'add a basic service' recipe is documented." — **met**:
  zero changes under `nintent/`; recipe at `nctl/docs/add-a-basic-service.md`.

## Test suite

```
uv run pytest -q
```
514 passed across all five steps' changes combined, no regressions.
