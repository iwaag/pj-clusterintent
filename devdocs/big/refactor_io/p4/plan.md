# Phase 4 Plan — Remove Private Desired State from Git

Status: **planned** (implementation not started).

Input: [`../roadmap.md`](../roadmap.md) Phase 4, [`../p3/plan.md`](../p3/plan.md) and
[`../p3/report5.md`](../p3/report5.md). Phase 3 already made
`POST /api/plugins/intent-catalog/desired-state/batch/` the only desired-state writer and deleted
the Import Job and the loader stack. Nothing in nintent reads `intent_sources.yaml` any more —
only the build and the documentation still do.

## Goal

A fresh checkout of this superproject contains no real cluster desired state. The scratch database
keeps the current desired state, and an operator updates it from a private local document with
`nctl desired apply` without touching Git.

## Scope

In scope:

- Delete `nauto/seed/intent_sources.yaml` and the `devenv/nautobot/Dockerfile` lines that bake it
  into the image.
- Remove real cluster identifiers, addresses, and MACs from committed tests, fixtures, and docs
  where they describe desired state.
- Rewrite the nauto and nctl documents that still instruct the reader to edit the seed file.
- Document the private-file operator workflow.
- One coordinated rebuild proving the image no longer needs the file.

Out of scope: `nauto/seed/home_cluster.yaml` and `nauto/seed/nodeutils_ingest.yaml` (reusable
prerequisites and ingest policy — both stay); the narrative documentation rewrite and the final
end-to-end verification (Phase 5); anything under `devdocs/` (historical records, left as written).

## Design decisions

Everything else — wording, fixture naming, file layout — is the implementer's choice.

### 1. The private document is the operator's input, not a backup

`.local/desired-state.yaml` (already ignored) is the working copy an operator edits and submits.
It is not authoritative and is not kept in sync automatically. The database is authoritative;
`.local/backups/` PostgreSQL dumps are the recovery path.

Do **not** add an `nctl desired export` command in this phase. If a repopulation source is ever
lost, GraphQL plus a dump is enough for this scratch environment.

### 2. Synthetic replacements must use documentation ranges

When a committed test or doc needs an address or MAC, use `192.0.2.0/24` / `198.51.100.0/24` and
`aa:bb:cc:*`-style MACs with example hostnames, as most of the nctl suite already does. Do not
invent a second real-looking cluster.

### 3. Actual-state ingest fixtures are a judgment call, not a mandate

`nauto/tests/test_proxmox_*.py`, `test_ip_namespace_host_identity.py`,
`test_nodeutils_ingest_batch.py`, and `nodeutils/tests/` carry real node names because they
reproduce observed Proxmox/nodeutils payloads. That is actual state, not desired state, so the
roadmap does not require changing them. Rename where it is a mechanical string swap that keeps the
test meaningful; leave the rest and say which ones you left in the report.

## Steps

One commit and one short report entry per step.

### Step 1 — Prove the private document still round-trips

`nauto/seed/intent_sources.yaml` changed after the Phase 3 Step 2 export (nauto `000c0bf`,
`f411f4f`). Before deleting anything:

1. Copy `.local/desired-state.yaml` to `.local/backups/` and take a `pg_dump` of the scratch
   database.
2. `uv run --project nctl nctl desired apply -f .local/desired-state.yaml` (dry) against the live
   deployment.
3. Every operation must report `unchanged`. Any `create`/`update`/`conflict` means the local
   document has drifted from the database — fix the local document (not the database) and repeat.

This is the gate for the whole phase: the deletions in Step 2 are only safe once a verified
repopulation document exists.

### Step 2 — Delete the seed file and its build path

- `git rm nauto/seed/intent_sources.yaml` (nauto submodule commit).
- Remove the `COPY nauto/seed/intent_sources.yaml …` and the following `sha256sum` line from
  `devenv/nautobot/Dockerfile`, along with the comment paragraph above them. Leave the
  `NINTENT_COMMIT`/`NAUTO_COMMIT` pins and `build_info.json` alone.
- `nauto/README.md`: drop the "retained only until Phase 4" note, the `Analyze Intent Sources` /
  `seed/intent_sources.yaml` paragraph, and the `editor seed/intent_sources.yaml` configuration
  block. Replace the last one with a one-line pointer to the batch endpoint.
- `nctl/docs/register-a-new-pc.md` and `nctl/docs/add-a-basic-service.md`: replace the
  "edit `nauto/seed/intent_sources.yaml`" instructions with the `nctl desired apply` flow and the
  batch operation shape.
- Grep the working tree for `intent_sources` and `/opt/nautobot/intent_sources` and confirm the
  only survivors are `devdocs/` and `nauto/tests/test_seed_home_cluster_ownership.py` (which
  asserts the seed Job does *not* touch intent sources — keep it).

### Step 3 — Sanitize committed desired data

- `nctl/tests/fixtures/compute_conformance.json`: real MAC `bc:24:11:23:dc:b7`, real platform and
  guest names, real VMIDs. Regenerate or rewrite with synthetic values. This fixture is
  owner-generated — the compute conformance gate compares it against the nintent side, so
  regenerate both sides rather than hand-editing one.
- `nctl/tests/test_sources_actual.py`: the `aghub-proxmox` / `agdnsmasq` / VMID-108 rows.
- Anything else surfaced by `git grep -niE 'agbach|aghub|agdnsmasq|agfixture|agstudio|agpc'` and
  `git grep -niE '([0-9a-f]{2}:){5}[0-9a-f]{2}|192\.168\.'` outside `devdocs/` — decide per hit
  under Decision 3 and record the decisions.
- `devenv/nautobot/docker-compose.yml` names a real host in `NAUTOBOT_ALLOWED_HOSTS`, and
  `README_DEV.md` line 87 names one narratively. These are local-environment facts, not desired
  state; change or keep them as you judge, and say which you chose.

### Step 4 — Document the operator workflow

A short section in `README.md` (and a pointer from `nauto/README.md`), roughly:

```bash
# preview, then commit
uv run --project nctl nctl desired apply -f .local/desired-state.yaml
uv run --project nctl nctl desired apply -f .local/desired-state.yaml --yes
# or from stdin
… | uv run --project nctl nctl desired apply -f - --yes
```

State the ownership line explicitly: database = current desired state, batch REST = the only
writer, GraphQL = the reader, Git = framework and policy. Note in `.local/localenv_memo.md` where
the private document lives and that it is an input, not a backup.

Phase 5 owns the full narrative rewrite; keep this to what an operator needs today.

### Step 5 — Rebuild proof (live)

Pause and report before this step. Commit `nauto`, `nctl`, and the superproject first, then ask the
user to push `nauto` (and `nctl` if changed).

1. Bump `NAUTO_COMMIT` in `devenv/nautobot/Dockerfile` to the pushed nauto commit.
2. `cd devenv/nautobot && docker compose --env-file ../.env build --no-cache`, then
   `docker compose --env-file ../.env up -d` and
   `docker exec nautobot-nautobot-1 nautobot-server post_upgrade`.
3. `docker exec nautobot-nautobot-1 ls /opt/nautobot/intent_sources.yaml` must fail.
4. GraphQL returns the same desired node/endpoint/platform/instance/service set as before the
   rebuild — the rebuild does not touch the database, and that is the point being proved.
5. `uv run --project nctl nctl drift --json` still returns `ok: true`.
6. Re-run Step 1's dry apply: still all `unchanged`, now with no file in the image.

Record the result in `p4/report5.md` and close the phase.

## Gates

| gate | working directory | command |
|---|---|---|
| nauto ordinary | `nauto` | `python3 -m unittest discover -s tests` |
| nctl ordinary | `nctl` | `uv run pytest -q --durations=20` |
| nintent Django-free fast | `nintent` | `python3 -m unittest discover -s nautobot_intent_catalog/tests` |
| compute conformance | superproject root | `uv run --project nctl pytest -q devtests/test_strategy/test_compute_conformance.py` |
| Nautobot runtime clean | superproject root | `./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean` |

The nintent Django-free suite's expected skip count (currently 14 in `README_DEV.md`) may include
file-location skips tied to the removed seed path; update the number if it moves.

## Prohibitions

Only these:

1. Do not delete `nauto/seed/intent_sources.yaml` before Step 1's dry apply reports every operation
   `unchanged` and a backup of `.local/desired-state.yaml` exists.
2. Do not commit real cluster addresses, MACs, or desired rows as "synthetic" replacements.
3. Do not reintroduce a file-based or Git-based desired-state input path to work around the
   deletion.
4. Do not modify the database in this phase except through the batch endpoint.

Everything else is at the implementer's discretion.

## Exit criteria

- `nauto/seed/intent_sources.yaml` is gone; the Dockerfile no longer copies it; the rebuilt image
  does not contain it and starts healthy.
- `git grep` outside `devdocs/` finds no real cluster desired row, address, or MAC.
- `home_cluster.yaml` and `nodeutils_ingest.yaml` are unchanged and still work.
- An operator can preview and apply a desired-state change from a private local file with no Git
  commit, and the workflow is written down.
- All gates pass and every worktree is clean.

## Known risks

- **Losing the only repopulation source.** `.local/desired-state.yaml` becomes the sole file-shaped
  copy of real desired state once the seed is deleted. Step 1's backup is mandatory.
- **Stale local document.** The seed file moved twice since the Phase 3 export; the Step 1 dry run
  is what catches that, so do not skip it because Phase 3 already passed it.
- **Conformance fixture drift.** `compute_conformance.json` is generated on the nintent side.
  Editing only the nctl copy will pass locally and fail the conformance gate.
- **Build cache pinning a stale commit.** Build with `--no-cache` and confirm the resolved nintent
  SHA in the log, as in Phase 3.
