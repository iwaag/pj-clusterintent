# Phase 4 Step 6 Report — Run the official live YAML preview and obtain apply approval

Plan: [plan.md](plan.md), Step 6.

Status: **halted, not complete**. The official `apply=false` `Import Intent Sources` preview was
run against live Nautobot and independently verified zero-write, but it surfaced an unauthorized
field-clearing side effect not named anywhere in Phase 0's disposition ledger. Per plan Section 6
Step 6 ("any... unexplained field update stops before apply and requires a new user decision") and
Section 5.3, apply approval was not requested. Recorded as
[problem.md](problem.md) "Phase 4 Step 6 — Open Problem" for an explicit user decision.

## 0. Approval

Before starting: approval to run the live `apply=false` preview ("Yes, run the preview"), per this
project's live-action pause convention (plan Section 3.4 lists read-only GraphQL/REST as
pre-approved, but a live Job run is Job execution against production, so approval was sought
explicitly).

## 1. Pre-preview fingerprint (plan item, gate precondition)

`.local/interface-contract/p4/20260726_step6/pre_preview_fingerprint.txt`:

| Check | Value |
|---|---:|
| `intentsource` | 2 |
| `desirednode` | 5 |
| `desiredendpoint` | 5 |
| `desiredipsrange` | 3 |
| `desiredcomputeplatform` | 0 |
| `desiredcomputeinstance` | 0 |
| `desiredservice` | 6 |
| `desiredserviceplacement` | 1 |
| `desirednodeoverride` | 0 |
| `objectchange` total | 898 |
| `objectchange` max `time` | 2026-07-25 18:57:17.841395+00:00 |
| active/pending `JobResult` | 0 |
| `device` | 5 |

Matches Section 5.3's 22-row identity hypothesis exactly (2+5+5+3+0+0+6+1+0 = 22). Per-row field
digests for all 22 rows plus the one `JobHook` (`AI Resource Auto Review`, enabled) were also
recorded in `pre_preview_row_digests.txt` for later comparison.

## 2. Running the preview (plan item 1)

`nautobot-server nbshell` required `--command` (not `-c`, which collides with the CLI's own global
`-c/--config-path` flag and silently swallows the script as a config path — discovered via a failed
`FileNotFoundError` with the script text embedded as the "path"). Ran:

```
nautobot-server runjob -u admin -d '{"source_file": "", "apply": false}' \
  nautobot_intent_catalog.jobs.ImportIntentSources
```

Log summary (`import_preview_run.log`): `SUCCESS`, "Intent source import preview summary:
{"conflict": 0, "create": 0, "unchanged": 9, "update": 13}". Not the expected all-unchanged result.

## 3. Artifact capture and schema verification (plan item 2)

The Job's `FileAttachment` (`intent-import-result.json`) required `bytes(fa.bytes).decode()` (the
field returns a `memoryview`) and its content is base64-encoded text; both steps are recorded so
the extraction is reproducible. Decoded artifact saved to
`.local/interface-contract/p4/20260726_step6/intent-import-result.json`.

- `schema_version`: `nintent.intent-import.v1` — matches plan Section 6 Step 6 item 2.
- `mode`: `preview`.
- `source.resolved_path`: `/opt/nautobot/intent_sources.yaml`; `source.sha256`:
  `598391e0...455b` — identical to Step 5's per-container YAML digest.
- `totals`: `{"conflict": 0, "create": 0, "unchanged": 9, "update": 13}`.
- `confirmation.status`: `not_applicable` (expected for `apply=false`).
- `writes`: `{"attempted": false, "committed": false, "requested": false}`.
- `transaction.status`: `not_requested`.
- `errors`: `[]`; `conflicts`: `[]`.

## 4. Independent zero-write proof (plan item 3)

`.local/interface-contract/p4/20260726_step6/post_preview_fingerprint.txt`:

| Check | Before | After |
|---|---:|---:|
| `objectchange` total | 898 | 898 |
| `objectchange` max `time` | 2026-07-25 18:57:17... | 2026-07-25 18:57:17... (unchanged) |
| `intentsource` | 2 | 2 |
| `desirednode` | 5 | 5 |
| `agbach.description` (live) | "main macbook" | "main macbook" (unchanged) |

No row count, `ObjectChange` count, or sampled field value changed. The preview's own `writes`/
`transaction` block plus this independent DB recheck together satisfy the zero-write requirement
regardless of what the preview *proposes*.

## 5. Comparing the 13 proposed updates against Phase 0's disposition ledger (plan items 4-6)

Full per-field diff extracted from the artifact:

| Model | Identity | Field | Old | New | Disposition |
|---|---|---|---|---|---|
| IntentSource | infrastructure | `source_config` | `{}` | computed catalog/basic-file-path defaults | benign: populates a previously-empty JSON default, nothing existing lost |
| IntentSource | manual | `source_config` | `{}` | same computed defaults | benign, same reasoning |
| DesiredNode | agbach | `description` | "main macbook" | `null` | **unauthorized — real content erased** |
| DesiredNode | agbach | `notes` | `""` | `null` | cosmetic (empty either way) |
| DesiredNode | agdnsmasq | `description` | "dnsmasq should be running on VE or light PC" | `null` | **unauthorized — real content erased** |
| DesiredNode | agdnsmasq | `notes` | `""` | `null` | cosmetic |
| DesiredNode | aghub | `description` | "proxmox VE mini pc" | `null` | **unauthorized — real content erased** |
| DesiredNode | aghub | `notes` | `""` | `null` | cosmetic |
| DesiredNode | agpc | `description` | "powerful ubuntu with graphic card" | `null` | **unauthorized — real content erased** |
| DesiredNode | agpc | `notes` | `""` | `null` | cosmetic |
| DesiredNode | agstudio | `description` | "powerful mac studio" | `null` | **unauthorized — real content erased** |
| DesiredNode | agstudio | `notes` | `""` | `null` | cosmetic |
| DesiredEndpoint | agdnsmasq/primary/primary | `description` | `""` | `null` | cosmetic |
| DesiredEndpoint | agpc/primary/primary | `description` | `""` | `null` | cosmetic |
| DesiredEndpoint | agstudio/primary/primary | `description` | `""` | `null` | cosmetic |
| DesiredIPRange | dhcp-reserved | `description` | `""` | `null` | cosmetic |
| DesiredIPRange | dhcp-unreserved | `description` | `""` | `null` | cosmetic |
| DesiredIPRange | network-infra | `description` | `""` | `null` | cosmetic |

Root cause traced to source: `nauto/seed/intent_sources.yaml` has never carried a `description` or
`notes` key on any `desired_nodes`/`desired_endpoints`/`desired_ip_ranges` row (confirmed by
reading the checked-in file directly), while `desired_node_update_fields()`
(`nintent/nautobot_intent_catalog/importers.py:321-331`) excludes only `lifecycle` from the fields
Import may overwrite on an existing `DesiredNode` — `description`/`notes` are always in the
writable set, and `DesiredEndpoint`/`DesiredIPRange` exclude nothing at all.

Phase 0's disposition ledger (`p0/report7.md`, "Ownership rules frozen") names only: `lifecycle`
(create-only, nctl-owned thereafter) and, separately, `DesiredService`
`lifecycle`/`requirements`/`notes` (analysis-owned, preserved on re-import). It says nothing about
`DesiredNode`/`DesiredEndpoint`/`DesiredIPRange` `description`/`notes` being an authorized
overwrite target. The 5 `DesiredNode.description` updates are therefore an unexplained field update
under plan Section 6 Step 6's stop condition.

## 6. Gate disposition

Per plan Section 6 Step 6 ("Gate: only the exact reviewed plan is authorized. Any changed
live/YAML ownership fact stops the phase before mutation.") and Section 9.1 ("If... live baseline
classification fails: do not run a live Job [further]... fix the implementation and restart at the
failed gate; report `partially complete`"):

- Apply approval was **not** requested.
- No `apply=true` run occurred.
- The finding is filed in `problem.md` with four candidate resolutions (add
  `description`/`notes` to the YAML; exclude them from Import's writable set; approve the clearing
  as intentional; or a narrower preserve-`DesiredNode`-only variant) for the user to choose from.
- Live state is unchanged from Step 5's end (`ObjectChange` total still 898, no new
  `JobResult` beyond the completed preview run itself — `JobResult` count check below).

## 7. Job/queue recheck after the preview run

```
active/pending JobResult after preview: 0
```

The preview `JobResult` itself completed (`SUCCESS`); no other Job was triggered.

## What Step 6 does not close

- No apply approval was requested or given.
- The 13-update preview is not yet resolved to an all-unchanged or fully-authorized state.
- Step 7 (apply/refetch/repeat) cannot start until this is resolved and Step 6 is re-run to a clean
  gate.

## Evidence retention

`.local/interface-contract/p4/20260726_step6/` (directory mode `0700`, files mode `0600`):
`pre_preview_fingerprint.txt`, `pre_preview_row_digests.txt`, `import_preview_run.log`,
`intent-import-result.json`, `post_preview_fingerprint.txt`. No token, credential, private prose,
or raw `ObjectChange` payload appears — only aggregate counts, the artifact's own field-diff
content (all non-secret domain data), and public hashes. Not committed (matches Section 5.5).

## Verification

- Preview artifact schema is `nintent.intent-import.v1`; `writes`/`transaction` blocks both report
  no write attempted/committed.
- Independent pre/post `ObjectChange` count and max `time` are identical (898,
  2026-07-25T18:57:17.841395Z).
- Independent pre/post row counts for all 9 canonical roots are identical.
- A sampled live field (`agbach.description`) is confirmed unchanged after the preview.
- Every one of the 13 proposed updates was individually classified against Phase 0's frozen
  ownership rules; 5 are confirmed unauthorized data loss, 8 are cosmetic, 2 are benign.
- `JobResult` active/pending count is 0 before and after.

Next: resolve the `problem.md` decision, then re-run Step 6 to a clean all-unchanged (or
fully-authorized) preview before requesting apply approval.
