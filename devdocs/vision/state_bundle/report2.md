# state_bundle Step 2 report — `nctl.bundle.v1` manifest + composition recipe

Status: **complete** (all stated exit criteria exercised and passed).

## What was defined

`nctl.bundle.v1` is a manifest convention plus a documented composition
recipe — no new nctl command, per the plan's scope decision (promote to
`nctl bundle` only if repetition proves painful under Easier Next Time).

Authoritative document: [`nctl/docs/state-bundle.md`](../../../nctl/docs/state-bundle.md).
It defines:

- the canonical layout: `cluster-state-<UTC timestamp>.zip` containing
  `manifest.json`, `desired.yaml` (`nctl desired export`), `drift.json`,
  `actual.json`, `relations.json` (the `--json` envelopes);
- `manifest.json` fields: `schema` (`nctl.bundle.v1`), `generated_at`,
  `nctl_git_sha`, and `contents` — one `{path, schema, generated_at}` entry
  per payload file, with per-file `generated_at` taken from each JSON file's
  own envelope header (and the export run time for the deliberately
  timestamp-free `desired.yaml`). The per-file timestamps are the honest
  record of sequential-fetch skew; no snapshot pinning, per plan;
- the exact command sequence ending in `nctl upload DIR --zip --ttl 2h`
  (the directory basename becomes the zip name), the composer writing
  `manifest.json` itself from the envelope headers;
- stop rules: a failing `desired export` (named errors) is a stop, never a
  partial bundle; an `"ok": false` view envelope must be surfaced to the
  requester; every step is read-only;
- a verification checklist (manifest parses, all four entries exist, inner
  envelope schemas match, `desired.yaml` is a batch envelope with keys
  exactly `dry_run` + `operations`).

## Where agents learn it (per plan: README command docs + cagent's surface)

- `nctl/README.md` — new Recipes entry linking `docs/state-bundle.md`.
- `nctl/docs/usage_example.md` — instruction→command rows for "export the
  desired state as a re-applyable file" and "bundle the whole cluster state
  into one downloadable file".
- `cagent/opencode/AGENTS.md` — the cluster-agent's instruction file now
  directs any "state as a file / download URL" request to follow
  `nctl/docs/state-bundle.md` exactly (and to answer desired-state-only
  requests with `nctl desired export` alone). The stale "there is no
  state-specific export command" text there and in the superproject
  `README.md` was replaced — README_DEV's breaking-change policy: no
  superseded contract left behind.

## Acceptance evidence

One bundle was produced by following the written recipe verbatim from the
superproject root (2026-08-05), then downloaded from its presigned URL,
unzipped, and checked:

- `cluster-state-20260805T052226Z.zip` (9,904 bytes) uploaded via
  `nctl upload "$DIR" --zip --ttl 2h --json` → `ok: true`, object key
  `2026-08-05/052251-967a36/cluster-state-20260805T052226Z.zip`,
  `expires_at 2026-08-05T07:22:51Z` (TTL 120 min).
- The downloaded zip contains exactly `manifest.json`, `desired.yaml`,
  `drift.json`, `actual.json`, `relations.json`.
- `manifest.json` verification passed: `schema` = `nctl.bundle.v1`,
  `nctl_git_sha` = `5cc7fe4176c11a1b4bd70ac787dc911eb04833a1`, and all four
  `contents` entries name existing files whose inner envelope schemas match
  (`nctl.desired.export.v1` / `nctl.drift.v1` / `nctl.actual.v1` /
  `nctl.relations.v1`); `desired.yaml` parsed as a batch envelope with 38
  operations (matching Step 1's live export).
- Per-file `generated_at` values span 05:22:26–05:22:28Z — the expected,
  honestly recorded sequential skew.

Evidence retained (git-ignored): `.local/state_bundle_step2/`
(`manifest.json` copy, upload URL, source dir path). No cluster or
desired-state mutation occurred; the only write was to the local MinIO
outbox bucket.

## Notes for Step 3

Step 3 sends the original Japanese request through the cagent human
entrance; the updated `cagent/opencode/AGENTS.md` is what should steer that
session to this recipe. Note the running cagent OpenCode instance reads its
working copy of `AGENTS.md` — the instance may need a restart (or at least a
fresh session) to pick up the updated instructions.
