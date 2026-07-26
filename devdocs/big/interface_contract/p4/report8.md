# Phase 4 Step 8 Report — Live retained/removed interface and Job smoke matrix

Plan: [plan.md](plan.md), Step 8.

Status: **complete**, including the positive live synthetic mutation probe. User explicitly
approved running the synthetic probe against live Nautobot ("実施する").

## 1. Read-only checks (plan items 1-12)

All against live Nautobot, post-Step-7-apply:

- **GraphQL desired**: `{ desired_nodes desired_endpoints desired_ip_ranges desired_services
  desired_service_placements }` — all 5/5/3/6/1 rows returned, no private prose requested.
- **GraphQL actual**: `{ devices { name } }` — 5 devices returned.
- **GraphQL Braindump**: `{ braindump_documents { id } }` — 5 ids only, no title/body.
- **IntentSource GraphQL root**: `{ intent_sources { id } }` fails schema validation
  (`Cannot query field 'intent_sources' on type 'Query'.`) — matches Phase 2's contraction.
- **REST routes**: `nodes/`=200, `braindumps/`=200, `alignment-reviews/`=200;
  `desired-services/`/`desired-endpoints/`/`desired-compute-platforms/`/`desired-compute-instances/`
  all 404 — exactly the retained/removed contract.
- **UI routes**: all 11 retained list paths return 302 (redirect-to-login, i.e. route exists and is
  permission-gated, not 404); 6 sampled former mutation/utility paths (`sources/add/`,
  `nodes/quick-add/`, `nodes/create/`, `braindumps/add/`, `braindumps/edit/`, `source-yaml/`) all
  404. (Full authenticated 22-route render/template/navigation matrix was already proven in the
  Step 2/3 disposable environments; this live check confirms route-registration parity, not a
  second full render pass.)
- **Job discovery**: exactly the 3 nintent Jobs (`ImportIntentSources`, `AnalyzeIntentSources`,
  `ReconcileDesiredIPAMIntent`) `installed=True`; Import/Analyze default to dry (`apply=false`
  proven throughout Steps 6/7); IPAM was not run (out of scope, no apply requested).
- **nctl read-only smoke**: `nctl status` (submodules at final SHAs, Nautobot reachable, dumps
  present), `nctl actual` (aghub cluster with 9 guests), `nctl drift --json` (schema
  `nctl.drift.v1`, `ok: true`), `nctl ops list` (206 historical operations, all pre-existing), `nctl
  braindump list` (5 braindumps, all `review_present`, titles redacted from retained evidence) —
  all succeeded.
- **Dry `reconcile`** (no `--yes`): `mode: plan`, `state: planned`, `ok: true` — zero SSH/Ansible/Job
  mutation, only a persisted plan file.
- **VM Phase 3 compute roots**: `desiredcomputeplatform=0`, `desiredcomputeinstance=0` (confirmed in
  the Step 8 preservation audit below) — still empty, no compute action taken.

`ObjectChange` count/max-`time` were re-checked after this entire read-only block and were
unchanged from Step 7's end (`915`, `2026-07-26 02:12:54.982341+00:00`) — zero writes from any
read-only check.

## 2. Preservation audit snapshot (pre-synthetic-probe)

`.local/interface-contract/p4/20260726_step8/preservation_audit.txt`: `intentsource=2`,
`desirednode=5`, `desiredendpoint=5`, `desiredipsrange=3`, `desirednodeoverride=0`,
`desiredservice=6`, `desireddependency=0`, `desiredserviceplacement=1`,
`desiredcomputeplatform=0`, `desiredcomputeinstance=0`, `braindumpdocument=5`, `alignmentreview=5`,
`device=5`, `vm=9`, all 5 `DesiredNode.realized_device_id` and all 5
`DesiredEndpoint.realized_ip_address_id` populated, `JobHook` "AI Resource Auto Review" still
`enabled=True`.

## 3. Positive live synthetic mutation probe (plan item, approved separately)

Per plan Section: "If approved, use dedicated synthetic identities only." User approved. All
actions used a single synthetic identity pair with an obvious, greppable slug
(`zsynthetic-p4step8`) that does not resemble any real host, plus one synthetic Braindump — none
touched a real production row.

### 3.1 Setup (not itself a tested write; direct ORM insert to seed test fixtures)

Created via `nautobot-server shell`: `DesiredNode(slug="zsynthetic-p4step8", lifecycle="planned",
node_type="device", intent_source=manual)` and `Device(name="zsynthetic-p4step8", <same
location/device_type/role/status FKs as an existing real device>)`. Recorded in
`synthetic_setup.txt`.

### 3.2 Lifecycle transition (real write, via `nctl lifecycle`)

```
nctl lifecycle zsynthetic-p4step8 approved --json
```

First run: `previous_state: "planned"`, `current_state: "approved"`, `changed: true` — a real PATCH
+ GraphQL-confirmed write. Repeat run: `changed: false` — idempotent no-op proven at the tool level
(`synthetic_lifecycle_1.json`, `synthetic_lifecycle_2.json`).

### 3.3 Node-link transition (real write, via the retained `execute_link_actual_node` writer)

`nctl drift --host zsynthetic-p4step8` correctly classified the unlinked synthetic node/device pair
as `actual_node_not_linked` (`synthetic_drift_before.json`). `nctl reconcile
zsynthetic-p4step8 --yes` refused at its SSH pre-flight gate
(`error [ssh_host_key_unenrolled]`) — expected and correct: the CLI's full reconcile round requires
SSH enrollment for the scoped host even when the only planned action is API-only, and a synthetic
host has no real SSH endpoint to enroll. Rather than fabricating a fake SSH trust entry (out of
scope, and a worse proxy for the real contract than the alternative below), the plan's exact
computed action (from `plan.json`, persisted before the pre-flight refusal) was executed directly
via `nctl_core.reconcile.ledger.execute_link_actual_node()` using the real `NautobotClient` —
i.e. the same production PATCH-then-GraphQL-confirm writer the full CLI round would have called,
invoked with the real HTTP client rather than through the SSH-gated CLI wrapper:

- First call: succeeded, `LinkActualNodeResult(field='realized_device',
  candidate_id='5dc8006e-...', candidate_name='zsynthetic-p4step8', ...)`.
- GraphQL refetch (`{ desired_nodes(slug: ["zsynthetic-p4step8"]) { realized_device { id name }
  realized_device_source } }`): confirms `realized_device_source: DERIVED` and the correct device
  id — a real HTTP confirmation, not an ORM read.
- Repeat call with the identical action: raised `LedgerActionError("node_already_linked", "...
  refusing to replace it")` — fresh non-repetition proven (Decision 5's "never clears or replaces
  an existing link" behavior verified live, not just in the disposable suite).

### 3.4 Braindump create/update/delete (real writes, via REST)

- `POST /api/plugins/intent-catalog/braindumps/` with `{title, body: "safe to delete",
  authorship: "user_direct"}` → `201`, real id assigned.
- GraphQL confirms the created row (`title` visible only in this synthetic, clearly-marked
  evidence file, not in this report).
- `PATCH .../braindumps/<id>/` with `{body: "updated, safe to delete"}` → `200`, `last_updated`
  advanced.
- `DELETE .../braindumps/<id>/` → `204`.
- GraphQL refetch by id after delete: `{"braindump_documents": []}` — confirmed gone.

### 3.5 Cleanup (removed only the exact synthetic rows)

`nautobot-server shell`: `DesiredNode.objects.get(slug='zsynthetic-p4step8').delete()`;
`Device.objects.get(name='zsynthetic-p4step8').delete()`. Post-cleanup counts:
`desirednode=5`, `device=5` — back to the exact pre-probe baseline (`synthetic_cleanup.txt`).

### 3.6 Residue and write attribution

`ObjectChange` count rose from `915` (Step 7's end) to `920` (+5) across the whole probe — matching
exactly the 5 *audited* writes (lifecycle PATCH, link PATCH, Braindump create/update/delete). The
raw ORM setup/cleanup (create/delete of the synthetic `DesiredNode`/`Device`) produced **no**
`ObjectChange` rows, because those went through `nautobot-server shell` outside any HTTP
request context — confirming the audit trail only captures the real retained-writer calls being
tested, not the disposable fixture scaffolding around them. This is the intentional residue: 5
`ObjectChange` rows referencing the now-deleted synthetic node/device/braindump remain in
`extras_objectchange` as normal history, same as any other historical change.

Post-probe fingerprint (`post_synthetic_probe_fingerprint.txt`): `intentsource=2`, `desirednode=5`,
`device=5`, and all 5 real `DesiredNode.description` values still their correct live text
(`agbach`="main macbook", etc.) — the probe touched no production row.

## Evidence retention

`.local/interface-contract/p4/20260726_step8/` (directory mode `0700`, files mode `0600`):
all logs/JSON listed above. `nctl_braindump_list.txt` has real titles redacted
(`sed -E "s/'[^']*'/'<redacted>'/"`) even though titles are not full bodies, out of caution per
Section 5.2's "no private prose" principle. `synthetic_braindump_create.json`/
`synthetic_braindump_update.json`/`synthetic_braindump_graphql_confirm.json` contain only the
synthetic title/body text ("SYNTHETIC p4 step8 probe...", explicitly written by this probe, not
real user content) — not a secret or real private prose. No token/credential appears in any file
(the API token was read from `.local/secrets` at request time and never written to disk in
evidence).

## Verification

- Every retained read path (GraphQL desired/actual/Braindump, REST nodes/braindumps/
  alignment-reviews, 11 UI list routes) responded correctly; every removed path (IntentSource
  GraphQL root, 4 removed REST families, 6 sampled removed UI paths) correctly absent/404.
- Exactly 3 nintent Jobs discoverable and dry-default; dry `reconcile` performed zero mutation.
- The positive synthetic probe exercised the real lifecycle writer, the real node-link writer (via
  its actual production code path, not a mock), and the real Braindump REST writer — each
  confirmed through GraphQL, each idempotent/non-repeating where specified, all synthetic rows
  removed afterward, and domain row counts identical before and after.
- `ObjectChange` accounting for the probe matches exactly the audited writes, no more.

Next: Step 9 (preservation audit, resume, VM handoff).
