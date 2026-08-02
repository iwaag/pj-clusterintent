# nauto Custom Field Minimization — Implementation Plan

Companion to [suggestion.md](suggestion.md). Experimental environment; no
backward compatibility required. Destructive steps are fine — just follow
the step order so raw observation data is preserved before columns that
duplicate it get deleted.

Scope note: the GUI replacement panel (TemplateExtension in nintent) is
out of scope for now. Removed columns' data still lives in
`inventory_raw_json`; it will just be less convenient to read until/unless
a display layer is built later. Some short-term GUI ugliness is accepted.

## Hard constraints (keep these, everything else is implementer's judgment)

- Never touch the 9 `ACTUAL_FACT_FIELDS` columns
  (`nctl/src/nctl_core/sources/actual.py:91-101`): `host_system`,
  `primary_ip_address`, `primary_mac_address`, `network_interface`,
  `last_seen`, `inventory_source`, `observed_services`,
  `service_inventory_updated_at`, `observed_workspaces`.
- nctl must not start reading `inventory_raw_json`
  (documented policy, `devdocs/big/vm/roadmap.md`).
- Do not touch the `proxmox_*` fields — they already follow the allowlist
  policy and are out of scope.

## Key facts discovered during planning (read before coding)

1. **`inventory_raw_json` is currently incomplete.** The ingest job
   (`nauto/jobs/ingest_nodeutils_inventory.py`, `build_custom_fields`,
   ~line 657) stores `identity` and `facts.{hardware,gpu,disk,network,
   software,services,workspaces}` — but NOT `facts.cpu`, `facts.memory`,
   `os_name`, `os_version`, `kernel_version`, `architecture`, `system`.
   Deleting the individual columns without first widening the raw blob
   loses OS/CPU/memory data. Simplest fix: store the whole `facts` dict
   (plus `identity`) instead of cherry-picking keys.

2. **The seed job only upserts, never prunes.** `ensure_custom_fields`
   (`nauto/jobs/seed_home_cluster.py:291`) does get-or-create; removing
   an entry from `seed/home_cluster.yaml` does NOT delete the
   CustomField from the live DB. Deletion needs an explicit step:
   either a small prune block in the seed job (delete CustomFields with
   `dcim.device` content type whose key is not in the YAML — careful to
   scope it so it never touches `proxmox_*` or fields owned by other
   apps), or a one-off `nautobot-server nbshell` command. Deleting a
   `CustomField` object cascades: Nautobot strips the key from every
   device's `_custom_field_data`, so no per-device cleanup is needed.

3. **AI review is fully isolated.** `nauto/jobs/ai_resource_review.py`
   is a JobHookReceiver registered in `nauto/jobs/__init__.py`; its four
   output fields plus its inputs `ai_resource_summary` /
   `agent_task_state` are referenced nowhere in nctl or nintent. The Job
   Hook itself was configured manually in the Nautobot admin UI — delete
   that hook first, then the code, or the hook will error on the next
   device update.

4. **`serial_number` custom field is redundant** — the ingest job writes
   the same value to the native `Device.serial` field (~line 594).
   Safe deletion candidate regardless of other decisions.

5. **Deployment loop**: nauto changes reach Nautobot via Git Repository
   sync, then re-run `Seed Home Cluster` and `Ingest Nodeutils
   Inventory`.

## Steps

Follow the usual per-step rhythm: report + commit per step; pause for
user approval before live (deployed-cluster) actions.

### Step 0 — Freeze the deletion list (with user)

Present the ~26 unreferenced columns to the user, column by column, and
confirm which (if any) are still wanted for list filtering/sorting.
Proposed default: delete all of them, i.e. keep only the 9 allowlist
fields + `owner`/`purpose` only if the user says so. Record the frozen
list in `report.md`. AI-review fields (`ai_resource_review*`,
`ai_resource_summary`, `agent_task_state`) are already decided: delete.

### Step 1 — Widen `inventory_raw_json`

In `build_custom_fields`, store the full `facts` dict + `identity`
(drop the cherry-picking). Update ingest tests. This must land and be
live-verified before any column deletion so no observation data is lost.

### Step 2 — Retire the AI review feature

- Live: delete the Job Hook in the Nautobot admin UI (user action or
  guided).
- Code: delete `nauto/jobs/ai_resource_review.py`, its registration in
  `jobs/__init__.py`, its tests, its README section, and the
  `AI_RESOURCE_REVIEW_*` env vars wherever the deployment sets them.
- Also remove `make_ai_resource_summary` and the `ai_resource_summary` /
  `agent_task_state` writes from the ingest job.

### Step 3 — Delete the frozen column list

- Remove entries from `nauto/seed/home_cluster.yaml` and the
  corresponding writes in `build_custom_fields`.
- Add the prune mechanism (fact 2) and run it live, or delete the
  CustomField rows via nbshell. Verify in the GUI that the Device page
  no longer shows the removed rows and that the 9 allowlist fields
  survived.
- Re-run ingest against a real report to confirm a clean pass.

### Step 4 — Docs + close-out

Update `nauto/README.md` (field list, remove AI-review section),
`README_DEV.md` if it mentions the deleted fields, and write the final
`report.md`.

## Notes

- Test suites to run: nauto job tests, nctl full suite (should be
  untouched — treat any failure as a scope violation).
